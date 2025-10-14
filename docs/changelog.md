# Changelog

All notable changes to ParquetFrame are documented here.

For the complete changelog with all releases, please see our [CHANGELOG.md](https://github.com/leechristophermurray/parquetframe/blob/main/CHANGELOG.md) file in the repository root.

## Latest Release

### [0.3.0] - 2025-10-14

#### 🎉 Major Feature Release: Multi-Format Support

This release transforms ParquetFrame into a comprehensive multi-format data processing framework while maintaining full backward compatibility.

#### ✨ New Features
- **Multi-Format Support**: CSV (.csv, .tsv), JSON (.json, .jsonl, .ndjson), ORC (.orc), and Parquet (.parquet, .pqt)
- **Automatic Format Detection**: Smart detection from file extensions with manual override capability
- **Handler-Based Architecture**: Extensible design with format-specific handlers
- **Enhanced CLI**: Multi-format support in all CLI commands (`pframe info`, `pframe run`)
- **Intelligent Backend Selection**: Improved file size threshold (100MB) for pandas/Dask selection
- **Format-Specific Features**: TSV delimiter detection, JSON Lines support, ORC big data integration

#### 🔧 Improvements
- Enhanced error handling with graceful dependency management
- Comprehensive path resolution for all file formats
- Updated documentation with multi-format examples and guides
- CLI format override with `--format` option
- Improved help text and examples throughout

#### 🧪 Testing
- 37 comprehensive tests (23 core + 14 CLI) covering all formats
- 47% code coverage on core modules with robust edge case handling
- End-to-end multi-format workflow testing

#### 📚 Documentation
- Complete multi-format guide (`docs/formats.md`)
- Updated README with comprehensive examples
- Enhanced CLI documentation
- Format-specific usage patterns and best practices

### Previous Releases

### [0.2.3.2] - Previous Version

#### Added
- Automatic pandas/Dask backend selection based on file size
- Smart file extension handling for parquet files (.parquet, .pqt)
- Seamless conversion between pandas and Dask DataFrames
- Full API compatibility with pandas and Dask operations
- Comprehensive CLI interface
- SQL query support with DuckDB
- AI-powered natural language queries
- Performance benchmarking tools

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
