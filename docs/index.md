# ParquetFrame

<div align="center">
  <img src="assets/logo.svg" alt="ParquetFrame Logo" width="400" style="max-width: 100%;">
</div>

<div align="center">
  <a href="https://pypi.org/project/parquetframe/"><img src="https://badge.fury.io/py/parquetframe.svg" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/parquetframe/"><img src="https://img.shields.io/pypi/pyversions/parquetframe.svg" alt="Python Support"></a>
  <a href="https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE"><img src="https://img.shields.io/github/license/leechristophermurray/parquetframe.svg" alt="License"></a>
  <br>
  <a href="https://github.com/leechristophermurray/parquetframe/actions"><img src="https://github.com/leechristophermurray/parquetframe/workflows/Tests/badge.svg" alt="Tests"></a>
  <a href="https://codecov.io/gh/leechristophermurray/parquetframe"><img src="https://codecov.io/gh/leechristophermurray/parquetframe/branch/main/graph/badge.svg" alt="Coverage"></a>
</div>

**A universal data processing framework with multi-format support (CSV, JSON, Parquet, ORC) and intelligent pandas/Dask backend selection.**

## ✨ Features

🚀 **Intelligent Backend Selection**: Memory-aware automatic switching between pandas and Dask based on file size, system resources, and file characteristics

📁 **Multi-Format Support**: Seamlessly work with CSV, JSON, ORC, and Parquet files with automatic format detection

📁 **Smart File Handling**: Reads files without requiring extensions - supports `.parquet`, `.pqt`, `.csv`, `.tsv`, `.json`, `.jsonl`, `.ndjson`, `.orc`

🔄 **Seamless Switching**: Convert between pandas and Dask with simple methods

⚡ **Full API Compatibility**: All pandas/Dask operations work transparently

🗃️ **SQL Support**: Execute SQL queries on DataFrames using DuckDB with automatic JOIN capabilities

🧬 **BioFrame Integration**: Genomic interval operations with parallel Dask implementations

🖥️ **Powerful CLI**: Command-line interface for data exploration, SQL queries, and batch processing

📝 **Script Generation**: Automatic Python script generation from CLI sessions

⚡ **Performance Optimization**: Built-in benchmarking tools and intelligent threshold detection

📋 **YAML Workflows**: Define complex data processing pipelines in YAML with declarative syntax

🎯 **Zero Configuration**: Works out of the box with sensible defaults

## 🚀 Quick Start

=== "Installation"

    ```bash
    # Basic installation
    pip install parquetframe

    # With CLI support (recommended)
    pip install parquetframe[cli]
    ```

=== "Basic Usage"

    ```python
    import parquetframe as pqf

    # Read a file - automatically chooses pandas or Dask based on size
    df = pqf.read("my_data")  # Handles .parquet/.pqt extensions automatically

    # All standard DataFrame operations work
    result = df.groupby("column").sum()

    # Save without worrying about extensions
    df.save("output")  # Saves as output.parquet
    ```

=== "Advanced Usage"

    ```python
    import parquetframe as pqf

    # Custom threshold
    df = pqf.read("data", threshold_mb=50)  # Use Dask for files >50MB

    # Force backend
    df = pqf.read("data", islazy=True)   # Force Dask
    df = pqf.read("data", islazy=False)  # Force pandas

    # Check current backend
    print(df.islazy)  # True for Dask, False for pandas

    # Chain operations
    result = (pqf.read("input")
              .groupby("category")
              .sum()
              .save("result"))
    ```

=== "CLI Usage"

    ```bash
    # Quick file info
    pframe info data.parquet

    # Data processing
    pframe run data.parquet --query "age > 30" --head 10

    # Interactive mode
    pframe interactive data.parquet

    # Performance benchmarking
    pframe benchmark --operations "groupby,filter"
    ```

## 🎯 Why ParquetFrame?

### The Problem

Working with dataframes in Python often means choosing between:

- **pandas**: Fast for small datasets, but runs out of memory on large files
- **Dask**: Memory-efficient for large datasets, but slower for small operations
- **Manual switching**: Writing boilerplate code to handle different backends

### The Solution

ParquetFrame automatically chooses the right backend based on your data size, while providing a consistent API that works with both pandas and Dask. No more manual backend management or code duplication.

## 📊 Performance Benefits

- **Intelligent optimization**: Memory-aware backend selection considering file size, system resources, and file characteristics
- **Built-in benchmarking**: Comprehensive performance analysis tools to optimize your workflows
- **Memory efficiency**: Never load more data than your system can handle
- **Speed optimization**: Fast pandas operations for small datasets, scalable Dask for large ones
- **CLI performance tools**: Built-in benchmarking and analysis from the command line
- **Zero overhead**: Direct delegation to underlying libraries without performance penalty

## 🛠️ Key Concepts

### Automatic Backend Selection

```python
import parquetframe as pqf

# Small file (< 10MB) → pandas (fast operations)
small_df = pqf.read("small_dataset.parquet")
print(type(small_df._df))  # <class 'pandas.core.frame.DataFrame'>

# Large file (> 10MB) → Dask (memory efficient)
large_df = pqf.read("large_dataset.parquet")
print(type(large_df._df))  # <class 'dask.dataframe.core.DataFrame'>
```

### Manual Control

```python
# Override automatic detection
pandas_df = pqf.read("any_file.parquet", islazy=False)  # Force pandas
dask_df = pqf.read("any_file.parquet", islazy=True)     # Force Dask

# Convert between backends
pandas_df.to_dask()    # Convert to Dask
dask_df.to_pandas()    # Convert to pandas

# Property-based control
df.islazy = True   # Convert to Dask
df.islazy = False  # Convert to pandas
```

### File Extension Handling

```python
# All of these work the same way:
df1 = pqf.read("data.parquet")  # Explicit extension
df2 = pqf.read("data.pqt")      # Alternative extension
df3 = pqf.read("data")          # Auto-detect extension

# Save with automatic extension
df.save("output")         # Saves as "output.parquet"
df.save("output.pqt")     # Saves as "output.pqt"
```

## 📋 Requirements

- Python 3.9+
- pandas >= 2.0.0
- dask[dataframe] >= 2023.1.0
- pyarrow >= 10.0.0

## 📚 Documentation

- [Installation Guide](installation.md) - Detailed installation instructions
- [Quick Start](quickstart.md) - Get up and running in minutes
- [User Guide](usage.md) - Comprehensive usage examples
- [CLI Guide](cli/index.md) - Complete command-line interface documentation
- [Performance Optimization](tutorials/performance.md) - Advanced performance features and benchmarking
- [API Reference](api/core.md) - Complete API documentation
- [Performance Tips](performance.md) - Optimize your workflows

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE) file for details.

---

**Ready to simplify your dataframe workflows?** Check out the [Quick Start Guide](quickstart.md) to get started!
