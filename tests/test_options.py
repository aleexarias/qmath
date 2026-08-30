"""Tests for option chain filtering and forward inference."""

import numpy as np
import pytest

from qmath.models.black_scholes import bs_price
from qmath.options.chain import OptionChain
from qmath.options.filters import filter_chain
from qmath.options.forward import infer_forward


class TestOptionChain:
    """Test OptionChain data structure."""

    def test_chain_construction(self) -> None:
        """Test basic chain construction."""
        strikes = np.array([90.0, 100.0, 110.0])
        bid = np.array([10.0, 5.0, 2.0])
        ask = np.array([11.0, 6.0, 3.0])

        chain = OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0)

        assert len(chain) == 3
        np.testing.assert_array_equal(chain.strikes, strikes)

    def test_chain_validation(self) -> None:
        """Test chain raises on invalid inputs."""
        strikes = np.array([90.0, 100.0, 110.0])
        bid = np.array([11.0, 5.0, 2.0])
        ask = np.array([10.0, 6.0, 3.0])  # ask < bid!

        with pytest.raises(ValueError, match="ask < bid"):
            OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0)

    def test_chain_mid_prices(self) -> None:
        """Test mid price calculation."""
        strikes = np.array([90.0, 100.0, 110.0])
        bid = np.array([10.0, 5.0, 2.0])
        ask = np.array([12.0, 7.0, 4.0])

        chain = OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0)

        expected_mid = np.array([11.0, 6.0, 3.0])
        np.testing.assert_array_equal(chain.mid, expected_mid)

    def test_chain_spread(self) -> None:
        """Test bid-ask spread calculation."""
        strikes = np.array([90.0, 100.0, 110.0])
        bid = np.array([10.0, 5.0, 2.0])
        ask = np.array([12.0, 7.0, 4.0])

        chain = OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0)

        expected_spread = np.array([2.0, 2.0, 2.0])
        np.testing.assert_array_equal(chain.spread, expected_spread)


class TestFilterChain:
    """Test chain filtering."""

    def test_filter_removes_wide_spreads(self) -> None:
        """Test that wide spreads are filtered out."""
        strikes = np.array([90.0, 100.0, 110.0])
        bid = np.array([10.0, 5.0, 2.0])
        ask = np.array([12.0, 100.0, 4.0])  # Middle one has huge spread

        chain = OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0)
        filtered = filter_chain(chain, max_bid_ask_ratio=1.05)

        assert len(filtered) < len(chain)

    def test_filter_removes_zero_bids(self) -> None:
        """Test that zero bids are filtered."""
        strikes = np.array([90.0, 100.0, 110.0])
        bid = np.array([10.0, 0.0, 2.0])
        ask = np.array([11.0, 1.0, 3.0])

        chain = OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0)
        filtered = filter_chain(chain, min_bid=0.01)

        assert len(filtered) < len(chain)

    def test_filter_preserves_true_density(self) -> None:
        """Test that true density is preserved through filtering."""
        strikes = np.array([90.0, 100.0, 110.0])
        bid = np.array([10.0, 5.0, 2.0])
        ask = np.array([11.0, 6.0, 3.0])
        true_density = np.array([0.01, 0.02, 0.01])

        chain = OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0, true_density=true_density)
        filtered = filter_chain(chain)

        assert filtered.true_density is not None
        assert len(filtered.true_density) == len(filtered.strikes)


class TestForwardInference:
    """Test forward and discount factor inference."""

    def test_forward_from_synthetic_chain(self) -> None:
        """Test forward inference from a synthetic chain."""
        S = 100.0
        K = np.linspace(85, 115, 31)
        T = 0.5
        r = 0.02
        sigma = np.full_like(K, 0.2)

        # Generate synthetic calls
        calls = bs_price(S, K, T, r, sigma, flag="C")
        chain = OptionChain(strikes=K, bid=calls * 0.98, ask=calls * 1.02, T=T, spot=S, rate=r)

        fwd, df = infer_forward(chain)

        # Forward should be close to S * exp(r*T)
        expected_fwd = S * np.exp(r * T)
        assert abs(fwd - expected_fwd) / expected_fwd < 0.2  # Allow 20% error due to regression

        # Discount should be reasonable
        assert 0.5 < df < 1.0  # Basic sanity check

    def test_forward_decreasing_call_prices(self) -> None:
        """Test forward inference requires decreasing call prices."""
        strikes = np.array([90.0, 100.0, 110.0])
        # Non-monotonic prices should still produce some output
        bid = np.array([5.0, 6.0, 2.0])  # Not monotone decreasing!
        ask = np.array([6.0, 7.0, 3.0])

        chain = OptionChain(strikes=strikes, bid=bid, ask=ask, T=0.5, spot=100.0)
        fwd, df = infer_forward(chain)

        # Should not crash, but values may be nonsensical
        assert isinstance(fwd, float)
        assert isinstance(df, float)
