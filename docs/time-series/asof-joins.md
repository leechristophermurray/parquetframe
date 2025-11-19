# As-of Joins

Point-in-time correctness for combining time-series data.

## Overview

As-of joins match each row in the left dataset with the most relevant row from the right dataset based on timestamps, ensuring **point-in-time correctness**.

Critical for:
- Financial data (trades ← quotes)
- Event correlation
- Sensor data fusion
- Audit trails

## Basic Usage

```python
from parquetframe.time import asof_join
import pandas as pd

# Trades (sparse)
trades = pd.DataFrame({
    "trade_time": pd.to_datetime(["2024-01-01 09:30:01", "2024-01-01 09:30:05"]),
    "price": [100.0, 101.0]
})

# Quotes (dense)
quotes = pd.DataFrame({
    "quote_time": pd.to_datetime([
        "2024-01-01 09:30:00",
        "2024-01-01 09:30:03",
        "2024-01-01 09:30:06"
    ]),
    "bid": [99.0, 99.5, 100.0]
})

# Join trades with most recent quote
result = asof_join(
    trades, quotes,
    "trade_time", "quote_time", "bid",
    strategy="backward"
)
# trade@09:30:01 gets quote@09:30:00 (bid=99.0)
# trade@09:30:05 gets quote@09:30:03 (bid=99.5)
```

## Join Strategies

### Backward (Default)

Use the **most recent** value before or at the timestamp.

```python
result = asof_join(..., strategy="backward")
```

**Use case:** "What was the last known quote when this trade occurred?"

### Forward

Use the **next** value after or at the timestamp.

```python
result = asof_join(..., strategy="forward")
```

**Use case:** "What quote came after this event?"

### Nearest

Use the **closest** value (before or after).

```python
result = asof_join(..., strategy="nearest")
```

**Use case:** "What quote was nearest in time to this trade?"

## Tolerance

Limit maximum time difference:

```python
# Maximum 1 second tolerance
result = asof_join(
    trades, quotes,
    "trade_time", "quote_time", "bid",
    strategy="backward",
    tolerance_ns=1_000_000_000  # 1 second in nanoseconds
)
# Returns NaN if no quote within 1 second
```

## Using TimeSeriesDataFrame

```python
from parquetframe.time import TimeSeriesDataFrame

trades_ts = TimeSeriesDataFrame(trades, "trade_time")
quotes_ts = TimeSeriesDataFrame(quotes, "quote_time")

# Method chaining
result = trades_ts.asof_join(quotes_ts, "bid", strategy="backward")
```

## Financial Example: Trade Execution Quality

```python
# Analyze trade execution against prevailing quotes
trades = pd.DataFrame({
    "trade_time": pd.date_range("2024-01-01 09:30", periods=100, freq="1s"),
    "trade_price": [100 + i * 0.01 for i in range(100)],
    "trade_size": [100] * 100
})

quotes = pd.DataFrame({
    "quote_time": pd.date_range("2024-01-01 09:30", periods=1000, freq="100ms"),
    "bid": [99.9 + i * 0.001 for i in range(1000)],
    "ask": [100.1 + i * 0.001 for i in range(1000)]
})

# Join trades with prevailing quotes
with_quotes = asof_join(
    trades, quotes,
    "trade_time", "quote_time", "bid",
    strategy="backward"
)

# Calculate slippage
with_quotes["slippage"] = with_quotes["trade_price"] - with_quotes["bid"]
print(f"Average slippage: {with_quotes['slippage'].mean():.4f}")
```

## Sensor Data Fusion

```python
# Temperature readings (every 5 minutes)
temp = pd.DataFrame({
    "temp_time": pd.date_range("2024-01-01", periods=288, freq="5min"),
    "temperature": [20 + i * 0.01 for i in range(288)]
})

# Humidity readings (every 10 minutes)
humidity = pd.DataFrame({
    "humid_time": pd.date_range("2024-01-01", periods=144, freq="10min"),
    "humidity": [50 + i * 0.1 for i in range(144)]
})

# Join temperature with nearest humidity reading
combined = asof_join(
    temp, humidity,
    "temp_time", "humid_time", "humidity",
    strategy="nearest",
    tolerance_ns=10 * 60 * 1_000_000_000  # 10 minutes
)
```

## Performance

As-of joins use binary search for O(log n) lookups:

```python
# 10,000 trades vs 100,000 quotes
trades_large = pd.DataFrame({
    "trade_time": pd.date_range("2024-01-01", periods=10_000, freq="1s"),
    "price": range(10_000)
})

quotes_large = pd.DataFrame({
    "quote_time": pd.date_range("2024-01-01", periods=100_000, freq="100ms"),
    "bid": range(100_000)
})

# Fast join (~200ms with Rust)
result = asof_join(
    trades_large, quotes_large,
    "trade_time", "quote_time", "bid"
)
```

## Requirements

1. **Right dataset must be sorted** by time column
2. **Timestamps as datetime64** (automatic conversion)
3. **Value column must be numeric** (for NaN support)

## Tips

1. **Sort right dataset** - Critical for performance
2. **Use tolerance** - Prevent unrealistic matches
3. **Choose strategy carefully** - Backward for most financial use cases
4. **Batch operations** - Join multiple columns in sequence

## See Also

- [Resampling](resampling.md) - Frequency conversion
- [Rolling Windows](rolling-windows.md) - Moving averages
- [Time-Series Index](index.md) - Overview
