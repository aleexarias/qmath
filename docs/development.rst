Development Guide
==================

This guide covers the development workflow for qmath contributors.

Branch Model
------------

- **main**: Always releasable. Protected with required checks.
- **develop**: Integration branch for features (optional staging).
- **Feature branches**: `feature/<name>`, `fix/<name>`, `docs/<name>`.
  Squash-merge back to main via PR.

All branches require:
- ✓ Tests (tests.yml passes)
- ✓ Lint (ruff check passes)
- ✓ Type checking (mypy --strict passes)
- ✓ Docs build (docs.yml passes)

Commit Convention
-----------------

Follow `Conventional Commits <https://www.conventionalcommits.org/>`_:

.. code-block:: text

   type(scope): subject

   body

   footer

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `ci`, `chore`.

Example:

.. code-block:: text

   feat(surface): implement Fengler constrained spline smoother

   Add convexity and monotonicity constraints via scipy.optimize SLSQP.
   Constraint matrix enforces arbitrage-free properties automatically.

   Closes #42

Changelog and version bumps are automated from these commits.

Setting Up Development Environment
-----------------------------------

Clone and install with dev dependencies:

.. code-block:: bash

   git clone https://github.com/aleexarias/qmath.git
   cd qmath
   pip install -e ".[dev,docs]"
   pre-commit install

Quality Checks
--------------

Run locally before pushing:

.. code-block:: bash

   ruff check src tests       # Lint
   ruff format src tests      # Format
   mypy --strict src          # Type check
   pytest tests/              # Unit tests

All checks must pass in CI before merge.

Testing Requirements
--------------------

Every numerical function gets:

1. **Unit tests** against known reference values or independently verified results
2. **Property tests** (via hypothesis) for invariants
3. **Integration tests** in the recovery pipeline

Example:

.. code-block:: python

   def test_bs_price_put_call_parity():
       """Test C - P = S - K*exp(-rT)."""
       # Unit test
       calls = bs_price(S, K, T, r, sigma, flag='C')
       puts = bs_price(S, K, T, r, sigma, flag='P')
       parity_lhs = calls - puts
       parity_rhs = S - K * df
       np.testing.assert_allclose(parity_lhs, parity_rhs, rtol=1e-10)

   @given(K=st.floats(50, 150))
   def test_bs_call_decreasing_in_strike(K):
       """Property: call price decreases with strike."""
       c1 = bs_price(100, K, T, r, sigma, flag='C')
       c2 = bs_price(100, K*1.01, T, r, sigma, flag='C')
       assert c1 > c2  # Stricter = lower price

Building Documentation
----------------------

Build locally:

.. code-block:: bash

   cd docs
   make clean
   make html
   # Open _build/html/index.html

The docs build will:
- Run all gallery examples
- Auto-generate API reference from docstrings
- Build theory pages from reStructuredText

API Documentation
------------------

Write numpydoc docstrings on all public functions/classes:

.. code-block:: python

   def density_estimation(chain: OptionChain, smoothness: float) -> RiskNeutralDensity:
       """Extract risk-neutral density from option chain.

       Fits an arbitrage-free surface using constrained cubic splines,
       then applies the Breeden-Litzenberger formula to extract density.

       Parameters
       ----------
       chain : OptionChain
           Option chain with bid-ask quotes.
       smoothness : float
           Regularization parameter (higher = smoother surface).

       Returns
       -------
       RiskNeutralDensity
           Object with pdf(), cdf(), moments, etc.

       References
       ----------
       Breeden, D. T., & Litzenberger, R. H. (1978).
       Prices of state-contingent claims implicit in option prices.
       Journal of Business, 51(4), 621-651.

       Examples
       --------
       >>> from qmath.datasets import synthetic_heston_chain
       >>> chain = synthetic_heston_chain(T=0.5, n_strikes=40)
       >>> density = density_estimation(chain, smoothness=0.001)
       >>> print(density.mean())  # Should be ~forward price
       """

Release Process
---------------

1. Update CHANGELOG.md with version and changes
2. Tag the release: `git tag vX.Y.Z`
3. Push tag: `git push origin vX.Y.Z`
4. GitHub Actions builds and publishes to PyPI (via trusted publishing)

Versioning
----------

Semantic versioning: MAJOR.MINOR.PATCH

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Version is single-sourced in `src/qmath/__init__.py` via hatch's version hook.

Performance
-----------

Profile hot paths before optimizing:

.. code-block:: bash

   python -m cProfile -s cumtime -m pytest tests/test_fengler.py

For C++ acceleration plans, see `cpp/README.md`.

Questions?
----------

See CLAUDE.md for conventions and the Contributing Guidelines (CONTRIBUTING.md).
