"""
Trading Signals Example using ParquetFrame FIN Module

This example demonstrates:
- Technical indicator calculation (SMA, EMA, RSI, MACD, Bollinger Bands)
- Trading signal generation
- Strategy backtesting using the FIN backtest framework
- Performance analysis
"""

import numpy as np
import pandas as pd

# Calculate technical indicators using FIN module
# Simple backtest simulation (using signal changes as trades)
from parquetframe._rustic import (
    fin_backtest,
    fin_bollinger_bands,
    fin_ema,
    fin_macd,
    fin_rsi,
    fin_sma,
)

# Generate sample stock data
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")

# Simulate price data with trend
base_price = 100
prices = [base_price]
for _i in range(1, len(dates)):
    # Add trend + noise
    change = np.random.randn() * 2 + 0.05  # Slight upward bias
    prices.append(prices[-1] * (1 + change / 100))

stock_data = pd.DataFrame(
    {
        "date": dates,
        "price": prices,
        "volume": np.random.randint(1000000, 10000000, len(dates)),
    }
)

print("=" * 80)
print("TRADING SIGNALS WITH PARQUETFRAME FIN")
print("=" * 80)
print(f"\nAnalyzing {len(dates)} days of stock data")
print(
    f"Price range: ${stock_data['price'].min():.2f} - ${stock_data['price'].max():.2f}"
)
print()


prices_array = stock_data["price"].values

print("📊 CALCULATING TECHNICAL INDICATORS")
print("-" * 80)

# Moving Averages
sma_20 = fin_sma(prices_array, 20)
sma_50 = fin_sma(prices_array, 50)
ema_12 = fin_ema(prices_array, 12)

stock_data["SMA_20"] = sma_20
stock_data["SMA_50"] = sma_50
stock_data["EMA_12"] = ema_12

print("✓ Moving Averages (SMA 20/50, EMA 12)")

# RSI
rsi_14 = fin_rsi(prices_array, 14)
stock_data["RSI_14"] = rsi_14
print("✓ RSI (14-period)")

# MACD
macd_line, signal_line, histogram = fin_macd(prices_array, 12, 26, 9)
stock_data["MACD"] = macd_line
stock_data["MACD_signal"] = signal_line
stock_data["MACD_hist"] = histogram
print("✓ MACD (12, 26, 9)")

# Bollinger Bands
bb_upper, bb_middle, bb_lower = fin_bollinger_bands(prices_array, 20, 2.0)
stock_data["BB_upper"] = bb_upper
stock_data["BB_middle"] = bb_middle
stock_data["BB_lower"] = bb_lower
print("✓ Bollinger Bands (20, 2σ)")

print()
print("🎯 GENERATING TRADING SIGNALS")
print("-" * 80)

# Initialize signals
stock_data["signal"] = 0.0

# Strategy 1: MA Crossover
ma_cross_buy = (stock_data["SMA_20"] > stock_data["SMA_50"]) & (
    stock_data["SMA_20"].shift(1) <= stock_data["SMA_50"].shift(1)
)
ma_cross_sell = (stock_data["SMA_20"] < stock_data["SMA_50"]) & (
    stock_data["SMA_20"].shift(1) >= stock_data["SMA_50"].shift(1)
)

# Strategy 2: RSI Overbought/Oversold
rsi_oversold = stock_data["RSI_14"] < 30
rsi_overbought = stock_data["RSI_14"] > 70

# Strategy 3: MACD Crossover
macd_cross_buy = (stock_data["MACD"] > stock_data["MACD_signal"]) & (
    stock_data["MACD"].shift(1) <= stock_data["MACD_signal"].shift(1)
)
macd_cross_sell = (stock_data["MACD"] < stock_data["MACD_signal"]) & (
    stock_data["MACD"].shift(1) >= stock_data["MACD_signal"].shift(1)
)

# Combined signal (majority vote)
buy_votes = (
    ma_cross_buy.astype(int) + rsi_oversold.astype(int) + macd_cross_buy.astype(int)
)
sell_votes = (
    ma_cross_sell.astype(int) + rsi_overbought.astype(int) + macd_cross_sell.astype(int)
)

stock_data.loc[buy_votes >= 2, "signal"] = 1.0  # Buy
stock_data.loc[sell_votes >= 2, "signal"] = -1.0  # Sell

# Count signals
num_buy = (stock_data["signal"] == 1.0).sum()
num_sell = (stock_data["signal"] == -1.0).sum()

print(f"Generated {num_buy} BUY signals")
print(f"Generated {num_sell} SELL signals")

# Display sample signals
print("\nSample Trading Signals:")
signal_days = stock_data[stock_data["signal"] != 0][
    ["date", "price", "signal", "RSI_14"]
].head(10)
for _, row in signal_days.iterrows():
    action = "📈 BUY " if row["signal"] > 0 else "📉 SELL"
    print(
        f"{action}  {row['date'].strftime('%Y-%m-%d')}  Price: ${row['price']:>7.2f}  RSI: {row['RSI_14']:>5.1f}"
    )

print()
print("📈 BACKTEST RESULTS")
print("-" * 80)


# Convert signals for backtest (0/1 for in/out of position)
backtest_signals = stock_data["signal"].copy()
backtest_signals = backtest_signals.fillna(0)

# Run backtest
bt_result = fin_backtest(prices_array, backtest_signals.values, 10000.0, 0.001)

print(f"Initial Capital:           ${10000:>12,.2f}")
print(f"Total Return:              {bt_result['total_return']:>12.2%}")
print(f"Sharpe Ratio:              {bt_result['sharpe_ratio']:>12.2f}")
print(f"Maximum Drawdown:          {bt_result['max_drawdown']:>12.2%}")
print(f"Number of Trades:          {bt_result['num_trades']:>12}")
print(f"Win Rate:                  {bt_result['win_rate']:>12.1%}")

# Calculate buy-and-hold for comparison
buy_hold_return = (prices[-1] - prices[0]) / prices[0]

print()
print("📊 STRATEGY COMPARISON")
print("-" * 80)
print(f"Strategy Return:           {bt_result['total_return']:>12.2%}")
print(f"Buy-and-Hold Return:       {buy_hold_return:>12.2%}")

if bt_result["total_return"] > buy_hold_return:
    outperformance = bt_result["total_return"] - buy_hold_return
    print(f"✅ Strategy OUTPERFORMED by {outperformance:>7.2%}")
else:
    underperformance = buy_hold_return - bt_result["total_return"]
    print(f"❌ Strategy UNDERPERFORMED by {underperformance:>7.2%}")

print()
print("=" * 80)
print("✅ Analysis complete!")
print("=" * 80)
print("\nKey Insights:")
print(
    f"• Generated {num_buy + num_sell} total signals ({num_buy} buys, {num_sell} sells)"
)
print(f"• Strategy Sharpe ratio: {bt_result['sharpe_ratio']:.2f}")
print(f"• Maximum drawdown: {bt_result['max_drawdown']:.2%}")
print(f"• Win rate: {bt_result['win_rate']:.1%}")
