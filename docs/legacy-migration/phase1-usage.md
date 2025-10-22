# Basic Usage (Phase 1 - Legacy)

!!! warning "Deprecated API"
    This documentation describes the **Phase 1 API**, which is now in legacy maintenance mode. For new projects, please use **[Phase 2](../phase2/README.md)** which offers multi-engine support (pandas/Polars/Dask), entity framework, and Zanzibar permissions.

    **Migration Guide**: See [Phase 1 → Phase 2 Migration](../legacy-migration/migration-guide.md)

This guide covers the core functionality of ParquetFrame Phase 1 with detailed examples and explanations.

## Reading Parquet Files

### Automatic Extension Detection

ParquetFrame can automatically detect and read both `.parquet` and `.pqt` files:

```python
import parquetframe as pqf

# These are equivalent:
df1 = pqf.read("data.parquet")  # Explicit extension
df2 = pqf.read("data.pqt")      # Alternative extension
df3 = pqf.read("data")          # Auto-detect extension
```

### Backend Selection

ParquetFrame automatically chooses the optimal backend based on file size:

```python
# Small file (< 10MB default) → pandas for speed
small_df = pqf.read("small_data.parquet")
print(f"Backend: {'Dask' if small_df.islazy else 'pandas'}")

# Large file (> 10MB default) → Dask for memory efficiency
large_df = pqf.read("large_data.parquet")
print(f"Backend: {'Dask' if large_df.islazy else 'pandas'}")
```

### Custom Parameters

```python
# Custom size threshold
df = pqf.read("data.parquet", threshold_mb=50)  # Use Dask for files > 50MB

# Force specific backend
pandas_df = pqf.read("data.parquet", islazy=False)  # Always pandas
dask_df = pqf.read("data.parquet", islazy=True)     # Always Dask

# Pass additional read options
df = pqf.read("data.parquet", columns=['id', 'name', 'value'])
df = pqf.read("data.parquet", filters=[('category', '==', 'A')])
```

## Working with DataFrames

### Accessing the Underlying DataFrame

```python
df = pqf.read("data.parquet")

# Access the underlying pandas or Dask DataFrame
underlying_df = df._df

# Check the type
print(type(underlying_df))  # pandas.DataFrame or dask.dataframe.DataFrame
```

### Standard Operations

All pandas and Dask operations work transparently:

```python
df = pqf.read("sales_data.parquet")

# Basic operations
print(df.shape)
print(df.columns)
print(df.dtypes)

# Data exploration
print(df.head())
print(df.describe())
print(df.info())

# Filtering
active_customers = df[df['status'] == 'active']
high_value = df.query("order_value > 1000")

# Grouping and aggregation
by_region = df.groupby('region').sum()
summary = df.groupby(['region', 'product']).agg({
    'sales': ['sum', 'mean'],
    'quantity': 'sum'
})
```

### Method Chaining

ParquetFrame supports fluent method chaining:

```python
result = (pqf.read("raw_data.parquet")
    .dropna()
    .query("amount > 0")
    .groupby(['region', 'product'])
    .agg({'sales': 'sum', 'profit': 'mean'})
    .reset_index()
    .sort_values('sales', ascending=False)
    .head(10))
```

## Backend Conversion

### Converting Between Backends

```python
df = pqf.read("data.parquet")

# Convert pandas to Dask
if not df.islazy:
    df.to_dask()
    print("Converted to Dask")

# Convert Dask to pandas
if df.islazy:
    df.to_pandas()
    print("Converted to pandas")
```

### Using the islazy Property

```python
df = pqf.read("data.parquet")

# Check current backend
print(f"Current backend: {'Dask' if df.islazy else 'pandas'}")

# Switch backends using property
df.islazy = True   # Convert to Dask
df.islazy = False  # Convert to pandas
```

### Custom Partitions for Dask

```python
df = pqf.read("data.parquet", islazy=False)  # Start with pandas

# Convert to Dask with specific number of partitions
df.to_dask(npartitions=8)
print(f"Dask partitions: {df._df.npartitions}")
```

## Saving Data

### Basic Saving

```python
df = pqf.read("input.parquet")

# Process data
result = df.groupby('category').sum()

# Save with automatic extension
result.save("output")  # Saves as "output.parquet"
```

### Custom Extensions and Options

```python
# Specify extension
result.save("output.pqt")

# Pass compression options
result.save("compressed_output", compression='snappy')
result.save("gzip_output", compression='gzip')

# Other parquet options
result.save("custom_output",
           compression='snappy',
           index=False,
           partition_cols=['region'])
```

### Chaining with Save

```python
# Save returns self, enabling chaining
final_result = (pqf.read("input.parquet")
    .groupby('category').sum()
    .save("intermediate_result")  # Save intermediate
    .query("total > 1000")
    .save("final_result"))        # Save final
```

## Working with Different Data Types

### Mixed Data Types

```python
import pandas as pd

# Create test data with mixed types
df = pd.DataFrame({
    'id': range(1000),
    'name': [f'item_{i}' for i in range(1000)],
    'price': [10.99 + i * 0.1 for i in range(1000)],
    'active': [i % 2 == 0 for i in range(1000)],
    'date': pd.date_range('2023-01-01', periods=1000, freq='H')
})

# Save and read back
pf = pqf.ParquetFrame(df)
pf.save("mixed_types")
loaded = pqf.read("mixed_types")

# Data types are preserved
print(loaded.dtypes)
```

### DateTime Operations

```python
df = pqf.read("time_series.parquet")

# DateTime operations work with both backends
daily_summary = df.groupby(df.timestamp.dt.date).sum()
monthly_avg = df.groupby(df.timestamp.dt.to_period('M')).mean()

# For Dask, some operations might need .compute()
if df.islazy:
    result = daily_summary.compute()
else:
    result = daily_summary
```

## Error Handling

### Common Error Patterns

```python
import parquetframe as pqf

# Handle missing files
try:
    df = pqf.read("nonexistent.parquet")
except FileNotFoundError as e:
    print(f"File not found: {e}")

# Handle empty ParquetFrame
try:
    empty_pf = pqf.create_empty()
    empty_pf.save("output")  # This will fail
except TypeError as e:
    print(f"Cannot save empty frame: {e}")

# Handle attribute errors
try:
    df = pqf.read("data.parquet")
    result = df.nonexistent_method()
except AttributeError as e:
    print(f"Method not found: {e}")
```

### Validating Data

```python
def validate_dataframe(pf):
    """Validate ParquetFrame data quality."""
    if pf._df is None:
        raise ValueError("ParquetFrame is empty")

    if len(pf) == 0:
        raise ValueError("DataFrame has no rows")

    # Check for required columns
    required_cols = ['id', 'amount', 'date']
    missing_cols = set(required_cols) - set(pf.columns)
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    print("✅ Data validation passed")

# Usage
df = pqf.read("data.parquet")
validate_dataframe(df)
```

## Performance Considerations

### When to Use Each Backend

```python
import os

def choose_backend_strategy(file_path):
    """Demonstrate backend selection strategy."""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if file_size_mb < 5:
        # Very small files - always use pandas for speed
        return pqf.read(file_path, islazy=False)
    elif file_size_mb < 50:
        # Medium files - let ParquetFrame decide
        return pqf.read(file_path)
    else:
        # Large files - ensure Dask for memory efficiency
        return pqf.read(file_path, islazy=True)
```

### Memory Management

```python
# For large datasets, be mindful of memory usage
large_df = pqf.read("huge_dataset.parquet", islazy=True)

# Avoid loading entire dataset into memory
# Instead of: result = large_df.compute()  # Don't do this
# Do this:
sample = large_df.sample(frac=0.01).compute()  # 1% sample
summary = large_df.describe().compute()        # Summary statistics

# Or process in chunks
chunks = []
for i in range(large_df.npartitions):
    chunk_result = large_df.get_partition(i).sum().compute()
    chunks.append(chunk_result)
```

## Integration Patterns

### With Pandas Ecosystem

```python
import pandas as pd
import numpy as np

df = pqf.read("data.parquet")

# Ensure pandas backend for pandas-specific operations
if df.islazy:
    df.to_pandas()

# Now use pandas-specific features
correlation_matrix = df._df.corr()
pivot_table = df._df.pivot_table(
    values='sales',
    index='region',
    columns='product',
    aggfunc='sum'
)
```

### With Dask Ecosystem

```python
import dask.dataframe as dd
from dask.distributed import Client

# Set up Dask client for distributed computing
client = Client()  # Connect to local cluster

df = pqf.read("large_dataset.parquet", islazy=True)

# Use Dask-specific features
print(f"Partitions: {df._df.npartitions}")
print(f"Memory usage: {df._df.memory_usage_per_partition().compute()}")

# Visualize computation graph
df._df.visualize("computation_graph.png")

client.close()
```

### With Machine Learning Workflows

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Load and prepare data
df = pqf.read("ml_dataset.parquet")

# For ML workflows, usually need pandas
if df.islazy:
    print("Converting large dataset to pandas for ML...")
    # Consider sampling for very large datasets
    if len(df) > 1_000_000:
        df = df.sample(frac=0.1)  # Use 10% sample
    df.to_pandas()

# Standard ML preprocessing
X = df.drop('target', axis=1)._df
y = df['target']._df

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

---

**Next**: Learn about [Advanced Features](phase1-advanced.md) for more sophisticated use cases.
