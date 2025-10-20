"""Tests for Rust I/O bindings.

This module tests the PyO3 bindings for Parquet metadata operations
implemented in Rust.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

try:
    from parquetframe import _rustic
    from parquetframe.io.io_backend import (
        get_parquet_column_names_fast,
        get_parquet_column_stats_fast,
        get_parquet_row_count_fast,
        is_rust_io_available,
        read_parquet_metadata_fast,
        try_get_row_count_fast,
        try_read_metadata_fast,
    )

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    _rustic = None


@pytest.fixture
def sample_parquet_file():
    """Create a sample Parquet file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        # Create sample data
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", None, "Eve"],
                "age": [25, 30, 35, 40, 45],
                "salary": [50000.0, 60000.0, 70000.0, 80000.0, None],
            }
        )

        # Write to Parquet
        df.to_parquet(f.name, index=False)
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink()


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestRustIOAvailability:
    """Test Rust I/O backend availability."""

    def test_rust_io_available(self):
        """Test that Rust I/O backend can be detected."""
        assert is_rust_io_available() is True

    def test_io_functions_exist(self):
        """Test that I/O functions are exported."""
        assert hasattr(_rustic, "read_parquet_metadata_rust")
        assert hasattr(_rustic, "get_parquet_row_count_rust")
        assert hasattr(_rustic, "get_parquet_column_names_rust")
        assert hasattr(_rustic, "get_parquet_column_stats_rust")


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestParquetMetadata:
    """Test Parquet metadata reading."""

    def test_read_metadata(self, sample_parquet_file):
        """Test reading full Parquet metadata."""
        metadata = read_parquet_metadata_fast(sample_parquet_file)

        assert isinstance(metadata, dict)
        assert metadata["num_rows"] == 5
        assert metadata["num_columns"] == 4
        assert metadata["num_row_groups"] == 1
        assert "version" in metadata
        assert "file_size_bytes" in metadata

    def test_column_names(self, sample_parquet_file):
        """Test extracting column names."""
        metadata = read_parquet_metadata_fast(sample_parquet_file)

        column_names = metadata["column_names"]
        assert isinstance(column_names, list)
        assert len(column_names) == 4
        assert "id" in column_names
        assert "name" in column_names
        assert "age" in column_names
        assert "salary" in column_names

    def test_column_types(self, sample_parquet_file):
        """Test extracting column types."""
        metadata = read_parquet_metadata_fast(sample_parquet_file)

        column_types = metadata["column_types"]
        assert isinstance(column_types, list)
        assert len(column_types) == 4

    def test_try_read_metadata(self, sample_parquet_file):
        """Test optional metadata reading."""
        metadata = try_read_metadata_fast(sample_parquet_file)

        assert metadata is not None
        assert metadata["num_rows"] == 5


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestRowCount:
    """Test row count extraction."""

    def test_get_row_count(self, sample_parquet_file):
        """Test getting row count."""
        row_count = get_parquet_row_count_fast(sample_parquet_file)

        assert isinstance(row_count, int)
        assert row_count == 5

    def test_row_count_direct_binding(self, sample_parquet_file):
        """Test direct binding call."""
        row_count = _rustic.get_parquet_row_count_rust(str(sample_parquet_file))

        assert isinstance(row_count, int)
        assert row_count == 5

    def test_try_get_row_count(self, sample_parquet_file):
        """Test optional row count reading."""
        row_count = try_get_row_count_fast(sample_parquet_file)

        assert row_count is not None
        assert row_count == 5


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestColumnNames:
    """Test column name extraction."""

    def test_get_column_names(self, sample_parquet_file):
        """Test getting column names."""
        columns = get_parquet_column_names_fast(sample_parquet_file)

        assert isinstance(columns, list)
        assert len(columns) == 4
        assert columns == ["id", "name", "age", "salary"]

    def test_column_names_direct_binding(self, sample_parquet_file):
        """Test direct binding call."""
        columns = _rustic.get_parquet_column_names_rust(str(sample_parquet_file))

        assert isinstance(columns, list)
        assert len(columns) == 4


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestColumnStatistics:
    """Test column statistics extraction."""

    def test_get_column_stats(self, sample_parquet_file):
        """Test getting column statistics."""
        stats = get_parquet_column_stats_fast(sample_parquet_file)

        assert isinstance(stats, list)
        assert len(stats) == 4  # 4 columns

        # Check structure
        for stat in stats:
            assert isinstance(stat, dict)
            assert "name" in stat
            assert "null_count" in stat

    def test_null_counts(self, sample_parquet_file):
        """Test null count statistics."""
        stats = get_parquet_column_stats_fast(sample_parquet_file)

        # Find stats for 'name' column (has 1 null)
        name_stats = next(s for s in stats if s["name"] == "name")
        assert name_stats["null_count"] == 1

        # Find stats for 'salary' column (has 1 null)
        salary_stats = next(s for s in stats if s["name"] == "salary")
        assert salary_stats["null_count"] == 1

        # Find stats for 'id' column (no nulls)
        id_stats = next(s for s in stats if s["name"] == "id")
        assert id_stats["null_count"] == 0

    def test_column_stats_direct_binding(self, sample_parquet_file):
        """Test direct binding call."""
        stats = _rustic.get_parquet_column_stats_rust(str(sample_parquet_file))

        assert isinstance(stats, list)
        assert len(stats) == 4


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestErrorHandling:
    """Test error handling in I/O operations."""

    def test_nonexistent_file(self):
        """Test reading nonexistent file raises error."""
        with pytest.raises(ValueError, match="File not found"):
            read_parquet_metadata_fast("/nonexistent/file.parquet")

    def test_nonexistent_file_row_count(self):
        """Test row count on nonexistent file raises error."""
        with pytest.raises(ValueError, match="File not found"):
            get_parquet_row_count_fast("/nonexistent/file.parquet")

    def test_invalid_path_type(self):
        """Test invalid path type handling."""
        with pytest.raises((TypeError, ValueError)):
            read_parquet_metadata_fast(None)

    def test_try_functions_handle_errors(self):
        """Test try_* functions return None on errors."""
        result = try_read_metadata_fast("/nonexistent/file.parquet")
        assert result is None

        result = try_get_row_count_fast("/nonexistent/file.parquet")
        assert result is None


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestPerformance:
    """Basic performance validation tests."""

    def test_large_row_count(self):
        """Test row count extraction on larger file."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            # Create larger dataset
            df = pd.DataFrame({"id": range(10000), "value": range(10000)})
            df.to_parquet(f.name, index=False)

            try:
                row_count = get_parquet_row_count_fast(f.name)
                assert row_count == 10000
            finally:
                Path(f.name).unlink()

    def test_many_columns(self):
        """Test metadata extraction with many columns."""
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            # Create dataset with many columns
            data = {f"col_{i}": [i] * 100 for i in range(50)}
            df = pd.DataFrame(data)
            df.to_parquet(f.name, index=False)

            try:
                metadata = read_parquet_metadata_fast(f.name)
                assert metadata["num_columns"] == 50
                assert len(metadata["column_names"]) == 50
            finally:
                Path(f.name).unlink()


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestPathHandling:
    """Test different path input types."""

    def test_string_path(self, sample_parquet_file):
        """Test string path input."""
        row_count = get_parquet_row_count_fast(str(sample_parquet_file))
        assert row_count == 5

    def test_pathlib_path(self, sample_parquet_file):
        """Test pathlib.Path input."""
        row_count = get_parquet_row_count_fast(sample_parquet_file)
        assert row_count == 5

    def test_relative_path(self):
        """Test relative path handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame({"a": [1, 2, 3]})
            df.to_parquet(file_path, index=False)

            # Use relative path
            import os

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                row_count = get_parquet_row_count_fast("test.parquet")
                assert row_count == 3
            finally:
                os.chdir(old_cwd)
