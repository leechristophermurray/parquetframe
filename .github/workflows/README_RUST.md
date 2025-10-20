# Rust Integration CI/CD Guide

## Overview

This guide documents the CI/CD changes needed to integrate Rust builds into ParquetFrame.

## Required Changes to `.github/workflows/ci.yml`

Add the following jobs to your CI workflow:

### 1. Rust Check Job

```yaml
rust-check:
  name: Rust Check
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: dtolnay/rust-toolchain@stable
    - uses: Swatinem/rust-cache@v2
    - run: cargo check --workspace
    - run: cargo clippy --workspace -- -D warnings
    - run: cargo fmt --check
```

### 2. Rust Test Job

```yaml
rust-test:
  name: Rust Tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: dtolnay/rust-toolchain@stable
    - uses: Swatinem/rust-cache@v2
    - run: cargo test --workspace
```

### 3. Build Wheels Job (Multi-Platform)

```yaml
build-wheels:
  name: Build Wheels
  strategy:
    matrix:
      os: [ubuntu-latest, macos-latest, windows-latest]
      python-version: ['3.10', '3.11', '3.12']
  runs-on: ${{ matrix.os }}
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - uses: dtolnay/rust-toolchain@stable
    - name: Install maturin
      run: pip install maturin
    - name: Build wheels
      run: maturin build --release --out dist
    - uses: actions/upload-artifact@v4
      with:
        name: wheels-${{ matrix.os }}-py${{ matrix.python-version }}
        path: dist/*.whl
```

## Local Development

### Building Rust Extension

```bash
# Install maturin
pip install maturin

# Development build (editable install)
maturin develop

# Release build
maturin develop --release

# Build wheel
maturin build --release
```

### Running Rust Tests

```bash
# Run all Rust tests
cargo test --workspace

# Run specific crate tests
cargo test -p pf-graph-core
cargo test -p pf-py

# Run with output
cargo test --workspace -- --nocapture
```

### Linting and Formatting

```bash
# Check formatting
cargo fmt --check

# Apply formatting
cargo fmt

# Run clippy
cargo clippy --workspace -- -D warnings
```

## Implementation Timeline

**Phase 0 (Current)**: Basic infrastructure in place
- CI documentation created
- Manual CI integration required

**Phase 1+**: Full CI/CD integration
- Automated Rust checks on PR
- Multi-platform wheel builds
- Performance regression testing

## Notes

- Rust toolchain installation adds ~1-2 minutes to CI runs
- Rust caching (rust-cache@v2) significantly speeds up subsequent builds
- Windows builds may require additional MSVC setup
- macOS arm64 builds require macos-14 or later runners
