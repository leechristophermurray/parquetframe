# ParquetFrame

[![PyPI Version](https://badge.fury.io/py/parquetframe.svg)](https://badge.fury.io/py/parquetframe)
[![Python Support](https://img.shields.io/pypi/pyversions/parquetframe.svg)](https://pypi.org/project/parquetframe/)
[![License](https://img.shields.io/github/license/leechristophermurray/parquetframe.svg)](https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE)
[![Tests](https://github.com/leechristophermurray/parquetframe/workflows/Tests/badge.svg)](https://github.com/leechristophermurray/parquetframe/actions)
[![Coverage](https://codecov.io/gh/leechristophermurray/parquetframe/branch/main/graph/badge.svg)](https://codecov.io/gh/leechristophermurray/parquetframe)

**A universal wrapper for working with dataframes in Python, seamlessly switching between pandas and Dask based on file size or manual control.**

## ✨ Features

🚀 **Automatic Backend Selection**: Automatically chooses pandas for small files (<10MB) and Dask for larger files  
📁 **Smart File Handling**: Reads parquet files without requiring file extensions (`.parquet`, `.pqt`)  
🔄 **Seamless Switching**: Convert between pandas and Dask with simple methods  
⚡ **Full API Compatibility**: All pandas/Dask operations work transparently  
🎯 **Zero Configuration**: Works out of the box with sensible defaults  

## 🚀 Quick Start

=== "Installation"

    ```bash
    pip install parquetframe
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

## 🎯 Why ParquetFrame?

### The Problem

Working with dataframes in Python often means choosing between:

- **pandas**: Fast for small datasets, but runs out of memory on large files
- **Dask**: Memory-efficient for large datasets, but slower for small operations
- **Manual switching**: Writing boilerplate code to handle different backends

### The Solution

ParquetFrame automatically chooses the right backend based on your data size, while providing a consistent API that works with both pandas and Dask. No more manual backend management or code duplication.

## 📊 Performance Benefits

- **Automatic optimization**: Use pandas for speed on small data, Dask for memory efficiency on large data
- **Memory efficiency**: Never load more data than your system can handle
- **Speed optimization**: Fast pandas operations for small datasets, scalable Dask for large ones
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
- [API Reference](api.md) - Complete API documentation
- [Performance Tips](performance.md) - Optimize your workflows

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE) file for details.

---

**Ready to simplify your dataframe workflows?** Check out the [Quick Start Guide](quickstart.md) to get started!