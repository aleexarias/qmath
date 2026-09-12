# qmath

qmath is a research library for quantitative finance. It provides tested
implementations of pricing models, volatility-surface fits, and option-implied
estimators behind a small and consistent API, so that methods from different
families can be composed and compared on the same data.

The library is designed to grow. Each area of the codebase is an extension
point with a documented base class, and new model families are added as
subpackages.

## Package Layout

| Subpackage | Role | Currently available |
| --- | --- | --- |
| `qmath.models` | Analytic and semi-analytic pricers | Black-Scholes prices, greeks and implied vol; Heston characteristic function with COS pricing and density |
| `qmath.surface` | Implied-volatility and call-price surface fitting | `FenglerSmoother` (constrained cubic spline), `SVISmoother` (raw SVI) |
| `qmath.rnd` | Risk-neutral density recovery and properties | Breeden-Litzenberger extraction, Pareto tail grafting, model-free moments |
| `qmath.options` | Market data structures and preprocessing | `OptionChain`, liquidity filtering, forward/discount inference |
| `qmath.datasets` | Chain generation and loading | Synthetic Heston chains with known ground truth, Deribit loader |
| `qmath.validation` | Quality assessment | Monotonicity, convexity and bound checks; Wasserstein, L2 and KS distances |
| `qmath.viz` | Plotting helpers | Placeholder for shared plotting utilities |
| `qmath.backend` | Kernel dispatch | Pure-Python reference implementations |

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/aleexarias/qmath.git
cd qmath
pip install -e .
```

With development and documentation dependencies:

```bash
pip install -e ".[dev,docs]"
```

Requires Python 3.12 or newer.

## Quick Start

The example below runs one end-to-end workflow: generate a chain with a known
ground-truth density, fit an arbitrage-free surface, and recover the density
from it.

```python
from qmath.datasets import synthetic_heston_chain
from qmath.options import filter_chain, infer_forward
from qmath.surface import FenglerSmoother
from qmath.rnd import breeden_litzenberger
import matplotlib.pyplot as plt

# Generate synthetic option chain with known true density
chain = synthetic_heston_chain(T=0.5, n_strikes=40, noise_bps=25, seed=0)
chain = filter_chain(chain)

# Infer forward and discount factor from put-call parity
fwd, df = infer_forward(chain)

# Fit arbitrage-free surface
smoother = FenglerSmoother(lambda_=1e-4).fit(chain, forward=fwd, discount=df)

# Extract risk-neutral density via Breeden-Litzenberger
density = breeden_litzenberger(smoother, forward=fwd, discount=df)

# Plot results
density.plot()
plt.show()
```

## Documentation

The documentation is not hosted yet. Build it from this repository:

```bash
pip install -e ".[docs]"
cd docs
make html
# Open docs/_build/html/index.html in a browser
```

The build renders the API reference, the theory pages, and the example gallery.
The gallery sources live in [examples/](examples/) and run as ordinary scripts
if you prefer not to build the docs.

## Scope

**qmath is a research library.** It is intended for academic work, method
development, backtesting, and validating numerical implementations against
references.

**It is not a trading system.** It does not provide real-time pricing, order
management, or execution. The Deribit loader fetches public historical chains
for research; it is not market-data infrastructure.

## Extending qmath

New model families are welcome. The pattern is:

1. Add or reuse a base class in `qmath/<module>/base.py` defining the
   `fit`/`predict` contract for that family.
2. Implement the subclass in `qmath/<module>/<name>.py` with complete type
   hints and a numpydoc docstring citing its source paper.
3. Add unit tests against a reference, property tests for its invariants,
   and an integration test in the end-to-end pipeline.
4. Add a gallery example, an API page under `docs/modules/`, and a CHANGELOG
   entry.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and
[CLAUDE.md](CLAUDE.md) for project conventions.

## Citation

If you use qmath in published research, please cite:

```bibtex
@software{ariasgomez_2026_qmath,
  author = {Arias Gomez, Alejandro},
  title = {qmath: A research library for quantitative finance},
  year = {2026},
  url = {https://github.com/aleexarias/qmath}
}
```

## License

BSD-3-Clause. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines.
