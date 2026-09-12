"""Tests for arbitrage-free validation checks."""

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from qmath.validation.arbitrage import (
    check_bounds,
    check_convexity,
    check_monotonicity,
)


class TestMonotonicity:
    """Test monotonicity checking for call prices."""

    def test_monotone_decreasing(self) -> None:
        """Test detection of monotone decreasing prices."""
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([12.0, 6.0, 2.0])

        is_monotone, violations = check_monotonicity(strikes, prices)

        assert violations == 0
        assert np.all(is_monotone)

    def test_non_monotone(self) -> None:
        """Test detection of non-monotone prices."""
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([10.0, 15.0, 2.0])

        is_monotone, violations = check_monotonicity(strikes, prices)

        assert violations > 0

    def test_monotone_near_boundary(self) -> None:
        """Test monotonicity near boundaries."""
        strikes = np.array([90.0, 100.0, 110.0, 120.0])
        prices = np.array([12.0, 6.0, 2.0, 2.001])

        is_monotone, violations = check_monotonicity(strikes, prices)

        assert violations >= 1

    def test_noise_within_tolerance_is_not_a_violation(self) -> None:
        """Test an increase smaller than atol is treated as monotone."""
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([12.0, 6.0, 6.0 + 1e-10])

        is_monotone, violations = check_monotonicity(strikes, prices)

        assert violations == 0
        assert np.all(is_monotone)

    def test_tolerance_is_configurable(self) -> None:
        """Test atol=0 restores the strict check."""
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([12.0, 6.0, 6.0 + 1e-10])

        _, violations = check_monotonicity(strikes, prices, atol=0.0)

        assert violations == 1


class TestConvexity:
    """Test convexity checking for call prices."""

    def test_convex_prices(self) -> None:
        """Test detection of convex prices."""
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([12.0, 6.0, 3.0])

        is_convex, violations = check_convexity(strikes, prices)

        assert violations == 0
        assert np.all(is_convex)

    def test_non_convex_prices(self) -> None:
        """Test detection of non-convex prices."""
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([10.0, 8.0, 2.0])

        is_convex, violations = check_convexity(strikes, prices)

        assert violations >= 1
        assert not np.all(is_convex)

    def test_noise_within_tolerance_is_not_a_violation(self) -> None:
        """Test a scaled second difference above -atol counts as convex."""
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([12.0, 6.0 + 0.5e-8, 0.0])

        is_convex, violations = check_convexity(strikes, prices)

        assert violations == 0
        assert np.all(is_convex)

    @given(
        magnitude=st.floats(min_value=1e-7, max_value=1.0),
        atol=st.floats(min_value=1e-12, max_value=1e-8),
    )
    def test_violation_beyond_tolerance_is_detected(
        self, magnitude: float, atol: float
    ) -> None:
        """Property: a middle bump exceeding atol is always flagged."""
        strikes = np.array([90.0, 100.0, 110.0])
        h2 = 10.0 * 10.0
        prices = np.array([12.0, 6.0 + magnitude * h2, 0.0])

        _, violations = check_convexity(strikes, prices, atol=atol)

        assert violations == 1


class TestBounds:
    """Test no-arbitrage bounds checking."""

    def test_prices_within_bounds(self) -> None:
        """Test detection of prices within bounds."""
        spot = 100.0
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([11.0, 5.0, 1.0])
        discount = 0.99

        in_bounds, violations = check_bounds(strikes, prices, spot, discount)

        assert violations == 0
        assert np.all(in_bounds)

    def test_prices_below_intrinsic(self) -> None:
        """Test detection of prices below intrinsic value."""
        spot = 100.0
        strikes = np.array([90.0, 100.0, 110.0])
        prices = np.array([8.0, 5.0, 1.0])
        discount = 0.99

        in_bounds, violations = check_bounds(strikes, prices, spot, discount)

        assert violations >= 1

    def test_prices_above_spot(self) -> None:
        """Test detection of prices above spot."""
        spot = 100.0
        strikes = np.array([50.0, 100.0, 110.0])
        prices = np.array([102.0, 5.0, 1.0])
        discount = 0.99

        in_bounds, violations = check_bounds(strikes, prices, spot, discount)

        assert violations >= 1
