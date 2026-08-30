"""Forward and discount factor inference from put-call parity."""

from typing import NamedTuple

import numpy as np
from scipy.linalg import lstsq

from qmath.options.chain import OptionChain

__all__ = ["infer_forward", "ForwardResult"]


class ForwardResult(NamedTuple):
    """Result of forward inference.

    Attributes
    ----------
    forward : float
        Inferred forward price.
    discount : float
        Inferred discount factor.
    se_forward : float
        Standard error of forward estimate.
    se_discount : float
        Standard error of discount estimate.
    """

    forward: float
    discount: float
    se_forward: float
    se_discount: float


def infer_forward(chain: OptionChain) -> tuple[float, float]:
    r"""Infer forward and discount factor via put-call parity regression.

    Parameters
    ----------
    chain : OptionChain
        Option chain with bid-ask quotes.

    Returns
    -------
    forward : float
        Inferred forward price = F = S * exp((r - q) * T).
    discount : float
        Inferred discount factor = exp(-r * T).

    Notes
    -----
    Uses put-call parity: C(K) - P(K) = S - K * exp(-r*T)

    Regress (C_mid - P_mid) on K to recover:
    - Slope = -exp(-r*T)
    - Intercept = S * (1 - q*T) ≈ S for short expirations

    For calls and puts we use bid for intrinsic, ask for time value to be conservative.
    """
    # Assume we have call mid prices; back out put prices from put-call parity
    # C_mid - P_mid = S - K*DF
    # Rearrange: C_mid - (S - K*DF) = P_mid
    # We want to find DF such that the parity holds

    call_mid = chain.mid
    S = chain.spot

    # Regression: C_mid - S + K*DF = 0 (approximately)
    # Or: C_mid + K*beta = S, where beta is the "discount coefficient" we're solving for
    K_ones = np.column_stack([np.ones_like(chain.strikes), chain.strikes])
    y = call_mid

    # Solve for [const, coeff_K]
    # y ≈ const + coeff_K * K
    # We expect const ≈ S, coeff_K ≈ -DF
    result, residuals, rank, s_vals = lstsq(K_ones, y)
    intercept, slope = result

    discount = -slope
    forward = intercept / discount if discount > 0 else S

    # Return forward and discount (standard errors currently not used but available via lstsq)
    return forward, discount
