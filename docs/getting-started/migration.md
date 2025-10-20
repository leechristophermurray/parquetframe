# Migration Guide: Phase 1 to Phase 2

This guide helps you migrate from ParquetFrame Phase 1 to Phase 2.

## Overview

Phase 2 is **100% backward compatible** with Phase 1. Your existing code will continue to work without changes. However, Phase 2 offers significant improvements that you may want to adopt.

## Key Differences

| Feature | Phase 1 | Phase 2 |
|---------|---------|---------|
| **Import** | `import parquetframe as pf` | `import parquetframe.core as pf2` |
| **Engines** | pandas or Dask | pandas, Polars, or Dask |
| **Selection** | Manual threshold | Intelligent automatic selection |
| **Formats** | CSV, JSON, Parquet, ORC | + Avro support |
| **Configuration** | None | Comprehensive config system |
| **Entities** | Not available | Declarative persistence framework |

## Migration Strategies

### Strategy 1: Keep Phase 1 (No Changes Needed)

Phase 1 remains fully functional. No migration is required.

```python
# Your existing code continues to work
import parquetframe as pf

df = pf.read("data.csv")
result = df.groupby("category").sum()
result.save("output.parquet")
```

### Strategy 2: Gradual Migration (Recommended)

Use Phase 2 for new code while keeping Phase 1 for existing code.

```python
# Existing code
import parquetframe as pf
old_df = pf.read("old_data.csv")

# New code
import parquetframe.core as pf2
new_df = pf2.read("new_data.csv")
```

### Strategy 3: Full Migration

Migrate all code to Phase 2 for maximum benefits.

## Step-by-Step Migration

### 1. Update Imports

**Phase 1:**
```python
import parquetframe as pf
```

**Phase 2:**
```python
import parquetframe.core as pf2
# or
from parquetframe.core import read, read_csv, read_parquet
```

### 2. Reading Data

**Phase 1:**
```python
import parquetframe as pf

# Auto-detect with threshold
df = pf.read("data.csv", threshold_mb=100)

# Force backend
df = pf.read("data.csv", islazy=True)  # Force Dask
```

**Phase 2:**
```python
import parquetframe.core as pf2

# Auto-detect with intelligent selection
df = pf2.read("data.csv")

# Force specific engine
df = pf2.read("data.csv", engine="polars")
```

### 3. Configuration

**Phase 1:**
```python
# Pass threshold to each read
df = pf.read("data.csv", threshold_mb=50)
```

**Phase 2:**
```python
from parquetframe import set_config

# Set once, applies everywhere
set_config(pandas_threshold_mb=50.0)

df = pf2.read("data.csv")  # Uses configured threshold
```

### 4. Working with DataFrames

**Phase 1:**
```python
df = pf.read("data.csv")

# Check backend
if df.islazy:
    print("Using Dask")
else:
    print("Using pandas")

# Access underlying DataFrame
native = df.df
```

**Phase 2:**
```python
df = pf2.read("data.csv")

# Check engine
print(f"Using {df.engine_name}")  # "pandas", "polars", or "dask"

# Access underlying DataFrame
native = df.native
```

### 5. Engine Conversion

**Phase 1:**
```python
# Limited conversion support
# Would require manual conversion
```

**Phase 2:**
```python
df = pf2.read("data.csv")

# Convert between engines easily
pandas_df = df.to_pandas()
polars_df = df.to_polars()
dask_df = df.to_dask()
```

## Feature Adoption

### Adopt Polars Engine

Polars offers better performance for medium-sized datasets.

**Before:**
```python
import parquetframe as pf

df = pf.read("medium_data.csv")  # Uses pandas or Dask
```

**After:**
```python
import parquetframe.core as pf2

df = pf2.read("medium_data.csv")  # Auto-selects Polars for medium files
# Or force it:
df = pf2.read("medium_data.csv", engine="polars")
```

### Adopt Entity Framework

Replace manual DataFrame persistence with declarative entities.

**Before:**
```python
import pandas as pd

# Manual persistence
users_df = pd.read_parquet("users.parquet")

# Add new user
new_user = pd.DataFrame([{"user_id": 1, "name": "Alice"}])
users_df = pd.concat([users_df, new_user])
users_df.to_parquet("users.parquet")

# Query
alice = users_df[users_df["name"] == "Alice"]
```

**After:**
```python
from dataclasses import dataclass
from parquetframe.entity import entity

@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str

# Add new user
User(1, "Alice").save()

# Query
alice = User.find_by(name="Alice")
```

### Adopt Configuration System

Replace per-call parameters with global configuration.

**Before:**
```python
import parquetframe as pf

# Repeat parameters everywhere
df1 = pf.read("file1.csv", threshold_mb=50)
df2 = pf.read("file2.csv", threshold_mb=50)
df3 = pf.read("file3.csv", threshold_mb=50)
```

**After:**
```python
from parquetframe import set_config
import parquetframe.core as pf2

# Set once
set_config(pandas_threshold_mb=50.0)

# Apply everywhere
df1 = pf2.read("file1.csv")
df2 = pf2.read("file2.csv")
df3 = pf2.read("file3.csv")
```

### Adopt Avro Format

Use Avro for better schema evolution and compression.

**New in Phase 2:**
```python
import parquetframe.core as pf2

# Read Avro
df = pf2.read_avro("data.avro")

# Write Avro
df.to_avro("output.avro", codec="deflate")

# Entity with Avro
from dataclasses import dataclass
from parquetframe.entity import entity

@entity(storage_path="./data/users", primary_key="user_id", format="avro")
@dataclass
class User:
    user_id: int
    name: str
```

## Common Migration Patterns

### Pattern 1: Simple Read/Write

**Phase 1:**
```python
import parquetframe as pf

df = pf.read("input.csv")
df = df[df["age"] > 30]
df.save("output.parquet")
```

**Phase 2:**
```python
import parquetframe.core as pf2

df = pf2.read("input.csv")
filtered = df[df["age"] > 30]
filtered.native.to_parquet("output.parquet")
```

### Pattern 2: Large File Processing

**Phase 1:**
```python
import parquetframe as pf

# Force Dask for large file
df = pf.read("large.csv", islazy=True)
result = df.groupby("category").sum()
result = result.compute()  # Trigger computation
```

**Phase 2:**
```python
import parquetframe.core as pf2
from parquetframe import set_config

# Auto-select Dask for large files
set_config(polars_threshold_mb=100)  # Lower threshold
df = pf2.read("large.csv")  # May auto-select Dask

# Or force it
df = pf2.read("large.csv", engine="dask")
result = df.groupby("category").sum()
```

### Pattern 3: Multi-Format Pipeline

**Phase 1:**
```python
import parquetframe as pf

csv_df = pf.read("data.csv")
json_df = pf.read("data.json")

# Manual merge
import pandas as pd
merged = pd.merge(csv_df.df, json_df.df, on="id")
```

**Phase 2:**
```python
import parquetframe.core as pf2

csv_df = pf2.read_csv("data.csv")
json_df = pf2.read("data.json")  # Auto-detects JSON
avro_df = pf2.read_avro("data.avro")  # New format!

# Convert to common engine
csv_pd = csv_df.to_pandas()
json_pd = json_df.to_pandas()

# Merge
merged = csv_pd.native.merge(json_pd.native, on="id")
```

## Breaking Changes

Phase 2 has **no breaking changes** for Phase 1 code. However, if you migrate to Phase 2 API:

### Minor API Differences

1. **Property names:**
   - Phase 1: `df.islazy`, `df.df`
   - Phase 2: `df.engine_name`, `df.native`

2. **Parameter names:**
   - Phase 1: `islazy=True/False`
   - Phase 2: `engine="pandas"/"polars"/"dask"`

3. **Return types:**
   - Phase 1: Returns `ParquetFrame`
   - Phase 2: Returns `DataFrameProxy`

Both have similar interfaces, so most code works identically.

## Performance Comparison

| Operation | Phase 1 | Phase 2 |
|-----------|---------|---------|
| **Small files (<100MB)** | pandas | pandas (same) |
| **Medium files (100MB-10GB)** | pandas/Dask | **Polars** (faster) |
| **Large files (>10GB)** | Dask | Dask (same) |
| **Format support** | 4 formats | **5 formats** (+Avro) |
| **Engine switching** | Limited | **Seamless** |

## Troubleshooting

### Issue: Import Error

```python
# Error
import parquetframe.core as pf2
# ImportError: No module named 'polars'
```

**Solution:** Install optional dependencies:
```bash
pip install polars  # For Polars engine
pip install dask[complete]  # For Dask engine
```

### Issue: Different Behavior

```python
# Phase 1
df = pf.read("data.csv")  # Always pandas for small files

# Phase 2
df = pf2.read("data.csv")  # May use polars
```

**Solution:** Force pandas if needed:
```python
df = pf2.read("data.csv", engine="pandas")
# Or configure globally
set_config(default_engine="pandas")
```

### Issue: Missing Attributes

```python
# Phase 1
if df.islazy:
    ...

# Phase 2 - AttributeError
if df.islazy:  # No such attribute
    ...
```

**Solution:** Use Phase 2 API:
```python
if df.engine_name == "dask":
    ...
```

## Recommendations

1. **For New Projects:** Start with Phase 2 directly
2. **For Existing Projects:** Migrate gradually, starting with new features
3. **For Production:** Test Phase 2 in development first
4. **For Performance:** Use Polars engine for medium-sized data
5. **For Entities:** Adopt entity framework for structured data models

## Next Steps

- Read the [User Guide](USER_GUIDE.md) for Phase 2 features
- See [API Reference](API_REFERENCE.md) for complete documentation
- Check [Examples](../examples/) for migration examples
- Run your tests to verify compatibility

## Support

- Phase 1 will remain supported indefinitely
- Both phases can coexist in the same project
- No forced migration timeline
- Community support available for migration questions
