# Resampling Operations

Convert time-series data between different frequencies with aggregation.

## Overview

Resampling changes the frequency of time-series data, either **upsampling** (increasing frequency) or **downsampling** (decreasing frequency).

## Basic Usage

```python
from parquetframe.time import resample
import pandas as pd

# Create second-level data
df = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01", periods=3600, freq="1s"),
    "value": range(3600)
})

# Downsample to 1-minute intervals
minutely = resample(df, "timestamp", "1min", agg="mean")
print(len(minutely))  # 60 rows

# Downsample to hourly
hourly = resample(df, "timestamp", "1h", agg="sum") 
print(len(hourly))  # 1 row
```

## Aggregation Methods

### Mean (Average)

```python
# Average values in each bin
avg = resample(df, "timestamp", "5min", agg="mean")
```

Best for: Temperature, prices, continuous metrics

### Sum

```python
# Sum values in each bin
total = resample(df, "timestamp", "1h", agg="sum")
```

Best for: Counts, volumes, cumulative metrics

### First / Last

```python
# First value in each bin
opening = resample(df, "timestamp", "1d", agg="first")

# Last value in each bin  
closing = resample(df, "timestamp", "1d", agg="last")
```

Best for: OHLC data, snapshots

### Min / Max

```python
# Minimum value in each bin
lows = resample(df, "timestamp", "1h", agg="min")

# Maximum value in each bin
highs = resample(df, "timestamp", "1h", agg="max")
```

Best for: Range analysis, extrema detection

### Count

```python
# Count of values in each bin
frequency = resample(df, "timestamp", "1h", agg="count")
```

Best for: Activity tracking, event counting

## Using TimeSeriesDataFrame

```python
from parquetframe.time import TimeSeriesDataFrame

ts = TimeSeriesDataFrame(df, "timestamp")

# Method chaining
result = ts.resample("1h", agg="mean").resample("1d", agg="sum")
```

## Multiple Columns

Resampling works on all numeric columns:

```python
df = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01", periods=100, freq="1s"),
    "temperature": range(100),
    "humidity": range(100, 200),
    "pressure": range(200, 300)
})

# All numeric columns are resampled
hourly = resample(df, "timestamp", "1h", agg="mean")
# Output has temperature, humidity, pressure averaged
```

## Financial Example

```python
# Stock tick data → OHLC bars
ticks = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01 09:30", periods=1000, freq="100ms"),
    "price": [100 + i * 0.01 for i in range(1000)]
})

ts = TimeSeriesDataFrame(ticks, "timestamp")

# 1-minute OHLC bars
bars = pd.DataFrame({
    "open": resample(ticks, "timestamp", "1min", agg="first")["price"],
    "high": resample(ticks, "timestamp", "1min", agg="max")["price"],
    "low": resample(ticks, "timestamp", "1min", agg="min")["price"],
    "close": resample(ticks, "timestamp", "1min", agg="last")["price"],
})
```

## Performance Tips

1. **Pre-sort data** - Resampling is faster on sorted timestamps
2. **Choose appropriate frequencies** - Don't oversample unnecessarily
3. **Batch processing** - Resample multiple columns at once
4. **Use Rust backend** - Automatic when using `from parquetframe.time`

## See Also

- [Rolling Windows](rolling-windows.md) - Moving averages
- [As-of Joins](asof-joins.md) - Point-in-time joins
- [Time-Series Index](index.md) - Overview
