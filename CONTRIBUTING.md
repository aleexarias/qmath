# Contributing to qmath

Thank you for your interest in contributing to qmath! This document provides guidelines
for contributing to the project.

## Branch Model

- **`main`**: Always releasable; protected with branch rules.
- **`develop`**: Integration branch for features.
- **Feature/fix branches**: `feature/<name>`, `fix/<name>`, `docs/<name>` branched from
  `develop`, merged back via squash-merge PR.

## Branch Protection Rules (on GitHub)

Apply these rules to `main`:

1. Require a pull request before merging
2. Require status checks to pass before merging:
   - `tests` (matrix: 3.11, 3.12, 3.13 × ubuntu/macos/windows)
   - `lint` (ruff + mypy)
   - `docs` (build with `-W`)
3. Require branches to be up to date before merging
4. Require linear history
5. Disable force pushes

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

Uses [Semantic Versioning](https://semver.org/). Version is single-sourced
in `src/qmath/__init__.py` via hatch's `version` hook.

## Release Process

1. Update `CHANGELOG.md` with a section for the new version.
2. Create a git tag: `git tag v<version>`.
3. Push the tag: `git push origin v<version>`.
4. CI builds sdist + wheel and publishes to PyPI via trusted publishing.

## Code Quality Standards

- **Type hints**: All public functions must have complete type hints; `mypy --strict`
  must pass.
- **Linting**: `ruff check` must pass; use `ruff format` to auto-fix style issues.
- **Testing**: All public functions require tests (unit + property-based where applicable).
- **Docstrings**: numpydoc format; include `References` section with papers and
  `Examples` with doctests.

## Definition of Done for New Modules

A new module is complete when it has:

1. Docstrings with references to source papers.
2. Unit tests covering the main cases.
3. Property-based tests (via hypothesis) for numerical invariants.
4. One or more gallery examples in `examples/`.
5. An API documentation page in `docs/modules/`.
6. A CHANGELOG entry.

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
