# Getting Started with ParquetFrame

Welcome to ParquetFrame! This tutorial will help you get started with data analysis, SQL queries, time series, and more.

## Installation

```bash
pip install parquetframe

# Or with extras
pip install parquetframe[sql,cli,geo]
```

## Quick Start

```python
import pandas as pd
import parquetframe as pf

# Load data
df = pd.read_csv("data.csv")

# SQL queries
result = pf.sql("SELECT * FROM df WHERE value > 100", df=df)

print(result.head())
```

## Tutorial 1: SQL Queries

```python
from parquetframe.sql import sql

# Create data
users = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35]
})

# Simple query
young_users = sql(
    "SELECT name, age FROM users WHERE age < 30",
    users=users
)

# Joins
orders = pd.DataFrame({
    'order_id': [101, 102],
    'user_id': [1, 3],
    'amount': [100, 200]
})

result = sql("""
    SELECT u.name, o.amount
    FROM users u
    JOIN orders o ON u.id = o.user_id
""", users=users, orders=orders)
```

## Tutorial 2: Time Series Analysis

```python
import parquetframe.time

# Create time series
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=365),
    'value': np.random.randn(365).cumsum() + 100
}).set_index('date')

# Resample to weekly
weekly = df.ts.resample('1W', agg='mean')

# Rolling average
smoothed = df.ts.rolling('7D', agg='mean')

# Fill missing values
filled = df.ts.interpolate('linear')
```

## Tutorial 3: Financial Indicators

```python
import parquetframe.finance

# Stock prices
prices = pd.read_csv("stock.csv", index_col='date', parse_dates=True)

# Technical indicators
prices['SMA_20'] = prices.fin.sma('close', 20)
prices['RSI'] = prices.fin.rsi('close', 14)

# MACD
macd = prices.fin.macd('close')
prices['MACD'] = macd['macd']
prices['Signal'] = macd['signal']

# Bollinger Bands
bb = prices.fin.bollinger_bands('close')
prices['BB_Upper'] = bb['upper']
prices['BB_Lower'] = bb['lower']
```

## Tutorial 4: GeoSpatial Operations

```python
import geopandas as gpd
import parquetframe.geo

# Load spatial data
cities = gpd.read_file("cities.geojson")

# Buffer
buffered = cities.geo.buffer(1000)  # 1km

# Spatial join
states = gpd.read_file("states.geojson")
cities_with_state = cities.geo.sjoin(states, predicate='within')

# Transform coordinates
web_mercator = cities.geo.to_crs('EPSG:3857')
```

## Tutorial 5: Complete Workflow

```python
import pandas as pd
import parquetframe as pf
import parquetframe.sql
import parquetframe.time
import parquetframe.finance

# 1. Load and clean data
df = pd.read_csv("stock_prices.csv", parse_dates=['date'])
df = df.set_index('date')

# 2. SQL filtering
df_filtered = pf.sql(
    "SELECT * FROM df WHERE volume > 1000000",
    df=df
)

# 3. Resample to daily
daily = df_filtered.ts.resample('1D', agg='mean')

# 4. Add technical indicators
daily['SMA_50'] = daily.fin.sma('close', 50)
daily['RSI'] = daily.fin.rsi('close', 14)

# 5. Calculate returns
daily['returns'] = daily.fin.returns('close')
daily['volatility'] = daily.fin.volatility('close', 20)

# 6. Analyze
print(f"Total return: {daily.fin.cumulative_returns('close').iloc[-1]:.2%}")
print(f"Current RSI: {daily['RSI'].iloc[-1]:.2f}")
```

## Next Steps

- [API Reference](../api_reference.md)
- [SQL Documentation](../sql/index.md)
- [Time Series Guide](../time/index.md)
- [Financial Indicators](../finance/index.md)
- [GeoSpatial Operations](../geo/index.md)
- [Interactive CLI](../cli/index.md)
