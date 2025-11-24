# ParquetFrame API Reference

Complete API reference for all ParquetFrame modules and accessors.

## Core Modules

### parquetframe.sql

SQL query engine for DataFrames.

```python
from parquetframe.sql import sql, SQLContext

# Quick queries
result = sql("SELECT * FROM users WHERE age > 25", users=users_df)

# Persistent context
ctx = SQLContext()
ctx.register("users", users_df)
ctx.register("orders", orders_df)
result = ctx.query("SELECT * FROM users JOIN orders ON users.id = orders.user_id")
```

**Functions**:
- `sql(query, **tables)` - Execute SQL query
- `SQLContext()` - Create persistent SQL context

[Full Documentation](../sql/index.md)

---

### parquetframe.time

Time series operations via `.ts` accessor.

```python
import parquetframe.time

# Resample
daily = df.ts.resample('1D', agg='mean')

# Rolling windows
smoothed = df.ts.rolling('7D', agg='mean')

# Interpolate
filled = df.ts.interpolate('linear')
```

**Methods**:
- `.ts.resample(rule, agg)` - Resample time series
- `.ts.rolling(window, agg)` - Rolling window aggregation
- `.ts.interpolate(method)` - Fill missing values
- `.ts.shift(periods)` - Lag/lead data
- `.ts.diff(periods)` - Calculate differences
- `.ts.pct_change(periods)` - Percentage change

[Full Documentation](../time/index.md)

---

### parquetframe.geo

GeoSpatial operations via `.geo` accessor.

```python
import parquetframe.geo

# Buffer
buffered = gdf.geo.buffer(1000)

# Spatial join
joined = cities.geo.sjoin(states, predicate='within')

# Transform CRS
web_mercator = gdf.geo.to_crs('EPSG:3857')
```

**Methods**:
- `.geo.buffer(distance)` - Create buffer
- `.geo.area()` - Calculate area
- `.geo.distance(other)` - Calculate distance
- `.geo.sjoin(other, how, predicate)` - Spatial join
- `.geo.to_crs(crs)` - Transform coordinates

[Full Documentation](../geo/index.md)

---

### parquetframe.finance

Financial indicators via `.fin` accessor.

```python
import parquetframe.finance

# Moving averages
sma = df.fin.sma('close', 20)
ema = df.fin.ema('close', 12)

# Momentum
rsi = df.fin.rsi('close', 14)
macd = df.fin.macd('close')

# Volatility
bb = df.fin.bollinger_bands('close')
```

**Methods**:
- `.fin.sma(column, window)` - Simple Moving Average
- `.fin.ema(column, span)` - Exponential Moving Average
- `.fin.rsi(column, period)` - Relative Strength Index
- `.fin.macd(column, fast, slow, signal)` - MACD
- `.fin.bollinger_bands(column, window, num_std)` - Bollinger Bands
- `.fin.returns(column, periods)` - Calculate returns
- `.fin.volatility(column, window)` - Rolling volatility

[Full Documentation](../finance/index.md)

---

### parquetframe.knowlogy

Knowledge graph with computable formulas.

```python
from parquetframe import knowlogy

# Search concepts
concepts = knowlogy.search("linear regression")

# Get formulas
formula = knowlogy.get_formula("variance")

# List libraries
libraries = knowlogy.list_libraries()
```

**Functions**:
- `search(query)` - Search knowledge graph
- `get_formula(concept)` - Retrieve formula
- `list_libraries()` - Available knowledge libraries

[Full Documentation](../knowlogy/index.md)

---

### parquetframe.ai

RAG pipeline with Knowlogy integration.

```python
from parquetframe.ai import SimpleRagPipeline, AIConfig

# Create RAG pipeline
config = AIConfig(models=["gpt-4"], default_generation_model="gpt-4")
pipeline = SimpleRagPipeline(config, entity_store, use_knowlogy=True)

# Query
result = pipeline.run_query("What is the formula for variance?", user_context="analyst")
```

**Classes**:
- `SimpleRagPipeline` - RAG query pipeline
- `AIConfig` - Configuration
- `KnowlogyRetriever` - Knowledge graph retriever

[Full Documentation](../rag/index.md)

---

### parquetframe.tetnus

DataFrame-native ML framework.

```python
from parquetframe.tetnus import Model, dataframe_to_tensor

# Create model
model = Model(input_size=10, hidden_sizes=[64, 32], output_size=1)

# Convert DataFrame to tensor
X_tensor = dataframe_to_tensor(X_df)

# Train
model.fit(X_tensor, y_tensor, epochs=100, lr=0.01)

# Predict
predictions = model.predict(X_test_tensor)
```

**Classes**:
- `Model` - Neural network model
- `dataframe_to_tensor()` - Convert DataFrame to tensor

---

## CLI

Interactive REPL for data exploration.

```python
from parquetframe.cli import start_repl

# Start interactive shell
start_repl()
```

**Features**:
- Syntax highlighting
- Tab completion (with IPython)
- Pre-loaded libraries (pf, pd, np)

[Full Documentation](../cli/index.md)

---

## Complete Example

```python
import pandas as pd
import parquetframe as pf
import parquetframe.sql
import parquetframe.time
import parquetframe.finance
import parquetframe.geo

# Load data
df = pd.read_csv("stock_prices.csv", parse_dates=['date'])
df = df.set_index('date')

# SQL query
filtered = pf.sql("SELECT * FROM df WHERE volume > 1000000", df=df)

# Time series resampling
daily = filtered.ts.resample('1D', agg='mean')

# Financial indicators
daily['SMA_20'] = daily.fin.sma('close', 20)
daily['RSI'] = daily.fin.rsi('close', 14)

# Load GeoDataFrame
import geopandas as gpd
cities = gpd.read_file("cities.geojson")

# Spatial operations
buffered = cities.geo.buffer(1000)
area = buffered.geo.area()
```

---

## Installation

```bash
# Core package
pip install parquetframe

# With extras
pip install parquetframe[sql,cli,geo]

# All features
pip install parquetframe[all]
```

---

## Module Index

- **Core**: SQL, Time Series
- **Domain**: GeoSpatial, Financial
- **AI/ML**: Knowlogy, Tetnus, RAG
- **Interactive**: CLI REPL
