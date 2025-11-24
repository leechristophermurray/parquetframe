# Financial Indicators

ParquetFrame provides a `.fin` accessor for financial and technical analysis operations.

## Quick Start

```python
import pandas as pd
import parquetframe.finance  # Register accessor

# Load stock data
df = pd.read_csv("stock_prices.csv", index_col='date', parse_dates=True)

# Calculate indicators
sma = df.fin.sma(column='close', window=20)
rsi = df.fin.rsi(column='close', period=14)
macd = df.fin.macd(column='close')
```

## Moving Averages

### Simple Moving Average (SMA)

```python
# 20-day SMA
sma_20 = df.fin.sma('close', window=20)

# 50-day SMA
sma_50 = df.fin.sma('close', window=50)

# Add to DataFrame
df['SMA_20'] = sma_20
df['SMA_50'] = sma_50
```

### Exponential Moving Average (EMA)

```python
# 12-period EMA
ema_12 = df.fin.ema('close', span=12)

# 26-period EMA
ema_26 = df.fin.ema('close', span=26)
```

## Momentum Indicators

### Relative Strength Index (RSI)

```python
# 14-period RSI
rsi = df.fin.rsi('close', period=14)

# Interpretation
# RSI > 70: Overbought
# RSI < 30: Oversold
# 30 < RSI < 70: Neutral
```

### MACD (Moving Average Convergence Divergence)

```python
# Calculate MACD
macd = df.fin.macd('close', fast=12, slow=26, signal=9)

# Returns DataFrame with:
# - macd: MACD line
# - signal: Signal line
# - histogram: MACD histogram

# Interpretation
# MACD > Signal: Bullish
# MACD < Signal: Bearish
```

## Volatility Indicators

### Bollinger Bands

```python
# Calculate Bollinger Bands
bb = df.fin.bollinger_bands('close', window=20, num_std=2)

# Returns DataFrame with:
# - upper: Upper band
# - middle: Middle band (SMA)
# - lower: Lower band

# Interpretation
# Price near upper: Potentially overbought
# Price near lower: Potentially oversold
```

### Average True Range (ATR)

```python
# Calculate ATR
atr = df.fin.atr(
    high='high',
    low='low',
    close='close',
    period=14
)

# Measures volatility
```

## Returns & Risk

### Returns

```python
# Daily returns
returns = df.fin.returns('close')

# 5-day returns
returns_5d = df.fin.returns('close', periods=5)

# Cumulative returns
cum_returns = df.fin.cumulative_returns('close')
```

### Volatility

```python
# 20-day rolling volatility
vol = df.fin.volatility('close', window=20)

# Annualized volatility
vol_annual = df.fin.volatility('close', window=20, annualize=True)
```

## Complete Example

```python
import pandas as pd
import numpy as np
import parquetframe.finance

# Generate sample data
np.random.seed(42)
dates = pd.date_range('2023-01-01', periods=252, freq='D')
prices = pd.DataFrame({
    'close': 100 * (1 + np.random.randn(252) * 0.02).cumprod()
}, index=dates)

# Technical indicators
prices['SMA_20'] = prices.fin.sma('close', 20)
prices['SMA_50'] = prices.fin.sma('close', 50)
prices['RSI'] = prices.fin.rsi('close', 14)

# MACD
macd = prices.fin.macd('close')
prices['MACD'] = macd['macd']
prices['Signal'] = macd['signal']

# Bollinger Bands
bb = prices.fin.bollinger_bands('close')
prices['BB_Upper'] = bb['upper']
prices['BB_Lower'] = bb['lower']

# Risk metrics
prices['Returns'] = prices.fin.returns('close')
prices['Volatility'] = prices.fin.volatility('close', 20)

print(prices.tail())

# Trading signals
current = prices.iloc[-1]

if current['close'] > current['SMA_50']:
    print("✅ Uptrend (Price > 50-SMA)")

if current['RSI'] > 70:
    print("⚠️  Overbought (RSI > 70)")
elif current['RSI'] < 30:
    print("⚠️  Oversold (RSI < 30)")

if current['MACD'] > current['Signal']:
    print("📈 Bullish MACD crossover")
```

## Examples

See [`examples/finance/technical_analysis.py`](../../examples/finance/technical_analysis.py) for complete examples including:
- Moving averages (SMA, EMA)
- Momentum indicators (RSI, MACD)
- Bollinger Bands
- Risk metrics
- Complete technical analysis

## API Reference

### .fin.sma()

```python
df.fin.sma(column: str, window: int = 20) -> Series
```

Simple Moving Average.

### .fin.ema()

```python
df.fin.ema(column: str, span: int = 20) -> Series
```

Exponential Moving Average.

### .fin.rsi()

```python
df.fin.rsi(column: str, period: int = 14) -> Series
```

Relative Strength Index (0-100).

### .fin.macd()

```python
df.fin.macd(column: str, fast=12, slow=26, signal=9) -> DataFrame
```

MACD with signal line and histogram.

### .fin.bollinger_bands()

```python
df.fin.bollinger_bands(column: str, window=20, num_std=2) -> DataFrame
```

Bollinger Bands (upper, middle, lower).

### .fin.returns()

```python
df.fin.returns(column: str, periods: int = 1) -> Series
```

Calculate percentage returns.

### .fin.volatility()

```python
df.fin.volatility(column: str, window=20, annualize=True) -> Series
```

Rolling volatility.
