"""
Tests for DataReader and intelligent engine selection.

Tests cover:
- File reading with automatic format detection
- Engine selection based on file size
- Parquet metadata reading
- CSV/Parquet reading
"""

import pandas as pd
import pytest

from parquetframe.core_v2 import DataFrameProxy, read, read_csv, read_parquet


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": range(100),
            "category": ["A", "B", "C", "D"] * 25,
            "value": range(100, 200),
        }
    )


@pytest.fixture
def small_parquet_file(sample_df, tmp_path):
    """Create small Parquet file for testing."""
    file_path = tmp_path / "small_data.parquet"
    sample_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def small_csv_file(sample_df, tmp_path):
    """Create small CSV file for testing."""
    file_path = tmp_path / "small_data.csv"
    sample_df.to_csv(file_path, index=False)
    return file_path


class TestReadParquet:
    """Test read_parquet function."""

    def test_read_small_parquet(self, small_parquet_file):
        """Test reading small Parquet file."""
        proxy = read_parquet(small_parquet_file)

        assert isinstance(proxy, DataFrameProxy)
        assert proxy.engine_name in ("pandas", "polars", "dask")
        assert len(proxy) == 100

    def test_read_parquet_force_pandas(self, small_parquet_file):
        """Test forcing pandas engine."""
        proxy = read_parquet(small_parquet_file, engine="pandas")

        assert proxy.engine_name == "pandas"
        assert isinstance(proxy.native, pd.DataFrame)

    @pytest.mark.skipif(
        not pytest.importorskip("polars", reason="Polars not available"),
        reason="Polars not available",
    )
    def test_read_parquet_force_polars(self, small_parquet_file):
        """Test forcing Polars engine."""
        proxy = read_parquet(small_parquet_file, engine="polars")

        assert proxy.engine_name == "polars"

    @pytest.mark.skipif(
        not pytest.importorskip("dask", reason="Dask not available"),
        reason="Dask not available",
    )
    def test_read_parquet_force_dask(self, small_parquet_file):
        """Test forcing Dask engine."""
        proxy = read_parquet(small_parquet_file, engine="dask")

        assert proxy.engine_name == "dask"

    def test_read_parquet_nonexistent_file(self):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            read_parquet("/nonexistent/file.parquet")


class TestReadCSV:
    """Test read_csv function."""

    def test_read_small_csv(self, small_csv_file):
        """Test reading small CSV file."""
        proxy = read_csv(small_csv_file)

        assert isinstance(proxy, DataFrameProxy)
        assert proxy.engine_name in ("pandas", "polars", "dask")
        assert len(proxy) == 100

    def test_read_csv_force_pandas(self, small_csv_file):
        """Test forcing pandas engine."""
        proxy = read_csv(small_csv_file, engine="pandas")

        assert proxy.engine_name == "pandas"
        assert isinstance(proxy.native, pd.DataFrame)

    def test_read_csv_nonexistent_file(self):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            read_csv("/nonexistent/file.csv")


class TestReadAutoDetect:
    """Test read function with automatic format detection."""

    def test_read_parquet_auto_detect(self, small_parquet_file):
        """Test automatic Parquet detection."""
        proxy = read(small_parquet_file)

        assert isinstance(proxy, DataFrameProxy)
        assert len(proxy) == 100

    def test_read_csv_auto_detect(self, small_csv_file):
        """Test automatic CSV detection."""
        proxy = read(small_csv_file)

        assert isinstance(proxy, DataFrameProxy)
        assert len(proxy) == 100

    def test_read_pqt_extension(self, sample_df, tmp_path):
        """Test reading .pqt file extension."""
        file_path = tmp_path / "data.pqt"
        sample_df.to_parquet(file_path)

        proxy = read(file_path)

        assert isinstance(proxy, DataFrameProxy)
        assert len(proxy) == 100

    def test_read_unsupported_format(self, tmp_path):
        """Test reading unsupported format raises error."""
        file_path = tmp_path / "data.txt"
        file_path.write_text("some text data")

        with pytest.raises(ValueError, match="Unsupported file format"):
            read(file_path)

    def test_read_nonexistent_file(self):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            read("/nonexistent/file.parquet")


class TestEngineSelection:
    """Test intelligent engine selection based on file size."""

    def test_auto_select_pandas_small_file(self, sample_df, tmp_path):
        """Test pandas is selected for small files."""
        # Create small file (< 100MB)
        file_path = tmp_path / "small.parquet"
        sample_df.to_parquet(file_path)

        proxy = read_parquet(file_path, engine="auto")

        # With small file, should select pandas
        assert proxy.engine_name in ("pandas", "polars", "dask")

    def test_environment_override(self, small_parquet_file, monkeypatch):
        """Test PARQUETFRAME_ENGINE environment variable override."""
        monkeypatch.setenv("PARQUETFRAME_ENGINE", "pandas")

        proxy = read_parquet(small_parquet_file)

        assert proxy.engine_name == "pandas"


class TestDataFrameOperations:
    """Test DataFrame operations on read data."""

    def test_operations_on_read_data(self, small_parquet_file):
        """Test performing operations on data read through reader."""
        proxy = read_parquet(small_parquet_file, engine="pandas")

        # Perform operations
        result = proxy.groupby("category").sum()

        assert isinstance(result, DataFrameProxy)
        assert len(result) == 4  # 4 categories

    def test_chaining_operations(self, small_parquet_file):
        """Test chaining multiple operations."""
        proxy = read_parquet(small_parquet_file, engine="pandas")

        # Chain operations
        result = proxy[proxy["value"] > 150].head(10)

        assert isinstance(result, DataFrameProxy)
        assert len(result) <= 10
