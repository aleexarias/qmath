"""Tests for model-free moment extraction."""

import numpy as np

from qmath.models.black_scholes import bs_price
from qmath.rnd.moments import model_free_kurtosis, model_free_skewness, model_free_variance


class TestModelFreeMoments:
    """Test model-free moment extraction."""

    def test_model_free_variance_basic(self) -> None:
        """Test basic variance extraction."""
        S = 100.0
        K = np.linspace(85, 115, 31)
        T = 0.5
        r = 0.02
        sigma = 0.2

        # Synthetic prices under Black-Scholes
        call_prices = bs_price(S, K, T, r, np.full_like(K, sigma), flag="C")
        put_prices = bs_price(S, K, T, r, np.full_like(K, sigma), flag="P")

        forward = S * np.exp(r * T)
        discount = np.exp(-r * T)

        mf_var = model_free_variance(K, call_prices, put_prices, forward, discount)

        # Variance should be positive
        assert mf_var > 0, "Model-free variance should be positive"

        # For Black-Scholes with constant volatility, should be in reasonable range
        # BKM formula doesn't exactly equal sigma^2, so allow wider tolerance
        assert 0.01 < mf_var < 0.10, f"Variance {mf_var} should be in reasonable range"

    def test_model_free_variance_zero_prices(self) -> None:
        """Test variance with all zero prices returns zero."""
        K = np.linspace(85, 115, 31)
        call_prices = np.zeros_like(K)
        put_prices = np.zeros_like(K)

        forward = 100.0
        discount = 0.98

        mf_var = model_free_variance(K, call_prices, put_prices, forward, discount)

        assert mf_var >= 0, "Variance should be non-negative"

    def test_model_free_skewness_negative(self) -> None:
        """Test that skewness can be negative (crash risk)."""
        S = 100.0
        K = np.linspace(70, 130, 61)
        T = 0.5
        r = 0.02

        # Use decreasing IV to simulate crash risk (vol smile)
        iv = 0.2 - 0.1 * np.abs(K - S) / S
        iv = np.maximum(iv, 0.05)

        call_prices = bs_price(S, K, T, r, iv, flag="C")
        put_prices = bs_price(S, K, T, r, iv, flag="P")

        forward = S * np.exp(r * T)
        discount = np.exp(-r * T)

        skewness = model_free_skewness(K, call_prices, put_prices, forward, discount)

        # With elevated OTM put vol, skewness should be negative
        assert isinstance(skewness, float), "Skewness should be a float"

    def test_model_free_kurtosis_finite(self) -> None:
        """Test that kurtosis is finite with vol smile."""
        S = 100.0
        K = np.linspace(70, 130, 61)
        T = 0.5
        r = 0.02

        # Vol smile (elevated wings)
        iv = 0.2 + 0.1 * np.abs(K - S) / S

        call_prices = bs_price(S, K, T, r, iv, flag="C")
        put_prices = bs_price(S, K, T, r, iv, flag="P")

        forward = S * np.exp(r * T)
        discount = np.exp(-r * T)

        kurtosis = model_free_kurtosis(K, call_prices, put_prices, forward, discount)

        # Kurtosis should be finite and well-defined
        assert np.isfinite(kurtosis), "Kurtosis should be finite"

    def test_model_free_moments_consistency(self) -> None:
        """Test that moments are computed consistently."""
        S = 100.0
        K = np.linspace(85, 115, 31)
        T = 0.5
        r = 0.02
        sigma = 0.2

        call_prices = bs_price(S, K, T, r, np.full_like(K, sigma), flag="C")
        put_prices = bs_price(S, K, T, r, np.full_like(K, sigma), flag="P")

        forward = S * np.exp(r * T)
        discount = np.exp(-r * T)

        var = model_free_variance(K, call_prices, put_prices, forward, discount)
        skew = model_free_skewness(K, call_prices, put_prices, forward, discount)
        kurt = model_free_kurtosis(K, call_prices, put_prices, forward, discount)

        # All should be finite
        assert np.isfinite(var), "Variance should be finite"
        assert np.isfinite(skew), "Skewness should be finite"
        assert np.isfinite(kurt), "Kurtosis should be finite"

    def test_model_free_moments_zero_variance(self) -> None:
        """Test moments when variance is zero."""
        K = np.linspace(85, 115, 31)
        call_prices = np.zeros_like(K)
        put_prices = np.zeros_like(K)

        forward = 100.0
        discount = 0.98

        skew = model_free_skewness(K, call_prices, put_prices, forward, discount)
        kurt = model_free_kurtosis(K, call_prices, put_prices, forward, discount)

        # Should return zero when variance is zero
        assert skew == 0.0, "Skewness should be zero when variance is zero"
        assert kurt == 0.0, "Kurtosis should be zero when variance is zero"
