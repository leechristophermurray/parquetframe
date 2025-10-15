# Analytics Features

ParquetFrame provides powerful analytics capabilities through two specialized accessors: `.stats` for statistical analysis and `.ts` for time-series operations. These features work seamlessly with both pandas and Dask backends, automatically selecting the optimal approach based on your data size.

## Statistical Analysis (.stats)

The `.stats` accessor provides advanced statistical functionality beyond basic pandas operations, with intelligent dispatching between pandas and Dask backends.

### Extended Descriptive Statistics

Get comprehensive statistical summaries beyond the basic `.describe()` method:

```python
import parquetframe as pf

# Load your data
df = pf.read("sales_data.csv")

# Extended statistics for all numeric columns
extended_stats = df.stats.describe_extended()
print(extended_stats)
```

The extended statistics include:
- Count, mean, median, standard deviation
- Skewness and kurtosis for distribution shape analysis
- Multiple percentiles (10th, 25th, 50th, 75th, 90th)
- Min/max values and range

### Distribution Analysis

Perform comprehensive distribution analysis on your data:

```python
# Analyze distribution of a single column
sales_dist = df.stats.distribution_summary('sales_amount')

# Key information included:
print(f"Distribution shape: {sales_dist['distribution_shape']}")
print(f"Outliers (IQR): {sales_dist['outliers_iqr_count']} ({sales_dist['outliers_iqr_percent']:.2f}%)")
print(f"Skewness: {sales_dist['skewness']:.3f}")
print(f"Kurtosis: {sales_dist['kurtosis']:.3f}")

# Analyze all numeric columns
all_distributions = df.stats.distribution_summary()
for col, dist in all_distributions.items():
    print(f"{col}: {dist['distribution_shape']}")
```

Distribution analysis provides:
- Basic statistics (count, mean, median, std, variance)
- Shape assessment (skewness, kurtosis, distribution type)
- Percentile analysis (1st, 5th, 10th, ..., 99th percentiles)
- Outlier counts and percentages using both IQR and Z-score methods
- Data quality metrics (null counts, unique values)

### Correlation Analysis

Generate correlation matrices with multiple methods:

```python
# Pearson correlation (linear relationships)
pearson_corr = df.stats.corr_matrix(method='pearson')

# Spearman correlation (monotonic relationships)
spearman_corr = df.stats.corr_matrix(method='spearman')

# Kendall correlation (robust to outliers)
kendall_corr = df.stats.corr_matrix(method='kendall')

print("Strong correlations (|r| > 0.7):")
for col1 in pearson_corr.columns:
    for col2 in pearson_corr.columns:
        if col1 != col2 and abs(pearson_corr.loc[col1, col2]) > 0.7:
            print(f"{col1} <-> {col2}: r = {pearson_corr.loc[col1, col2]:.3f}")
```

### Outlier Detection

Detect outliers using statistical methods:

```python
# IQR method (Interquartile Range)
outliers_iqr = df.stats.detect_outliers('sales_amount', method='iqr', multiplier=1.5)
print(f"IQR outliers detected: {outliers_iqr.pandas_df['sales_amount_outlier_iqr'].sum()}")

# Z-score method
outliers_zscore = df.stats.detect_outliers('price', method='zscore', threshold=3.0)
print(f"Z-score outliers detected: {outliers_zscore.pandas_df['price_outlier_zscore'].sum()}")

# Detect outliers in all numeric columns
all_outliers = df.stats.detect_outliers(method='iqr')

# Filter out outliers for further analysis
clean_data = all_outliers.sql("SELECT * FROM df WHERE sales_amount_outlier_iqr = false")
```

### Statistical Testing

Perform statistical hypothesis tests:

```python
# Test normality of a distribution
normality = df.stats.normality_test('revenue')
print(f"Shapiro-Wilk test: p-value = {normality.get('shapiro_wilk', {}).get('p_value', 'N/A')}")
print(f"Data appears normal: {normality.get('shapiro_wilk', {}).get('is_normal', False)}")

# Test correlation significance
corr_test = df.stats.correlation_test('advertising_spend', 'sales')
if 'pearson' in corr_test:
    pearson = corr_test['pearson']
    print(f"Correlation: r = {pearson['correlation']:.3f}")
    print(f"Significance: p = {pearson['p_value']:.3f} ({'significant' if pearson['significant'] else 'not significant'})")
```

### Regression Analysis

Perform linear regression with comprehensive metrics:

```python
# Simple linear regression
regression = df.stats.linear_regression('advertising_spend', 'sales')

print(f"Equation: {regression['equation']}")
print(f"R-squared: {regression['r_squared']:.3f}")
print(f"P-value: {regression['p_value']:.3f}")
print(f"RMSE: {regression['rmse']:.2f}")

# Get formatted regression summary
summary = df.stats.regression_summary('advertising_spend', 'sales')
print(summary)
```

## Time-Series Analysis (.ts)

The `.ts` accessor provides specialized time-series functionality with automatic datetime detection and intelligent backend selection.

### Datetime Detection

Automatically detect datetime columns in your data:

```python
import parquetframe as pf

# Load data with potential datetime columns
df = pf.read("timeseries_data.csv")

# Detect datetime columns
datetime_cols = df.ts.detect_datetime_columns()
print(f"Detected datetime columns: {datetime_cols}")

# Parse a specific column as datetime
df_parsed = df.ts.parse_datetime('timestamp_string', format='%Y-%m-%d %H:%M:%S')
```

The datetime detection supports multiple formats:
- ISO format: `2023-01-01`, `2023-01-01 10:30:00`
- US format: `01/15/2023`, `01/15/2023 14:30:00`
- European format: `15/01/2023`, `15/01/2023 14:30:00`
- Custom formats via the `format` parameter

### Resampling Operations

Resample time-series data to different frequencies:

```python
# Assuming 'timestamp' column exists
df = pf.read("hourly_sales.csv")

# Resample to daily averages
daily_avg = df.ts.resample('1D').mean()

# Resample to weekly sums
weekly_sum = df.ts.resample('1W').sum()

# Monthly maximum values
monthly_max = df.ts.resample('1M').max()

# Custom aggregations
monthly_stats = df.ts.resample('1M').agg({
    'sales': ['mean', 'std', 'count'],
    'profit': ['sum', 'mean']
})
```

Supported resampling frequencies:
- `1H`, `2H`, `6H` - Hourly intervals
- `1D`, `2D`, `7D` - Daily intervals
- `1W`, `2W` - Weekly intervals
- `1M`, `3M`, `6M` - Monthly intervals
- `1Y` - Yearly intervals

### Rolling Window Operations

Calculate rolling statistics with various window sizes:

```python
# 7-day rolling average
rolling_avg = df.ts.rolling(7).mean()

# 30-day rolling standard deviation
rolling_std = df.ts.rolling(30).std()

# Rolling sum with time-based window
rolling_sum_time = df.ts.rolling('7D').sum()

# Multiple rolling statistics
rolling_stats = df.ts.rolling(14).agg(['mean', 'std', 'min', 'max'])
```

### Time-Based Filtering

Filter data based on time of day or time ranges:

```python
# Filter business hours (9 AM to 5 PM)
business_hours = df.ts.between_time('09:00', '17:00')

# Filter specific time points
market_open = df.ts.at_time('09:30')  # Market opening time
market_close = df.ts.at_time('16:00')  # Market closing time

# Combine with other operations
lunch_break_avg = (df.ts.between_time('12:00', '13:00')
                     .groupby('day_of_week')
                     .mean())
```

### Lag and Lead Operations

Create lagged or leading versions of your time series:

```python
# Create 1-period lag
lagged_sales = df.ts.lag(1)

# Create 2-period lead
leading_sales = df.ts.lead(2)

# Manual shift (positive = forward, negative = backward)
shifted_data = df.ts.shift(-5)  # 5 periods backward

# Create multiple lags for analysis
lags_df = df.copy()
for i in range(1, 8):  # Create 7 lags
    lags_df[f'sales_lag_{i}'] = df.ts.lag(i).pandas_df['sales']
```

## CLI Integration

Both statistical and time-series analysis are available through the command line interface:

### Statistical Analysis CLI

```bash
# Analyze a specific column
pframe analyze data.csv --column sales_amount

# Perform correlation test
pframe analyze data.parquet --correlation-test price demand

# Detect outliers using Z-score
pframe analyze data.json --outlier-method zscore --zscore-threshold 2.5

# Test normality and save results
pframe analyze data.csv --normality-test revenue --output analysis.json

# Linear regression analysis
pframe analyze data.parquet --linear-regression advertising sales
```

### Time-Series Analysis CLI

```bash
# Detect datetime columns
pframe timeseries data.csv --detect-datetime

# Resample to hourly averages
pframe timeseries data.parquet --resample 1H --agg mean

# Apply rolling window
pframe timeseries data.csv --rolling 7 --agg mean --datetime-col timestamp

# Filter by time range
pframe timeseries data.json --between-time 09:00 17:00 --output filtered.csv

# Shift time series
pframe timeseries data.parquet --shift 1 --output lagged.parquet
```

## Performance Considerations

The analytics features are optimized for performance across different data sizes:

### Backend Selection

- **Small datasets (< 100MB)**: Uses pandas for optimal performance
- **Large datasets (>= 100MB)**: Automatically switches to Dask for memory efficiency
- **Manual control**: Override with `islazy=True/False` parameter

### Memory Optimization

```python
# For large datasets, operations are computed efficiently
large_df = pf.read("large_dataset.parquet", islazy=True)

# Statistical operations automatically handle Dask computation
stats = large_df.stats.describe_extended()  # Computed efficiently

# Time-series operations preserve backend choice
resampled = large_df.ts.resample('1D').mean()  # Stays in Dask
```

### Best Practices

1. **Use appropriate backends**: Let ParquetFrame choose automatically or override when needed
2. **Chain operations**: Combine multiple operations before computing final results
3. **Filter early**: Apply filters before expensive statistical computations
4. **Cache results**: Store intermediate results for repeated analysis

```python
# Efficient workflow example
result = (pf.read("large_data.parquet")
           .query("status == 'active'")  # Filter early
           .ts.resample('1D')            # Time-series operation
           .mean()                       # Aggregation
           .stats.detect_outliers('value')  # Statistical analysis
           .save("processed_data.parquet"))  # Save result
```

## Integration with Other Features

Analytics features integrate seamlessly with ParquetFrame's other capabilities:

### SQL Integration

```python
# Combine analytics with SQL
outliers_detected = df.stats.detect_outliers('sales', method='iqr')

# Use SQL to analyze outlier patterns
outlier_analysis = outliers_detected.sql("""
    SELECT
        region,
        COUNT(*) as total_records,
        SUM(CAST(sales_outlier_iqr AS INTEGER)) as outlier_count,
        AVG(sales) as avg_sales
    FROM df
    GROUP BY region
    ORDER BY outlier_count DESC
""")
```

### AI-Powered Queries

```python
from parquetframe.ai import LLMAgent

agent = LLMAgent()

# Natural language analytics queries
result = await agent.generate_query(
    "Find customers with sales patterns that are statistical outliers",
    df.stats.detect_outliers('sales_amount')
)
```

This comprehensive analytics functionality makes ParquetFrame a powerful tool for data analysis, combining the ease of use of pandas with the scalability of Dask and the convenience of a unified interface.
