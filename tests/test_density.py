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

        rnd = RiskNeutralDensity(
            strikes, density, forward=100.0, discount=0.99
        )

        integral = np.trapezoid(rnd.density, rnd.strikes)
        np.testing.assert_allclose(integral, 1.0, rtol=1e-2)

    def test_density_pdf_evaluation(self) -> None:
        """Test PDF evaluation."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(
            strikes, density, forward=100.0, discount=0.99
        )

        pdf_vals = rnd.pdf(np.array([90.0, 100.0, 110.0]))
        assert np.all(pdf_vals >= 0)

    def test_density_cdf_evaluation(self) -> None:
        """Test CDF evaluation and bounds."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(
            strikes, density, forward=100.0, discount=0.99
        )

        cdf_vals = rnd.cdf(np.array([80.0, 100.0, 120.0]))
        assert np.all((cdf_vals >= 0) & (cdf_vals <= 1))

        assert cdf_vals[1] > cdf_vals[0]
        assert cdf_vals[2] > cdf_vals[1]

    def test_density_quantile(self) -> None:
        """Test quantile (inverse CDF) evaluation."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(
            strikes, density, forward=100.0, discount=0.99
        )

        q = rnd.quantile(np.array([0.25, 0.5, 0.75]))
        assert np.all((q >= strikes.min()) & (q <= strikes.max()))

    def test_density_moments(self) -> None:
        """Test density moment calculations."""
        strikes = np.linspace(80, 120, 100)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2))

        rnd = RiskNeutralDensity(
            strikes, density, forward=100.0, discount=0.99
        )

        mean = rnd.mean()
        var = rnd.variance()
        skew = rnd.skewness()

        assert 95 < mean < 105

        assert var > 0

        assert abs(skew) < 0.1

    def test_density_non_negative(self) -> None:
        """Test that density remains non-negative."""
        strikes = np.linspace(80, 120, 50)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 15**2)) - 0.001

        rnd = RiskNeutralDensity(
            strikes, density, forward=100.0, discount=0.99
        )

        assert np.all(rnd.density >= -1e-10)


class TestBreedenLitzenberger:
    """Test Breeden-Litzenberger density extraction."""

    def test_bl_extraction(self) -> None:
        """Test basic B-L density extraction."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(
            chain, forward=fwd, discount=df
        )
        density = breeden_litzenberger(smoother, forward=fwd, discount=df)

        integral = np.trapezoid(density.density, density.strikes)
        np.testing.assert_allclose(integral, 1.0, rtol=1e-2)

    def test_bl_density_non_negative(self) -> None:
        """Test that extracted density is non-negative."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(
            chain, forward=fwd, discount=df
        )
        density = breeden_litzenberger(smoother, forward=fwd, discount=df)

        assert np.all(density.density >= 0)

    def test_bl_density_mean(self) -> None:
        """Test that extracted density has mean close to forward."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=30, seed=0)
        chain = filter_chain(chain)

        fwd = chain.spot * np.exp(chain.rate * chain.T)
        df = np.exp(-chain.rate * chain.T)

        smoother = FenglerSmoother(lambda_=1e-3).fit(
            chain, forward=fwd, discount=df
        )
        density = breeden_litzenberger(smoother, forward=fwd, discount=df)

        mean = density.mean()
        assert abs(mean - fwd) / fwd < 0.1

    def test_bl_requires_fitted_smoother(self) -> None:
        """Test that B-L extraction requires fitted smoother."""
        smoother = FenglerSmoother(lambda_=1e-3)

        with pytest.raises(ValueError, match="must be fitted first"):
            breeden_litzenberger(smoother, forward=100.0, discount=0.99)
