"""Tests for risk-neutral density extraction and properties."""

import numpy as np
import pytest

from qmath.datasets import synthetic_heston_chain
from qmath.options.filters import filter_chain
from qmath.rnd.density import RiskNeutralDensity, breeden_litzenberger
from qmath.surface.fengler import FenglerSmoother


class TestRiskNeutralDensity:
    """Test RiskNeutralDensity class."""

    def test_density_initialization(self) -> None:
        """Test density initialization and normalization."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(strikes, density, forward=100.0, discount=0.99)

        # Should integrate to 1
        integral = np.trapz(rnd.density, rnd.strikes)
        np.testing.assert_allclose(integral, 1.0, rtol=1e-2)

    def test_density_pdf_evaluation(self) -> None:
        """Test PDF evaluation."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(strikes, density, forward=100.0, discount=0.99)

        # PDF should be non-negative
        pdf_vals = rnd.pdf(np.array([90.0, 100.0, 110.0]))
        assert np.all(pdf_vals >= 0)

    def test_density_cdf_evaluation(self) -> None:
        """Test CDF evaluation and bounds."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(strikes, density, forward=100.0, discount=0.99)

        # CDF should be in [0, 1]
        cdf_vals = rnd.cdf(np.array([80.0, 100.0, 120.0]))
        assert np.all((cdf_vals >= 0) & (cdf_vals <= 1))

        # CDF should be increasing
        assert cdf_vals[1] > cdf_vals[0]
        assert cdf_vals[2] > cdf_vals[1]

    def test_density_quantile(self) -> None:
        """Test quantile (inverse CDF) evaluation."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(strikes, density, forward=100.0, discount=0.99)

        # Quantiles should be in strike range
        q = rnd.quantile(np.array([0.25, 0.5, 0.75]))
        assert np.all((q >= strikes.min()) & (q <= strikes.max()))

    def test_density_moments(self) -> None:
        """Test density moment calculations."""
        strikes = np.linspace(80, 120, 100)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(strikes, density, forward=100.0, discount=0.99)

        mean = rnd.mean()
        var = rnd.variance()
        skew = rnd.skewness()

        # Mean should be close to 100 (center of density)
        assert 95 < mean < 105

        # Variance should be positive
        assert var > 0

        # Skewness should be close to 0 for symmetric density
        assert abs(skew) < 0.1

    def test_density_non_negative(self) -> None:
        """Test that density remains non-negative."""
        strikes = np.linspace(80, 120, 50)
        # Create density with some negative values (should be corrected)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2)) - 0.001

        rnd = RiskNeutralDensity(strikes, density, forward=100.0, discount=0.99)

        # All density values should be non-negative after initialization
        assert np.all(rnd.density >= -1e-10)  # Allow small numerical error


class TestBreedenLitzenberger:
    """Test Breeden-Litzenberger density extraction."""

    def test_bl_extraction(self) -> None:
        """Test basic B-L density extraction."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
        density = breeden_litzenberger(smoother, forward=fwd, discount=df)

        # Density should integrate to 1
        integral = np.trapz(density.density, density.strikes)
        np.testing.assert_allclose(integral, 1.0, rtol=1e-2)

    def test_bl_density_non_negative(self) -> None:
        """Test that extracted density is non-negative."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
        density = breeden_litzenberger(smoother, forward=fwd, discount=df)

        # All density values should be non-negative
        assert np.all(density.density >= 0)

    def test_bl_density_mean(self) -> None:
        """Test that extracted density has mean close to forward."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=30, seed=0)
        chain = filter_chain(chain)

        fwd = chain.spot * np.exp(chain.rate * chain.T)
        df = np.exp(-chain.rate * chain.T)

        smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
        density = breeden_litzenberger(smoother, forward=fwd, discount=df)

        # Mean should be close to forward (within ~10%)
        mean = density.mean()
        assert abs(mean - fwd) / fwd < 0.1

    def test_bl_requires_fitted_smoother(self) -> None:
        """Test that B-L extraction requires fitted smoother."""
        smoother = FenglerSmoother(lambda_=1e-3)

        with pytest.raises(ValueError, match="must be fitted first"):
            breeden_litzenberger(smoother, forward=100.0, discount=0.99)
