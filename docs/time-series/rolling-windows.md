# Rolling Windows

Apply functions over sliding windows for smoothing and trend analysis.

## Overview

Rolling windows compute aggregations over a sliding window of data points, useful for:
- Moving averages (trend analysis)
- Signal smoothing
- Volatility measurement
- Outlier detection

## Basic Usage

```python
from parquetframe.time import rolling_window
import pandas as pd

# Create time-series
series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

# 3-period moving average
ma3 = rolling_window(series, window=3, agg="mean")
# Result: [1.0, 1.5, 2.0, 3.0, 4.0, ...]
```

## Window Functions

### Mean (Moving Average)

```python
# Simple moving average
sma = rolling_window(prices, window=20, agg="mean")
```

**Use cases:** Trend identification, noise reduction

### Standard Deviation

```python
# Rolling volatility
volatility = rolling_window(returns, window=30, agg="std")
```

**Use cases:** Risk measurement, volatility tracking

### Min / Max

```python
# Rolling support/resistance
support = rolling_window(prices, window=50, agg="min")
resistance = rolling_window(prices, window=50, agg="max")
```

**Use cases:** Technical analysis, range detection

## Using TimeSeriesDataFrame

```python
from parquetframe.time import TimeSeriesDataFrame

df = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01", periods=100, freq="1d"),
    "price": range(100),
    "volume": range(100, 200)
})

ts = TimeSeriesDataFrame(df, "timestamp")

# Apply rolling window to all columns
smoothed = ts.rolling(window=7, agg="mean")
```

## Financial Example: Moving Averages

```python
prices = pd.DataFrame({
    "timestamp": pd.date_range("2024-01-01", periods=200, freq="1d"),
    "close": [100 + i * 0.5 for i in range(200)]
})

ts = TimeSeriesDataFrame(prices, "timestamp")

# Fast MA (10-day)
fast_ma = rolling_window(prices["close"], window=10, agg="mean")

# Slow MA (50-day)
slow_ma = rolling_window(prices["close"], window=50, agg="mean")

# Crossover strategy
signals = fast_ma > slow_ma
```

## Volatility Measurement

```python
# Calculate returns
returns = prices["close"].pct_change()

# 30-day rolling volatility
volatility = rolling_window(returns, window=30, agg="std")

# Annualized volatility
annual_vol = volatility * (252 ** 0.5)
```

## Window Behavior

Rolling windows use an **expanding** approach at the beginning:

```python
series = pd.Series([1, 2, 3, 4, 5])
result = rolling_window(series, window=3, agg="mean")

# Window 1: [1] → mean = 1.0
# Window 2: [1, 2] → mean = 1.5
# Window 3: [1, 2, 3] → mean = 2.0
# Window 4: [2, 3, 4] → mean = 3.0 (full window)
# Window 5: [3, 4, 5] → mean = 4.0 (full window)
```

## Performance Comparison

```python
import time
import numpy as np

# Large dataset
data = pd.Series(np.random.randn(1_000_000))

# Pandas rolling
start = time.time()
pandas_result = data.rolling(window=100).mean()
pandas_time = time.time() - start

# TIME rolling (Rust)
start = time.time()
rust_result = rolling_window(data, window=100, agg="mean")
rust_time = time.time() - start

print(f"Pandas: {pandas_time:.3f}s")
print(f"Rust: {rust_time:.3f}s")
print(f"Speedup: {pandas_time / rust_time:.1f}x")
```

## Tips

1. **Choose window size carefully** - Too small = noise, too large = lag
2. **Use appropriate aggregations** - Mean for trends, std for volatility
3. **Combine windows** - Fast/slow MAs for signal generation
4. **Pre-allocate** - Rust backend handles memory efficiently

## See Also

- [Resampling](resampling.md) - Frequency conversion
- [As-of Joins](asof-joins.md) - Point-in-time joins
- [Time-Series Index](index.md) - Overview
