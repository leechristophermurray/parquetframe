# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-09-24

### Added
- 🎉 **Initial release of ParquetFrame**
- ✨ **Automatic pandas/Dask backend selection** based on file size (default 10MB threshold)
- 📁 **Smart file extension handling** for parquet files (`.parquet`, `.pqt`)
- 🔄 **Seamless conversion** between pandas and Dask DataFrames (`to_pandas()`, `to_dask()`)
- ⚡ **Full API compatibility** with pandas and Dask operations through transparent delegation
- 🎯 **Zero configuration** - works out of the box with sensible defaults
- 🧪 **Comprehensive test suite** with 95%+ coverage (410+ tests)
- 📚 **Complete documentation** with MkDocs, API reference, and examples
- 🔧 **Modern development tooling** (ruff, black, mypy, pre-commit hooks)
- 🚀 **CI/CD pipeline** with GitHub Actions for testing and PyPI publishing
- 📦 **Professional packaging** with hatchling build backend

### Features
- `ParquetFrame` class with automatic backend selection
- Convenience functions: `read()`, `create_empty()`
- Property-based backend switching with `islazy` setter
- Method chaining support for data pipeline workflows
- Comprehensive error handling and validation
- Support for all pandas/Dask parquet reading options
- Flexible file path handling (Path objects, relative/absolute paths)
- Memory-efficient processing for large datasets

### Testing
- Unit tests for all core functionality
- Integration tests for backend switching logic
- I/O format tests for compression and data types
- Edge case and error handling tests
- Platform-specific and performance tests
- Test fixtures for various DataFrame scenarios

### Documentation
- Complete user guide with installation, quickstart, and usage examples
- API reference with automatic docstring generation
- Real-world examples for common use cases
- Performance optimization tips
- Contributing guidelines and development setup

[0.1.0]: https://github.com/leechristophermurray/parquetframe/releases/tag/v0.1.0
