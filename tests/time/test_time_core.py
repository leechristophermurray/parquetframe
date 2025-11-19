"""
Tests for TIME core - time-series operations.
"""

import pandas as pd
import pytest

from parquetframe.time import TimeSeriesDataFrame, resample, rolling_window, asof_join


def test_resample_mean():
    """Test resampling with mean aggregation."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="1s"),
        "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
    })

    # Resample to 2-second intervals
    result = resample(df, "timestamp", "2s", "mean")

    assert len(result) == 5
    assert result["value"].iloc[0] == pytest.approx(1.5)  # mean of [1, 2]
    assert result["value"].iloc[1] == pytest.approx(3.5)  # mean of [3, 4]


def test_resample_sum():
    """Test resampling with sum aggregation."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=6, freq="1s"),
        "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    })

    result = resample(df, "timestamp", "3s", "sum")

    assert len(result) == 2
    assert result["value"].iloc[0] == pytest.approx(6.0)  # sum of [1, 2, 3]
    assert result["value"].iloc[1] == pytest.approx(15.0)  # sum of [4, 5, 6]


def test_rolling_mean():
    """Test rolling window mean."""
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])

    result = rolling_window(series, window=3, agg="mean")

    assert len(result) == 5
    assert result.iloc[0] == pytest.approx(1.0)  # [1]
    assert result.iloc[1] == pytest.approx(1.5)  # [1, 2]
    assert result.iloc[2] == pytest.approx(2.0)  # [1, 2, 3]
    assert result.iloc[3] == pytest.approx(3.0)  # [2, 3, 4]
    assert result.iloc[4] == pytest.approx(4.0)  # [3, 4, 5]


def test_rolling_std():
    """Test rolling window standard deviation."""
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])

    result = rolling_window(series, window=2, agg="std")

    assert len(result) == 5
    # First window is just [1], std = 0
    assert result.iloc[0] == pytest.approx(0.0)


def test_asof_join_backward():
    """Test as-of join with backward strategy."""
    left = pd.DataFrame({
        "trade_time": pd.to_datetime(["2024-01-01 00:00:01", "2024-01-01 00:00:03"]),
        "price": [100.0, 102.0],
    })

    right = pd.DataFrame({
        "quote_time": pd.to_datetime([
            "2024-01-01 00:00:00",
            "2024-01-01 00:00:02",
            "2024-01-01 00:00:04",
        ]),
        "bid": [99.0, 101.0, 103.0],
    })

    result = asof_join(left, right, "trade_time", "quote_time", "bid", strategy="backward")

    assert len(result) == 2
    assert result["bid"].iloc[0] == pytest.approx(99.0)  # trade@01 -> quote@00
    assert result["bid"].iloc[1] == pytest.approx(101.0)  # trade@03 -> quote@02


def test_timeseries_dataframe():
    """Test TimeSeriesDataFrame class."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="1s"),
        "value": range(10),
    })

    ts = TimeSeriesDataFrame(df, "timestamp")

    # Test resample
    hourly = ts.resample("5s", agg="mean")
    assert isinstance(hourly, TimeSeriesDataFrame)
    assert len(hourly) == 2

    # Test rolling
    smoothed = ts.rolling(window=3, agg="mean")
    assert isinstance(smoothed, TimeSeriesDataFrame)
    assert len(smoothed) == 10


def test_timeseries_asof_join():
    """Test TimeSeriesDataFrame as-of join."""
    trades = pd.DataFrame({
        "trade_time": pd.date_range("2024-01-01", periods=5, freq="1s"),
        "price": [100.0, 101.0, 102.0, 103.0, 104.0],
    })

    quotes = pd.DataFrame({
        "quote_time": pd.date_range("2024-01-01", periods=10, freq="500ms"),
        "bid": range(10),
    })

    trades_ts = TimeSeriesDataFrame(trades, "trade_time")
    quotes_ts = TimeSeriesDataFrame(quotes, "quote_time")

    result = trades_ts.asof_join(quotes_ts, "bid", strategy="backward")

    assert isinstance(result, TimeSeriesDataFrame)
    assert "bid" in result.df.columns
    assert len(result) == 5


if __name__ == "__main__":
    print("Testing TIME core...")

    test_resample_mean()
    print("✓ Resample mean works")

    test_resample_sum()
    print("✓ Resample sum works")

    test_rolling_mean()
    print("✓ Rolling mean works")

    test_rolling_std()
    print("✓ Rolling std works")

    test_asof_join_backward()
    print("✓ As-of join backward works")

    test_timeseries_dataframe()
    print("✓ TimeSeriesDataFrame works")

    test_timeseries_asof_join()
    print("✓ TimeSeriesDataFrame as-of join works")

    print("\n✅ All TIME tests passed!")
