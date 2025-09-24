# ParquetFrame

[![PyPI Version](https://badge.fury.io/py/parquetframe.svg)](https://badge.fury.io/py/parquetframe)
[![Python Support](https://img.shields.io/pypi/pyversions/parquetframe.svg)](https://pypi.org/project/parquetframe/)
[![License](https://img.shields.io/github/license/leechristophermurray/parquetframe.svg)](https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE)
[![Tests](https://github.com/leechristophermurray/parquetframe/workflows/Tests/badge.svg)](https://github.com/leechristophermurray/parquetframe/actions?query=workflow%3ATests)
[![Coverage](https://codecov.io/gh/leechristophermurray/parquetframe/branch/main/graph/badge.svg)](https://codecov.io/gh/leechristophermurray/parquetframe)

A universal wrapper for working with dataframes in Python, seamlessly switching between pandas and Dask based on file size or manual control.

## Features

🚀 **Intelligent Backend Selection**: Memory-aware automatic switching between pandas and Dask based on file size, system resources, and file characteristics
📁 **Smart File Handling**: Reads parquet files without requiring file extensions (`.parquet`, `.pqt`)
🔄 **Seamless Switching**: Convert between pandas and Dask with simple methods
⚡ **Full API Compatibility**: All pandas/Dask operations work transparently
🗃️ **SQL Support**: Execute SQL queries on DataFrames using DuckDB with automatic JOIN capabilities
🧬 **BioFrame Integration**: Genomic interval operations with parallel Dask implementations
🖥️ **Powerful CLI**: Command-line interface for data exploration, SQL queries, and batch processing
📝 **Script Generation**: Automatic Python script generation from CLI sessions
⚡ **Performance Optimization**: Built-in benchmarking tools and intelligent threshold detection
📋 **YAML Workflows**: Define complex data processing pipelines in YAML with declarative syntax
🎯 **Zero Configuration**: Works out of the box with sensible defaults

## Quick Start

### Installation

```bash
# Basic installation
pip install parquetframe

# With CLI support
pip install parquetframe[cli]

# With SQL support (includes DuckDB)
pip install parquetframe[sql]

# With genomics support (includes bioframe)
pip install parquetframe[bio]

# All features
pip install parquetframe[all]

# Development installation
pip install parquetframe[dev,all]
```

### Basic Usage

```python
import parquetframe as pf

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
df = pf.read("data", threshold_mb=50)  # Use Dask for files >50MB

# Force backend
df = pf.read("data", islazy=True)   # Force Dask
df = pf.read("data", islazy=False)  # Force pandas

# Check current backend
print(df.islazy)  # True for Dask, False for pandas

# Chain operations
result = (pf.read("input")
          .groupby("category")
          .sum()
          .save("result"))
```

### SQL Operations

```python
import parquetframe as pf

# Read data
customers = pf.read("customers.parquet")
orders = pf.read("orders.parquet")

# Execute SQL queries with automatic JOIN
result = customers.sql("""
    SELECT c.name, c.age, SUM(o.amount) as total_spent
    FROM df c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE c.age > 25
    GROUP BY c.name, c.age
    ORDER BY total_spent DESC
""", orders=orders)

# Works with both pandas and Dask backends
print(result.head())
```

### Genomic Data Analysis

```python
import parquetframe as pf

# Read genomic interval data
genes = pf.read("genes.parquet")
peaks = pf.read("chip_seq_peaks.parquet")

# Find overlapping intervals with parallel processing
overlaps = genes.bio.overlap(peaks, broadcast=True)

# Cluster nearby genomic features
clustered = genes.bio.cluster(min_dist=1000)

# Works efficiently with both small and large datasets
print(f"Found {len(overlaps)} gene-peak overlaps")
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

# SQL queries on parquet files
pframe sql "SELECT * FROM df WHERE age > 30" --file data.parquet
pframe sql --interactive --file data.parquet
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

# SQL operations with JOINs
pframe sql "SELECT * FROM df JOIN customers ON df.id = customers.id" \
  --file orders.parquet \
  --join "customers=customers.parquet" \
  --output results.parquet
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

### Performance Benchmarking

```bash
# Run comprehensive performance benchmarks
pframe benchmark

# Benchmark specific operations
pframe benchmark --operations "groupby,filter,sort"

# Test with custom file sizes
pframe benchmark --file-sizes "1000,10000,100000"

# Save benchmark results
pframe benchmark --output results.json --quiet
```

### YAML Workflows

```bash
# Create an example workflow
pframe workflow --create-example my_pipeline.yml

# List available workflow step types
pframe workflow --list-steps

# Execute a workflow
pframe workflow my_pipeline.yml

# Execute with custom variables
pframe workflow my_pipeline.yml --variables "input_dir=data,min_age=21"

# Validate workflow without executing
pframe workflow --validate my_pipeline.yml
```

## Key Benefits

- **Intelligent Performance**: Memory-aware backend selection considering file size, system resources, and file characteristics
- **Built-in Benchmarking**: Comprehensive performance analysis tools to optimize your data processing workflows
- **Simplicity**: One consistent API regardless of backend
- **Flexibility**: Override automatic decisions when needed
- **Compatibility**: Drop-in replacement for pandas.read_parquet()
- **CLI Power**: Full command-line interface for data exploration, batch processing, and performance benchmarking
- **Reproducibility**: Automatic Python script generation from CLI sessions
- **Zero-Configuration Optimization**: Automatic performance improvements with intelligent defaults

## Requirements

- Python 3.9+
- pandas >= 2.0.0
- dask[dataframe] >= 2023.1.0
- pyarrow >= 10.0.0

### Optional Dependencies

**CLI Features (`[cli]`)**
- click >= 8.0 (for CLI interface)
- rich >= 13.0 (for enhanced terminal output)
- psutil >= 5.8.0 (for performance monitoring and memory-aware backend selection)
- pyyaml >= 6.0 (for YAML workflow support)

**SQL Features (`[sql]`)**
- duckdb >= 0.9.0 (for SQL query functionality)

**Genomics Features (`[bio]`)**
- bioframe >= 0.4.0 (for genomic interval operations)

### Development Status

✅ **Stable & Production Ready**: All 203 tests passing with 65% test coverage
🔄 **Active Development**: Regular updates and improvements
🐛 **Bug-Free Core**: Recently resolved all critical issues and test failures
📦 **Latest Release**: v0.1.1 with enhanced stability and bug fixes

## CLI Reference

### Commands

- `pframe info <file>` - Display file information and schema
- `pframe run <file> [options]` - Process data with various options
- `pframe interactive [file]` - Start interactive Python session
- `pframe sql <query> [options]` - Execute SQL queries on parquet files
- `pframe benchmark [options]` - Run performance benchmarks and analysis
- `pframe workflow [file] [options]` - Execute or manage YAML workflow files

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

### Options for `pframe sql`

- `--file, -f` - Main parquet file to query (available as 'df')
- `--join, -j` - Additional files for JOINs in format 'name=path'
- `--output, -o` - Save query results to file
- `--interactive, -i` - Start interactive SQL mode
- `--explain` - Show query execution plan
- `--validate` - Validate SQL query syntax

### Options for `pframe benchmark`

- `--output, -o` - Save benchmark results to JSON file
- `--quiet, -q` - Run in quiet mode (minimal output)
- `--operations` - Comma-separated operations to benchmark (groupby,filter,sort,aggregation,join)
- `--file-sizes` - Comma-separated test file sizes in rows (e.g., '1000,10000,100000')

### Options for `pframe workflow`

- `--validate, -v` - Validate workflow file without executing
- `--variables, -V` - Set workflow variables as key=value pairs
- `--list-steps` - List all available workflow step types
- `--create-example PATH` - Create an example workflow file
- `--quiet, -q` - Run in quiet mode (minimal output)

## Documentation

Full documentation is available at [https://leechristophermurray.github.io/parquetframe/](https://leechristophermurray.github.io/parquetframe/)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
