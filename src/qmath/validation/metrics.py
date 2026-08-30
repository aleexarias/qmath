"""Density distance metrics for RND validation."""

import numpy as np

from qmath._typing import FloatArray
from qmath.rnd.density import RiskNeutralDensity

__all__ = ["wasserstein", "l2_distance", "ks_distance"]


def wasserstein(rnd: RiskNeutralDensity, true_rnd: RiskNeutralDensity | FloatArray) -> float:
    r"""Compute Wasserstein-1 distance between estimated and true density.

    Parameters
    ----------
    rnd : RiskNeutralDensity
        Estimated risk-neutral density.
    true_rnd : RiskNeutralDensity or FloatArray
        True density (either a RND object or array of values on rnd.strikes).

    Returns
    -------
    float
        Wasserstein distance (mean absolute quantile difference).

    Notes
    -----
    The Wasserstein-1 distance is the optimal transport cost:

    .. math::

        W_1(P, Q) = \int_0^1 |F_P^{-1}(u) - F_Q^{-1}(u)| du

    Approximated via:

    .. math::

        W_1 \approx \frac{1}{n} \sum_i |q_P(u_i) - q_Q(u_i)|
    """
    if isinstance(true_rnd, np.ndarray):
        # true_rnd is an array of values on rnd.strikes
        true_density_vals = true_rnd
    else:
        true_density_vals = true_rnd.pdf(rnd.strikes)

    # Normalize both densities
    p_norm = rnd.density / float(np.trapz(rnd.density, rnd.strikes))
    q_norm = true_density_vals / float(np.trapz(true_density_vals, rnd.strikes))

    # Build CDFs
    from scipy.integrate import cumulative_trapezoid

    p_cdf = cumulative_trapezoid(p_norm, rnd.strikes, initial=0)
    q_cdf = cumulative_trapezoid(q_norm, rnd.strikes, initial=0)

    # Quantiles at uniform grid
    u_grid = np.linspace(0, 1, 100)
    from scipy.interpolate import interp1d

    # Use linear interpolation to handle duplicate CDF values
    p_quantile = interp1d(
        p_cdf, rnd.strikes, kind="linear", bounds_error=False, fill_value="extrapolate"
    )
    q_quantile = interp1d(
        q_cdf, rnd.strikes, kind="linear", bounds_error=False, fill_value="extrapolate"
    )

    p_q = p_quantile(u_grid)
    q_q = q_quantile(u_grid)

    wasserstein_dist = np.mean(np.abs(p_q - q_q))

    return float(wasserstein_dist)


def l2_distance(rnd: RiskNeutralDensity, true_rnd: RiskNeutralDensity | FloatArray) -> float:
    r"""Compute L2 distance between densities.

    Parameters
    ----------
    rnd : RiskNeutralDensity
        Estimated density.
    true_rnd : RiskNeutralDensity or FloatArray
        True density.

    Returns
    -------
    float
        Integrated squared difference: sqrt(int (p - q)^2 dS).
    """
    if isinstance(true_rnd, np.ndarray):
        true_density_vals = true_rnd
    else:
        true_density_vals = true_rnd.pdf(rnd.strikes)

    # Normalize
    p_norm = rnd.density / float(np.trapz(rnd.density, rnd.strikes))
    q_norm = true_density_vals / float(np.trapz(true_density_vals, rnd.strikes))

    diff_sq = (p_norm - q_norm) ** 2
    l2_val: float = float(np.sqrt(np.trapz(diff_sq, rnd.strikes)))

    return l2_val


def ks_distance(rnd: RiskNeutralDensity, true_rnd: RiskNeutralDensity | FloatArray) -> float:
    r"""Compute Kolmogorov-Smirnov distance between CDFs.

    Parameters
    ----------
    rnd : RiskNeutralDensity
        Estimated density.
    true_rnd : RiskNeutralDensity or FloatArray
        True density.

    Returns
    -------
    float
        max |F_p - F_q|.
    """
    if isinstance(true_rnd, np.ndarray):
        true_density_vals = true_rnd
    else:
        true_density_vals = true_rnd.pdf(rnd.strikes)

    # Normalize
    p_norm = rnd.density / float(np.trapz(rnd.density, rnd.strikes))
    q_norm = true_density_vals / float(np.trapz(true_density_vals, rnd.strikes))

    # CDFs
    from scipy.integrate import cumulative_trapezoid

    p_cdf = cumulative_trapezoid(p_norm, rnd.strikes, initial=0)
    q_cdf = cumulative_trapezoid(q_norm, rnd.strikes, initial=0)

    ks_val: float = float(np.max(np.abs(p_cdf - q_cdf)))

    return ks_val
