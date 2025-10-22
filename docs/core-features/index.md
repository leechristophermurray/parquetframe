# Core Features

Essential DataFrame operations, filtering, grouping, and data manipulation powered by pandas and Dask with optional Rust acceleration.

## Overview

- **📊 DataFrame Operations** - Full pandas/Dask API compatibility
- **🔍 Advanced Filtering** - SQL-like query expressions
- **📈 Aggregations** - groupby, pivot, statistics
- **🔄 Joins & Merges** - Efficient data combining
- **⚡ Rust Fast-Paths** - 8x faster metadata operations

## Quick Start

```python
import parquetframe as pf

# Read data
df = pf.read_parquet("data.parquet")

# Filter
active = df[df['status'] == 'active']

# Group and aggregate
summary = df.groupby('category').agg({'value': ['sum', 'mean', 'count']})

# Join
result = pf.merge(df1, df2, on='id', how='left')
```

## Related Categories

- **[Analytics & Statistics](../analytics-statistics/index.md)**
- **[SQL Support](../sql-support/index.md)**
- **[Rust Acceleration](../rust-acceleration/index.md)**
