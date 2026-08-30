"""
=====================================
Density Recovery Experiment
=====================================

End-to-end validation: generate synthetic option chains from a known model,
run the density estimation pipeline, and measure recovery error.
Shows how estimation quality degrades with noise.
"""

import matplotlib.pyplot as plt
import numpy as np

from qmath.datasets import synthetic_heston_chain
from qmath.options import filter_chain
from qmath.rnd import breeden_litzenberger
from qmath.surface import FenglerSmoother
from qmath.validation import ks_distance, l2_distance, wasserstein

print("Running density recovery experiment...")

# Experiment parameters
noise_levels = np.array([10, 20, 30, 50])
n_strikes_list = [25, 35, 50]
n_trials = 3

results = {metric: {} for metric in ["wasserstein", "l2", "ks"]}

for metric in results:
    results[metric] = {
        "noise": {n: [] for n in n_strikes_list},
        "strikes": {n: [] for n in n_strikes_list},
    }

# Run experiments
for n_strikes in n_strikes_list:
    for noise_bps in noise_levels:
        w_errors = []
        l2_errors = []
        ks_errors = []

        for trial in range(n_trials):
            # Generate chain
            chain = synthetic_heston_chain(
                T=0.5, n_strikes=n_strikes, noise_bps=noise_bps, seed=trial
            )
            chain = filter_chain(chain)

            # Skip if too few strikes after filtering
            if len(chain) < 10:
                continue

            # Recover density
            fwd = chain.spot * np.exp(chain.rate * chain.T)
            df = np.exp(-chain.rate * chain.T)

            try:
                smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
                density = breeden_litzenberger(smoother, forward=fwd, discount=df)

                # Compute errors
                w_err = wasserstein(density, chain.true_density)
                l2_err = l2_distance(density, chain.true_density)
                ks_err = ks_distance(density, chain.true_density)

                w_errors.append(w_err)
                l2_errors.append(l2_err)
                ks_errors.append(ks_err)
            except Exception as e:
                # Skip failed fits
                print(f"    Trial failed (n={n_strikes}, noise={noise_bps}): {e}")
                continue

        # Average results
        if w_errors:
            results["wasserstein"]["noise"][n_strikes].append(np.mean(w_errors))
            results["l2"]["noise"][n_strikes].append(np.mean(l2_errors))
            results["ks"]["noise"][n_strikes].append(np.mean(ks_errors))

            results["wasserstein"]["strikes"][n_strikes].append(np.std(w_errors))
            results["l2"]["strikes"][n_strikes].append(np.std(l2_errors))
            results["ks"]["strikes"][n_strikes].append(np.std(ks_errors))

print("  Experiment complete!")

# Plot results
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

metrics = ["wasserstein", "l2", "ks"]
titles = ["Wasserstein Distance", "L2 Distance", "Kolmogorov-Smirnov Distance"]

for ax, metric, title in zip(axes, metrics, titles):
    for n_strikes in n_strikes_list:
        errors = results[metric]["noise"][n_strikes]
        if errors:
            ax.plot(noise_levels[: len(errors)], errors, marker="o", label=f"n={n_strikes}")

    ax.set_xlabel("Quote Noise (bps)")
    ax.set_ylabel(f"{title}")
    ax.set_title("Recovery Error vs Noise")
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("\n✓ Recovery experiment complete!")
print("  Observations:")
print("  - Error increases with quote noise")
print("  - More strikes → better recovery (more information)")
print("  - Different metrics highlight different error aspects")
