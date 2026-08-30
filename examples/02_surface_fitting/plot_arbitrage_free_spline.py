"""
============================================
Arbitrage-Free Spline Fitting (Fengler 2009)
============================================

Demonstrates the Fengler constrained cubic-spline smoother,
which automatically enforces no-arbitrage constraints:
monotonicity (decreasing in strike) and convexity.
"""

import matplotlib.pyplot as plt
import numpy as np

from qmath.datasets import synthetic_heston_chain
from qmath.options import filter_chain
from qmath.surface import FenglerSmoother
from qmath.validation.arbitrage import check_convexity, check_monotonicity

# Generate noisy market quotes
print("Generating market data...")
chain = synthetic_heston_chain(T=0.25, n_strikes=35, noise_bps=30, seed=123)
chain = filter_chain(chain)
print(f"  {len(chain)} liquid strikes")

# Parameters for smoothing
fwd = chain.spot * np.exp(chain.rate * chain.T)
df = np.exp(-chain.rate * chain.T)

# Fit with different regularization levels
lambdas = [1e-5, 1e-4, 1e-3]
fits = []

for lam in lambdas:
    smoother = FenglerSmoother(lambda_=lam).fit(chain, forward=fwd, discount=df)
    prices = smoother.predict(chain.strikes)
    fits.append((smoother, prices))

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(13, 10))

# Top left: raw market data
ax = axes[0, 0]
ax.scatter(chain.strikes, chain.bid, alpha=0.4, s=20, c="red", label="Bid")
ax.scatter(chain.strikes, chain.ask, alpha=0.4, s=20, c="blue", label="Ask")
ax.scatter(chain.strikes, chain.mid, alpha=0.6, s=30, c="black", label="Mid", zorder=5)
ax.set_xlabel("Strike")
ax.set_ylabel("Price")
ax.set_title("Raw Market Quotes (noisy)")
ax.legend()
ax.grid(True, alpha=0.3)

# Top right: fitted surfaces at different lambdas
ax = axes[0, 1]
ax.scatter(chain.strikes, chain.mid, alpha=0.3, s=30, c="gray", label="Market mid")
colors = ["green", "blue", "red"]
for (smoother, prices), lam, color in zip(fits, lambdas, colors):
    ax.plot(chain.strikes, prices, linewidth=2, label=f"λ={lam:.0e}", color=color)
ax.set_xlabel("Strike")
ax.set_ylabel("Call Price")
ax.set_title("Fitted Surfaces (different smoothness)")
ax.legend()
ax.grid(True, alpha=0.3)

# Bottom left: monotonicity check
ax = axes[1, 0]
violations_mono = []
for smoother, prices in fits:
    _, viol = check_monotonicity(chain.strikes, prices)
    violations_mono.append(viol)

ax.bar(range(len(lambdas)), violations_mono, color=colors, alpha=0.7)
ax.set_xticks(range(len(lambdas)))
ax.set_xticklabels([f"λ={lam:.0e}" for lam in lambdas])
ax.set_ylabel("Monotonicity Violations")
ax.set_title("Constraint Satisfaction")
ax.set_ylim(0, max(violations_mono) + 1)
ax.grid(True, alpha=0.3, axis="y")

# Bottom right: convexity check
ax = axes[1, 1]
violations_conv = []
for smoother, prices in fits:
    _, viol = check_convexity(chain.strikes, prices)
    violations_conv.append(viol)

ax.bar(range(len(lambdas)), violations_conv, color=colors, alpha=0.7)
ax.set_xticks(range(len(lambdas)))
ax.set_xticklabels([f"λ={lam:.0e}" for lam in lambdas])
ax.set_ylabel("Convexity Violations")
ax.set_title("Constraint Satisfaction")
ax.set_ylim(0, max(violations_conv) + 1)
ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.show()

print("\n✓ Fengler smoother demonstration complete!")
print("  Note: Smaller λ → less smoothing (closer to data, less violations)")
print("        Larger λ → more smoothing (smoother surface, more violations possible)")
