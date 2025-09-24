# CLI Commands Reference

This page provides comprehensive documentation for all `pframe` CLI commands and their options.

## `pframe info`

Display detailed information about parquet files without loading them into memory.

### Usage

```bash
pframe info <file>
```

### Description

The `info` command provides:

- **File metadata**: Size, path, recommended backend
- **Schema information**: Column names, types, nullability  
- **Parquet metadata**: Row groups, total rows/columns
- **Storage details**: Compression, encoding information

### Examples

```bash
# Basic file info
pframe info data.parquet

# Works with .pqt files too
pframe info dataset.pqt
```

### Sample Output

```
File Information: data.parquet
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property            ┃ Value                               ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Size           │ 2,345,678 bytes (2.24 MB)          │
│ Recommended Backend │ pandas (eager)                      │
└─────────────────────┴─────────────────────────────────────┘

Parquet Schema:
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ Column   ┃ Type   ┃ Nullable ┃
┡━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ user_id  │ int64  │ No       │
│ name     │ string │ Yes      │
│ email    │ string │ Yes      │
└──────────┴────────┴──────────┘
```

---

## `pframe run`

Process parquet files with filtering, transformations, and analysis operations.

### Usage

```bash
pframe run <file> [OPTIONS]
```

### Core Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--query` | `-q` | TEXT | Filter data with pandas/Dask query expressions |
| `--columns` | `-c` | TEXT | Select specific columns (comma-separated) |
| `--output` | `-o` | PATH | Save results to output file |
| `--save-script` | `-S` | PATH | Generate Python script of operations |

### Display Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--head` | `-h` | INT | Show first N rows |
| `--tail` | `-t` | INT | Show last N rows |
| `--sample` | `-s` | INT | Show N random rows |
| `--describe` | | FLAG | Statistical description |
| `--info` | | FLAG | Data types and info |

### Backend Options

| Option | Type | Description |
|--------|------|-------------|
| `--threshold` | FLOAT | File size threshold in MB (default: 10) |
| `--force-pandas` | FLAG | Force pandas backend |
| `--force-dask` | FLAG | Force Dask backend |

### Examples

#### Basic Data Exploration

```bash
# Quick preview
pframe run data.parquet

# Show first 10 rows
pframe run data.parquet --head 10

# Statistical summary
pframe run data.parquet --describe
```

#### Filtering and Selection

```bash
# Filter rows
pframe run data.parquet --query "age > 25 and status == 'active'"

# Select columns
pframe run data.parquet --columns "name,email,age"

# Combine filtering and selection
pframe run data.parquet \
  --query "department == 'Engineering'" \
  --columns "name,salary,hire_date" \
  --head 20
```

#### Data Processing Pipeline

```bash
# Complete processing with output
pframe run sales_data.parquet \
  --query "region in ['North', 'South'] and revenue > 10000" \
  --columns "customer_id,product,revenue,date" \
  --output "high_value_sales.parquet" \
  --save-script "sales_analysis.py"
```

#### Backend Control

```bash
# Force pandas for small operations
pframe run data.parquet --force-pandas --describe

# Force Dask for memory efficiency
pframe run large_data.parquet --force-dask --sample 1000

# Custom threshold
pframe run data.parquet --threshold 50 --info
```

---

## `pframe interactive`

Start an interactive Python REPL with ParquetFrame integration.

### Usage

```bash
pframe interactive [file] [OPTIONS]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--threshold` | FLOAT | File size threshold in MB (default: 10) |

### Description

Interactive mode provides:

- **Full Python REPL** with ParquetFrame pre-loaded
- **Session history** with persistent readline support
- **Rich output formatting** for data exploration
- **Script generation** from session commands
- **Pre-loaded variables**: `pf`, `pd`, `dd`, `console`

### Examples

#### Start Interactive Session

```bash
# Empty session
pframe interactive

# Load file automatically
pframe interactive data.parquet

# Custom threshold
pframe interactive large_data.parquet --threshold 50
```

#### Interactive Session Example

```python
# In the interactive session
>>> pf.info()
>>> pf.head(10)
>>> filtered = pf.query("age > 30")
>>> result = filtered.groupby("department").size()
>>> result.save("department_counts.parquet", save_script="analysis.py")
>>> exit()
```

### Available Variables

| Variable | Description |
|----------|-------------|
| `pf` | Your ParquetFrame instance |
| `pd` | pandas module |
| `dd` | dask.dataframe module |
| `console` | rich Console for pretty printing |

### Session Features

- **Tab completion** for all ParquetFrame methods
- **Command history** saved between sessions
- **Rich formatting** for DataFrames and tables  
- **Error handling** with helpful messages
- **Script generation** from session commands

---

## Global Options

These options are available for all commands:

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message |

## Error Handling

The CLI provides helpful error messages for common issues:

- **File not found**: Clear message with suggested fixes
- **Invalid queries**: Pandas/Dask error context
- **Backend issues**: Automatic fallback suggestions
- **Permission errors**: System-specific guidance

## Performance Notes

- **File size detection** happens before backend selection
- **Memory usage** is optimized based on chosen backend
- **Progress indicators** for long-running operations
- **Interrupt handling** with Ctrl+C support