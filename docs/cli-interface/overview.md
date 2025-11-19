# CLI Guide

ParquetFrame includes a powerful command-line interface (`pframe`) that brings the full capabilities of the library to your terminal. Whether you need to quickly explore data, process files in batch mode, or work interactively with parquet files, the CLI has you covered.

## Quick Overview

The `pframe` CLI provides three main commands:

=== "Info"

    Get detailed information about parquet files without loading them into memory:

    ```bash
    pframe info data.parquet
    ```

=== "Run"

    Process parquet files with filtering, transformations, and output generation:

    ```bash
    pframe run data.parquet --query "age > 30" --output filtered.parquet
    ```

=== "Interactive"

    Start a full Python REPL with ParquetFrame integration:

    ```bash
    pframe interactive data.parquet
    ```

## Key Features

### 🚀 **Smart Backend Selection**
Automatically chooses between pandas and Dask based on file size, with manual override options.

### 🎨 **Beautiful Output**
Rich terminal formatting with tables, colors, and progress indicators for enhanced readability.

### 📝 **Script Generation**
Automatically generate reproducible Python scripts from your CLI sessions and operations.

### 🔍 **Data Exploration**
Powerful filtering, column selection, sampling, and statistical analysis capabilities.

### 🔄 **Session Persistence**
Interactive mode with command history, tab completion, and session management.

### 📊 **Comprehensive Analysis**
Built-in statistical descriptions, data profiling, and schema inspection tools.

## Installation

Install ParquetFrame with CLI support:

```bash
pip install parquetframe[cli]
```

This installs the core library plus CLI dependencies (click, rich).

## Getting Help

Get help for any command:

```bash
# General help
pframe --help

# Command-specific help
pframe run --help
pframe interactive --help
pframe info --help
```

## Next Steps

- [CLI Installation](../getting-started/installation.md) - Detailed installation instructions
- [Basic Commands](commands.md) - Learn all the available commands
- [Interactive Mode](interactive.md) - Master the interactive Python environment
- [CLI Examples](../documentation-examples/examples-gallery.md) - See real-world usage examples
