"""
Financial Indicators Examples

Demonstrates technical analysis using the .fin accessor.
"""

import pandas as pd
import numpy as np


def generate_stock_data(days=252):
    """Generate synthetic stock price data."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=days, freq="D")

    # Random walk for price
    returns = np.random.randn(days) * 0.02  # 2% daily std
    price = 100 * (1 + returns).cumprod()

    # Generate OHLC data
    high = price * (1 + np.abs(np.random.randn(days)) * 0.01)
    low = price * (1 - np.abs(np.random.randn(days)) * 0.01)
    open_price = price * (1 + np.random.randn(days) * 0.005)
    volume = np.random.randint(1000000, 10000000, days)

    return pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": price,
            "volume": volume,
        },
        index=dates,
    )


def moving_averages():
    """Moving average examples."""
    import parquetframe.finance  # noqa

    print("=" * 60)
    print("Moving Averages")
    print("=" * 60)

    prices = generate_stock_data()

    print("\nStock prices:")
    print(prices.head())

    # Simple Moving Average
    prices["SMA_20"] = prices.fin.sma(column="close", window=20)
    prices["SMA_50"] = prices.fin.sma(column="close", window=50)

    # Exponential Moving Average
    prices["EMA_12"] = prices.fin.ema(column="close", span=12)
    prices["EMA_26"] = prices.fin.ema(column="close", span=26)

    print("\nWith moving averages:")
    print(prices[["close", "SMA_20", "SMA_50", "EMA_12"]].tail())


def momentum_indicators():
    """Momentum indicator examples."""
    import parquetframe.finance  # noqa

    print("\n" + "=" * 60)
    print("Momentum Indicators")
    print("=" * 60)

    prices = generate_stock_data()

    # RSI
    prices["RSI"] = prices.fin.rsi(column="close", period=14)

    print("\nRSI (Relative Strength Index):")
    print(prices[["close", "RSI"]].tail(10))
    print(f"\nCurrent RSI: {prices['RSI'].iloc[-1]:.2f}")

    # Interpretation
    if prices["RSI"].iloc[-1] > 70:
        print("⚠️  Overbought territory (RSI > 70)")
    elif prices["RSI"].iloc[-1] < 30:
        print("⚠️  Oversold territory (RSI < 30)")
    else:
        print("✅ Neutral range (30 < RSI < 70)")


def macd_analysis():
    """MACD indicator example."""
    import parquetframe.finance  # noqa

    print("\n" + "=" * 60)
    print("MACD (Moving Average Convergence Divergence)")
    print("=" * 60)

    prices = generate_stock_data()

    # Calculate MACD
    macd_data = prices.fin.macd(column="close", fast=12, slow=26, signal=9)

    # Combine with prices
    prices = pd.concat([prices, macd_data], axis=1)

    print("\nMACD indicators:")
    print(prices[["close", "macd", "signal", "histogram"]].tail())

    # Signal interpretation
    if prices["macd"].iloc[-1] > prices["signal"].iloc[-1]:
        print("\n✅ Bullish signal (MACD > Signal)")
    else:
        print("\n⚠️  Bearish signal (MACD < Signal)")


def bollinger_bands():
    """Bollinger Bands example."""
    import parquetframe.finance  # noqa

    print("\n" + "=" * 60)
    print("Bollinger Bands")
    print("=" * 60)

    prices = generate_stock_data()

    # Calculate Bollinger Bands
    bb = prices.fin.bollinger_bands(column="close", window=20, num_std=2)
    prices = pd.concat([prices, bb], axis=1)

    print("\nBollinger Bands:")
    print(prices[["close", "lower", "middle", "upper"]].tail())

    # Check current position
    current_price = prices["close"].iloc[-1]
    bb_position = (current_price - prices["lower"].iloc[-1]) / (
        prices["upper"].iloc[-1] - prices["lower"].iloc[-1]
    )

    print(f"\nCurrent price: ${current_price:.2f}")
    print(f"Lower band: ${prices['lower'].iloc[-1]:.2f}")
    print(f"Upper band: ${prices['upper'].iloc[-1]:.2f}")
    print(f"Position in band: {bb_position:.1%}")


def risk_metrics():
    """Risk and return metrics."""
    import parquetframe.finance  # noqa

    print("\n" + "=" * 60)
    print("Risk & Return Metrics")
    print("=" * 60)

    prices = generate_stock_data()

    # Calculate returns
    prices["returns"] = prices.fin.returns(column="close")
    prices["cum_returns"] = prices.fin.cumulative_returns(column="close")

    # Volatility
    prices["volatility"] = prices.fin.volatility(column="close", window=20)

    print("\nReturns and volatility:")
    print(prices[["close", "returns", "cum_returns", "volatility"]].tail())

    # Summary statistics
    total_return = prices["cum_returns"].iloc[-1]
    avg_volatility = prices["volatility"].mean()
    sharpe_ratio = (prices["returns"].mean() * 252) / avg_volatility

    print(f"\n📊 Performance Summary:")
    print(f"Total return: {total_return:.2%}")
    print(f"Annualized volatility: {avg_volatility:.2%}")
    print(f"Sharpe ratio: {sharpe_ratio:.2f}")


def complete_analysis():
    """Complete technical analysis."""
    import parquetframe.finance  # noqa

    print("\n" + "=" * 60)
    print("Complete Technical Analysis")
    print("=" * 60)

    prices = generate_stock_data()

    # Add all indicators
    prices["SMA_50"] = prices.fin.sma("close", 50)
    prices["RSI"] = prices.fin.rsi("close", 14)

    macd_data = prices.fin.macd("close")
    bb_data = prices.fin.bollinger_bands("close")

    prices = pd.concat([prices, macd_data, bb_data], axis=1)

    print("\nComplete analysis:")
    print(prices[["close", "SMA_50", "RSI", "macd", "upper", "lower"]].tail())

    # Trading signals
    print("\n📈 Trading Signals:")

    current = prices.iloc[-1]

    # Trend
    trend = "Uptrend" if current["close"] > current["SMA_50"] else "Downtrend"
    print(f"Trend (vs 50-SMA): {trend}")

    # RSI
    if current["RSI"] > 70:
        rsi_signal = "Overbought"
    elif current["RSI"] < 30:
        rsi_signal = "Oversold"
    else:
        rsi_signal = "Neutral"
    print(f"RSI Signal: {rsi_signal}")

    # MACD
    macd_signal = "Bullish" if current["macd"] > current["signal"] else "Bearish"
    print(f"MACD Signal: {macd_signal}")


def main():
    """Run all examples."""
    moving_averages()
    momentum_indicators()
    macd_analysis()
    bollinger_bands()
    risk_metrics()
    complete_analysis()

    print("\n" + "=" * 60)
    print("✅ All financial examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
