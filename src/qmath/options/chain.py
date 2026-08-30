"""OptionChain: market data structure for option quotes.

Represents a snapshot of an option expiration: strikes, bid-ask quotes,
time to maturity, and optional true risk-neutral density for validation.
"""

from dataclasses import dataclass

import numpy as np

from qmath._typing import FloatArray

__all__ = ["OptionChain"]


@dataclass
class OptionChain:
    """A single option expiration's market quotes and metadata.

    Parameters
    ----------
    strikes : FloatArray
        Strike prices.
    bid : FloatArray
        Bid prices (calls).
    ask : FloatArray
        Ask prices (calls).
    T : float
        Time to maturity (years).
    spot : float
        Spot price at snapshot time.
    rate : float, default=0.0
        Risk-free rate.
    dividend_yield : float, default=0.0
        Continuous dividend yield (not yet used).
    true_density : FloatArray, optional
        True risk-neutral density on the strike grid (for synthetic/validation data).
    """

    strikes: FloatArray
    bid: FloatArray
    ask: FloatArray
    T: float
    spot: float
    rate: float = 0.0
    dividend_yield: float = 0.0
    true_density: FloatArray | None = None

    def __post_init__(self) -> None:
        """Validate the chain structure."""
        n = len(self.strikes)
        if len(self.bid) != n or len(self.ask) != n:
            msg = "bid, ask, strikes must have same length"
            raise ValueError(msg)
        if np.any(self.ask < self.bid):
            msg = "Some ask < bid (bad spread)"
            raise ValueError(msg)
        if self.T <= 0:
            msg = f"T must be positive, got {self.T}"
            raise ValueError(msg)
        if self.spot <= 0:
            msg = f"spot must be positive, got {self.spot}"
            raise ValueError(msg)

    @property
    def mid(self) -> FloatArray:
        """Mid price = (bid + ask) / 2."""
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> FloatArray:
        """Bid-ask spread."""
        return self.ask - self.bid

    def __len__(self) -> int:
        """Number of strikes."""
        return len(self.strikes)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OptionChain(n_strikes={len(self)}, T={self.T:.4f}, "
            f"spot={self.spot:.2f}, bid_range=[{self.bid.min():.4f}, {self.bid.max():.4f}])"
        )
