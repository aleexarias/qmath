"""Validation: arbitrage checks and density distance metrics."""

from qmath.validation.arbitrage import check_bounds, check_convexity, check_monotonicity
from qmath.validation.metrics import ks_distance, l2_distance, wasserstein

__all__ = [
    "check_bounds",
    "check_convexity",
    "check_monotonicity",
    "ks_distance",
    "l2_distance",
    "wasserstein",
]
