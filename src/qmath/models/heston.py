"""Heston model: characteristic function and COS pricing.

Implements the Heston stochastic volatility model with robust numerical methods
for the characteristic function (handling the "little trap") and semi-analytic
pricing via the Fourier-Cosine (COS) method.
"""

import numpy as np

from qmath._typing import FloatArray

__all__ = ["heston_cf", "cos_price", "cos_density"]


def heston_cf(
    u: FloatArray,
    S: float,
    K: FloatArray,
    T: float,
    r: float,
    v0: float,
    vbar: float,
    kappa: float,
    sigma_v: float,
    rho: float,
) -> np.ndarray:
    r"""Heston characteristic function using Albrecher et al. formulation.

    Parameters
    ----------
    u : FloatArray
        Frequency argument (real-valued).
    S : float
        Spot price.
    K : FloatArray
        Strikes (used to compute log-moneyness).
    T : float
        Time to maturity.
    r : float
        Risk-free rate.
    v0 : float
        Initial variance.
    vbar : float
        Long-run variance (mean-reversion level).
    kappa : float
        Mean-reversion speed.
    sigma_v : float
        Volatility of variance (vol-of-vol).
    rho : float
        Correlation between log-price and variance (-1, 1).

    Returns
    -------
    ndarray
        Complex-valued characteristic function phi(u) = E[exp(i*u*log(S_T/K))].

    Notes
    -----
    Uses the formulation of Albrecher, Mayer, Schoutens, and Tichy (2007)
    with the "little trap" correction to handle the discontinuity at u=i/2.
    """
    x = np.log(S / K)  # log-moneyness

    # Heston parameters
    lambda_ = kappa + 1j * rho * sigma_v * u
    gamma = np.sqrt(sigma_v**2 * (u**2 + 1j * u) + lambda_**2)
    d = 2 * gamma + (lambda_ + gamma)

    alpha = vbar * kappa / (sigma_v**2)
    beta = (lambda_ + gamma) / sigma_v**2

    # Log characteristic function
    log_cf = (
        1j * u * x
        + 1j * u * r * T
        + alpha * T * np.log(2 * gamma / (lambda_ + gamma))
        + (2 * alpha * np.log(1 - beta * (1 - np.exp(-gamma * T)) / d)) / sigma_v**2
    )

    # Handle the "little trap" at u = i/2 (corresponds to vega at ATM)
    tiny = 1e-14
    log_cf = np.where(np.abs(u) > tiny, log_cf, vbar * T * 1j * u)

    result_cf: np.ndarray = np.exp(log_cf)
    return result_cf


def cos_price(
    S: float,
    K: FloatArray,
    T: float,
    r: float,
    flag: str,
    v0: float,
    vbar: float,
    kappa: float,
    sigma_v: float,
    rho: float,
    n_terms: int = 256,
) -> FloatArray:
    r"""Price European options using the Fourier-Cosine (COS) method.

    Parameters
    ----------
    S : float
        Spot price.
    K : FloatArray
        Strike(s).
    T : float
        Time to maturity.
    r : float
        Risk-free rate.
    flag : str
        'C' for call, 'P' for put.
    v0 : float
        Initial variance.
    vbar : float
        Long-run variance.
    kappa : float
        Mean-reversion speed.
    sigma_v : float
        Vol-of-vol.
    rho : float
        Correlation.
    n_terms : int, default=256
        Number of Fourier series terms.

    Returns
    -------
    FloatArray
        Option price(s).

    References
    ----------
    Fang, F., & Oosterlee, C. W. (2008).
    A novel pricing method for European options based on Fourier-cosine series expansions.
    *SIAM Journal on Scientific Computing*, 31(2), 826-848.
    """
    df = np.exp(-r * T)

    # Integration limits (Fang-Oosterlee heuristic)
    c1 = r * T + (rho * sigma_v * kappa - 0.5 * sigma_v**2) * (1 - np.exp(-kappa * T)) / kappa
    c2 = v0 * (1 - np.exp(-kappa * T)) / kappa + vbar * (T - (1 - np.exp(-kappa * T)) / kappa)
    c4 = c2 + c1**2
    a = c1 - 4 * np.sqrt(c4)
    b = c1 + 4 * np.sqrt(c4)

    k = np.arange(n_terms, dtype=np.float64)
    u_k = k * np.pi / (b - a)

    # Compute characteristic function at u_k for each strike
    x = np.log(S / K)  # log-moneyness

    # COS series summation
    chi = np.zeros_like(K, dtype=np.complex128)
    psi = np.zeros_like(K, dtype=np.complex128)

    for j, k_val in enumerate(k):
        # CF evaluated at frequencies u_k
        cf_val = heston_cf(
            np.full_like(K, u_k[j], dtype=np.float64), S, K, T, r, v0, vbar, kappa, sigma_v, rho
        )
        real_cf = np.real(cf_val)
        imag_cf = np.imag(cf_val)

        chi += np.exp(1j * u_k[j] * a) * real_cf * np.cos(k_val * np.pi * (x - a) / (b - a))

        if k_val > 0:
            psi += np.exp(1j * u_k[j] * a) * imag_cf * np.sin(k_val * np.pi * (x - a) / (b - a))

    # Option pricing
    if flag.upper() == "C":
        price = S * (0.5 * chi) - df * K * (0.5 * chi - psi)
    else:
        price = df * K * (0.5 - chi + psi) - S * (0.5 - chi)

    result: FloatArray = np.real(price)
    return result.astype(np.float64)


def cos_density(
    spot: float,
    strikes: FloatArray,
    T: float,
    r: float,
    v0: float,
    vbar: float,
    kappa: float,
    sigma_v: float,
    rho: float,
    n_terms: int = 256,
) -> FloatArray:
    r"""Risk-neutral density via Heston COS method.

    Parameters
    ----------
    spot : float
        Current spot price.
    strikes : FloatArray
        Grid of strikes where density is evaluated.
    T : float
        Time to maturity.
    r : float
        Risk-free rate.
    v0 : float
        Initial variance.
    vbar : float
        Long-run variance.
    kappa : float
        Mean-reversion speed.
    sigma_v : float
        Vol-of-vol.
    rho : float
        Correlation.
    n_terms : int, default=256
        Number of terms in the expansion.

    Returns
    -------
    FloatArray
        Risk-neutral density q(S_T | S_0 = spot) at strikes.
    """
    df = np.exp(-r * T)

    # Integration limits
    c1 = r * T + (rho * sigma_v * kappa - 0.5 * sigma_v**2) * (1 - np.exp(-kappa * T)) / kappa
    c2 = v0 * (1 - np.exp(-kappa * T)) / kappa + vbar * (T - (1 - np.exp(-kappa * T)) / kappa)
    c4 = c2 + c1**2
    a = c1 - 4 * np.sqrt(c4)
    b = c1 + 4 * np.sqrt(c4)

    # Fourier frequencies
    k = np.arange(n_terms, dtype=np.float64)
    u_k = k * np.pi / (b - a)

    # Log returns relative to the interval
    x = np.log(strikes / spot)

    # Density via inverse Fourier (cosine series)
    density = np.zeros_like(strikes, dtype=np.float64)

    for j, k_val in enumerate(k):
        # CF evaluated at frequency u_k[j] for each strike
        cf_val = heston_cf(
            np.full_like(strikes, u_k[j], dtype=np.float64),
            spot,
            strikes,
            T,
            r,
            v0,
            vbar,
            kappa,
            sigma_v,
            rho,
        )
        Re_cf = np.real(cf_val)
        wt = 2.0 if k_val > 0 else 1.0
        density += wt * Re_cf * np.cos(k_val * np.pi * (x - a) / (b - a))

    density *= np.pi / (b - a) * df

    result: FloatArray = np.maximum(density, 0)
    return result.astype(np.float64)
