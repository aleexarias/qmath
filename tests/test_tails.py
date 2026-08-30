"""Tests for tail modeling via Pareto grafting."""

import numpy as np

from qmath.rnd.tails import graft_pareto_tail


class TestParetoTail:
    """Test Pareto tail grafting."""

    def test_graft_tail_basic(self) -> None:
        """Test basic tail grafting."""
        strikes = np.linspace(80, 120, 41)
        # Simple normal-like density
        density = np.exp(-((strikes - 100) ** 2) / (2 * 10**2))
        density /= np.trapz(density, strikes)

        strikes_ext, density_ext = graft_pareto_tail(strikes, density, threshold_pct=10)

        # Extended domain should be larger
        assert len(strikes_ext) > len(strikes)
        assert strikes_ext[0] < strikes[0]
        assert strikes_ext[-1] > strikes[-1]

    def test_graft_tail_normalization(self) -> None:
        """Test that extended density is normalized."""
        strikes = np.linspace(80, 120, 41)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 10**2))
        density /= np.trapz(density, strikes)

        strikes_ext, density_ext = graft_pareto_tail(strikes, density, threshold_pct=10)

        # Extended density should integrate to 1
        integral = np.trapz(density_ext, strikes_ext)
        assert 0.95 < integral < 1.05, f"Integral is {integral}, should be ~1"

    def test_graft_tail_non_negative(self) -> None:
        """Test that extended density is non-negative."""
        strikes = np.linspace(80, 120, 41)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 10**2))
        density /= np.trapz(density, strikes)

        strikes_ext, density_ext = graft_pareto_tail(strikes, density, threshold_pct=10)

        # All densities should be non-negative
        assert np.all(density_ext >= 0), "Density has negative values"

    def test_graft_tail_different_thresholds(self) -> None:
        """Test tail grafting with different thresholds."""
        strikes = np.linspace(80, 120, 41)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 10**2))
        density /= np.trapz(density, strikes)

        for threshold_pct in [5, 10, 20]:
            strikes_ext, density_ext = graft_pareto_tail(strikes, density, threshold_pct=threshold_pct)

            # Should still be normalized
            integral = np.trapz(density_ext, strikes_ext)
            assert 0.95 < integral < 1.05

            # All non-negative
            assert np.all(density_ext >= 0)

    def test_graft_tail_preserves_interior(self) -> None:
        """Test that original strikes are included in extended grid."""
        strikes = np.linspace(80, 120, 41)
        density = np.exp(-((strikes - 100) ** 2) / (2 * 10**2))
        density /= np.trapz(density, strikes)

        strikes_ext, density_ext = graft_pareto_tail(strikes, density, threshold_pct=10)

        # Original strikes should be in extended strikes (approximately)
        for s in [strikes[0], strikes[len(strikes) // 2], strikes[-1]]:
            assert np.any(np.abs(strikes_ext - s) < 1e-10), f"Strike {s} not in extended grid"
