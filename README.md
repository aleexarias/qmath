# qmath

Research library for estimating risk-neutral probability densities from option market data. Specializes in the Breeden-Litzenberger framework with emphasis on arbitrage-free surface fitting and robust density recovery from noisy quotes.

## Installation

```bash
pip install qmath
```

For development:

```bash
pip install -e ".[dev,docs]"
```

## Quick Start

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

Full documentation available at [qmath.readthedocs.io](https://qmath.readthedocs.io).

See the [gallery](https://qmath.readthedocs.io/auto_examples) for complete examples.

## What This Is (and Isn't)

**qmath is a research library** for studying option-implied density estimation. It provides
tools for academic research, backtesting strategies, and validating numerical methods.

**It is not a trading system.** It does not provide market data connectors, real-time
pricing, or execution. Use it for research and analysis, not for live trading without
additional infrastructure.

## Citation

If you use qmath in published research, please cite:

```bibtex
@software{arias2024qmath,
  author = {Arias, Alexander},
  title = {qmath: Research library for option-implied risk-neutral density estimation},
  year = {2024},
  url = {https://github.com/aleexarias/qmath}
}
```

## License

BSD-3-Clause. See [LICENSE](LICENSE).

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
