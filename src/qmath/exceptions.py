"""Exception classes for qmath."""


class QmathError(Exception):
    """Base exception for qmath."""

    pass


class ArbitrageViolationError(QmathError):
    """Raised when arbitrage-free constraints are violated."""

    pass


class FitError(QmathError):
    """Raised when fitting a model fails."""

    pass
