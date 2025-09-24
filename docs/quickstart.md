# Quick Start Guide

Get up and running with ParquetFrame in minutes!

## Installation

```bash
pip install parquetframe
```

## Basic Usage

### 1. Import ParquetFrame

```python
import parquetframe as pqf
```

### 2. Read Parquet Files

ParquetFrame automatically detects file extensions and chooses the optimal backend:

```python
# These all work the same way:
df = pqf.read("data.parquet")    # Explicit .parquet extension
df = pqf.read("data.pqt")        # Alternative .pqt extension  
df = pqf.read("data")            # Auto-detect extension
```

### 3. Check Current Backend

```python
print(f"Using {'Dask' if df.islazy else 'pandas'} backend")
print(f"Shape: {df.shape}")
```

### 4. Perform Operations

All pandas and Dask operations work transparently:

```python
# Standard DataFrame operations
summary = df.describe()
filtered = df[df['value'] > 100]
grouped = df.groupby('category').sum()

# Method chaining works too
result = (df
    .query("status == 'active'")
    .groupby(['region', 'product'])
    .agg({'sales': 'sum', 'quantity': 'mean'})
    .reset_index())
```

### 5. Save Results

```python
# Save with automatic .parquet extension
result.save("output")

# Or specify extension
result.save("output.pqt")

# Pass additional options
result.save("compressed_output", compression='snappy')
```

## Key Features Demo

### Automatic Backend Selection

```python
# Small file → pandas (fast)
small_df = pqf.read("small_dataset.parquet")  # < 10MB
print(f"Small file: {type(small_df._df)}")    # pandas.DataFrame

# Large file → Dask (memory efficient)  
large_df = pqf.read("large_dataset.parquet")  # > 10MB
print(f"Large file: {type(large_df._df)}")    # dask.dataframe.DataFrame
```

### Manual Backend Control

```python
# Override automatic selection
pandas_df = pqf.read("any_file.parquet", islazy=False)  # Force pandas
dask_df = pqf.read("any_file.parquet", islazy=True)     # Force Dask

# Convert between backends
pandas_df.to_dask()     # Convert to Dask
dask_df.to_pandas()     # Convert to pandas

# Or use properties
df.islazy = True        # Switch to Dask
df.islazy = False       # Switch to pandas
```

### Custom Thresholds

```python
# Use Dask for files larger than 50MB
df = pqf.read("data.parquet", threshold_mb=50)

# Use pandas for files larger than 1MB (force small threshold)
df = pqf.read("data.parquet", threshold_mb=1)
```

## Common Patterns

### Data Pipeline

```python
result = (pqf.read("raw_data.parquet")
    .query("date >= '2023-01-01'")
    .groupby('customer_id')
    .agg({
        'sales_amount': 'sum',
        'order_count': 'count',
        'avg_order_value': 'mean'
    })
    .reset_index()
    .save("customer_summary"))

print("Pipeline completed!")
```

### Conditional Processing

```python
df = pqf.read("data.parquet")

if df.islazy:
    # Large dataset - use Dask aggregations
    result = df.groupby('category').sales.sum().compute()
else:
    # Small dataset - use pandas for speed
    result = df.groupby('category')['sales'].sum()

print(result)
```

### Batch Processing

```python
from pathlib import Path

input_dir = Path("raw_data")
output_dir = Path("processed_data")
output_dir.mkdir(exist_ok=True)

for file_path in input_dir.glob("*.parquet"):
    print(f"Processing {file_path.name}...")
    
    # Automatic backend selection for each file
    df = pqf.read(file_path)
    
    # Apply transformations
    processed = (df
        .dropna()
        .query("amount > 0")
        .groupby('category')
        .sum())
    
    # Save with same base name
    processed.save(output_dir / file_path.stem)

print("Batch processing complete!")
```

## Working with Different File Sizes

### Small Files (< 10MB)
```python
# Automatically uses pandas for speed
small_df = pqf.read("transactions.parquet")

# Fast operations
daily_summary = small_df.groupby(small_df.date.dt.date).sum()
top_customers = small_df.nlargest(10, 'amount')
```

### Large Files (> 10MB)
```python
# Automatically uses Dask for memory efficiency
large_df = pqf.read("historical_data.parquet")

# Memory-efficient operations
monthly_totals = large_df.groupby('month').amount.sum().compute()
sample_data = large_df.sample(frac=0.01).compute()  # 1% sample
```

### Very Large Files (> 1GB)
```python
# Force Dask for very large files
huge_df = pqf.read("big_data.parquet", islazy=True)

# Use Dask operations with progress tracking
from dask.diagnostics import ProgressBar

with ProgressBar():
    result = huge_df.groupby('region').sales.mean().compute()
```

## Integration Examples

### With Pandas
```python
import pandas as pd
import parquetframe as pqf

# Read with ParquetFrame, convert to pandas if needed
df = pqf.read("data.parquet")
if df.islazy:
    pandas_df = df.to_pandas()._df
else:
    pandas_df = df._df

# Use pandas-specific features
correlation = pandas_df.corr()
```

### With Dask
```python
import dask.dataframe as dd
import parquetframe as pqf

# Read with ParquetFrame, ensure Dask backend
df = pqf.read("data.parquet", islazy=True)
dask_df = df._df

# Use Dask-specific features
partitions = dask_df.npartitions
graph_info = dask_df.visualize("computation_graph.png")
```

### With Machine Learning
```python
import parquetframe as pqf
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load data
df = pqf.read("ml_dataset.parquet")

# Ensure pandas for sklearn compatibility
if df.islazy:
    df = df.to_pandas()

# Prepare data
X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = RandomForestClassifier()
model.fit(X_train, y_train)
```

## Next Steps

Now that you've got the basics down:

1. **[Basic Usage](usage.md)** - Dive deeper into core functionality
2. **[Advanced Features](advanced.md)** - Learn about advanced patterns and optimizations  
3. **[API Reference](api.md)** - Complete documentation of all methods
4. **[Performance Tips](performance.md)** - Optimize your workflows

## Need Help?

- Check the [API Reference](api.md) for detailed method documentation
- Browse [examples](examples.md) for common use cases
- Report issues on [GitHub](https://github.com/leechristophermurray/parquetframe/issues)

Happy data processing! 🚀