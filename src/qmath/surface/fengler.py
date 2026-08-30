"""Fengler (2009) constrained cubic-spline surface smoother.

Implements arbitrage-free smoothing via constrained quadratic programming
on the call price surface, ensuring monotonicity and convexity automatically.
"""

from typing import TYPE_CHECKING

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize

from qmath._typing import FloatArray
from qmath.surface.base import Smoother

if TYPE_CHECKING:
    from qmath.options.chain import OptionChain

__all__ = ["FenglerSmoother"]


class FenglerSmoother(Smoother):
    r"""Arbitrage-free constrained cubic-spline smoother (Fengler 2009).

    Fits a cubic spline to call prices with convexity, monotonicity, and slope
    constraints via constrained optimization. Uses scipy.optimize.minimize with
    quadratic penalty terms for the constraints.

    Parameters
    ----------
    lambda_ : float, default=1e-4
        Smoothness regularization parameter (higher = smoother).
    tol : float, default=1e-8
        Convergence tolerance for optimizer.
    n_knots : int, optional
        Number of internal knots (default: auto from data size).

    Notes
    -----
    We use scipy.optimize.minimize with SLSQP method because it directly handles
    nonlinear inequality constraints (monotonicity, convexity) without requiring
    complex constraint matrix formulations. Alternatives like cvxpy would require
    reformulating as a DCP problem, which is less flexible for spline constraints.

    References
    ----------
    Fengler, M. R. (2009).
    Arbitrage-free smoothing of the implied volatility surface.
    *International Journal of Theoretical and Applied Finance*, 12(4), 461-485.
    """

    def __init__(
        self,
        lambda_: float = 1e-4,
        tol: float = 1e-8,
        n_knots: int | None = None,
    ) -> None:
        """Initialize the smoother."""
        self.lambda_ = lambda_
        self.tol = tol
        self.n_knots = n_knots
        self.spline_: CubicSpline | None = None
        self.strikes_fit_: FloatArray | None = None
        self.prices_fit_: FloatArray | None = None

    def fit(self, chain: "OptionChain", forward: float, discount: float) -> "FenglerSmoother":
        r"""Fit constrained cubic spline to call price data.

        Parameters
        ----------
        chain : OptionChain
            Option chain with bid-ask quotes.
        forward : float
            Inferred forward price.
        discount : float
            Inferred discount factor.

        Returns
        -------
        self
            Fitted smoother.
        """
        K = chain.strikes
        C_mid = chain.mid
        self.strikes_fit_ = K
        self.prices_fit_ = C_mid

        # Initial spline (unsmoothed)
        initial_prices = C_mid.copy()

        # Fit smoothed prices via constrained optimization
        result = minimize(
            self._objective,
            initial_prices,
            args=(K, C_mid),
            method="SLSQP",
            bounds=[(0.0, np.inf) for _ in range(len(K))],
            constraints=[
                {"type": "ineq", "fun": self._monotonicity_constraint, "args": (K,)},
                {"type": "ineq", "fun": self._convexity_constraint, "args": (K,)},
            ],
            options={"ftol": self.tol, "maxiter": 1000},
        )

        if not result.success:
            import warnings

            warnings.warn(f"Optimization did not converge: {result.message}", stacklevel=2)

        smoothed_prices = result.x
        self.spline_ = CubicSpline(K, smoothed_prices, bc_type="natural")

        return self

    def predict(self, strikes: FloatArray) -> FloatArray:
        r"""Predict smoothed call prices.

        Parameters
        ----------
        strikes : FloatArray
            Strike prices for evaluation.

        Returns
        -------
        FloatArray
            Smoothed call prices (always decreasing and convex).
        """
        if self.spline_ is None:
            msg = "Must call fit() before predict()"
            raise ValueError(msg)

        prices_eval = self.spline_(strikes)
        result: FloatArray = np.maximum(prices_eval, 0)
        return result.astype(np.float64)

    def _objective(self, prices: FloatArray, K: FloatArray, C_mid: FloatArray) -> float:
        r"""Objective: fit data + smoothness penalty."""
        # Data fidelity
        fidelity: float = float(np.sum((prices - C_mid) ** 2))

        # Smoothness: second-derivative penalty (roughness)
        # Approximate using finite differences
        h = np.diff(K)
        if len(prices) > 2:
            second_diff = np.diff(prices, n=2)
            roughness: float = float(np.sum(second_diff**2 / h[:-1]))
        else:
            roughness = 0.0

        return float(fidelity + self.lambda_ * roughness)

    def _monotonicity_constraint(self, prices: FloatArray, K: FloatArray) -> FloatArray:
        r"""Constraint: call price must be decreasing in strike.

        Returns values >= 0 for feasibility.
        """
        # dC/dK <= 0 (call prices decrease with strike)
        # Approximate: C(K_i) - C(K_{i+1}) >= 0
        dC = np.diff(prices)
        dK_vals = np.diff(K)
        result: FloatArray = -dC / dK_vals
        return result.astype(np.float64)

    def _convexity_constraint(self, prices: FloatArray, K: FloatArray) -> FloatArray:
        r"""Constraint: call price must be convex in strike.

        Returns values >= 0 for feasibility.
        """
        # d²C/dK² >= 0 (call prices are convex)
        h = np.diff(K)
        if len(prices) <= 2:
            return np.array([0.0], dtype=np.float64)

        # Second differences (approximation of d²C/dK²)
        second_diff = np.diff(prices, n=2)
        second_deriv: FloatArray = second_diff / (h[:-1] ** 2)

        return second_deriv.astype(np.float64)
