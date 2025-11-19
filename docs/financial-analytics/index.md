# Financial Analytics

High-performance financial technical indicators powered by Rust.

## Overview

ParquetFrame's FIN module provides blazing-fast financial analytics built on Rust-accelerated time-series operations.

**Key Features:**
- 🚀 **Rust-powered performance** - 10-50x faster than pure Python
- 📈 **Technical Indicators** - SMA, EMA, RSI, Bollinger Bands
- 💹 **Trading Signals** - Automated signal generation
- 🎯 **Production-Ready** - Battle-tested algorithms

## Quick Start

```python
import pandas as pd

# Load stock data
df = pd.read_parquet("stock_prices.parquet")

# Calculate technical indicators
df = df.fin.sma("close", window=20, output_column="sma_20")
df = df.fin.rsi("close", window=14)
df = df.fin.bollinger_bands("close", window=20, num_std=2.0)
```

## API Reference

### Simple Moving Average (SMA)

Calculate the mean of a rolling window.

```python
df.fin.sma(column, window, output_column=None)
```

**Parameters:**
- `column` (str): Column to calculate SMA on
- `window` (int): Number of periods for averaging
- `output_column` (str, optional): Output column name

**Returns:** DataFrame with SMA column added

### Exponential Moving Average (EMA)

Calculate exponentially-weighted moving average.

```python
df.fin.ema(column, span, output_column=None)
```

**Parameters:**
- `column` (str): Column to calculate EMA on
- `span` (int): Span (number of periods)
- `output_column` (str, optional): Output column name

**Returns:** DataFrame with EMA column added

### Relative Strength Index (RSI)

Momentum oscillator measuring speed and magnitude of price changes.

```python
df.fin.rsi(column, window=14, output_column=None)
```

**Parameters:**
- `column` (str): Column to calculate RSI on
- `window` (int): Lookback period (default: 14)
- `output_column` (str, optional): Output column name

**Returns:** DataFrame with RSI column (0-100)

### Bollinger Bands

Volatility bands placed above and below a moving average.

```python
df.fin.bollinger_bands(column, window=20, num_std=2.0, prefix=None)
```

**Parameters:**
- `column` (str): Column to calculate bands on
- `window` (int): Window size (default: 20)
- `num_std` (float): Number of standard deviations (default: 2.0)
- `prefix` (str, optional): Prefix for output columns

**Returns:** DataFrame with upper, middle, and lower band columns

## Examples

### Stock Analysis

```python
import pandas as pd

# Load data
df = pd.read_parquet("AAPL.parquet")

# Moving averages for trend
df = df.fin.sma("close", 20, "sma_20")
df = df.fin.sma("close", 50, "sma_50")

# RSI for momentum
df = df.fin.rsi("close", 14)

# Bollinger Bands for volatility
df = df.fin.bollinger_bands("close", 20, 2.0)

# Generate signals
df['signal'] = 'HOLD'
df.loc[df['sma_20'] > df['sma_50'], 'signal'] = 'BUY'
df.loc[df['sma_20'] < df['sma_50'], 'signal'] = 'SELL'
```

### Trading Strategy Backtesting

```python
# Calculate returns
df['returns'] = df['close'].pct_change()

# Generate signals based on RSI
df['position'] = 0
df.loc[df['rsi'] < 30, 'position'] = 1  # Oversold - buy
df.loc[df['rsi'] > 70, 'position'] = -1  # Overbought - sell

# Calculate strategy returns
df['strategy_returns'] = df['position'].shift(1) * df['returns']

# Performance metrics
total_return = (1 + df['strategy_returns']).prod() - 1
sharpe_ratio = df['strategy_returns'].mean() / df['strategy_returns'].std() * (252 ** 0.5)
```

## Performance

Rust backend provides significant speedups:

| Operation | pandas | FIN (Rust) | Speedup |
|-----------|--------|------------|---------|
| SMA (1M rows) | ~200ms | ~15ms | 13x |
| EMA (1M rows) | ~180ms | ~12ms | 15x |
| RSI (1M rows) | ~500ms | ~30ms | 17x |
| Bollinger Bands | ~400ms | ~25ms | 16x |

## Further Reading

- [Stock Analysis Example](../../examples/fin_stock_analysis.py)
- [TIME Module](../time-series/index.md) - Underlying time-series operations
- [Performance Guide](../performance.md) - Optimization tips
