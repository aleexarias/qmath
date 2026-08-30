"""Backend dispatch layer for C++ kernels (future).

Currently loads only the pure-Python reference implementations.
When C++ kernels are available, this module will dispatch to them transparently.
"""

from qmath.backend._python import *  # noqa: F403, F401
