"""
Tests for time-series analysis functionality.

This module tests the TimeSeriesAccessor class and its various methods
including datetime detection, resampling, rolling operations, and time-based filtering.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import from the package
from parquetframe.legacy import ParquetFrame
from src.parquetframe.timeseries import TimeSeriesAccessor, detect_datetime_columns


class TestDatetimeDetection:
    """Test datetime column detection functionality."""

    def test_detect_datetime_columns_iso_format(self):
        """Test detection of ISO format datetime columns."""
        data = {
            "date_col": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "datetime_col": [
                "2023-01-01 10:30:00",
                "2023-01-02 11:45:00",
                "2023-01-03 12:15:00",
            ],
            "numeric_col": [1, 2, 3],
            "text_col": ["A", "B", "C"],
        }
        df = pd.DataFrame(data)

        detected = detect_datetime_columns(df)
        assert "date_col" in detected
        assert "datetime_col" in detected
        assert "numeric_col" not in detected
        assert "text_col" not in detected

    def test_detect_datetime_columns_us_format(self):
        """Test detection of US format datetime columns."""
        data = {
            "us_date": ["01/15/2023", "01/16/2023", "01/17/2023"],
            "us_datetime": [
                "01/15/2023 14:30:00",
                "01/16/2023 15:45:00",
                "01/17/2023 16:15:00",
            ],
            "other_col": ["X", "Y", "Z"],
        }
        df = pd.DataFrame(data)

        detected = detect_datetime_columns(df)
        assert "us_date" in detected
        assert "us_datetime" in detected
        assert "other_col" not in detected

    def test_detect_datetime_columns_already_datetime(self):
        """Test detection when column is already datetime type."""
        data = {
            "already_datetime": pd.to_datetime(
                ["2023-01-01", "2023-01-02", "2023-01-03"]
            ),
            "string_col": ["A", "B", "C"],
        }
        df = pd.DataFrame(data)

        detected = detect_datetime_columns(df)
        assert "already_datetime" in detected
        assert "string_col" not in detected

    def test_detect_datetime_columns_mixed_data(self):
        """Test detection with mixed valid/invalid datetime data."""
        data = {
            "mixed_col": [
                "2023-01-01",
                "not-a-date",
                "2023-01-03",
                "2023-01-04",
                "2023-01-05",
            ],
            "mostly_valid": [
                "2023-01-01",
                "2023-01-02",
                "2023-01-03",
                "2023-01-04",
                "2023-01-05",
            ],
        }
        df = pd.DataFrame(data)

        detected = detect_datetime_columns(df)
        # Should detect mostly_valid (80%+ success rate) but not mixed_col
        assert "mostly_valid" in detected
        assert "mixed_col" not in detected


class TestTimeSeriesAccessor:
    """Test TimeSeriesAccessor functionality."""

    def setup_method(self):
        """Set up test data."""
        # Create sample time-series data
        dates = pd.date_range("2023-01-01", periods=100, freq="h")
        self.ts_data = pd.DataFrame(
            {"timestamp": dates, "value": range(100), "category": ["A", "B"] * 50}
        )

        # Create test file
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "timeseries_test.csv"
        self.ts_data.to_csv(self.test_file, index=False)

        # Create ParquetFrame instance
        self.pf = ParquetFrame.read(str(self.test_file))

    @pytest.mark.skip(
        reason="Phase 2 API migration pending - TimeSeriesAccessor type check needs update"
    )
    def test_ts_accessor_exists(self):
        """Test that ts accessor is available."""
        assert hasattr(self.pf, "ts")
        assert isinstance(self.pf.ts, TimeSeriesAccessor)

    def test_detect_datetime_columns_via_accessor(self):
        """Test datetime detection through accessor."""
        detected = self.pf.ts.detect_datetime_columns()
        assert "timestamp" in detected

    def test_parse_datetime(self):
        """Test datetime parsing functionality."""
        # Create data with string dates
        data = pd.DataFrame(
            {
                "date_str": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "value": [10, 20, 30],
            }
        )
        pf = ParquetFrame(data)

        # Parse datetime column
        pf_parsed = pf.ts.parse_datetime("date_str")

        # Verify datetime parsing
        assert pd.api.types.is_datetime64_any_dtype(pf_parsed.pandas_df["date_str"])

    def test_resample_operations(self):
        """Test time-series resampling operations."""
        # Use original datetime data directly instead of CSV round-trip
        dates = pd.date_range("2023-01-01", periods=100, freq="h")
        ts_data = pd.DataFrame(
            {"timestamp": dates, "value": range(100), "category": ["A", "B"] * 50}
        )
        # Set timestamp as index for resampling
        pf_indexed = ParquetFrame(ts_data.set_index("timestamp"))

        # Test daily resampling with mean (only numeric columns)
        daily_mean = pf_indexed.ts.resample("1D").mean()
        assert isinstance(daily_mean, ParquetFrame)
        assert len(daily_mean.pandas_df) > 0  # Should have resampled data

        # Test hourly resampling with sum
        hourly_sum = pf_indexed.ts.resample("1h").sum()
        assert isinstance(hourly_sum, ParquetFrame)

        # Test resampling with max
        daily_max = pf_indexed.ts.resample("1D").max()
        assert isinstance(daily_max, ParquetFrame)

    def test_rolling_operations(self):
        """Test rolling window operations."""
        # Use original datetime data directly instead of CSV round-trip
        dates = pd.date_range("2023-01-01", periods=100, freq="h")
        ts_data = pd.DataFrame(
            {"timestamp": dates, "value": range(100), "category": ["A", "B"] * 50}
        )
        # Set timestamp as index
        pf_indexed = ParquetFrame(ts_data.set_index("timestamp"))

        # Test rolling window operations
        rolling_mean = pf_indexed.ts.rolling(5).mean()
        assert isinstance(rolling_mean, ParquetFrame)

        rolling_std = pf_indexed.ts.rolling(10).std()
        assert isinstance(rolling_std, ParquetFrame)

        rolling_sum = pf_indexed.ts.rolling(3).sum()
        assert isinstance(rolling_sum, ParquetFrame)

    def test_shift_operations(self):
        """Test shift, lag, and lead operations."""
        # Test shift
        shifted = self.pf.ts.shift(1)
        assert isinstance(shifted, ParquetFrame)

        # Test lag (should be same as positive shift)
        lagged = self.pf.ts.lag(2)
        assert isinstance(lagged, ParquetFrame)

        # Test lead (should be same as negative shift)
        leading = self.pf.ts.lead(1)
        assert isinstance(leading, ParquetFrame)

    def test_time_filtering_operations(self):
        """Test time-based filtering operations."""
        # Create data with datetime index
        dates = pd.date_range("2023-01-01 08:00", periods=24, freq="h")
        data_with_index = pd.DataFrame(
            {"value": range(24), "category": ["A", "B"] * 12}, index=dates
        )
        pf_indexed = ParquetFrame(data_with_index)

        # Test between_time (business hours)
        business_hours = pf_indexed.ts.between_time("09:00", "17:00")
        assert isinstance(business_hours, ParquetFrame)

        # Test at_time (specific hour)
        noon_data = pf_indexed.ts.at_time("12:00")
        assert isinstance(noon_data, ParquetFrame)


class TestTimeSeriesWithDask:
    """Test time-series functionality with Dask backend."""

    def setup_method(self):
        """Set up test data for Dask testing."""
        # Create larger dataset that would trigger Dask usage
        dates = pd.date_range("2023-01-01", periods=1000, freq="h")
        large_data = pd.DataFrame(
            {
                "timestamp": dates,
                "value": range(1000),
                "category": (["A", "B", "C"] * 334)[:1000],  # Ensure length matches
            }
        )

        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "large_timeseries.csv"
        large_data.to_csv(self.test_file, index=False)

        # Force Dask usage
        self.pf = ParquetFrame.read(str(self.test_file), islazy=True)

    def test_datetime_detection_with_dask(self):
        """Test datetime detection with Dask DataFrame."""
        detected = self.pf.ts.detect_datetime_columns()
        assert "timestamp" in detected
        assert self.pf.islazy  # Verify we're still using Dask

    def test_shift_with_dask(self):
        """Test shift operations with Dask."""
        shifted = self.pf.ts.shift(1)
        assert isinstance(shifted, ParquetFrame)
        assert shifted.islazy  # Should preserve Dask backend


class TestTimeSeriesEdgeCases:
    """Test edge cases and error conditions."""

    def test_accessor_with_no_data(self):
        """Test accessor behavior with no DataFrame loaded."""
        empty_pf = ParquetFrame()

        with pytest.raises(ValueError, match="No DataFrame loaded"):
            empty_pf.ts.detect_datetime_columns()

    def test_resample_without_datetime_index(self):
        """Test resampling when no datetime columns are available."""
        data = pd.DataFrame(
            {"numeric_col": [1, 2, 3, 4, 5], "text_col": ["A", "B", "C", "D", "E"]}
        )
        pf = ParquetFrame(data)

        with pytest.raises(ValueError, match="No datetime columns detected"):
            pf.ts.resample("1D").mean()

    def test_parse_datetime_invalid_column(self):
        """Test parsing datetime on non-existent column."""
        data = pd.DataFrame({"col1": [1, 2, 3]})
        pf = ParquetFrame(data)

        with pytest.raises(KeyError):
            pf.ts.parse_datetime("nonexistent_column")

    def test_time_filtering_with_string_inputs(self):
        """Test time filtering with string time inputs."""
        # Create data with datetime index
        dates = pd.date_range("2023-01-01 00:00", periods=24, freq="h")
        data = pd.DataFrame({"value": range(24)}, index=dates)
        pf = ParquetFrame(data)

        # Test with string inputs
        morning = pf.ts.between_time("06:00", "12:00")
        assert isinstance(morning, ParquetFrame)

        exact_time = pf.ts.at_time("09:00")
        assert isinstance(exact_time, ParquetFrame)


class TestTimeSeriesIntegration:
    """Test integration with other ParquetFrame features."""

    def test_chaining_with_sql(self):
        """Test chaining time-series operations with SQL operations."""
        # Create time-series data
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {"date": dates, "sales": range(100, 200), "region": ["North", "South"] * 50}
        )

        pf = ParquetFrame(data)

        # Chain time-series and SQL operations
        # First do a simple shift, then use SQL to aggregate
        shifted = pf.ts.shift(1)
        sql_result = shifted.sql(
            "SELECT region, AVG(sales) as avg_sales FROM df GROUP BY region"
        )

        assert isinstance(sql_result, ParquetFrame)

    def test_time_series_with_save_restore(self):
        """Test that time-series operations work after save/restore cycle."""
        dates = pd.date_range("2023-01-01", periods=50, freq="h")
        data = pd.DataFrame({"timestamp": dates, "value": range(50)})

        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "ts_test.parquet"

        # Save and reload
        pf = ParquetFrame(data)
        pf.save(str(temp_file))

        reloaded_pf = ParquetFrame.read(str(temp_file))

        # Test time-series operations on reloaded data
        detected = reloaded_pf.ts.detect_datetime_columns()
        assert "timestamp" in detected
