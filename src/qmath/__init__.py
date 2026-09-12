"""
qmath: A research library for quantitative finance.

This library provides typed, tested implementations of pricing models,
volatility-surface fits, and option-implied estimators behind a small and
consistent API, so that methods from different families can be composed and
compared on the same data. Everything fitted to data follows the same
``fit(data, **params) -> self`` / ``predict(data) -> result`` contract.

The first area built out is option-implied risk-neutral density recovery:
arbitrage-free surface fitting followed by Breeden-Litzenberger extraction.
"""

# Single source of truth for the project version. pyproject.toml and
# docs/conf.py derive from this line; CITATION.cff must be bumped by hand.
__version__ = "0.1.0"

from qmath.options import OptionChain, filter_chain, infer_forward
from qmath.rnd import RiskNeutralDensity, breeden_litzenberger
from qmath.surface import FenglerSmoother
from qmath.validation import wasserstein

__all__ = [
    "OptionChain",
    "filter_chain",
    "infer_forward",
    "RiskNeutralDensity",
    "breeden_litzenberger",
    "FenglerSmoother",
    "wasserstein",
]
