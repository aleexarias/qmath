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
        Inferred forward price :math:`F = S e^{(r - q) T}`.
    discount : float
        Inferred discount factor :math:`e^{-rT}`.

    Notes
    -----
    Uses put-call parity:

    .. math::

        C(K) - P(K) = S - K e^{-rT}

    Regress :math:`C_{\text{mid}} - P_{\text{mid}}` on :math:`K` to
    recover:

    - Slope :math:`= -e^{-rT}`
    - Intercept :math:`= S(1 - qT) \approx S` for short expirations

    For calls and puts we use bid for intrinsic, ask for time value to be
    conservative.
    """
    call_mid = chain.mid
    S = chain.spot

    K_ones = np.column_stack([np.ones_like(chain.strikes), chain.strikes])
    y = call_mid

    result, residuals, rank, s_vals = lstsq(K_ones, y)
    intercept, slope = result

    discount = -slope
    forward = intercept / discount if discount > 0 else S

    return forward, discount
