"""Tests for the Deribit option chain loader."""

import os
from collections.abc import Callable
from typing import Any

import numpy as np
import pytest
import requests

from qmath.datasets import _deribit, load_deribit_chain

DAY_MS = 86400 * 1000
NOW_MS = 1_757_700_000_000
BTC_USD = 77_000.0


def _instrument(
    name: str, strike: float, expiry_ms: int, kind: str
) -> dict[str, Any]:
    return {
        "instrument_name": name,
        "strike": strike,
        "expiration_timestamp": expiry_ms,
        "option_type": kind,
        "quote_currency": "BTC",
    }


def _summary(
    name: str,
    bid: float | None,
    ask: float | None,
    underlying: float = BTC_USD,
) -> dict[str, Any]:
    return {
        "instrument_name": name,
        "bid_price": bid,
        "ask_price": ask,
        "underlying_price": underlying,
        "estimated_delivery_price": BTC_USD,
        "creation_timestamp": NOW_MS,
        "mark_iv": 50.0,
    }


NEAR = NOW_MS + 7 * DAY_MS
FAR = NOW_MS + 30 * DAY_MS

INSTRUMENTS = [
    _instrument("BTC-NEAR-70000-C", 70_000, NEAR, "call"),
    _instrument("BTC-NEAR-80000-C", 80_000, NEAR, "call"),
    _instrument("BTC-NEAR-90000-C", 90_000, NEAR, "call"),
    _instrument("BTC-NEAR-80000-P", 80_000, NEAR, "put"),
    _instrument("BTC-FAR-80000-C", 80_000, FAR, "call"),
    _instrument("BTC-FAR-80000-P", 80_000, FAR, "put"),
]

SUMMARIES = [
    _summary("BTC-NEAR-90000-C", 0.001, 0.002),
    _summary("BTC-NEAR-70000-C", 0.10, 0.11),
    _summary("BTC-NEAR-80000-C", 0.02, 0.025),
    _summary("BTC-NEAR-80000-P", 0.05, 0.055),
    _summary("BTC-FAR-80000-C", 0.04, 0.045, underlying=78_000.0),
    _summary("BTC-FAR-80000-P", 0.06, 0.065, underlying=78_000.0),
]


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, payload: dict[str, Any], status: int = 200) -> None:
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error")

    def json(self) -> dict[str, Any]:
        return self._payload


def _install_api(
    monkeypatch: pytest.MonkeyPatch,
    instruments: list[dict[str, Any]] | None = None,
    summaries: list[dict[str, Any]] | None = None,
    responder: Callable[[str], FakeResponse] | None = None,
) -> list[dict[str, str]]:
    calls: list[dict[str, str]] = []

    def fake_get(
        url: str, params: dict[str, str], timeout: float
    ) -> FakeResponse:
        calls.append({"url": url, **params})
        if responder is not None:
            return responder(url)
        if url.endswith("get_instruments"):
            return FakeResponse({"result": instruments or []})
        return FakeResponse({"result": summaries or []})

    monkeypatch.setattr(_deribit.requests, "get", fake_get)
    return calls


class TestLoadDeribitChain:
    """Behaviour of load_deribit_chain against a mocked API."""

    def test_selects_closest_expiry_and_filters_calls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test the 7-day target picks the near expiry and only calls."""
        _install_api(monkeypatch, INSTRUMENTS, SUMMARIES)

        chain = load_deribit_chain("BTC", "call", maturity_days=7)

        np.testing.assert_array_equal(
            chain.strikes, [70_000.0, 80_000.0, 90_000.0]
        )
        assert chain.T == pytest.approx(7 / 365.25)

    def test_prices_converted_from_coin_to_usd(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test bid and ask are scaled by each instrument's underlying."""
        _install_api(monkeypatch, INSTRUMENTS, SUMMARIES)

        chain = load_deribit_chain("BTC", "call", maturity_days=7)

        np.testing.assert_allclose(
            chain.bid, np.array([0.10, 0.02, 0.001]) * BTC_USD
        )
        np.testing.assert_allclose(
            chain.ask, np.array([0.11, 0.025, 0.002]) * BTC_USD
        )
        assert chain.spot == BTC_USD
        assert chain.rate == 0.0

    def test_far_expiry_uses_its_own_underlying(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test a 30-day target picks the far expiry and its forward."""
        _install_api(monkeypatch, INSTRUMENTS, SUMMARIES)

        chain = load_deribit_chain("BTC", "put", maturity_days=30)

        np.testing.assert_array_equal(chain.strikes, [80_000.0])
        assert chain.bid[0] == pytest.approx(0.06 * 78_000.0)
        assert chain.T == pytest.approx(30 / 365.25)

    def test_requests_use_option_kind_not_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test both endpoints are queried with kind='option'."""
        calls = _install_api(monkeypatch, INSTRUMENTS, SUMMARIES)

        load_deribit_chain("BTC", "call", maturity_days=7)

        methods = [c["url"].rsplit("/", 1)[1] for c in calls]
        assert methods == ["get_instruments", "get_book_summary_by_currency"]
        assert all(c["kind"] == "option" for c in calls)
        assert all(c["currency"] == "BTC" for c in calls)

    def test_one_sided_quotes_are_dropped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test missing, zero, or crossed quotes are skipped."""
        summaries = [
            _summary("BTC-NEAR-70000-C", None, 0.11),
            _summary("BTC-NEAR-80000-C", 0.0, 0.025),
            _summary("BTC-NEAR-90000-C", 0.003, 0.002),
            _summary("BTC-FAR-80000-C", 0.04, 0.045),
        ]
        _install_api(monkeypatch, INSTRUMENTS, summaries)

        chain = load_deribit_chain("BTC", "call", maturity_days=7)

        np.testing.assert_array_equal(chain.strikes, [80_000.0])
        assert chain.T == pytest.approx(30 / 365.25)

    def test_invalid_kind_raises_before_any_request(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test kind validation happens locally."""
        calls = _install_api(monkeypatch, INSTRUMENTS, SUMMARIES)

        with pytest.raises(ValueError, match="kind must be"):
            load_deribit_chain("BTC", "straddle")
        assert calls == []

    def test_http_error_becomes_runtime_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test transport failures are wrapped with the method name."""
        _install_api(
            monkeypatch, responder=lambda url: FakeResponse({}, status=400)
        )

        with pytest.raises(RuntimeError, match="get_instruments failed"):
            load_deribit_chain("BTC", "call")

    def test_api_error_payload_becomes_runtime_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test a JSON-RPC error body is surfaced."""
        error = {"error": {"code": -32602, "message": "Invalid params"}}
        _install_api(monkeypatch, responder=lambda url: FakeResponse(error))

        with pytest.raises(RuntimeError, match="Invalid params"):
            load_deribit_chain("BTC", "call")

    def test_no_quotes_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test an empty book raises a clear error."""
        _install_api(monkeypatch, INSTRUMENTS, [])

        with pytest.raises(RuntimeError, match="No quoted BTC call options"):
            load_deribit_chain("BTC", "call")


@pytest.mark.network
@pytest.mark.skipif(
    os.environ.get("QMATH_NETWORK_TESTS") != "1",
    reason="set QMATH_NETWORK_TESTS=1 to hit the live Deribit API",
)
def test_live_chain_is_well_formed() -> None:
    """Test the live API returns a consistent, USD-denominated chain."""
    chain = load_deribit_chain("BTC", "call", maturity_days=30)

    assert len(chain) >= 5
    assert np.all(np.diff(chain.strikes) > 0)
    assert np.all(chain.ask >= chain.bid)
    assert 0 < chain.T < 1
    assert chain.strikes.min() < chain.spot < chain.strikes.max()
    assert chain.mid.max() < chain.spot
