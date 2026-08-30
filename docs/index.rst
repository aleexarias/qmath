qmath: Option-Implied Risk-Neutral Density Estimation
======================================================

**qmath** is a research library for estimating risk-neutral probability densities
from option market data. It specializes in the Breeden-Litzenberger framework
with emphasis on arbitrage-free surface fitting and robust density recovery.

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   theory/index
   auto_examples/index
   modules/index
   development
   contributors

Key Features
------------

- **Arbitrage-free surface fitting**: Constrained cubic-spline smoothing (Fengler 2009)
  automatically enforces monotonicity and convexity constraints.

- **Breeden-Litzenberger density extraction**: Analytic second derivatives avoid
  numerical instability of finite differences.

- **Comprehensive validation**: Distance metrics (Wasserstein, L2, KS) and
  arbitrage checks for quality assessment.

- **Type-safe and performant**: Full type hints, vectorized NumPy/SciPy,
  ready for C++ acceleration.

Quick Start
-----------

Generate a synthetic option chain, filter noisy quotes, fit an arbitrage-free
surface, and extract the risk-neutral density:

.. code-block:: python

   from qmath.datasets import synthetic_heston_chain
   from qmath.options import filter_chain
   from qmath.surface import FenglerSmoother
   from qmath.rnd import breeden_litzenberger
   import numpy as np

   # Generate and filter
   chain = synthetic_heston_chain(T=0.5, n_strikes=40)
   chain = filter_chain(chain)

   # Estimate forward/discount
   fwd = 100.0
   df = 0.99

   # Fit arbitrage-free surface and extract density
   smoother = FenglerSmoother(lambda_=1e-4).fit(chain, forward=fwd, discount=df)
   density = breeden_litzenberger(smoother, forward=fwd, discount=df)

   # Evaluate density
   print(f"Mean: {density.mean():.2f}")
   print(f"Std:  {np.sqrt(density.variance()):.2f}")

See the :doc:`quickstart` for a full worked example and the
:doc:`auto_examples/index` for additional use cases.

About
-----

**Author**: Alexander Arias

**License**: BSD-3-Clause

**Documentation**: https://qmath.readthedocs.io

**Repository**: https://github.com/aleexarias/qmath

Citing qmath
------------

If you use qmath in published research, please cite:

.. code-block:: bibtex

   @software{arias2024qmath,
     author = {Arias, Alexander},
     title = {qmath: Research library for option-implied risk-neutral density estimation},
     year = {2024},
     url = {https://github.com/aleexarias/qmath}
   }

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
