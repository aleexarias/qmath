# Changelog

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-12

First functional release. The library is organised as independent
subpackages behind a common sklearn-style `fit`/`predict` contract; the
first pipeline built out end to end is option-implied risk-neutral density
recovery.

### Added

- `qmath.models`: Black-Scholes prices, vega and implied volatility; Heston
  characteristic function in the little-trap formulation with COS pricing
  and COS density.
- `qmath.surface`: `Smoother` base class, `FenglerSmoother` (constrained
  cubic spline, monotonicity and convexity enforced via SLSQP) and
  `SVISmoother` (raw SVI fit with parameter-validity constraints).
- `qmath.rnd`: `RiskNeutralDensity` (pdf, cdf, quantile, moments, plot),
  `breeden_litzenberger` extraction from a fitted smoother,
  `graft_pareto_tail`, and model-free variance, skewness and kurtosis.
- `qmath.options`: `OptionChain` container, `filter_chain` liquidity filter,
  `infer_forward` put-call-parity regression.
- `qmath.datasets`: `synthetic_heston_chain` with a known ground-truth
  density, and `load_deribit_chain`, a live loader that joins Deribit's
  instrument and book-summary endpoints and returns USD-denominated quotes.
- `qmath.validation`: monotonicity, convexity and bound checks; Wasserstein,
  L2 and Kolmogorov-Smirnov distances between densities.
- Every public name re-exported from its subpackage, so
  `from qmath.models import bs_price` is the supported import path.
- Package is fully typed (`py.typed`, `mypy --strict`); version single-sourced
  in `qmath.__version__` and read by `pyproject.toml` and the docs build.
- Test suite with unit tests, hypothesis property tests, and an opt-in live
  Deribit test (`QMATH_NETWORK_TESTS=1`).
- Sphinx documentation, built warning-free with `-W`: API reference per
  subpackage, theory pages, sphinx-gallery examples, and a References page
  generated from `docs/theory/references.bib`. Docstrings cite papers with
  `:footcite:` and write mathematics as LaTeX. The package version appears in
  the footer of every page.
- Project conventions: 79-character lines enforced by ruff, BibTeX keys of
  the form `surname+surname_year_word`, `CITATION.cff`.
- Requires Python 3.12+, NumPy 2.0+, SciPy, pandas, matplotlib and requests.
