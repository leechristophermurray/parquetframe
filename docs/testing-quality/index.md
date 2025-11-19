# Testing & Quality

This page outlines the testing, coverage, linting, typing, and docs quality gates used in this project.

## Python

- Tests: `pytest -q` with coverage (`--cov=src/parquetframe`)
- Linting: `ruff check .` and `ruff format --check .`
- Typing: `mypy src/parquetframe` (config relaxed)

## Rust

- Unit tests: `cargo test -q` across workspace
- Benchmarks: `cargo bench` (Criterion), not required in CI

## Documentation

- MkDocs Material build must pass: `mkdocs build --strict`
- Cross‑links and nav entries are validated before merging

## CI Gates

- Fast fail on tests, lint, and strict docs
- Wheel builds smoke‑import on all platforms prior to release

## Local Dev Tips

- Use a virtualenv and install extras: `pip install -e .[dev,docs]`
- Run selective test subsets with `-k` and markers for faster iteration
