Quick Start
===========

This guide walks through the basic workflow of density estimation using qmath.

The Pipeline
------------

The typical qmath workflow has four steps:

1. **Generate or load** an option chain
2. **Filter** for liquidity and data quality
3. **Fit** an arbitrage-free surface
4. **Extract** the risk-neutral density

Step 1: Generate a Synthetic Chain
-----------------------------------

For this example, we'll use a synthetic chain to know the ground truth:

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

The chain includes:
- `strikes`: the strike prices
- `bid`, `ask`: quoted prices
- `mid`: (bid + ask) / 2
- `true_density`: the known ground-truth density (for validation)

Step 2: Filter Low-Liquidity Quotes
------------------------------------

Real market data is noisy. Filter for liquid strikes:

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

Use the Fengler smoother to fit a cubic-spline surface with automatic
no-arbitrage constraints (monotonicity, convexity):

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

Apply the Breeden-Litzenberger formula to extract density from the smoothed
surface:

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

For synthetic data, we can compute recovery error:

.. code-block:: python

   from qmath.validation import wasserstein

   # Wasserstein distance to true density
   error = wasserstein(density, chain.true_density)
   print(f"Recovery error (Wasserstein): {error:.6f}")

For real data, use density properties (mean = forward, positive, integrating to 1)
as sanity checks.

Visualization
-------------

Plot the results:

.. code-block:: python

   import matplotlib.pyplot as plt

   fig, axes = plt.subplots(1, 2, figsize=(12, 4))

   # Left: fitted surface vs market data
   ax = axes[0]
   ax.scatter(chain.strikes, chain.mid, alpha=0.5, s=20, label="Market")
   ax.plot(chain.strikes, smoother.predict(chain.strikes), "b-", label="Fitted")
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
