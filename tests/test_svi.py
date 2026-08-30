"""Tests for SVI (Stochastic Volatility Inspired) surface fitting."""

import numpy as np
import pytest

from qmath.datasets._synthetic import synthetic_heston_chain
from qmath.surface.svi import SVISmoother


class TestSVISmoother:
    """Test SVI surface fitting."""

    def test_svi_fit_basic(self) -> None:
        """Test basic SVI fitting to synthetic data."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=15, spot=100.0)
        smoother = SVISmoother()

        smoother.fit(chain, forward=chain.spot * np.exp(chain.rate * chain.T), discount=np.exp(-chain.rate * chain.T))

        assert smoother.params is not None
        assert "a" in smoother.params
        assert "b" in smoother.params
        assert "m" in smoother.params
        assert "rho" in smoother.params
        assert "sigma" in smoother.params

    def test_svi_parameters_valid(self) -> None:
        """Test that fitted SVI parameters satisfy constraints."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=20, spot=100.0)
        smoother = SVISmoother(enforce_no_arb=True)

        smoother.fit(chain, forward=chain.spot * np.exp(chain.rate * chain.T), discount=np.exp(-chain.rate * chain.T))

        assert smoother.params is not None
        a, b, m, rho, sigma = (smoother.params[k] for k in ["a", "b", "m", "rho", "sigma"])

        # Check parameter constraints
        assert a >= 0, "ATM variance must be non-negative"
        assert b >= 0, "Slope parameter must be non-negative"
        assert sigma >= 0, "Vol-of-vol must be non-negative"
        assert abs(rho) < 1, "Correlation must be in (-1, 1)"

    def test_svi_stores_training_data(self) -> None:
        """Test that SVI stores training strikes and IVs."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=15, spot=100.0)
        smoother = SVISmoother()

        smoother.fit(chain, forward=chain.spot * np.exp(chain.rate * chain.T), discount=np.exp(-chain.rate * chain.T))

        assert smoother.strikes_fit_ is not None
        assert smoother.iv_fit_ is not None
        assert len(smoother.strikes_fit_) == len(chain.strikes)
        assert len(smoother.iv_fit_) == len(chain.strikes)

    def test_svi_predict_not_implemented(self) -> None:
        """Test that predict raises NotImplementedError."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=10, spot=100.0)
        smoother = SVISmoother()

        smoother.fit(chain, forward=chain.spot * np.exp(chain.rate * chain.T), discount=np.exp(-chain.rate * chain.T))

        with pytest.raises(NotImplementedError):
            smoother.predict(chain.strikes)

    def test_svi_unfitted_raises(self) -> None:
        """Test that predict without fit raises error."""
        smoother = SVISmoother()
        strikes = np.array([90.0, 100.0, 110.0])

        with pytest.raises(ValueError, match="Must fit"):
            smoother.predict(strikes)
