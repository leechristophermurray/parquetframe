"""
Stock Market Analysis Example using FIN module.

Demonstrates technical indicators on stock price data.
"""

import numpy as np
import pandas as pd

# Generate sample stock data (simulating daily OHLCV data)
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=100, freq="D")

# Simulate stock price with random walk
returns = np.random.normal(0.001, 0.02, 100)
prices = 100 * np.exp(np.cumsum(returns))

stock_data = pd.DataFrame(
    {
        "date": dates,
        "open": prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
        "high": prices * (1 + np.random.uniform(0, 0.02, 100)),
        "low": prices * (1 + np.random.uniform(-0.02, 0, 100)),
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, 100),
    }
)

print("📈 Stock Market Analysis with ParquetFrame FIN\n")
print("=" * 70)

# Example 1: Simple Moving Averages
print("\n1️⃣  Calculating Moving Averages (SMA-20, SMA-50)...")
print("-" * 70)

stock_data = stock_data.fin.sma("close", window=20, output_column="sma_20")
stock_data = stock_data.fin.sma("close", window=50, output_column="sma_50")

print("✅ Added SMA-20 and SMA-50 columns")
print(stock_data[["date", "close", "sma_20", "sma_50"]].tail(10))

# Example 2: Exponential Moving Average
print("\n\n2️⃣  Calculating Exponential Moving Average (EMA-12)...")
print("-" * 70)

stock_data = stock_data.fin.ema("close", span=12, output_column="ema_12")

print("✅ Added EMA-12 column")
print(stock_data[["date", "close", "ema_12", "sma_20"]].tail(10))

# Example 3: Relative Strength Index
print("\n\n3️⃣  Calculating Relative Strength Index (RSI-14)...")
print("-" * 70)

stock_data = stock_data.fin.rsi("close", window=14, output_column="rsi")

print("✅ Added RSI column")
print(stock_data[["date", "close", "rsi"]].tail(10))

# Identify overbought/oversold conditions
overbought = stock_data[stock_data["rsi"] > 70]
oversold = stock_data[stock_data["rsi"] < 30]

print("\n📊 RSI Analysis:")
print(f"  Overbought periods (RSI > 70): {len(overbought)}")
print(f"  Oversold periods (RSI < 30): {len(oversold)}")

# Example 4: Bollinger Bands
print("\n\n4️⃣  Calculating Bollinger Bands (20-day, 2σ)...")
print("-" * 70)

stock_data = stock_data.fin.bollinger_bands(
    "close", window=20, num_std=2.0, prefix="bb"
)

print("✅ Added Bollinger Bands")
print(stock_data[["date", "close", "bb_upper", "bb_middle", "bb_lower"]].tail(10))

# Calculate Bollinger Band width (volatility indicator)
stock_data["bb_width"] = (stock_data["bb_upper"] - stock_data["bb_lower"]) / stock_data[
    "bb_middle"
]

print("\n📊 Bollinger Band Width (Volatility):")
print(f"  Mean width: {stock_data['bb_width'].mean():.4f}")
print(f"  Current width: {stock_data['bb_width'].iloc[-1]:.4f}")

# Example 5: Trading Signal Generation
print("\n\n5️⃣  Generating Trading Signals...")
print("-" * 70)

# Golden Cross / Death Cross signals (SMA crossover)
stock_data["signal"] = "HOLD"
stock_data.loc[stock_data["sma_20"] > stock_data["sma_50"], "signal"] = "BUY"
stock_data.loc[stock_data["sma_20"] < stock_data["sma_50"], "signal"] = "SELL"

# Add RSI filter
stock_data.loc[(stock_data["signal"] == "BUY") & (stock_data["rsi"] > 70), "signal"] = (
    "HOLD"
)
stock_data.loc[
    (stock_data["signal"] == "SELL") & (stock_data["rsi"] < 30), "signal"
] = "HOLD"

signal_counts = stock_data["signal"].value_counts()
print("📊 Trading Signals:")
for signal, count in signal_counts.items():
    print(f"  {signal}: {count} days")

# Show recent signals
print("\nRecent signals:")
print(stock_data[["date", "close", "sma_20", "sma_50", "rsi", "signal"]].tail(10))

print("\n" + "=" * 70)
print("✅ Analysis complete! Rust-accelerated financial indicators ready.")
print("\n💡 Key Takeaways:")
print("  • Moving averages smooth price trends")
print("  • RSI identifies overbought/oversold conditions")
print("  • Bollinger Bands measure volatility")
print("  • Combine indicators for robust trading signals")
