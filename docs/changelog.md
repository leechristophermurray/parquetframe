# Changelog

All notable changes to ParquetFrame are documented here.

For the complete changelog with all releases, please see our [CHANGELOG.md](https://github.com/leechristophermurray/parquetframe/blob/main/CHANGELOG.md) file in the repository root.

## Latest Release

### [0.1.0] - TBD

#### Added
- Initial release of ParquetFrame
- Automatic pandas/Dask backend selection based on file size
- Smart file extension handling for parquet files (.parquet, .pqt)
- Seamless conversion between pandas and Dask DataFrames
- Full API compatibility with pandas and Dask operations
- Comprehensive test suite with 95%+ coverage
- Complete documentation and examples
- CI/CD pipeline with automated testing and PyPI publishing

#### Features
- ✨ **Automatic Backend Selection**: Files <10MB use pandas, larger files use Dask
- 📁 **Smart File Handling**: Auto-detects .parquet and .pqt extensions
- 🔄 **Seamless Conversion**: Easy switching between pandas and Dask
- ⚡ **Full Compatibility**: All DataFrame operations work transparently
- 🎯 **Zero Configuration**: Works out of the box with sensible defaults

## View Full Changelog

For detailed release notes, breaking changes, and migration guides, see the complete [CHANGELOG.md](https://github.com/leechristophermurray/parquetframe/blob/main/CHANGELOG.md).

## Release Schedule

We follow [Semantic Versioning](https://semver.org/) for releases:

- **Major versions** (1.0, 2.0): Breaking changes
- **Minor versions** (0.1, 0.2): New features, backwards compatible  
- **Patch versions** (0.1.1, 0.1.2): Bug fixes, backwards compatible

## Stay Updated

- **GitHub Releases**: Watch the repository for release notifications
- **PyPI**: Check [PyPI](https://pypi.org/project/parquetframe/) for latest versions
- **RSS Feed**: Subscribe to [GitHub releases RSS](https://github.com/leechristophermurray/parquetframe/releases.atom)