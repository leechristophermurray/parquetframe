# Rust Distribution & Release Process

ParquetFrame uses a hybrid Python/Rust distribution model. The core logic is in Python, while performance-critical sections are implemented in Rust using PyO3.

## Wheel Building

We use [maturin](https://github.com/PyO3/maturin) to build Python wheels that include the compiled Rust extension.

### CI Matrix

Our GitHub Actions workflow (`wheels.yml`) builds wheels for the following platforms:

- **Linux**: `x86_64`, `aarch64` (via manylinux)
- **macOS**: `x86_64` (Intel), `aarch64` (Apple Silicon)
- **Windows**: `x64`

### Local Development

To build the extension locally for development:

```bash
# Install maturin
pip install maturin

# Build and install in current environment
maturin develop
```

To build a release wheel locally:

```bash
maturin build --release
```

The resulting wheel will be placed in `target/wheels/`.

## Release Process

1.  **Version Bump**: Update version in `pyproject.toml` and `Cargo.toml`.
2.  **Tag**: Create a git tag (e.g., `v0.2.0`).
3.  **CI Build**: Pushing the tag triggers the release workflow (if configured) or manually trigger `wheels.yml`.
4.  **PyPI Upload**: The CI workflow uploads the built wheels to PyPI.

## Troubleshooting

### "No module named _rustic"

If you see this error, it means the Rust extension hasn't been compiled or installed correctly.

- **Solution**: Run `maturin develop` to rebuild the extension in your current environment.

### Linker Errors

On some systems, you might need to install python development headers.

- **Ubuntu/Debian**: `sudo apt install python3-dev`
- **Fedora**: `sudo dnf install python3-devel`
