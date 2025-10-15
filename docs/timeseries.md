# Time-Series Analysis

ParquetFrame provides comprehensive time-series analysis capabilities through the `.ts` accessor. This guide covers datetime handling, resampling, rolling operations, and advanced time-series workflows.

## Getting Started

### Automatic Datetime Detection

ParquetFrame can automatically detect datetime columns in your data:

```python
import parquetframe as pf

# Load data with potential datetime columns
df = pf.read("sensor_data.csv")

# Detect all datetime columns
datetime_columns = df.ts.detect_datetime_columns()
print(f"Found datetime columns: {datetime_columns}")
```

The detection supports various formats:
- **ISO 8601**: `2023-01-01`, `2023-01-01T10:30:00`, `2023-01-01 10:30:00+00:00`
- **US Format**: `01/15/2023`, `1/15/2023 2:30 PM`
- **European Format**: `15/01/2023`, `15.01.2023 14:30`
- **Timestamp**: Unix timestamps (seconds or milliseconds)

### Manual Datetime Parsing

For specific datetime formats, use manual parsing:

```python
# Parse with specific format
df_parsed = df.ts.parse_datetime('date_string', format='%Y-%m-%d %H:%M:%S')

# Parse with automatic inference
df_inferred = df.ts.parse_datetime('timestamp_col', infer=True)

# Parse in-place to modify original DataFrame
df.ts.parse_datetime('date_col', inplace=True)
```

## Resampling Operations

Resampling changes the frequency of your time-series data, useful for aggregating high-frequency data or filling gaps in low-frequency data.

### Basic Resampling

```python
# Load time-series data
sales_data = pf.read("daily_sales.csv")

# Resample to weekly averages
weekly_avg = sales_data.ts.resample('1W').mean()

# Resample to monthly totals
monthly_total = sales_data.ts.resample('1M').sum()

# Resample to quarterly statistics
quarterly_stats = sales_data.ts.resample('1Q').agg(['mean', 'std', 'count'])
```

### Frequency Aliases

ParquetFrame supports pandas frequency aliases:

| Alias | Description | Example |
|-------|-------------|---------|
| `S` | Seconds | `30S` (30 seconds) |
| `T`, `min` | Minutes | `15T` (15 minutes) |
| `H` | Hours | `2H` (2 hours) |
| `D` | Days | `1D` (daily) |
| `W` | Weeks | `2W` (bi-weekly) |
| `M` | Month end | `1M` (monthly) |
| `MS` | Month start | `1MS` (month start) |
| `Q` | Quarter end | `1Q` (quarterly) |
| `Y` | Year end | `1Y` (yearly) |

### Advanced Resampling

```python
# Resample with custom aggregations
custom_agg = sales_data.ts.resample('1W').agg({
    'sales': ['sum', 'mean', 'std'],
    'profit': ['sum', 'mean'],
    'customers': 'nunique'  # Count unique customers per week
})

# Resample with multiple methods
multi_resample = (sales_data.ts.resample('1M')
                            .agg(['sum', 'mean', 'median', 'std', 'min', 'max']))
```

## Rolling Window Operations

Rolling operations calculate statistics over a moving window of your time-series data.

### Basic Rolling Operations

```python
# 7-day rolling average (smoothing)
rolling_avg = sales_data.ts.rolling(7).mean()

# 30-day rolling standard deviation (volatility)
rolling_vol = sales_data.ts.rolling(30).std()

# 14-day rolling sum
rolling_sum = sales_data.ts.rolling(14).sum()

# Rolling minimum and maximum
rolling_range = sales_data.ts.rolling(21).agg(['min', 'max'])
```

### Time-Based Windows

Use time-based windows for irregular time series:

```python
# 7-day time window (regardless of data frequency)
time_rolling = sales_data.ts.rolling('7D').mean()

# 30-day rolling statistics
monthly_rolling = sales_data.ts.rolling('30D').agg(['mean', 'std'])

# Business day rolling (excludes weekends)
business_rolling = sales_data.ts.rolling('5B').mean()
```

### Advanced Rolling Operations

```python
# Custom rolling function
def rolling_sharpe(series, window=30, risk_free_rate=0.02):
    """Calculate rolling Sharpe ratio"""
    returns = series.pct_change()
    rolling_mean = returns.rolling(window).mean() * 252  # Annualized
    rolling_std = returns.rolling(window).std() * np.sqrt(252)  # Annualized
    return (rolling_mean - risk_free_rate) / rolling_std

# Apply custom rolling function
stock_data = pf.read("stock_prices.csv")
sharpe_ratios = stock_data.ts.rolling(30).apply(lambda x: rolling_sharpe(x))
```

## Time-Based Filtering

Filter your time-series data based on time of day, day of week, or specific time ranges.

### Time of Day Filtering

```python
# Filter business hours (9 AM to 5 PM)
business_hours = sales_data.ts.between_time('09:00', '17:00')

# Filter lunch hours
lunch_time = sales_data.ts.between_time('12:00', '14:00')

# Filter specific time points
opening_bell = stock_data.ts.at_time('09:30')  # Market open
closing_bell = stock_data.ts.at_time('16:00')  # Market close
```

### Advanced Time Filtering

```python
# Combine with other operations
weekend_patterns = (sales_data
                   .ts.between_time('10:00', '18:00')  # Business hours
                   .query("dayofweek >= 5")            # Weekends only
                   .ts.resample('1H')                  # Hourly aggregation
                   .mean())

# Morning vs evening comparison
morning_sales = sales_data.ts.between_time('06:00', '12:00')
evening_sales = sales_data.ts.between_time('18:00', '23:00')

morning_avg = morning_sales.groupby('day_of_week')['sales'].mean()
evening_avg = evening_sales.groupby('day_of_week')['sales'].mean()
```

## Lag and Lead Operations

Create lagged or leading versions of your time series for analysis and modeling.

### Basic Shift Operations

```python
# Create 1-period lag
lagged_sales = sales_data.ts.lag(1)

# Create 2-period lead (future values)
leading_sales = sales_data.ts.lead(2)

# Manual shift (positive = forward, negative = backward)
shifted_back = sales_data.ts.shift(-5)  # 5 periods back
shifted_forward = sales_data.ts.shift(3)  # 3 periods forward
```

### Multiple Lags for Modeling

```python
# Create multiple lags for time series modeling
def create_lags(df, column, max_lags=7):
    """Create multiple lag features for modeling"""
    result_df = df.copy()

    for lag in range(1, max_lags + 1):
        lag_col = f"{column}_lag_{lag}"
        result_df[lag_col] = df.ts.lag(lag).pandas_df[column]

    return result_df

# Create lagged features
modeling_data = create_lags(sales_data, 'sales', max_lags=7)

# Remove rows with NaN values (due to lagging)
clean_data = modeling_data.dropna()
```

### Lead-Lag Analysis

```python
# Compare current values with future and past values
analysis_df = sales_data.copy()

# Add lag and lead columns
analysis_df['sales_lag_1'] = sales_data.ts.lag(1).pandas_df['sales']
analysis_df['sales_lead_1'] = sales_data.ts.lead(1).pandas_df['sales']

# Calculate momentum indicators
analysis_df['momentum'] = (analysis_df['sales'] - analysis_df['sales_lag_1']) / analysis_df['sales_lag_1']
analysis_df['future_change'] = (analysis_df['sales_lead_1'] - analysis_df['sales']) / analysis_df['sales']

# Analyze relationships
correlation = analysis_df[['momentum', 'future_change']].corr()
print(f"Momentum-Future Change Correlation: {correlation.iloc[0, 1]:.3f}")
```

## Advanced Time-Series Workflows

### Seasonal Analysis

```python
# Decompose time series into trend, seasonal, and residual components
import numpy as np

def seasonal_decompose_simple(df, column, period=7):
    """Simple seasonal decomposition"""
    # Calculate moving average (trend)
    trend = df.ts.rolling(period).mean().pandas_df[column]

    # Remove trend to get seasonal + noise
    detrended = df.pandas_df[column] - trend

    # Calculate seasonal component
    seasonal_means = detrended.groupby(df.pandas_df.index.dayofweek).mean()
    seasonal = df.pandas_df.index.dayofweek.map(seasonal_means)

    # Calculate residuals
    residual = detrended - seasonal

    return {
        'original': df.pandas_df[column],
        'trend': trend,
        'seasonal': seasonal,
        'residual': residual
    }

# Apply seasonal decomposition
decomposition = seasonal_decompose_simple(sales_data, 'sales')
```

### Anomaly Detection in Time Series

```python
# Time-series anomaly detection using rolling statistics
def detect_time_series_anomalies(df, column, window=30, threshold=3):
    """Detect anomalies using rolling Z-score"""
    # Calculate rolling mean and std
    rolling_mean = df.ts.rolling(window).mean().pandas_df[column]
    rolling_std = df.ts.rolling(window).std().pandas_df[column]

    # Calculate Z-score
    z_scores = np.abs((df.pandas_df[column] - rolling_mean) / rolling_std)

    # Mark anomalies
    anomalies = z_scores > threshold

    return {
        'anomalies': anomalies,
        'z_scores': z_scores,
        'anomaly_values': df.pandas_df[column][anomalies]
    }

# Detect anomalies
anomaly_results = detect_time_series_anomalies(sales_data, 'sales')
print(f"Found {anomaly_results['anomalies'].sum()} anomalies")
```

### Multi-Series Analysis

```python
# Analyze multiple time series together
def correlation_analysis(df, date_col, value_cols, freq='1D'):
    """Analyze correlations between multiple time series"""
    # Ensure datetime index
    df_indexed = df.set_index(date_col)

    results = {}

    # Resample all series to same frequency
    for col in value_cols:
        resampled = df_indexed[col].resample(freq).mean()
        results[col] = resampled

    # Create correlation matrix
    combined_df = pd.DataFrame(results)
    correlation_matrix = combined_df.corr()

    return correlation_matrix, combined_df

# Example with multiple metrics
metrics = ['sales', 'profit', 'customers', 'advertising_spend']
corr_matrix, daily_data = correlation_analysis(
    sales_data.pandas_df, 'date', metrics, '1D'
)

print("Cross-correlation matrix:")
print(corr_matrix)
```

## Performance Optimization

### Dask Integration

For large time-series datasets, ParquetFrame automatically uses Dask:

```python
# Large time-series dataset
large_ts = pf.read("large_timeseries.parquet", islazy=True)

# Operations are automatically optimized for Dask
daily_avg = large_ts.ts.resample('1D').mean()  # Computed in parallel
rolling_stats = large_ts.ts.rolling(30).mean()  # Memory-efficient rolling

# Convert to pandas only when needed
final_result = rolling_stats.to_pandas()
```

### Memory-Efficient Operations

```python
# Chain operations to minimize memory usage
efficient_pipeline = (pf.read("huge_sensor_data.parquet")
                     .query("sensor_id == 'TEMP_01'")      # Filter early
                     .ts.resample('1H')                     # Reduce frequency
                     .mean()                                # Aggregate
                     .ts.rolling(24)                       # 24-hour rolling
                     .mean()                                # Smooth
                     .save("processed_temp_data.parquet"))  # Save result
```

## CLI Integration

All time-series operations are available through the command line:

```bash
# Detect datetime columns
pframe timeseries sensor_data.csv --detect-datetime

# Resample to hourly averages
pframe timeseries stock_prices.parquet --resample 1H --agg mean --output hourly_prices.parquet

# Apply 7-day rolling average
pframe timeseries sales_daily.csv --rolling 7 --agg mean --datetime-col date

# Filter business hours
pframe timeseries trading_data.json --between-time 09:30 16:00 --output business_hours.csv

# Create lagged version
pframe timeseries time_series.parquet --shift 1 --output lagged_series.parquet

# Combine operations with output
pframe timeseries raw_data.csv --resample 1D --agg mean --rolling 7 --output smoothed_daily.parquet
```

## Integration with Other Features

### SQL Integration

Combine time-series operations with SQL queries:

```python
# Time-series processing with SQL analysis
ts_processed = (sales_data
                .ts.resample('1W')
                .mean()
                .sql("""
                    SELECT
                        strftime('%Y-%m', date) as year_month,
                        AVG(sales) as avg_weekly_sales,
                        STDDEV(sales) as sales_volatility
                    FROM df
                    GROUP BY year_month
                    ORDER BY year_month
                """))
```

### Statistical Analysis Integration

```python
# Combine with statistical analysis
resampled_data = sales_data.ts.resample('1D').mean()

# Detect outliers in resampled data
outliers = resampled_data.stats.detect_outliers('sales', method='iqr')

# Analyze outlier patterns by day of week
outlier_analysis = outliers.sql("""
    SELECT
        strftime('%w', date) as day_of_week,
        COUNT(*) as total_days,
        SUM(CAST(sales_outlier_iqr as INTEGER)) as outlier_days,
        AVG(sales) as avg_sales
    FROM df
    GROUP BY day_of_week
    ORDER BY day_of_week
""")
```

This comprehensive time-series functionality makes ParquetFrame ideal for temporal data analysis, from simple resampling to complex multi-series analysis and anomaly detection.
