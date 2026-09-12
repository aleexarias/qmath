# Contributing to qmath

Thank you for your interest in contributing to qmath! This document provides
guidelines for contributing to the project.

qmath is built to accommodate many model families, not one. New pricers,
surface fits and estimators are welcome contributions: because every fitted
object shares the same `fit`/`predict` contract, a new implementation plugs
into the existing pipelines and validation tooling without changes elsewhere.
See "Definition of Done for New Modules" below for the bar a new family has to
clear.

## Design Principles

Contributions should preserve the principles the library is built on;
they are what let a new model family slot in without changes elsewhere.

- **A common estimator API.** Everything that is fitted to data follows the
  same sklearn-like contract: `fit(data, **params) -> self`, then
  `predict(data) -> result`. Swapping one smoother, pricer, or estimator for
  another is a one-line change.
- **Arbitrage awareness.** Fitting routines that can enforce no-arbitrage
  constraints do so, and `qmath.validation` provides independent checks so that
  any output can be audited.
- **Reference implementations first.** Every algorithm exists as readable,
  vectorized NumPy/SciPy. `qmath.backend` is a dispatch layer so that
  accelerated C++ kernels can be introduced later without changing any public
  API.
- **Typed and tested.** `mypy --strict` passes over the whole source tree, and
  every numerical function has unit tests against reference values plus
  property-based tests for its invariants.

## Branch Model

- **`main`**: Always releasable; protected with branch rules.
- **`develop`**: Integration branch for features.
- **Feature/fix branches**: `feature/<name>`, `fix/<name>`, `docs/<name>`
  branched from `develop`, merged back via squash-merge PR.

## Branch Protection Rules (on GitHub)

These rules are active on `main`:

1. Require a pull request before merging
2. Require status checks to pass before merging: `lint`, `docs`, and the
   six `test (<python>, <os>)` jobs (3.12, 3.13 × ubuntu/macos/windows)
3. Require branches to be up to date before merging

Merged pull request branches are deleted automatically.

## Automated Updates

Dependabot opens pull requests for GitHub Actions versions only, targeting
`develop` so they are tested there before reaching `main`. Python
dependencies are not updated by bots: for a library without a lockfile
Dependabot would only raise minimum versions in `pyproject.toml`, and CI
already installs the latest releases on every run.

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `ci`, `chore`.

Example:
```
feat(rnd): implement Breeden-Litzenberger density extraction

Add analytic second-derivative computation for fitted spline surfaces.
Includes vectorized evaluation and numerical stability improvements.

Closes #42
```

The changelog and version bumps will be keyed off these commits.

## Versioning

Uses [Semantic Versioning](https://semver.org/). The version is single-sourced
in `src/qmath/__init__.py` as `__version__`. Everything else derives from it:

- **Distribution metadata**: `pyproject.toml` declares
  `dynamic = ["version"]` and `[tool.hatch.version]` reads that line, so
  wheels and sdists pick it up at build time.
- **Documentation**: `docs/conf.py` imports `qmath.__version__`, exposing it
  as the `|release|` and `|version|` substitutions and in the footer of every
  page.

`CITATION.cff` is the one exception. It is static metadata read by GitHub and
citation managers, so it cannot derive the version and must be bumped by hand.

To bump the version:

1. Edit `__version__` in `src/qmath/__init__.py`.
2. Edit `version:` in `CITATION.cff` to match.

## Release Process

1. Bump the version as above.
2. Update `CHANGELOG.md` with a section for the new version.
3. Create a git tag: `git tag v<version>`.
4. Push the tag: `git push origin v<version>`.
5. CI builds sdist + wheel and publishes to PyPI via trusted publishing.

The tag must match `__version__`; nothing enforces this automatically yet.

## Code Quality Standards

- **Type hints**: All public functions must have complete type hints;
  `mypy --strict` must pass.
- **Linting**: `ruff check` must pass; use `ruff format` to auto-fix style
  issues.
- **Testing**: All public functions require tests (unit + property-based
  where applicable).
- **Docstrings**: numpydoc format; cite papers with `:footcite:t:` against
  `docs/theory/references.bib` and close with a `References` section holding
  `.. footbibliography::`; include `Examples` with doctests. BibTeX keys are
  `<surnames>_<year>_<word>` with surnames joined by `+`
  (e.g. `fang+oosterlee_2008_novel`).

## Definition of Done for New Modules

A new module is complete when it has:

1. A base class for its family in `qmath/<module>/base.py` defining the
   `fit`/`predict` contract, if one does not already exist.
2. Docstrings with references to source papers.
3. Unit tests covering the main cases.
4. Property-based tests (via hypothesis) for numerical invariants.
5. One or more gallery examples in `examples/`.
6. An API documentation page in `docs/modules/`.
7. A CHANGELOG entry.

## Running Tests and Checks

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check src tests

# Format code
ruff format src tests

# Type check
mypy --strict src

# Run tests with coverage
pytest --cov=qmath --cov-report=html tests

# Run benchmarks
pytest --benchmark-only benchmarks
```

## Documentation

Documentation lives in `docs/` and builds with Sphinx. Gallery examples are
in `examples/` organized by numbered subfolders. Each `.py` file in `examples/`
must start with a docstring header (see `sphinx-gallery` docs).

```bash
# Build docs locally
cd docs && make html
# Open _build/html/index.html
```

## Questions?

Open an issue on GitHub or check the `CLAUDE.md` file for project conventions.
