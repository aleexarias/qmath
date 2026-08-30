"""Risk-neutral density estimation via Breeden-Litzenberger."""

from typing import TYPE_CHECKING, Any

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d

from qmath._typing import FloatArray

if TYPE_CHECKING:
    from qmath.surface.base import Smoother

__all__ = ["RiskNeutralDensity", "breeden_litzenberger"]


class RiskNeutralDensity:
    r"""Risk-neutral probability density of future spot price.

    Encapsulates the extracted density with methods for evaluation (pdf, cdf, quantile)
    and properties (moments).

    Parameters
    ----------
    strikes : FloatArray
        Grid of strikes where density is available.
    density : FloatArray
        Probability density values on the strike grid.
    forward : float
        Forward price (expected value under Q).
    discount : float
        Discount factor.
    """

    def __init__(
        self,
        strikes: FloatArray,
        density: FloatArray,
        forward: float,
        discount: float,
    ) -> None:
        """Initialize the density object."""
        self.strikes = np.asarray(strikes, dtype=np.float64)
        self.density = np.asarray(density, dtype=np.float64)
        self.forward = forward
        self.discount = discount

        # Normalize density to integrate to 1
        area_val: float = float(np.trapezoid(self.density, self.strikes))
        if area_val > 0:
            self.density = self.density / area_val

        # Build CDF via cumulative integration
        self.cdf_vals = cumulative_trapezoid(self.density, self.strikes, initial=0)
        self._cdf_interp = interp1d(
            self.strikes, self.cdf_vals, kind="cubic", bounds_error=False, fill_value=(0, 1)
        )

    def pdf(self, strikes: FloatArray) -> FloatArray:
        r"""Evaluate probability density function.

        Parameters
        ----------
        strikes : FloatArray
            Strikes where PDF is evaluated.

        Returns
        -------
        FloatArray
            Density values (non-negative, integrate to 1).
        """
        pdf_interp = interp1d(
            self.strikes, self.density, kind="cubic", bounds_error=False, fill_value=0
        )
        result: FloatArray = np.maximum(pdf_interp(strikes), 0)
        return result.astype(np.float64)

    def cdf(self, strikes: FloatArray) -> FloatArray:
        r"""Evaluate cumulative distribution function.

        Parameters
        ----------
        strikes : FloatArray
            Strikes where CDF is evaluated.

        Returns
        -------
        FloatArray
            CDF values in [0, 1].
        """
        result: FloatArray = np.clip(self._cdf_interp(strikes), 0, 1)
        return result.astype(np.float64)

    def quantile(self, p: float | FloatArray) -> FloatArray:
        r"""Compute quantile (inverse CDF).

        Parameters
        ----------
        p : float or FloatArray
            Probability level(s) in (0, 1).

        Returns
        -------
        FloatArray
            Quantile value(s).
        """
        p = np.atleast_1d(p)
        quantile_interp = interp1d(
            self.cdf_vals, self.strikes, kind="cubic", bounds_error=False, fill_value="extrapolate"
        )
        result: FloatArray = quantile_interp(p)
        return result.astype(np.float64)

    def mean(self) -> float:
        r"""Expected value under risk-neutral measure.

        Returns
        -------
        float
            E[S_T | S_0] = forward.
        """
        mean_computed = np.trapezoid(self.strikes * self.density, self.strikes)
        return float(mean_computed)

    def variance(self) -> float:
        r"""Variance under risk-neutral measure.

        Returns
        -------
        float
            Var[S_T | S_0].
        """
        mean_val = self.mean()
        second_moment: float = float(np.trapezoid(self.strikes**2 * self.density, self.strikes))
        return float(second_moment - mean_val * mean_val)

    def skewness(self) -> float:
        r"""Skewness of the density.

        Returns
        -------
        float
            (mu_3 - 3*mu_2*mu_1 + 2*mu_1^3) / sigma^3.
        """
        mean_val = self.mean()
        var = self.variance()
        std = np.sqrt(var)

        if std < 1e-10:
            return 0.0

        third_moment: float = float(
            np.trapezoid((self.strikes - mean_val) ** 3 * self.density, self.strikes)
        )
        return float(third_moment / (std**3))

    def plot(self, ax: Any = None) -> Any:
        r"""Plot the density (PDF and CDF).

        Parameters
        ----------
        ax : matplotlib.pyplot.Axes, optional
            Matplotlib axes object. If None, creates a new figure.

        Returns
        -------
        matplotlib.pyplot.Axes
            The axes object.
        """
        import matplotlib.pyplot as plt

        if ax is None:
            fig, ax_result = plt.subplots(figsize=(10, 6))
            ax = ax_result

        ax.plot(self.strikes, self.density, "b-", linewidth=2, label="PDF")
        ax.axvline(self.forward, color="r", linestyle="--", label=f"Forward = {self.forward:.2f}")
        ax.set_xlabel("Strike")
        ax.set_ylabel("Density")
        ax.set_title("Risk-Neutral Density")
        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RiskNeutralDensity(forward={self.forward:.4f}, "
            f"mean={self.mean():.4f}, std={np.sqrt(self.variance()):.4f})"
        )


def breeden_litzenberger(
    smoother: "Smoother",
    forward: float,
    discount: float,
) -> RiskNeutralDensity:
    r"""Extract risk-neutral density via Breeden-Litzenberger formula.

    Parameters
    ----------
    smoother : Smoother
        Fitted arbitrage-free surface smoother (e.g., FenglerSmoother).
    forward : float
        Inferred forward price.
    discount : float
        Inferred discount factor.

    Returns
    -------
    RiskNeutralDensity
        Object wrapping the extracted density.

    Notes
    -----
    The Breeden-Litzenberger formula relates the risk-neutral density to the
    second derivative of call prices with respect to strike:

    .. math::

        q(K) = e^{rT} \frac{\partial^2 C}{\partial K^2}

    We compute the second derivative analytically from the fitted cubic spline,
    avoiding numerical instability of finite differences on raw market data.

    References
    ----------
    Breeden, D. T., & Litzenberger, R. H. (1978).
    Prices of state-contingent claims implicit in option prices.
    *Journal of Business*, 51(4), 621-651.
    """
    from qmath.surface.fengler import FenglerSmoother

    if not isinstance(smoother, FenglerSmoother):
        msg = "Currently only FenglerSmoother is supported"
        raise TypeError(msg)

    if smoother.spline_ is None:
        msg = "Smoother must be fitted first"
        raise ValueError(msg)

    # Evaluation grid (use fitted strikes with some extra points)
    strikes = smoother.strikes_fit_
    if strikes is None:
        msg = "Smoother has no fitted strikes"
        raise ValueError(msg)

    # Compute second derivative analytically from cubic spline
    second_deriv_fn = smoother.spline_.derivative(nu=2)
    second_deriv = second_deriv_fn(strikes)

    # Breeden-Litzenberger: q(K) = e^{rT} * d²C/dK²
    density_vals: FloatArray = np.maximum(second_deriv / discount, 0)

    return RiskNeutralDensity(strikes, density_vals, forward, discount)
