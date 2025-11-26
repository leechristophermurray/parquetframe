"""
Unit tests for backend selection logic.
"""

from unittest.mock import patch

import pytest

from parquetframe.core.backend import BackendSelector


class TestBackendSelector:
    """Test intelligent backend selection."""

    def test_check_rust_available_true(self):
        """Test Rust availability check when available."""
        with patch("parquetframe.core.backend.parquetframe.pf_py"):
            assert BackendSelector.check_rust_available() is True

    def test_check_rust_available_false(self):
        """Test Rust availability check when not available."""
        with patch("parquetframe.core.backend.parquetframe", side_effect=ImportError):
            assert BackendSelector.check_rust_available() is False

    def test_estimate_size_file(self, tmp_path):
        """Test size estimation for single file."""
        test_file = tmp_path / "test.parquet"
        test_file.write_text("x" * 1000)  # 1KB file

        size = BackendSelector.estimate_size(str(test_file))
        assert size == 1000

    def test_estimate_size_directory(self, tmp_path):
        """Test size estimation for directory."""
        (tmp_path / "file1.parquet").write_text("x" * 500)
        (tmp_path / "file2.parquet").write_text("x" * 300)

        size = BackendSelector.estimate_size(str(tmp_path))
        assert size == 800

    def test_estimate_size_nonexistent(self):
        """Test error for nonexistent path."""
        with pytest.raises(FileNotFoundError):
            BackendSelector.estimate_size("/nonexistent/path")

    @patch("parquetframe.core.backend.BackendSelector.estimate_size")
    @patch("parquetframe.core.backend.BackendSelector.check_rust_available")
    def test_select_backend_small_data(self, mock_rust, mock_size):
        """Small data should select pandas."""
        mock_rust.return_value = True
        mock_size.return_value = 500_000_000  # 500MB

        backend, use_rust = BackendSelector.select_backend("test.parquet")

        assert backend == "pandas"
        assert use_rust is True

    @patch("parquetframe.core.backend.BackendSelector.estimate_size")
    @patch("parquetframe.core.backend.BackendSelector.check_rust_available")
    @patch("parquetframe.core.backend.POLARS_AVAILABLE", True)
    def test_select_backend_medium_data(self, mock_rust, mock_size):
        """Medium data should select Polars."""
        mock_rust.return_value = True
        mock_size.return_value = 5_000_000_000  # 5GB

        backend, use_rust = BackendSelector.select_backend("test.parquet")

        assert backend == "polars"
        assert use_rust is True

    @patch("parquetframe.core.backend.BackendSelector.estimate_size")
    @patch("parquetframe.core.backend.BackendSelector.check_rust_available")
    def test_select_backend_large_data(self, mock_rust, mock_size):
        """Large data should select Dask."""
        mock_rust.return_value = True
        mock_size.return_value = 200_000_000_000  # 200GB

        backend, use_rust = BackendSelector.select_backend("test.parquet")

        assert backend == "dask"
        assert use_rust is True

    @patch("parquetframe.core.backend.BackendSelector.estimate_size")
    def test_select_backend_user_preference(self, mock_size):
        """User preference should override auto-selection."""
        mock_size.return_value = 100_000_000  # 100MB

        backend, _ = BackendSelector.select_backend(
            "test.parquet", user_preference="dask"
        )

        assert backend == "dask"

    @patch("parquetframe.core.backend.BackendSelector.estimate_size")
    @patch("parquetframe.core.backend.BackendSelector.check_rust_available")
    def test_select_backend_no_rust_io(self, mock_rust, mock_size):
        """Non-Parquet should not use Rust I/O."""
        mock_rust.return_value = True
        mock_size.return_value = 100_000_000

        backend, use_rust = BackendSelector.select_backend("test.csv")

        assert use_rust is False  # CSV not supported by Rust I/O


class TestBackendSelectorDataFrame:
    """Test backend selection for existing DataFrames."""

    def test_select_pandas(self):
        """Test pandas DataFrame detection."""
        import pandas as pd

        df = pd.DataFrame({"a": [1, 2, 3]})

        backend = BackendSelector.select_for_dataframe(df)
        assert backend == "pandas"

    def test_select_unknown_type(self):
        """Test error for unknown type."""
        with pytest.raises(TypeError):
            BackendSelector.select_for_dataframe({"not": "a dataframe"})
