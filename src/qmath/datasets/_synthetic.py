"""Synthetic option chain generation from known models."""

import numpy as np

from qmath.models.black_scholes import bs_price
from qmath.options.chain import OptionChain

__all__ = ["synthetic_heston_chain"]


def synthetic_heston_chain(
    T: float,
    n_strikes: int = 40,
    noise_bps: float = 25,
    seed: int | None = None,
    spot: float = 100.0,
    rate: float = 0.02,
    v0: float = 0.04,
    vbar: float = 0.04,
    kappa: float = 2.0,
    sigma_v: float = 0.3,
    rho: float = -0.5,
) -> OptionChain:
    r"""Generate a synthetic option chain from a Black-Scholes model with smile.

    Parameters
    ----------
    T : float
        Time to maturity (years).
    n_strikes : int, default=40
        Number of strikes.
    noise_bps : float, default=25
        Bid-ask spread as basis points of mid price.
    seed : int, optional
        Random seed for reproducibility.
    spot : float, default=100.0
        Current spot price.
    rate : float, default=0.02
        Risk-free rate.
    v0 : float, default=0.04
        Initial variance (annualized squared).
    vbar : float, default=0.04
        Long-run variance.
    kappa : float, default=2.0
        Mean-reversion speed.
    sigma_v : float, default=0.3
        Volatility of variance (vol-of-vol).
    rho : float, default=-0.5
        Correlation between log-price and variance.

    Returns
    -------
    OptionChain
        Synthetic chain with true density attached.

    Notes
    -----
    For now, uses Black-Scholes with a volatility smile (moneyness-dependent vol).
    Future versions will use full Heston COS pricing and density extraction.
    """
    rng = np.random.default_rng(seed)

    # Strike grid: symmetric in log-space around forward
    forward = spot * np.exp(rate * T)
    std_log = np.sqrt(v0 * T)
    log_strikes = np.linspace(-2 * std_log, 2 * std_log, n_strikes)
    strikes = forward * np.exp(log_strikes)

    # Create a simple volatility smile (increases away from ATM)
    moneyness = strikes / forward
    smile_vol = np.sqrt(v0) * (1 + 0.1 * (moneyness - 1) ** 2)

    # Price calls under Black-Scholes with smile
    spot_arr = np.asarray(spot, dtype=np.float64)
    call_prices = bs_price(spot_arr, strikes, T, rate, smile_vol, flag="C")

    # Simple proxy for true density (from BS Smile)
    # Compute from numerical second derivative
    dk = (strikes[1] - strikes[0]) / 2
    true_density = np.zeros(n_strikes)
    df = np.exp(-rate * T)
    for i in range(1, n_strikes - 1):
        c_up = bs_price(
            spot_arr, np.asarray(strikes[i] + dk, dtype=np.float64), T, rate, smile_vol[i], flag="C"
        )
        c_down = bs_price(
            spot_arr, np.asarray(strikes[i] - dk, dtype=np.float64), T, rate, smile_vol[i], flag="C"
        )
        true_density[i] = (float(c_up) - 2 * call_prices[i] + float(c_down)) / (dk**2) / df

    # Handle boundaries
    true_density[0] = true_density[1]
    true_density[-1] = true_density[-2]
    true_density = np.maximum(true_density, 0)

    # Add bid-ask spread and noise
    mid_calls = call_prices
    spread_abs = np.maximum(mid_calls * noise_bps / 10000, 0.01)
    bid_calls = mid_calls - spread_abs / 2 + rng.normal(0, spread_abs / 4, n_strikes)
    ask_calls = mid_calls + spread_abs / 2 + rng.normal(0, spread_abs / 4, n_strikes)

    # Ensure bid < ask and bid >= 0
    bid_calls = np.maximum(bid_calls, 0.001)
    ask_calls = np.maximum(ask_calls, bid_calls + 0.001)

    return OptionChain(
        strikes=strikes,
        bid=bid_calls,
        ask=ask_calls,
        T=T,
        spot=spot,
        rate=rate,
        true_density=true_density,
    )
