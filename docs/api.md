# API Reference

This page provides detailed documentation for all ParquetFrame classes, functions, and methods.

## Core Module

::: parquetframe.core.ParquetFrame

## Convenience Functions

::: parquetframe.read

::: parquetframe.create_empty

## Type Information

The ParquetFrame class works with the following types:

### DataFrame Types
- `pandas.DataFrame`: Standard pandas DataFrame
- `dask.dataframe.DataFrame`: Dask DataFrame for larger datasets

### Path Types
- `str`: String path to file
- `pathlib.Path`: Path object

### Threshold Types
- `float`: Size threshold in megabytes (MB)
- `None`: Use default threshold (10MB)

### Boolean Flags
- `bool`: True/False values for `islazy` parameter
- `None`: Use automatic detection based on file size

## Examples

### Basic Usage

```python
import parquetframe as pqf

# Read with automatic backend detection
df = pqf.read("data.parquet")

# Check current backend
if df.islazy:
    print("Using Dask backend")
else:
    print("Using pandas backend")

# Perform operations
result = df.groupby("category").mean()

# Save result
result.save("output.parquet")
```

### Advanced Usage

```python
import parquetframe as pqf
from pathlib import Path

# Custom threshold and parameters
df = pqf.read(
    Path("large_dataset"),
    threshold_mb=50,
    columns=["id", "value", "category"]
)

# Manual backend control
df.islazy = True  # Convert to Dask
df.to_pandas()    # Convert to pandas

# Method chaining
result = (df
    .to_dask()
    .groupby("category")
    .sum()
    .to_pandas()
    .save("summary")
)
```

### Error Handling

```python
import parquetframe as pqf

try:
    df = pqf.read("nonexistent.parquet")
except FileNotFoundError as e:
    print(f"File not found: {e}")

try:
    empty_pf = pqf.create_empty()
    empty_pf.save("output")  # This will raise TypeError
except TypeError as e:
    print(f"Cannot save empty frame: {e}")
```

## Backend Comparison

| Feature | pandas | Dask | ParquetFrame |
|---------|--------|------|--------------|
| Memory Usage | High for large data | Memory-efficient | Automatic optimization |
| Speed | Fast for small data | Slower startup, scalable | Best of both |
| API | Rich API | Subset of pandas | Full pandas/Dask API |
| Complexity | Simple | Requires .compute() | Transparent |

## Performance Characteristics

### File Size Recommendations

| File Size | Recommended Backend | ParquetFrame Behavior |
|-----------|-------------------|----------------------|
| < 1 MB | pandas | Automatic pandas |
| 1-10 MB | pandas | Automatic pandas |
| 10-100 MB | Depends on RAM | Automatic Dask |
| 100+ MB | Dask | Automatic Dask |

### Memory Usage Patterns

```python
import parquetframe as pqf

# For small files - pandas is loaded into memory
small_df = pqf.read("small_data.parquet")  # ~5MB file
print(small_df.memory_usage(deep=True).sum())  # Full memory usage

# For large files - Dask uses lazy loading
large_df = pqf.read("large_data.parquet")  # ~100MB file
print(len(large_df))  # This triggers computation only for length
result = large_df.groupby("col").mean().compute()  # Explicit computation
```

## Integration Examples

### With Jupyter Notebooks

```python
import parquetframe as pqf

# ParquetFrame works seamlessly in Jupyter
df = pqf.read("data.parquet")

# Display works for both backends
display(df.head())

# Progress bars work with Dask
if df.islazy:
    from dask.diagnostics import ProgressBar
    with ProgressBar():
        result = df.groupby("category").sum().compute()
```

### With Other Libraries

```python
import parquetframe as pqf
import matplotlib.pyplot as plt
import seaborn as sns

# Read data
df = pqf.read("sales_data.parquet")

# Convert to pandas for plotting if needed
if df.islazy:
    plot_data = df.head(1000).compute()  # Sample for plotting
else:
    plot_data = df

# Create plots
plt.figure(figsize=(10, 6))
sns.histplot(data=plot_data, x="sales_amount")
plt.show()
```

## Common Patterns

### Data Pipeline Pattern

```python
import parquetframe as pqf

def process_sales_data(input_path: str, output_path: str):
    """Process sales data with automatic backend selection."""
    return (pqf.read(input_path)
            .query("sales_amount > 0")
            .groupby(["region", "product"])
            .agg({"sales_amount": "sum", "quantity": "sum"})
            .reset_index()
            .save(output_path))

# Usage
result = process_sales_data("raw_sales.parquet", "processed_sales")
```

### Batch Processing Pattern

```python
import parquetframe as pqf
from pathlib import Path

def process_directory(input_dir: Path, output_dir: Path):
    """Process all parquet files in a directory."""
    output_dir.mkdir(exist_ok=True)
    
    for file_path in input_dir.glob("*.parquet"):
        # Automatic backend selection for each file
        df = pqf.read(file_path)
        
        # Process data
        processed = df.groupby("category").sum()
        
        # Save with same name
        processed.save(output_dir / file_path.stem)

# Usage
process_directory(Path("raw_data"), Path("processed_data"))
```

## Troubleshooting

### Common Issues

#### Memory Errors
```python
# If you get memory errors, force Dask backend
df = pqf.read("large_file.parquet", islazy=True)

# Or reduce threshold
df = pqf.read("file.parquet", threshold_mb=5)
```

#### Performance Issues
```python
# For small operations, ensure pandas backend
df = pqf.read("file.parquet", islazy=False)

# For large operations, use Dask
df = pqf.read("file.parquet", islazy=True)
```

#### Type Errors
```python
# Ensure proper types for parameters
df = pqf.read("file.parquet", threshold_mb=10.0)  # float, not str
df = pqf.read("file.parquet", islazy=True)        # bool, not str
```