"""
=====================================
Simple Density Recovery from Synthetic Chain
=====================================

This example demonstrates the core qmath workflow:
generate a synthetic option chain, filter noisy quotes,
fit an arbitrage-free surface, and extract the risk-neutral density
via the Breeden-Litzenberger formula.
"""

import matplotlib.pyplot as plt
import numpy as np

from qmath.datasets import synthetic_heston_chain
from qmath.options import filter_chain
from qmath.rnd import breeden_litzenberger
from qmath.surface import FenglerSmoother
from qmath.validation import wasserstein

# Generate synthetic option chain from a known model
print("Generating synthetic chain...")
chain = synthetic_heston_chain(T=0.5, n_strikes=40, noise_bps=20, seed=42)
print(f"  Generated {len(chain)} strikes")

# Filter out low-liquidity quotes
print("Filtering chain...")
chain = filter_chain(chain)
print(f"  {len(chain)} strikes remain after filtering")

# Estimate forward and discount factor
# (In practice, infer_forward() would be used; here we use ground truth)
fwd = chain.spot * np.exp(chain.rate * chain.T)
df = np.exp(-chain.rate * chain.T)
print(f"  Forward: {fwd:.4f}")
print(f"  Discount factor: {df:.6f}")

# Fit arbitrage-free surface via constrained cubic splines
print("Fitting Fengler smoother...")
smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
print("  Smooth surface fitted successfully")

# Extract risk-neutral density via Breeden-Litzenberger formula
print("Extracting density...")
density = breeden_litzenberger(smoother, forward=fwd, discount=df)

# Compute recovery error
error = wasserstein(density, chain.true_density)
print(f"  Wasserstein distance to true density: {error:.6f}")

# Plot results
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Left: option prices (market vs smoothed)
axes[0].scatter(chain.strikes, chain.mid, alpha=0.6, s=30, label="Market (mid)")
smooth_prices = smoother.predict(chain.strikes)
axes[0].plot(chain.strikes, smooth_prices, "b-", linewidth=2, label="Fitted")
axes[0].set_xlabel("Strike")
axes[0].set_ylabel("Call Price")
axes[0].set_title("Arbitrage-Free Surface Fit")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Right: extracted density vs true density
axes[1].plot(density.strikes, density.density, "b-", linewidth=2, label="Extracted (B-L)")
axes[1].plot(chain.strikes, chain.true_density, "r--", linewidth=2, label="True")
axes[1].axvline(fwd, color="gray", linestyle=":", alpha=0.7, label=f"Forward={fwd:.1f}")
axes[1].set_xlabel("Price (Strike)")
axes[1].set_ylabel("Density")
axes[1].set_title("Risk-Neutral Density Recovery")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("\n✓ Example complete!")
