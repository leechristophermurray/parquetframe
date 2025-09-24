# ParquetFrame

[![PyPI Version](https://badge.fury.io/py/parquetframe.svg)](https://badge.fury.io/py/parquetframe)
[![Python Support](https://img.shields.io/pypi/pyversions/parquetframe.svg)](https://pypi.org/project/parquetframe/)
[![License](https://img.shields.io/github/license/yourusername/parquetframe.svg)](https://github.com/yourusername/parquetframe/blob/main/LICENSE)
[![Tests](https://github.com/yourusername/parquetframe/workflows/Tests/badge.svg)](https://github.com/yourusername/parquetframe/actions?query=workflow%3ATests)
[![Coverage](https://codecov.io/gh/yourusername/parquetframe/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/parquetframe)

A universal wrapper for working with dataframes in Python, seamlessly switching between pandas and Dask based on file size or manual control.

## Features

🚀 **Automatic Backend Selection**: Automatically chooses pandas for small files (<10MB) and Dask for larger files  
📁 **Smart File Handling**: Reads parquet files without requiring file extensions (`.parquet`, `.pqt`)  
🔄 **Seamless Switching**: Convert between pandas and Dask with simple methods  
⚡ **Full API Compatibility**: All pandas/Dask operations work transparently  
🎯 **Zero Configuration**: Works out of the box with sensible defaults  

## Quick Start

### Installation

```bash
pip install parquetframe
```

### Basic Usage

```python
from parquetframe import pf

# Read a file - automatically chooses pandas or Dask based on size
df = pf.read("my_data")  # Handles .parquet/.pqt extensions automatically

# All standard DataFrame operations work
result = df.groupby("column").sum()

# Save without worrying about extensions
df.save("output")  # Saves as output.parquet

# Manual control
df.to_dask()    # Convert to Dask
df.to_pandas()  # Convert to pandas
```

### Advanced Usage

```python
import parquetframe as pqf

# Custom threshold
df = pqf.pf.read("data", threshold_mb=50)  # Use Dask for files >50MB

# Force backend
df = pqf.pf.read("data", islazy=True)   # Force Dask
df = pqf.pf.read("data", islazy=False)  # Force pandas

# Check current backend
print(df.islazy)  # True for Dask, False for pandas

# Chain operations
result = (pqf.pf.read("input")
          .groupby("category")
          .sum()
          .save("result"))
```

## Key Benefits

- **Performance**: Automatically optimizes for file size - use pandas for speed on small data, Dask for memory efficiency on large data
- **Simplicity**: One consistent API regardless of backend
- **Flexibility**: Override automatic decisions when needed
- **Compatibility**: Drop-in replacement for pandas.read_parquet()

## Requirements

- Python 3.9+
- pandas >= 2.0.0
- dask[dataframe] >= 2023.1.0
- pyarrow >= 10.0.0

## Documentation

Full documentation is available at [https://yourusername.github.io/parquetframe/](https://yourusername.github.io/parquetframe/)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.