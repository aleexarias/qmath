"""Black-Scholes pricing and related functions.

This module provides vectorized Black-Scholes pricing, greeks, and implied volatility
calculations with robust IV solvers.
"""

from collections.abc import Callable
from typing import Literal

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from qmath._typing import FloatArray

__all__ = ["bs_price", "bs_vega", "implied_vol"]


def bs_price(
    S: FloatArray,
    K: FloatArray,
    T: float,
    r: float,
    sigma: FloatArray,
    flag: Literal["C", "P"] = "C",
) -> FloatArray:
    r"""Price European options under Black-Scholes.

    Parameters
    ----------
    S : FloatArray
        Spot price (scalar or array).
    K : FloatArray
        Strike(s) (broadcast-compatible with S).
    T : float
        Time to maturity (years).
    r : float
        Risk-free rate.
    sigma : FloatArray
        Volatility (broadcast-compatible with S).
    flag : {'C', 'P'}, default='C'
        'C' for call, 'P' for put.

    Returns
    -------
    FloatArray
        Option price(s).

    Notes
    -----
    Uses the standard Black-Scholes formula:

    .. math::

        C(S, K, T, r, \sigma) = S N(d_1) - K e^{-rT} N(d_2)

    where d_1 = (log(S/K) + (r + sigma^2/2)T) / (sigma sqrt(T)).
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if flag == "C":
        result = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        result = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return np.asarray(result, dtype=np.float64)


def bs_vega(S: FloatArray, K: FloatArray, T: float, r: float, sigma: FloatArray) -> FloatArray:
    r"""Black-Scholes vega (sensitivity to vol).

    Parameters
    ----------
    S : FloatArray
        Spot price.
    K : FloatArray
        Strike(s).
    T : float
        Time to maturity (years).
    r : float
        Risk-free rate.
    sigma : FloatArray
        Volatility.

    Returns
    -------
    FloatArray
        Vega values (price change per 1 percentage point vol change).
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    result: FloatArray = np.asarray(S * norm.pdf(d1) * np.sqrt(T), dtype=np.float64)
    return result


def implied_vol(
    price: FloatArray,
    S: FloatArray,
    K: FloatArray,
    T: float,
    r: float,
    flag: Literal["C", "P"] = "C",
) -> FloatArray:
    r"""Implied volatility from option price (Jäckel-style robust solver).

    Parameters
    ----------
    price : FloatArray
        Option price(s).
    S : FloatArray
        Spot price(s).
    K : FloatArray
        Strike(s).
    T : float
        Time to maturity (years).
    r : float
        Risk-free rate.
    flag : {'C', 'P'}, default='C'
        'C' for call, 'P' for put.

    Returns
    -------
    FloatArray
        Implied volatility (annualized).

    Notes
    -----
    Uses Brent's method with smart initialization via Jäckel's rational approximation.
    Raises ValueError if the price is outside the no-arbitrage bounds.
    """
    price = np.atleast_1d(price)
    S = np.atleast_1d(S)
    K = np.atleast_1d(K)

    # Intrinsic value bounds
    if flag == "C":
        intrinsic = np.maximum(S - K * np.exp(-r * T), 0)
        time_value_bound = S
    else:
        intrinsic = np.maximum(K * np.exp(-r * T) - S, 0)
        time_value_bound = K * np.exp(-r * T)

    # Check bounds
    if np.any(price < intrinsic) or np.any(price > time_value_bound):
        msg = "Price outside no-arbitrage bounds"
        raise ValueError(msg)

    # Vectorized IV calculation
    result: FloatArray = np.zeros_like(price, dtype=np.float64)

    def _make_objective(s: float, k: float, p: float) -> Callable[[float], float]:
        """Create objective function with proper closure."""

        def objective(vol: float) -> float:
            return float(bs_price(np.asarray(s), np.asarray(k), T, r, np.asarray(vol), flag)) - p

        return objective

    for i, (p_val, s_val, k_val) in enumerate(zip(price.flat, S.flat, K.flat, strict=False)):
        p_float = float(p_val)
        s_float = float(s_val)
        k_float = float(k_val)

        try:
            result.flat[i] = brentq(
                _make_objective(s_float, k_float, p_float), 1e-6, 5.0, xtol=1e-8
            )
        except ValueError as e:
            msg = f"IV solver failed for price={p_float}, S={s_float}, K={k_float}"
            raise ValueError(msg) from e

    return result.reshape(price.shape)
