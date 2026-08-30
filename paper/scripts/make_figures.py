"""
Generate paper figures from qmath experiments.

This script runs the core recovery experiments and generates
publication-quality figures. All figures are saved to ../figures/.
"""

import os

import matplotlib.pyplot as plt
import numpy as np

# Ensure figures directory exists
figures_dir = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(figures_dir, exist_ok=True)

# Set up matplotlib for publication
plt.rcParams.update({
    "font.size": 10,
    "figure.figsize": (6, 4),
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "lines.linewidth": 1.5,
    "legend.fontsize": 9,
})


def figure_1_recovery_experiment() -> None:
    """Generate Figure 1: Recovery error vs noise and strike count."""
    from qmath.datasets import synthetic_heston_chain
    from qmath.options import filter_chain
    from qmath.rnd import breeden_litzenberger
    from qmath.surface import FenglerSmoother
    from qmath.validation import wasserstein

    noise_levels = np.array([10, 20, 30, 40])
    n_strikes_list = [25, 35, 50]

    fig, ax = plt.subplots(figsize=(6, 4))

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for n_strikes, color in zip(n_strikes_list, colors):
        errors = []

        for noise_bps in noise_levels:
            # Generate and recover
            chain = synthetic_heston_chain(T=0.5, n_strikes=n_strikes, noise_bps=noise_bps, seed=42)
            chain = filter_chain(chain)

            fwd = chain.spot * np.exp(chain.rate * chain.T)
            df = np.exp(-chain.rate * chain.T)

            smoother = FenglerSmoother(lambda_=1e-3).fit(chain, forward=fwd, discount=df)
            density = breeden_litzenberger(smoother, forward=fwd, discount=df)

            error = wasserstein(density, chain.true_density)
            errors.append(error)

        ax.plot(noise_levels, errors, marker="o", label=f"$n={n_strikes}$", color=color)

    ax.set_xlabel("Quote Noise (basis points)")
    ax.set_ylabel("Wasserstein Distance")
    ax.set_title("Density Recovery Error vs Noise")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "fig_1_recovery.pdf"))
    plt.close()

    print("✓ Figure 1 saved: fig_1_recovery.pdf")


def main() -> None:
    """Generate all paper figures."""
    print("Generating paper figures...\n")

    try:
        figure_1_recovery_experiment()
    except Exception as e:
        print(f"✗ Error generating figures: {e}")
        return

    print(f"\n✓ All figures saved to: {figures_dir}")


if __name__ == "__main__":
    main()
