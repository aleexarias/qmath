"""Base class for surface smoothers.

Provides sklearn-like fit/predict interface for smoothing option price surfaces.
"""

from abc import ABC, abstractmethod

from qmath._typing import FloatArray
from qmath.options.chain import OptionChain

__all__ = ["Smoother"]


class Smoother(ABC):
    """Abstract base class for option surface smoothers.

    All smoothers follow the sklearn-like pattern: fit(data) returns self,
    predict(strikes) returns smoothed values.
    """

    @abstractmethod
    def fit(self, chain: OptionChain, forward: float, discount: float) -> "Smoother":
        r"""Fit the smoother to the option chain data.

        Parameters
        ----------
        chain : OptionChain
            Option chain with mid prices.
        forward : float
            Inferred forward price.
        discount : float
            Inferred discount factor.

        Returns
        -------
        self
            Fitted smoother.
        """
        pass

    @abstractmethod
    def predict(self, strikes: FloatArray) -> FloatArray:
        r"""Predict smoothed call prices at strikes.

        Parameters
        ----------
        strikes : FloatArray
            Strike prices for evaluation.

        Returns
        -------
        FloatArray
            Smoothed call prices (arbitrage-free).
        """
        pass
