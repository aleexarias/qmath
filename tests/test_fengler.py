"""Tests for Fengler arbitrage-free surface smoother."""

import numpy as np

from qmath.datasets import synthetic_heston_chain
from qmath.options.filters import filter_chain
from qmath.surface.fengler import FenglerSmoother
from qmath.validation.arbitrage import check_convexity, check_monotonicity


class TestFenglerSmoother:
    """Test Fengler constrained cubic-spline smoother."""

    def test_smoother_fit_predict(self) -> None:
        """Test basic fit and predict workflow."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)

        # Should be able to predict on original strikes
        prices = smoother.predict(chain.strikes)

        assert len(prices) == len(chain.strikes)
        assert np.all(prices > 0)

    def test_smoother_monotonicity(self) -> None:
        """Test that fitted prices are monotone decreasing."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
        prices = smoother.predict(chain.strikes)

        # Check monotonicity
        is_monotone, violations = check_monotonicity(chain.strikes, prices)

        # Should have few or no violations
        assert violations <= 2  # Allow small numerical violations

    def test_smoother_convexity(self) -> None:
        """Test that fitted prices are convex."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
        prices = smoother.predict(chain.strikes)

        # Check convexity
        is_convex, violations = check_convexity(chain.strikes, prices)

        # Should have few or no violations
        assert violations <= 2  # Allow small numerical violations

    def test_smoother_extrapolation(self) -> None:
        """Test that smoother can extrapolate beyond fitted strikes."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=20, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)

        # Evaluate at strikes beyond the fitted range
        new_strikes = np.array([chain.strikes.min() - 10, chain.strikes.max() + 10])
        prices = smoother.predict(new_strikes)

        assert len(prices) == 2
        assert np.all(np.isfinite(prices))

    def test_smoother_lambda_effect(self) -> None:
        """Test that lambda parameter affects smoothness."""
        chain = synthetic_heston_chain(T=0.5, n_strikes=25, seed=0)
        chain = filter_chain(chain)

        fwd = 100.0
        df = 0.99

        # Small lambda: less smoothing, closer to data
        smoother_small = FenglerSmoother(lambda_=1e-5).fit(chain, forward=fwd, discount=df)
        prices_small = smoother_small.predict(chain.strikes)

        # Large lambda: more smoothing, less oscillation
        smoother_large = FenglerSmoother(lambda_=1e-1).fit(chain, forward=fwd, discount=df)
        prices_large = smoother_large.predict(chain.strikes)

        # Large lambda should produce smoother prices (lower second derivative norm)
        second_diff_small = np.diff(prices_small, n=2)
        second_diff_large = np.diff(prices_large, n=2)

        roughness_small = np.sum(second_diff_small**2)
        roughness_large = np.sum(second_diff_large**2)

        assert roughness_large <= roughness_small
