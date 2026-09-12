Quick Start
===========

This guide walks through one complete qmath workflow end to end: recovering a
risk-neutral density from an option chain. It is a good introduction to the
conventions every module follows.

The Pipeline
------------

This particular workflow has four steps:

1. **Generate or load** an option chain
2. **Filter** for liquidity and data quality
3. **Fit** an arbitrage-free surface
4. **Extract** the risk-neutral density

Steps 3 and 4 use objects that follow the standard qmath estimator contract,
``fit(data, **params) -> self`` then ``predict(data) -> result``, so
alternative smoothers and estimators drop into the same script unchanged.

Step 1: Generate a Synthetic Chain
-----------------------------------

For this example, we'll use :func:`~qmath.datasets.synthetic_heston_chain`
so that the ground truth is known:

.. code-block:: python

   from qmath.datasets import synthetic_heston_chain

   # Generate a 6-month option chain with 40 strikes
   chain = synthetic_heston_chain(
       T=0.5,              # 6-month expiration
       n_strikes=40,       # Number of strikes
       noise_bps=25,       # 25bp bid-ask spread + noise
       seed=0
   )
   print(f"Generated {len(chain)} strikes")

The resulting :class:`~qmath.options.OptionChain` includes:

- :attr:`~qmath.options.OptionChain.strikes`: the strike prices
- :attr:`~qmath.options.OptionChain.bid`,
  :attr:`~qmath.options.OptionChain.ask`: quoted prices
- :attr:`~qmath.options.OptionChain.mid`:
  :math:`(\mathrm{bid} + \mathrm{ask}) / 2`
- :attr:`~qmath.options.OptionChain.true_density`: the known
  ground-truth density (for validation)

Step 2: Filter Low-Liquidity Quotes
------------------------------------

Real market data is noisy. :func:`~qmath.options.filter_chain` keeps only
the liquid strikes:

.. code-block:: python

   from qmath.options import filter_chain

   # Remove wide spreads and stale quotes
   chain = filter_chain(
       chain,
       min_bid=0.01,           # Ignore zero bids
       max_bid_ask_ratio=1.1,  # Remove bids/asks that are too far apart
       min_spread=0.01         # Ignore negligible spreads
   )
   print(f"{len(chain)} strikes remain after filtering")

Step 3: Fit an Arbitrage-Free Surface
--------------------------------------

Use :class:`~qmath.surface.FenglerSmoother` to fit a cubic-spline surface
with automatic no-arbitrage constraints (monotonicity, convexity). Any
other :class:`~qmath.surface.Smoother`, such as
:class:`~qmath.surface.SVISmoother`, is a drop-in replacement here:

.. code-block:: python

   from qmath.surface import FenglerSmoother
   import numpy as np

   # Estimate forward and discount factor
   fwd = chain.spot * np.exp(chain.rate * chain.T)
   df = np.exp(-chain.rate * chain.T)

   # Fit the smoother
   smoother = FenglerSmoother(lambda_=1e-3).fit(
       chain,
       forward=fwd,
       discount=df
   )

   # Evaluate at any strikes
   test_strikes = np.linspace(80, 120, 100)
   smooth_prices = smoother.predict(test_strikes)

Step 4: Extract Risk-Neutral Density
-------------------------------------

Apply :func:`~qmath.rnd.breeden_litzenberger` to extract the density from
the smoothed surface:

.. code-block:: python

   from qmath.rnd import breeden_litzenberger

   # Extract density via Breeden-Litzenberger
   density = breeden_litzenberger(
       smoother,
       forward=fwd,
       discount=df
   )

   # Evaluate density at any prices
   prices = np.linspace(80, 120, 100)
   pdf_vals = density.pdf(prices)

   # Get density properties
   print(f"Mean:     {density.mean():.2f}")
   print(f"Std:      {np.sqrt(density.variance()):.2f}")
   print(f"Skewness: {density.skewness():.3f}")

Validation: Compare to Ground Truth
------------------------------------

For synthetic data, :func:`~qmath.validation.wasserstein` measures the
recovery error against the known density:

.. code-block:: python

   from qmath.validation import wasserstein

   # Wasserstein distance to true density
   error = wasserstein(density, chain.true_density)
   print(f"Recovery error (Wasserstein): {error:.6f}")

For real data, use the :class:`~qmath.rnd.RiskNeutralDensity` properties
(mean equal to the forward, positive, integrating to 1) as sanity checks.

Visualization
-------------

Plot the results:

.. code-block:: python

   import matplotlib.pyplot as plt

   fig, axes = plt.subplots(1, 2, figsize=(12, 4))

   # Left: fitted surface vs market data
   ax = axes[0]
   ax.scatter(chain.strikes, chain.mid, alpha=0.5, s=20, label="Market")
   ax.plot(
       chain.strikes,
       smoother.predict(chain.strikes),
       "b-",
       label="Fitted",
   )
   ax.set_xlabel("Strike")
   ax.set_ylabel("Call Price")
   ax.set_title("Arbitrage-Free Fit")
   ax.legend()
   ax.grid(True, alpha=0.3)

   # Right: extracted vs true density
   ax = axes[1]
   ax.plot(density.strikes, density.density, "b-", label="Extracted")
   ax.plot(chain.strikes, chain.true_density, "r--", label="True")
   ax.set_xlabel("Price")
   ax.set_ylabel("Density")
   ax.set_title("Risk-Neutral Density")
   ax.legend()
   ax.grid(True, alpha=0.3)

   plt.tight_layout()
   plt.show()

Next Steps
----------

- See :doc:`auto_examples/index` for more detailed examples
- Explore :doc:`theory/index` for the mathematical foundations
- Check :doc:`modules/index` for the full API reference
