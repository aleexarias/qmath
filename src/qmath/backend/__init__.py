"""Backend dispatch layer for C++ kernels.

When C++ kernels are available, this module will dispatch to them
transparently.
"""

from qmath.backend._python import *  # noqa: F403, F401
