# Paper: Option-Implied Density Estimation

This directory contains the paper and its associated figures.

## Structure

- `main.tex` - Main LaTeX document
- `refs.bib` - Bibliography
- `figures/` - Generated figures (gitignored)
- `scripts/` - Scripts that generate figures

## Philosophy

**No hand-drawn figures.** Every figure is produced by a script in `scripts/`.
This ensures:

1. Reproducibility: Run the scripts to regenerate figures
2. Consistency: All figures use the same color scheme and fonts
3. Maintainability: Update a script, not dozens of figure files

## Generating Figures

Each script in `scripts/` produces one or more figures for the paper:

```bash
cd scripts/
python make_figures.py
# Produces figures/ directory with PDF/PNG output
```

## Dependencies

The scripts use qmath and standard scientific Python:

```bash
pip install -e "..[dev]"
```

## Figure List

- Figure 1: Recovery experiment (noise vs estimation error)
- Figure 2: Arbitrage-free surface fit
- Figure 3: Density comparison (estimated vs parametric)
- Figure 4: Constraint satisfaction (monotonicity, convexity)

(To be updated as paper develops)
