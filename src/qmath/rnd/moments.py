"""Model-free variance, skewness, and kurtosis from option prices.

Implements model-free moment extraction via the Bakshi-Kapadia-Madan (2003) method.
These moments are extracted directly from option prices without any distributional
assumptions, providing pure market-implied measures of risk.
"""

import numpy as np

from qmath._typing import FloatArray

__all__ = ["model_free_variance", "model_free_skewness", "model_free_kurtosis"]


def model_free_variance(
    strikes: FloatArray,
    call_prices: FloatArray,
    put_prices: FloatArray,
    forward: float,
    discount: float,
) -> float:
    r"""Model-free variance from option prices (Bakshi-Kapadia-Madan 2003).

    Parameters
    ----------
    strikes : FloatArray
        Strike prices.
    call_prices : FloatArray
        European call prices.
    put_prices : FloatArray
        European put prices.
    forward : float
        Forward price.
    discount : float
        Discount factor.

    Returns
    -------
    float
        Model-free variance (squared volatility).

    Notes
    -----
    The model-free variance is:

    .. math::

        \sigma_{MF}^2 = \frac{2}{T} \left[ \int_0^F \frac{P(K)}{K^2} dK +
                                        \int_F^\infty \frac{C(K)}{K^2} dK \right]

    This integrates the "volatility surface" implied by option prices, weighting
    each strike by 1/K^2.
    """
    K = strikes
    otm_put_mask = K < forward
    otm_call_mask = K >= forward

    # Split into OTM regions
    K_put = K[otm_put_mask]
    P_put = put_prices[otm_put_mask]

    K_call = K[otm_call_mask]
    C_call = call_prices[otm_call_mask]

    # Integrate using trapezoidal rule
    if len(K_put) > 1:
        variance_put = np.trapz(P_put / K_put**2, K_put)
    else:
        variance_put = 0.0

    if len(K_call) > 1:
        variance_call = np.trapz(C_call / K_call**2, K_call)
    else:
        variance_call = 0.0

    T = 1.0  # Assume T=1 for annualized measure
    mf_var = (2 / T) * (variance_put + variance_call) / discount

    return float(np.maximum(mf_var, 0))


def model_free_skewness(
    strikes: FloatArray,
    call_prices: FloatArray,
    put_prices: FloatArray,
    forward: float,
    discount: float,
) -> float:
    r"""Model-free skewness from option prices.

    Parameters
    ----------
    strikes : FloatArray
        Strike prices.
    call_prices : FloatArray
        European call prices.
    put_prices : FloatArray
        European put prices.
    forward : float
        Forward price.
    discount : float
        Discount factor.

    Returns
    -------
    float
        Model-free skewness (normalized third moment).

    Notes
    -----
    Skewness measures the asymmetry of the risk-neutral distribution.
    Negative values indicate left tail risk (crash risk).
    """
    var = model_free_variance(strikes, call_prices, put_prices, forward, discount)

    if var < 1e-10:
        return 0.0

    K = strikes
    otm_put_mask = K < forward
    otm_call_mask = K >= forward

    # Compute third moment
    K_put = K[otm_put_mask]
    P_put = put_prices[otm_put_mask]

    K_call = K[otm_call_mask]
    C_call = call_prices[otm_call_mask]

    T = 1.0
    third_moment_put = (2 / T) * np.trapz(P_put * np.log(forward / K_put) / K_put**2, K_put) / discount
    third_moment_call = (2 / T) * np.trapz(C_call * np.log(forward / K_call) / K_call**2, K_call) / discount

    skewness = (third_moment_put + third_moment_call) / (var ** 1.5)

    return float(skewness)


def model_free_kurtosis(
    strikes: FloatArray,
    call_prices: FloatArray,
    put_prices: FloatArray,
    forward: float,
    discount: float,
) -> float:
    r"""Model-free kurtosis from option prices.

    Parameters
    ----------
    strikes : FloatArray
        Strike prices.
    call_prices : FloatArray
        European call prices.
    put_prices : FloatArray
        European put prices.
    forward : float
        Forward price.
    discount : float
        Discount factor.

    Returns
    -------
    float
        Model-free (excess) kurtosis.

    Notes
    -----
    Kurtosis measures tail fatness. Values > 0 indicate fatter tails than normal.
    This is model-free and purely extracted from observed option prices.
    """
    var = model_free_variance(strikes, call_prices, put_prices, forward, discount)

    if var < 1e-10:
        return 0.0

    K = strikes
    otm_put_mask = K < forward
    otm_call_mask = K >= forward

    K_put = K[otm_put_mask]
    P_put = put_prices[otm_put_mask]

    K_call = K[otm_call_mask]
    C_call = call_prices[otm_call_mask]

    T = 1.0
    fourth_moment_put = (2 / T) * np.trapz(P_put * (np.log(forward / K_put)) ** 2 / K_put**2, K_put) / discount
    fourth_moment_call = (2 / T) * np.trapz(C_call * (np.log(forward / K_call)) ** 2 / K_call**2, K_call) / discount

    kurtosis = (fourth_moment_put + fourth_moment_call) / (var**2) - 3  # Excess kurtosis

    return float(kurtosis)
