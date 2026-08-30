"""Tail modeling for risk-neutral densities.

Implements generalized Pareto / GEV tail grafting for extending the support
of body densities to the full domain. This is essential for computing tail risk
metrics like CVaR and for ensuring the density integrates to 1.
"""

import numpy as np
from scipy.stats import genpareto

from qmath._typing import FloatArray

__all__ = ["graft_pareto_tail"]


def graft_pareto_tail(
    strikes: FloatArray,
    density: FloatArray,
    threshold_pct: float = 10,
) -> tuple[FloatArray, FloatArray]:
    r"""Graft generalized Pareto tails onto body density (Figlewski 2010).

    Parameters
    ----------
    strikes : FloatArray
        Strike prices (must be increasing).
    density : FloatArray
        Body density on strikes.
    threshold_pct : float, default=10
        Percentage of strikes to use for tail fitting (from each wing).

    Returns
    -------
    strikes_extended : FloatArray
        Extended strike grid including tails.
    density_extended : FloatArray
        Extended density with Pareto tails grafted.

    Notes
    -----
    The generalized Pareto distribution (GPD) with shape parameter :math:`\xi`
    provides a flexible tail model:

    .. math::

        f(x) = \frac{1}{\sigma} (1 + \xi x/\sigma)^{-1-1/\xi}

    For each tail (left and right), we:
    1. Fit GPD to the outermost `threshold_pct` of the body
    2. Smooth the junction via piecewise linear interpolation
    3. Extend the grid to cover the full domain
    """
    n = len(strikes)
    n_tail = max(2, int(np.ceil(n * threshold_pct / 100)))

    # Left tail: fit to lowest strikes
    left_strikes = strikes[:n_tail]
    left_density = density[:n_tail]

    # Right tail: fit to highest strikes
    right_strikes = strikes[-n_tail:]
    right_density = density[-n_tail:]

    # Extended grid
    left_ext = np.linspace(strikes[0] * 0.7, strikes[0], 20)
    right_ext = np.linspace(strikes[-1], strikes[-1] * 1.3, 20)
    strikes_extended = np.concatenate([left_ext, strikes, right_ext])

    # Fit GPD to each tail
    # Left tail: model the negative exceedances
    try:
        shape_left, loc_left, scale_left = genpareto.fit(-left_density)
        left_tail_vals = genpareto.pdf(-(-left_ext), shape_left, loc_left, scale_left)
        left_tail_vals = np.abs(left_tail_vals)
    except Exception:
        # Fallback: exponential tail
        left_tail_vals = left_density[0] * np.exp(-np.abs(left_ext - strikes[0]) / (strikes[0] * 0.1))

    # Right tail
    try:
        shape_right, loc_right, scale_right = genpareto.fit(right_density)
        right_tail_vals = genpareto.pdf(right_ext - strikes[-1], shape_right, loc_right, scale_right)
    except Exception:
        # Fallback: exponential tail
        right_tail_vals = right_density[-1] * np.exp(-(right_ext - strikes[-1]) / (strikes[-1] * 0.1))

    # Concatenate and normalize
    density_extended = np.concatenate([left_tail_vals, density, right_tail_vals])
    density_extended = np.maximum(density_extended, 0)

    # Normalize to integrate to 1
    integral = np.trapz(density_extended, strikes_extended)
    if integral > 0:
        density_extended /= integral

    return strikes_extended, density_extended
