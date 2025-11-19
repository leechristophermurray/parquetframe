# Installation

## Quick Install

The simplest way to install ParquetFrame is via pip:

```bash
pip install parquetframe
```

## Installation Options

### Standard Installation

```bash
pip install parquetframe
```

This installs ParquetFrame with all required dependencies:
- `pandas >= 2.0.0`
- `dask[dataframe] >= 2023.1.0`
- `pyarrow >= 10.0.0`

### Development Installation

For contributors or those wanting to run tests:

```bash
git clone https://github.com/leechristophermurray/parquetframe.git
cd parquetframe
pip install -e ".[dev]"
```

### From Source

```bash
pip install git+https://github.com/leechristophermurray/parquetframe.git
```

### Rust Backend

To enable the Rust backend for performance acceleration:

```bash
pip install parquetframe[rust]
```

This installs the `pf-py` bindings and required Rust crates.


## Verify Installation

Test your installation:

```python
import parquetframe as pqf
print(pqf.__version__)

# Create a simple test
import pandas as pd
test_df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
pf = pqf.ParquetFrame(test_df)
print(f"Backend: {'Dask' if pf.islazy else 'pandas'}")
print("✅ ParquetFrame is working correctly!")
```

## Requirements

### Python Version
- **Python 3.10** or higher

### Core Dependencies
- **pandas >= 2.0.0**: DataFrame operations
- **dask[dataframe] >= 2023.1.0**: Distributed computing
- **pyarrow >= 10.0.0**: Parquet file format support

### Optional Dependencies
For development:
- **pytest >= 7.0**: Testing framework
- **pytest-cov >= 4.0**: Coverage reporting
- **ruff >= 0.1.0**: Code linting
- **black >= 23.0**: Code formatting
- **mypy >= 1.0**: Type checking

## Platform Support

ParquetFrame is tested on:
- **Linux** (Ubuntu, CentOS, Amazon Linux)
- **macOS** (Intel and Apple Silicon)
- **Windows** (Windows 10/11)

## Troubleshooting

### Common Installation Issues

#### ImportError: No module named 'parquetframe'
```bash
# Make sure pip installed to the correct environment
pip show parquetframe

# If using virtual environment, activate it first
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install parquetframe
```

#### Version Conflicts
```bash
# Check for conflicting versions
pip list | grep -E "(pandas|dask|pyarrow)"

# Update conflicting packages
pip install --upgrade pandas dask[dataframe] pyarrow
```

#### Permission Errors
```bash
# Install for current user only
pip install --user parquetframe

# Or use virtual environment (recommended)
python -m venv parquetframe-env
source parquetframe-env/bin/activate  # Linux/Mac
pip install parquetframe
```

### Environment-Specific Issues

#### Conda Environments
```bash
# Create new conda environment
conda create -n parquetframe python=3.11
conda activate parquetframe

# Install via pip (recommended)
pip install parquetframe

# Or install dependencies via conda first
conda install pandas dask pyarrow
pip install parquetframe
```

#### Docker
```dockerfile
FROM python:3.11-slim

# Install ParquetFrame
RUN pip install parquetframe

# Your application code
COPY . /app
WORKDIR /app
```

#### Google Colab
```python
# In a Colab notebook cell
!pip install parquetframe

# Restart runtime if needed
import parquetframe as pqf
```

## Performance Optimization

### Memory Requirements

Recommended minimum system requirements:
- **4GB RAM**: Basic usage with small datasets
- **8GB RAM**: Comfortable usage with medium datasets
- **16GB+ RAM**: Large dataset processing

### Storage Requirements

- **Disk space**: 100MB for ParquetFrame and dependencies
- **Temporary space**: 2-3x your largest parquet file size for processing

### Network Requirements

Initial installation requires internet access to download:
- ParquetFrame package (~50KB)
- Dependencies (~200MB total)

Once installed, ParquetFrame works offline.

## Upgrading

### Upgrade to Latest Version
```bash
pip install --upgrade parquetframe
```

### Upgrade with Dependencies
```bash
pip install --upgrade parquetframe pandas dask[dataframe] pyarrow
```

### Check Version
```python
import parquetframe as pqf
print(f"ParquetFrame version: {pqf.__version__}")
```

## Uninstalling

```bash
pip uninstall parquetframe
```

This removes ParquetFrame but keeps dependencies. To remove dependencies:

```bash
pip uninstall parquetframe pandas dask pyarrow
```

---

**Next Steps**: Once installed, check out the [Quick Start Guide](quickstart.md) to start using ParquetFrame!
