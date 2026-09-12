# qmath: Project conventions for Claude Code sessions

This document specifies the conventions and workflows for contributing to
qmath.

## Quick Checks Before Claiming Done

Always run these before marking work complete:

```bash
ruff check src tests
mypy --strict src
pytest tests/
```

Fix any errors. Do not commit with warnings or failures.

## Project Layout

```
src/qmath/
├── __init__.py              # version, top-level re-exports
├── py.typed                 # marks package as typed
├── _typing.py               # FloatArray, BoolArray type aliases
├── backend/                 # dispatch layer for future C++ kernels
├── datasets/                # synthetic chain generation
├── models/                  # analytic pricers (Black-Scholes, Heston COS)
├── options/                 # OptionChain, filtering, forward inference
├── surface/                 # arbitrage-free smoothing (Fengler)
├── rnd/                     # risk-neutral density (Breeden-Litzenberger)
├── validation/              # arbitrage checks and metrics
└── viz/                     # plotting functions
```

## Code Conventions

1. **Type hints everywhere**: `mypy --strict` must pass. No `Any` types
   except in very rare cases, justified with a comment.

2. **Docstrings**: numpydoc format on all public functions/classes. Include:
   - Brief one-liner
   - Extended description (if needed)
   - Parameters, Returns, Raises sections
   - Papers cited via `docs/theory/references.bib`, never written out:
     `:footcite:t:`key`` in the text and a References section that
     contains only `.. footbibliography::`. Hand-written `.rst` pages
     use `:cite:t:` / `:cite:p:` instead. Keys are
     `<surnames>_<year>_<word>`: lowercase author surnames joined with
     `+`, the year, and one identifying word, e.g.
     `heston_1993_closed`, `breeden+litzenberger_1978_prices`.
   - Examples section with executable code
   - Mathematics as LaTeX, never plain text: short expressions inline with
     :math:`...`, larger ones in a `.. math::` block. Any docstring with a
     backslash must be a raw string (`r"""`).

3. **No comments by default**: Code should be self-documenting. Only add
   comments when the WHY is non-obvious (hidden constraint, workaround, subtle
   invariant). Never leave step labels that restate the code, comments that
   narrate a thought process or an arithmetic walk-through, or comments that
   restate the assertion below them.

4. **79-character lines**: Applies to code and prose alike (Python, Markdown,
   reStructuredText, config). `ruff format` wraps code; docstrings, comments
   and string literals must be wrapped by hand, and `ruff check` enforces the
   limit via E501. The only exceptions are things that cannot be broken
   without changing meaning: URLs and Markdown table rows.

5. **Numerical functions**: Every function that computes or manipulates
   numbers:
   - Has unit tests against analytic or reference results
   - Has property-based tests (hypothesis) for invariants
   - Is tested in isolation AND in the recovery pipeline

6. **Estimators and smoothers**: All subclasses of base classes follow
   sklearn-like `fit(data, **params) -> self; predict(data) -> result` API.

7. **No results in paper without scripts**: Every numerical result that goes
   in the paper must be produced by a reproducible script in `paper/scripts/`,
   never by hand.

## Workflow: Adding a New Numerical Function

1. Write the function with complete type hints and numpydoc docstring.
2. Write a unit test against a known reference (analytic formula, another
   library, etc.).
3. Write a property test (hypothesis) for invariants (if applicable).
4. Run the full suite: `pytest tests/`, `ruff check`, `mypy --strict src`.
5. Add a CHANGELOG entry and an API doc page.

## Workflow: Adding a New Estimator/Smoother

1. Add a base class in `qmath/<module>/base.py` (if it doesn't exist) with:
   - Abstract `fit(data, **params)` returning `self`
   - Abstract `predict(data)` returning result
   - `__repr__` and parameter storage

2. Subclass it in `qmath/<module>/<name>.py` with your implementation.

3. Write tests:
   - Unit test: known input → known output
   - Property test: fitted object maintains invariants
   - Integration test: recovered result in recovery pipeline achieves target
     accuracy

4. Add a gallery example in `examples/<n>_<topic>/plot_<name>.py`.

5. Update `docs/modules/` API page and CHANGELOG.

## Testing

- `pytest tests/` runs all tests
- `pytest tests/ -k <substring>` runs tests matching a name
- `pytest tests/ -m slow` runs only slow tests
- `QMATH_NETWORK_TESTS=1 pytest tests/ -m network` runs the live Deribit
  test; it is skipped otherwise
- `pytest --benchmark-only benchmarks/` runs performance benchmarks
- `pytest --cov=qmath --cov-report=html tests/` generates coverage report

## Documentation

- Sphinx builds from `docs/`
- Gallery examples in `examples/` (numbered by section)
- Each `.py` file must start with a docstring header (sphinx-gallery
  requirement)
- Build locally: `cd docs && make html`
- `docs.yml` CI builds with `-W` (warnings are errors)
- Library objects named in prose are cross-references, not literals:
  `:class:`~qmath.surface.SVISmoother``, `:func:`~qmath.rnd.wasserstein``,
  `:attr:`~qmath.options.OptionChain.mid``, `:mod:`~qmath.models``
- A bullet or numbered list needs a blank line before it, or RST renders
  it as a run-on paragraph

## Branch Model and Release

- **`main`**: Always releasable, protected, square-merge PRs only
- **`develop`**: Integration branch
- **Feature branches**: `feature/<name>` from `develop`, PR with squash merge
- **Version**: Single-sourced in `src/qmath/__init__.py` as `__version__`.
  `pyproject.toml` (via `[tool.hatch.version]`) and `docs/conf.py` derive from
  it; `CITATION.cff` is the only file that must be bumped by hand. Never
  hardcode the version anywhere else.
- **Release**: Tag with `vX.Y.Z`, CI publishes to PyPI via trusted publishing

See CONTRIBUTING.md for branch protection rules and commit conventions.

## Common Pitfalls

1. **Don't invent numbers**: If a benchmark or test threshold needs a
   number, run the code and use the actual result. Document why the threshold
   is reasonable.

2. **Don't add dependencies lightly**: Stick to numpy, scipy, pandas,
   matplotlib, and requests (for the Deribit loader). cvxpy is allowed for
   optimization. Ask before adding anything else.

3. **Don't leave stubs**: If you're not implementing a module this session,
   leave it with a docstring explaining what goes there. Do not create `.py`
   files with `NotImplementedError` or `pass` at the module level.

4. **Don't skip tests for "structure"**: Every line of code is tested, even
   if it just calls other functions.

5. **Don't break the recovery pipeline**: The primary validation is the
   end-to-end recovery test. If a new function breaks it, fix it before
   merging.

## Contact

For questions about conventions or blocked work, check this file first or open
a GitHub issue.
