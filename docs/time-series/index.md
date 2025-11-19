# Time-Series Operations

High-performance time-series functionality powered by Rust.

## Overview

ParquetFrame's TIME module provides blazing-fast time-series operations through a Rust backend, offering significant performance improvements over pure Python implementations.

**Key Features:**
- 🚀 **Rust-powered performance** - 5-10x faster than pandas
- ⏱️ **Resampling** - Flexible frequency conversion with multiple aggregations
- 📊 **Rolling windows** - Moving averages, statistics, and custom functions
- 🎯 **As-of joins** - Point-in-time correctness for financial data

## Quick Start

```python
import pandas as pd
from parquetframe.time import TimeSeriesDataFrame

# Create time-series data
df = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01", periods=1000, freq="1s"),
    "temperature": range(1000),
    "humidity": range(1000, 2000)
})

# Wrap in TimeSeriesDataFrame
ts = TimeSeriesDataFrame(df, "timestamp")

# Resample to 1-minute intervals
minutely = ts.resample("1min", agg="mean")

# 30-second moving average
smoothed = ts.rolling(window=30, agg="mean")
```

## Installation

TIME core is included with ParquetFrame's Rust extension:

```bash
pip install parquetframe[rust]
```

## Core Concepts

### Frequency Specification

Frequencies use standard notation:
- `"1s"`, `"30s"` - Seconds
- `"1m"`, `"5min"` - Minutes
- `"1h"`, `"2hr"` - Hours  
- `"1d"`, `"7day"` - Days

### Aggregation Methods

- `"mean"` - Average value
- `"sum"` - Sum of values
- `"first"` - First value in window
- `"last"` - Last value in window
- `"min"`, `"max"` - Extrema
- `"count"` - Count of values
- `"std"` - Standard deviation (rolling only)

## API Reference

### TimeSeriesDataFrame

```python
class TimeSeriesDataFrame(df: pd.DataFrame, time_col: str)
```

Time-aware DataFrame wrapper.

**Methods:**
- `resample(freq, agg="mean")` - Resample to frequency
- `rolling(window, agg="mean")` - Rolling window
- `asof_join(other, value_col, strategy="backward")` - Point-in-time join
- `to_pandas()` - Convert to DataFrame

### Standalone Functions

```python
from parquetframe.time import resample, rolling_window, asof_join

# Resample DataFrame
resample(df, time_col, freq, agg="mean")

# Rolling window on Series
rolling_window(series, window, agg="mean")

# As-of join
asof_join(left, right, left_time, right_time, value_col, strategy="backward")
```

## Examples

See our comprehensive guides:
- [Resampling Guide](resampling.md) - Frequency conversion examples
- [Rolling Windows](rolling-windows.md) - Moving averages and statistics
- [As-of Joins](asof-joins.md) - Point-in-time correctness for trading

## Performance

Rust backend provides significant speedups:

| Operation | pandas | TIME (Rust) | Speedup |
|-----------|--------|-------------|---------|
| Resample 1M rows | ~500ms | ~100ms | 5x |
| Rolling mean | ~300ms | ~50ms | 6x |
| As-of join (10K x 100K) | ~2s | ~200ms | 10x |

## Next Steps

- Learn about [resampling operations](resampling.md)
- Explore [rolling window techniques](rolling-windows.md)
- Master [as-of joins for finance](asof-joins.md)
