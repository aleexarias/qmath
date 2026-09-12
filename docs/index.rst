qmath: A Research Library for Quantitative Finance
===================================================

**qmath** provides typed, tested implementations of pricing models,
volatility-surface fits, and option-implied estimators behind a small and
consistent API, so that methods from different families can be composed and
compared on the same data.

The library is designed to grow. Each area of the codebase is an extension
point with a documented base class, and new model families are added as
subpackages rather than as changes to existing ones.

.. toctree::
   :maxdepth: 1

   installation
   quickstart
   theory/index
   auto_examples/index
   modules/index
   references
   development
   contributors

Package Layout
--------------

.. list-table::
   :header-rows: 1
   :widths: 20 35 45

   * - Subpackage
     - Role
     - Currently available
   * - :doc:`modules/models`
     - Analytic and semi-analytic pricers
     - Black-Scholes prices, greeks and implied vol; Heston characteristic
       function with COS pricing and density
   * - :doc:`modules/surface`
     - Implied-volatility and call-price surface fitting
     - :class:`~qmath.surface.FenglerSmoother` (constrained cubic
       spline), :class:`~qmath.surface.SVISmoother` (raw SVI)
   * - :doc:`modules/rnd`
     - Risk-neutral density recovery and properties
     - Breeden-Litzenberger extraction, Pareto tail grafting, model-free
       moments
   * - :doc:`modules/options`
     - Market data structures and preprocessing
     - :class:`~qmath.options.OptionChain`, liquidity filtering,
       forward/discount inference
   * - :doc:`modules/datasets`
     - Chain generation and loading
     - Synthetic Heston chains with known ground truth, Deribit loader
   * - :doc:`modules/validation`
     - Quality assessment
     - Monotonicity, convexity and bound checks; Wasserstein, L2 and KS
       distances

Quick Start
-----------

The example below runs one end-to-end workflow: generate a synthetic option
chain, filter noisy quotes, fit an arbitrage-free surface, and recover the
risk-neutral density from it.

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
   smoother = FenglerSmoother(lambda_=1e-4).fit(
       chain, forward=fwd, discount=df
   )
   density = breeden_litzenberger(smoother, forward=fwd, discount=df)

   # Evaluate density
   print(f"Mean: {density.mean():.2f}")
   print(f"Std:  {np.sqrt(density.variance()):.2f}")

Because smoothers share the :class:`~qmath.surface.Smoother` base class,
substituting :class:`~qmath.surface.SVISmoother` for
:class:`~qmath.surface.FenglerSmoother` leaves the rest of the script
untouched.

See the :doc:`quickstart` for a full worked example and the
:doc:`auto_examples/index` for additional use cases.

About
-----

**Version**: |release| (this documentation is built from the installed package,
so it always describes the version shown here and in the page footer)

**Author**: Alejandro Arias Gomez

**License**: BSD-3-Clause

**Repository**: https://github.com/aleexarias/qmath

**Documentation**: not hosted yet; build it from the repository with
``cd docs && make html`` (see :doc:`installation`).

Citing qmath
------------

If you use qmath in published research, please cite:

.. code-block:: bibtex

   @software{ariasgomez_2026_qmath,
     author = {Arias Gomez, Alejandro},
     title = {qmath: A research library for quantitative finance},
     year = {2026},
     url = {https://github.com/aleexarias/qmath}
   }

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
