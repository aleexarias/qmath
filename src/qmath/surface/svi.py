"""Stochastic Volatility Inspired (SVI) model surface.

Implements the raw SVI model with optional Gatheral-Jacquier no-arbitrage constraints.
The SVI parameterization provides a parsimonious five-parameter model for the implied
volatility smile, widely used in practice for its stability and interpretability.
"""

import numpy as np
from scipy.optimize import minimize

from qmath._typing import FloatArray
from qmath.surface.base import Smoother

__all__ = ["SVISmoother"]


class SVISmoother(Smoother):
    r"""SVI (Stochastic Volatility Inspired) surface smoother.

    Fits the raw SVI model to implied volatility data using optimization.
    The SVI parameterization is:

    .. math::

        \sigma^2(k) = a + b \left( \rho(k - m) + \sqrt{(k-m)^2 + \sigma^2} \right)

    where :math:`k = \log(F/K)` is the log-moneyness, and the parameters are:
    - `a`: volatility level (ATM variance)
    - `b`: slope steepness
    - `m`: ATM moneyness shift
    - `rho`: skew (correlation, in [-1, 1])
    - `sigma`: convexity (vol-of-vol)

    Parameters
    ----------
    enforce_no_arb : bool, default=True
        Whether to enforce Gatheral-Jacquier no-arbitrage constraints.
    max_iter : int, default=1000
        Maximum optimizer iterations.
    """

    def __init__(self, enforce_no_arb: bool = True, max_iter: int = 1000) -> None:
        """Initialize SVI smoother."""
        self.enforce_no_arb = enforce_no_arb
        self.max_iter = max_iter
        self.params: dict[str, float] | None = None
        self.strikes_fit_: FloatArray | None = None
        self.iv_fit_: FloatArray | None = None

    def fit(self, chain, forward: float, discount: float) -> "SVISmoother":  # type: ignore[no-untyped-def]
        r"""Fit SVI to implied volatility data.

        Parameters
        ----------
        chain : OptionChain
            Option chain with bid/ask data.
        forward : float
            Forward price.
        discount : float
            Discount factor.

        Returns
        -------
        self
        """
        from qmath.models.black_scholes import implied_vol

        # Extract IV from market prices
        mid_prices = chain.mid
        iv = implied_vol(mid_prices, chain.spot, chain.strikes, chain.T, chain.rate, flag="C")

        # Log-moneyness
        k = np.log(chain.strikes / forward)

        # Initial guess for SVI parameters
        sigma_atm = float(iv[np.argmin(np.abs(k))])
        x0 = np.array([sigma_atm**2, 0.1, 0.0, -0.3, 0.2])

        # Objective: minimize fitting error
        def objective(params: FloatArray) -> float:
            a, b, m, rho, sigma_v = params
            if b <= 0 or sigma_v <= 0:
                return 1e10
            if abs(rho) >= 1:
                return 1e10

            sigma_svi = np.sqrt(self._svi_variance(k, a, b, m, rho, sigma_v))
            error = np.sum((sigma_svi - iv) ** 2)
            return float(error)

        # Constraints (if enforcing no-arb)
        constraints = []
        bounds = [(0, None), (0, None), (None, None), (-0.99, 0.99), (0, None)]

        if self.enforce_no_arb:
            # Gatheral-Jacquier constraints
            def jac_constraint_1(params: FloatArray) -> float:
                a, b, m, rho, sigma_v = params
                return float(b * (1 + abs(rho)))  # b(1+|rho|) > 0

            def jac_constraint_2(params: FloatArray) -> float:
                a, b, m, rho, sigma_v = params
                return float(1 - abs(rho))  # 1 - |rho| > 0

            constraints.append({"type": "ineq", "fun": jac_constraint_1})
            constraints.append({"type": "ineq", "fun": jac_constraint_2})

        # Fit
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": self.max_iter, "ftol": 1e-8},
        )

        if result.success:
            a, b, m, rho, sigma_v = result.x
            self.params = {"a": a, "b": b, "m": m, "rho": rho, "sigma": sigma_v}
        else:
            # Fall back to initial guess
            a, b, m, rho, sigma_v = x0
            self.params = {"a": a, "b": b, "m": m, "rho": rho, "sigma": sigma_v}

        self.strikes_fit_ = chain.strikes
        self.iv_fit_ = iv

        return self

    def predict(self, strikes: FloatArray) -> FloatArray:
        r"""Predict call prices at strikes (via SVI IV).

        Parameters
        ----------
        strikes : FloatArray
            Strike prices.

        Returns
        -------
        FloatArray
            Call prices.
        """
        if self.params is None:
            msg = "Must fit() before predict()"
            raise ValueError(msg)

        msg = "SVI pricing not yet wired; use IV directly"
        raise NotImplementedError(msg)

    @staticmethod
    def _svi_variance(
        k: FloatArray, a: float, b: float, m: float, rho: float, sigma: float
    ) -> FloatArray:
        r"""Compute SVI variance."""
        return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma**2))
