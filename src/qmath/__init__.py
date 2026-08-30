"""
qmath: Research library for option-implied risk-neutral density estimation.

This library provides tools for estimating risk-neutral probability densities
from option market data using the Breeden-Litzenberger framework, with emphasis
on arbitrage-free surface fitting and robust density recovery.
"""

__version__ = "0.1.0.dev0"

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
