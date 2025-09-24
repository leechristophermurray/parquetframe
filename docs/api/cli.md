# CLI API Reference

> Complete reference for ParquetFrame command-line interface.

## Command Line Interface

The ParquetFrame CLI provides powerful command-line tools for data processing.

## Main Commands

### pframe

The main CLI entry point.

```bash
pframe [OPTIONS] COMMAND [ARGS]...
```

### info

Display information about parquet files.

```bash
pframe info [OPTIONS] FILE
```

### run

Execute data processing operations.

```bash
pframe run [OPTIONS] FILE
```

### benchmark

Run performance benchmarks.

```bash
pframe benchmark [OPTIONS]
```

## Command Options

### Global Options

Options available for all commands:
- `--version`: Show version information
- `--help`: Show help message
- `--verbose`: Enable verbose output
- `--quiet`: Suppress output

### File Processing Options

Options for data processing:
- `--output`: Specify output file
- `--format`: Output format
- `--compression`: Compression algorithm

### Query Options

Options for data querying:
- `--query`: SQL-like query expression
- `--columns`: Column selection
- `--head`: Show first N rows
- `--sample`: Random sample size

## Summary

The CLI API provides comprehensive command-line access to all ParquetFrame functionality.

## Examples

```bash
# Get file information
pframe info data.parquet

# Process data with query
pframe run data.parquet --query "age > 25" --output filtered.parquet

# Run benchmarks
pframe benchmark --operations read,write --file-sizes 1MB,10MB

# Interactive mode
pframe interactive data.parquet
```

## Further Reading

- [Core API Reference](core.md)
- [CLI Guide](../cli/index.md)
- [CLI Examples](../cli/examples.md)