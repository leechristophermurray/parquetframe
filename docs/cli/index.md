# Interactive CLI

ParquetFrame provides a rich interactive REPL for data exploration.

## Quick Start

```bash
# Start interactive REPL
python -m parquetframe.cli.repl
```

Or from Python:

```python
from parquetframe.cli import start_repl
start_repl()
```

## Features

### Syntax Highlighting

Powered by `rich`, the REPL provides:
- Colorized code syntax
- Beautiful output formatting
- Enhanced error messages

### Pre-loaded Libraries

The REPL automatically imports:
- `pf` - ParquetFrame
- `pd` - pandas
- `np` - numpy

### IPython Integration

If IPython is installed, you get:
- Tab completion
- Magic commands
- Better history

## Installation

For full features:

```bash
pip install parquetframe[cli]
# or
pip install rich ipython
```

## Usage Examples

```python
# Start REPL
from parquetframe.cli import start_repl
start_repl()

# Inside REPL:
>>> import parquetframe as pf
>>> df = pf.read_parquet("data.parquet")
>>> df.head()

# SQL queries
>>> result = pf.sql("SELECT * FROM data WHERE value > 100", data=df)

# Time series
>>> df.ts.resample('1D', agg='mean')

# Financial indicators
>>> df.fin.sma('close', 20)
```

## Basic REPL

If rich/IPython not installed, fallback to basic REPL:

```python
from parquetframe.cli import start_basic_repl
start_basic_repl()
```

## Command Line

Add to your workflow:

```bash
# Data exploration script
python -c "
from parquetframe.cli import start_repl
start_repl()
"
```

## Configuration

Customize your REPL:

```python
from parquetframe.cli import start_repl
from rich.console import Console

# Custom console
console = Console(width=120)
start_repl()
```

## Tips

### Quick Data Inspection

```python
>>> df.head()
>>> df.describe()
>>> df.info()
```

### Chaining Operations

```python
>>> (df
...   .ts.resample('1H', agg='mean')
...   .fin.sma('value', 20)
...   .head())
```

### Visual Output

```python
>>> from rich import print
>>> print(df.head())  # Pretty formatted tables
```

## Dependencies

- **Required**: None (basic REPL works without extras)
- **Recommended**:
  - `rich` - Syntax highlighting and formatting
  - `ipython` - Enhanced REPL features
  
Install with:
```bash
pip install rich ipython
```
