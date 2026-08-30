"""Arbitrage-free validation checks on option surfaces."""

import numpy as np

from qmath._typing import BoolArray, FloatArray

__all__ = ["check_monotonicity", "check_convexity", "check_bounds"]


def check_monotonicity(strikes: FloatArray, prices: FloatArray) -> tuple[BoolArray, float]:
    r"""Check call prices are monotonically decreasing in strike.

    Parameters
    ----------
    strikes : FloatArray
        Strike prices.
    prices : FloatArray
        Call prices.

    Returns
    -------
    is_monotone : BoolArray
        Boolean array indicating monotonicity at each adjacent pair.
    violation_count : float
        Number of violations (negative differences).
    """
    diffs = np.diff(prices)
    is_monotone = diffs <= 0
    violation_count = float(np.sum(diffs > 0))

    return is_monotone, violation_count


def check_convexity(strikes: FloatArray, prices: FloatArray) -> tuple[BoolArray, float]:
    r"""Check call prices are convex in strike.

    Parameters
    ----------
    strikes : FloatArray
        Strike prices.
    prices : FloatArray
        Call prices.

    Returns
    -------
    is_convex : BoolArray
        Boolean array indicating convexity at each middle point.
    violation_count : float
        Number of violations.

    Notes
    -----
    Convexity is checked via the discrete second difference:
    C(K_{i+1}) - 2*C(K_i) + C(K_{i-1}) >= 0
    """
    if len(strikes) < 3:
        return np.array([True] * (len(strikes) - 1)), 0.0

    h_left = np.diff(strikes[:-1])
    h_right = np.diff(strikes[1:])

    second_diff = np.diff(prices, n=2) / np.maximum(h_left * h_right, 1e-10)

    is_convex = second_diff >= 0
    violation_count = float(np.sum(second_diff < 0))

    return is_convex, violation_count


def check_bounds(
    strikes: FloatArray, prices: FloatArray, spot: float, discount: float
) -> tuple[BoolArray, float]:
    r"""Check call prices satisfy no-arbitrage bounds.

    Parameters
    ----------
    strikes : FloatArray
        Strike prices.
    prices : FloatArray
        Call prices.
    spot : float
        Spot price.
    discount : float
        Discount factor exp(-rT).

    Returns
    -------
    in_bounds : BoolArray
        Boolean array indicating in-bounds at each strike.
    violation_count : float
        Number of violations.

    Notes
    -----
    Call price C(K) must satisfy:
    - Lower bound: C(K) >= max(S - K*DF, 0)
    - Upper bound: C(K) <= S
    """
    intrinsic = np.maximum(spot - strikes * discount, 0)
    upper_bound = spot

    in_lower = prices >= intrinsic
    in_upper = prices <= upper_bound

    in_bounds = in_lower & in_upper
    violation_count = float(np.sum(~in_bounds))

    return in_bounds, violation_count
