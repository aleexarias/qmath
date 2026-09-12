"""Deribit API loader for live option data.

Fetches option chains from Deribit's public REST API. No authentication is
needed for public market data, but an internet connection is.

**Note**: Deribit is a cryptocurrency options exchange. For traditional
equity options, use another data provider.
"""

from typing import Any

import numpy as np
import requests

from qmath._typing import FloatArray
from qmath.options.chain import OptionChain

__all__ = ["load_deribit_chain"]

API_URL = "https://www.deribit.com/api/v2/public"
SECONDS_PER_YEAR = 365.25 * 86400
REQUEST_TIMEOUT = 10.0


def load_deribit_chain(
    currency: str = "BTC",
    kind: str = "call",
    maturity_days: int = 7,
) -> OptionChain:
    r"""Fetch a live option chain from Deribit.

    Parameters
    ----------
    currency : str, default='BTC'
        Underlying currency, e.g. ``'BTC'`` or ``'ETH'``.
    kind : str, default='call'
        Option type, ``'call'`` or ``'put'``.
    maturity_days : int, default=7
        Target time to expiry in days. The listed expiry closest to this is
        returned.

    Returns
    -------
    OptionChain
        Snapshot of the selected expiry with strikes and USD prices.

    Raises
    ------
    ValueError
        If ``kind`` is not ``'call'`` or ``'put'``.
    RuntimeError
        If a request fails or no quoted instruments are available.

    Notes
    -----
    Deribit quotes option prices in units of the underlying coin while
    strikes are in USD. Bid and ask are converted to USD with each
    instrument's ``underlying_price`` so that the chain is dimensionally
    consistent with :func:`qmath.options.infer_forward` and the
    Breeden-Litzenberger pipeline. Timestamps from the API are in
    milliseconds.

    The risk-free rate is set to zero: Deribit options are inverse
    contracts collateralised in the underlying, and the exchange itself
    reports a zero interest rate for them.

    Examples
    --------
    >>> chain = load_deribit_chain("BTC", maturity_days=30)  # doctest: +SKIP
    >>> 0 < chain.T < 1  # doctest: +SKIP
    True
    """
    if kind not in ("call", "put"):
        msg = f"kind must be 'call' or 'put', got {kind!r}"
        raise ValueError(msg)

    instruments = _get(
        "get_instruments",
        {"currency": currency, "kind": "option", "expired": "false"},
    )
    summaries = _get(
        "get_book_summary_by_currency",
        {"currency": currency, "kind": "option"},
    )

    by_name = {item["instrument_name"]: item for item in instruments}
    quoted = [
        {**by_name[s["instrument_name"]], **s}
        for s in summaries
        if s["instrument_name"] in by_name
        and by_name[s["instrument_name"]]["option_type"] == kind
        and _is_two_sided(s)
    ]
    if not quoted:
        msg = f"No quoted {currency} {kind} options on Deribit"
        raise RuntimeError(msg)

    now_ms = max(int(q["creation_timestamp"]) for q in quoted)
    target_ms = now_ms + maturity_days * 86400 * 1000
    expiry_ms = min(
        {int(q["expiration_timestamp"]) for q in quoted},
        key=lambda ts: abs(ts - target_ms),
    )
    chain_quotes = sorted(
        (q for q in quoted if int(q["expiration_timestamp"]) == expiry_ms),
        key=lambda q: float(q["strike"]),
    )

    strikes: FloatArray = np.array(
        [q["strike"] for q in chain_quotes], dtype=np.float64
    )
    bid: FloatArray = np.array(
        [q["bid_price"] * q["underlying_price"] for q in chain_quotes],
        dtype=np.float64,
    )
    ask: FloatArray = np.array(
        [q["ask_price"] * q["underlying_price"] for q in chain_quotes],
        dtype=np.float64,
    )
    spot = float(chain_quotes[0]["estimated_delivery_price"])
    T = (expiry_ms - now_ms) / 1000 / SECONDS_PER_YEAR

    return OptionChain(strikes=strikes, bid=bid, ask=ask, T=T, spot=spot)


def _is_two_sided(summary: dict[str, Any]) -> bool:
    bid = summary.get("bid_price")
    ask = summary.get("ask_price")
    return (
        bid is not None
        and ask is not None
        and bid > 0
        and ask > 0
        and ask >= bid
    )


def _get(method: str, params: dict[str, str]) -> list[dict[str, Any]]:
    # JSON payloads are untyped at the API boundary; ``Any`` stops here.
    try:
        response = requests.get(
            f"{API_URL}/{method}", params=params, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as e:
        msg = f"Deribit request {method} failed: {e}"
        raise RuntimeError(msg) from e

    if "error" in payload:
        msg = f"Deribit request {method} returned an error: {payload['error']}"
        raise RuntimeError(msg)

    result: list[dict[str, Any]] = payload["result"]
    return result
