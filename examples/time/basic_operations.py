"""
Time Series Examples

Demonstrates time series operations using the .ts accessor.
"""

import numpy as np
import pandas as pd


def basic_resampling():
    """Basic resampling examples."""
    print("=" * 60)
    print("Basic Resampling")
    print("=" * 60)

    # Create hourly time series
    dates = pd.date_range("2024-01-01", periods=168, freq="h")  # 1 week
    data = pd.DataFrame(
        {
            "value": np.random.randn(168).cumsum() + 100,
            "volume": np.random.randint(10, 100, 168),
        },
        index=dates,
    )

    print("\nOriginal (hourly) data:")
    print(data.head())
    print(f"Shape: {data.shape}")

    # Resample to daily
    daily = data.ts.resample("1D", agg="mean")
    print("\nDaily average:")
    print(daily)

    # Multiple aggregations
    daily_stats = data.ts.resample("1D", agg=["mean", "std", "min", "max"])
    print("\nDaily statistics:")
    print(daily_stats["value"].head())


def rolling_windows():
    """Rolling window examples."""
    print("\n" + "=" * 60)
    print("Rolling Windows")
    print("=" * 60)

    # Create daily time series
    dates = pd.date_range("2024-01-01", periods=90, freq="D")
    data = pd.DataFrame({"price": np.random.randn(90).cumsum() + 50}, index=dates)

    print("\nOriginal data:")
    print(data.head(10))

    # 7-day rolling average
    ma7 = data.ts.rolling("7D", agg="mean")
    print("\n7-day moving average:")
    print(ma7.head(10))

    # Multiple window sizes
    data["MA7"] = data.ts.rolling("7D", agg="mean")
    data["MA30"] = data.ts.rolling("30D", agg="mean")

    print("\nWith multiple moving averages:")
    print(data.tail())


def interpolation():
    """Interpolation examples."""
    print("\n" + "=" * 60)
    print("Interpolation")
    print("=" * 60)

    # Create data with missing values
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    values = np.random.randn(20).cumsum() + 100

    # Introduce some NaN values
    values[[3, 7, 12, 15]] = np.nan

    data = pd.DataFrame({"value": values}, index=dates)

    print("\nData with missing values:")
    print(data)

    # Linear interpolation
    filled = data.ts.interpolate("linear")
    print("\nAfter linear interpolation:")
    print(filled)


def transformations():
    """Time series transformations."""
    print("\n" + "=" * 60)
    print("Transformations")
    print("=" * 60)

    # Create stock price data
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    data = pd.DataFrame({"price": np.random.randn(30).cumsum() + 100}, index=dates)

    print("\nOriginal prices:")
    print(data.head(10))

    # Calculate returns
    data["returns"] = data.ts.pct_change()

    # Calculate differences
    data["diff"] = data["price"].ts.diff()

    # Lag values
    data["price_lag1"] = data["price"].ts.shift(1)

    print("\nWith transformations:")
    print(data.head(10))


def sensor_data_example():
    """Realistic sensor data example."""
    print("\n" + "=" * 60)
    print("Sensor Data Analysis")
    print("=" * 60)

    # Simulate sensor readings every 5 minutes
    dates = pd.date_range("2024-01-01", periods=288, freq="5min")  # 1 day
    data = pd.DataFrame(
        {
            "temperature": 20
            + 5 * np.sin(np.linspace(0, 4 * np.pi, 288))
            + np.random.randn(288) * 0.5,
            "humidity": 60
            + 10 * np.cos(np.linspace(0, 4 * np.pi, 288))
            + np.random.randn(288) * 2,
        },
        index=dates,
    )

    print("\nRaw sensor data (5-minute intervals):")
    print(data.head())

    # Resample to hourly averages
    hourly = data.ts.resample("1H", agg="mean")
    print("\nHourly averages:")
    print(hourly.head())

    # Apply smoothing
    smoothed = data.ts.rolling("1H", agg="mean")
    print("\n1-hour rolling average (smoothed):")
    print(smoothed.head(20))

    # Calculate hourly statistics
    hourly_stats = data.ts.resample("1H", agg=["mean", "std", "min", "max"])
    print("\nHourly statistics:")
    print(hourly_stats["temperature"].head())


def main():
    """Run all examples."""
    # Import accessor to register it
    import parquetframe.time  # noqa

    basic_resampling()
    rolling_windows()
    interpolation()
    transformations()
    sensor_data_example()

    print("\n" + "=" * 60)
    print("✅ All time series examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
