# ParquetFrame

[![PyPI Version](https://badge.fury.io/py/parquetframe.svg)](https://badge.fury.io/py/parquetframe)
[![Python Support](https://img.shields.io/pypi/pyversions/parquetframe.svg)](https://pypi.org/project/parquetframe/)
[![License](https://img.shields.io/github/license/leechristophermurray/parquetframe.svg)](https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE)
[![Tests](https://github.com/leechristophermurray/parquetframe/workflows/Tests/badge.svg)](https://github.com/leechristophermurray/parquetframe/actions?query=workflow%3ATests)
[![Coverage](https://codecov.io/gh/leechristophermurray/parquetframe/branch/main/graph/badge.svg)](https://codecov.io/gh/leechristophermurray/parquetframe)

A universal wrapper for working with dataframes in Python, seamlessly switching between pandas and Dask based on file size or manual control.

## Features

🚀 **Automatic Backend Selection**: Automatically chooses pandas for small files (<10MB) and Dask for larger files  
📁 **Smart File Handling**: Reads parquet files without requiring file extensions (`.parquet`, `.pqt`)  
🔄 **Seamless Switching**: Convert between pandas and Dask with simple methods  
⚡ **Full API Compatibility**: All pandas/Dask operations work transparently  
🖥️ **Powerful CLI**: Command-line interface for data exploration and batch processing  
📝 **Script Generation**: Automatic Python script generation from CLI sessions  
🎯 **Zero Configuration**: Works out of the box with sensible defaults  

## Quick Start

### Installation

```bash
# Basic installation
pip install parquetframe

# With CLI support (includes click and rich for enhanced terminal experience)
pip install parquetframe[cli]
```

### Basic Usage

```python
import parquetframe as pqf

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

## CLI Usage

ParquetFrame includes a powerful command-line interface for data exploration and processing:

### Basic Commands

```bash
# Get file information
pframe info data.parquet

# Quick data preview
pframe run data.parquet

# Interactive mode
pframe interactive data.parquet
```

### Data Processing

```bash
# Filter and transform data
pframe run data.parquet \
  --query "age > 30" \
  --columns "name,age,city" \
  --head 10

# Save processed data with script generation
pframe run data.parquet \
  --query "status == 'active'" \
  --output "filtered.parquet" \
  --save-script "my_analysis.py"

# Force specific backends
pframe run data.parquet --force-dask --describe
pframe run data.parquet --force-pandas --info
```

### Interactive Mode

```bash
# Start interactive session
pframe interactive data.parquet

# In the interactive session:
>>> pf.query("age > 25").groupby("city").size()
>>> pf.save("result.parquet", save_script="session.py")
>>> exit()
```

## Key Benefits

- **Performance**: Automatically optimizes for file size - use pandas for speed on small data, Dask for memory efficiency on large data
- **Simplicity**: One consistent API regardless of backend
- **Flexibility**: Override automatic decisions when needed
- **Compatibility**: Drop-in replacement for pandas.read_parquet()
- **CLI Power**: Full command-line interface for data exploration and batch processing
- **Reproducibility**: Automatic Python script generation from CLI sessions

## Requirements

- Python 3.9+
- pandas >= 2.0.0
- dask[dataframe] >= 2023.1.0
- pyarrow >= 10.0.0

### Optional CLI Dependencies

- click >= 8.0 (for CLI interface)
- rich >= 13.0 (for enhanced terminal output)

## CLI Reference

### Commands

- `pframe info <file>` - Display file information and schema
- `pframe run <file> [options]` - Process data with various options
- `pframe interactive [file]` - Start interactive Python session

### Options for `pframe run`

- `--query, -q` - Filter data (e.g., "age > 30")
- `--columns, -c` - Select columns (e.g., "name,age,city")
- `--head, -h N` - Show first N rows
- `--tail, -t N` - Show last N rows
- `--sample, -s N` - Show N random rows
- `--describe` - Statistical description
- `--info` - Data types and info
- `--output, -o` - Save to file
- `--save-script, -S` - Generate Python script
- `--threshold` - Size threshold for backend selection (MB)
- `--force-pandas` - Force pandas backend
- `--force-dask` - Force Dask backend

## Documentation

Full documentation is available at [https://leechristophermurray.github.io/parquetframe/](https://leechristophermurray.github.io/parquetframe/)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.