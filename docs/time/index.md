# Time Series Operations

ParquetFrame provides a `.ts` accessor for time series operations on time-indexed DataFrames.

## Quick Start

```python
import pandas as pd
import parquetframe.time  # Register .ts accessor

# Create time series
df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
    'value': range(100)
}).set_index('timestamp')

# Use .ts accessor
daily = df.ts.resample('1D', agg='mean')
smoothed = df.ts.rolling('7D', agg='mean')
```

## Resampling

Change time series frequency:

```python
# Hourly to daily
daily = df.ts.resample('1D', agg='mean')

# Multiple aggregations
stats = df.ts.resample('1D', agg=['mean', 'std', 'count'])

# Custom frequency
weekly = df.ts.resample('1W', agg='sum')
```

### Frequency Strings

- `1H`: Hourly
- `1D`: Daily
- `1W`: Weekly
- `1M`: Monthly
- `5min`: Every 5 minutes

## Rolling Windows

Compute rolling statistics:

```python
# 7-day moving average
ma7 = df.ts.rolling('7D', agg='mean')

# 30-period rolling sum
total = df.ts.rolling(30, agg='sum')

# Rolling standard deviation
volatility = df.ts.rolling('7D', agg='std')
```

## Interpolation

Fill missing values:

```python
# Linear interpolation
filled = df.ts.interpolate('linear')

# Time-aware interpolation
filled = df.ts.interpolate('time')

# Polynomial interpolation
filled = df.ts.interpolate('polynomial', order=2)
```

## Transformations

### Shift

```python
# Lag by 1 period
lagged = df.ts.shift(1)

# Lead by 1 period
lead = df.ts.shift(-1)
```

### Differences

```python
# First difference
diff = df.ts.diff()

# Percentage change
returns = df.ts.pct_change()
```

## Complete Example

```python
import pandas as pd
import numpy as np
import parquetframe.time

# Create hourly sensor data
dates = pd.date_range('2024-01-01', periods=168, freq='h')
df = pd.DataFrame({
    'temperature': 20 + np.random.randn(168),
    'humidity': 60 + np.random.randn(168) * 5
}, index=dates)

# Resample to daily averages
daily = df.ts.resample('1D', agg='mean')

# Calculate 12-hour rolling average
smoothed = df.ts.rolling('12H', agg='mean')

# Calculate hourly change
hourly_change = df.ts.diff()

# Fill any missing values
filled = df.ts.interpolate('linear')

print(daily.head())
```

## Advanced Operations

### Multiple Windows

```python
df['MA7'] = df.ts.rolling('7D', agg='mean')
df['MA30'] = df.ts.rolling('30D', agg='mean')
df['volatility'] = df.ts.rolling('7D', agg='std')
```

### Seasonal Decomposition

```python
# Coming soon - will use pf-time-core Rust backend
# df.ts.seasonal_decompose(period=24)
```

## Examples

See [`examples/time/basic_operations.py`](../../examples/time/basic_operations.py) for complete examples including:
- Basic resampling
- Rolling windows
- Interpolation
- Transformations
- Real sensor data analysis

## Performance Notes

Current implementation uses pandas native operations. Future versions will leverage the Rust `pf-time-core` backend for:
- Faster resampling
- Parallel rolling windows
- High-performance as-of joins

## API Reference

### .ts.resample()

```python
df.ts.resample(rule: str, agg: str = 'mean') -> DataFrame
```

Resample time series to different frequency.

### .ts.rolling()

```python
df.ts.rolling(window: Union[str, int], agg: str = 'mean') -> DataFrame
```

Compute rolling window statistics.

### .ts.interpolate()

```python
df.ts.interpolate(method: str = 'linear') -> DataFrame
```

Interpolate missing values.

### .ts.shift()

```python
df.ts.shift(periods: int = 1) -> DataFrame
```

Shift time series by specified periods.

### .ts.diff()

```python
df.ts.diff(periods: int = 1) -> DataFrame
```

Calculate difference between consecutive periods.

### .ts.pct_change()

```python
df.ts.pct_change(periods: int = 1) -> DataFrame
```

Calculate percentage change.
