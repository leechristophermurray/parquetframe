"""
Unit tests for DataFrameProxy.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from parquetframe.core.execution import ExecutionContext, ExecutionMode
from parquetframe.core.proxy import DataFrameProxy


class TestDataFrameProxyInit:
    """Test DataFrameProxy initialization."""

    def test_pandas_backend_detection(self):
        """Test pandas DataFrame detection."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        proxy = DataFrameProxy(df)
        assert proxy.backend == "pandas"
        assert proxy._native is df

    def test_auto_execution_mode(self):
        """Test automatic execution mode detection."""
        df = pd.DataFrame({"a": range(100)})
        proxy = DataFrameProxy(df)
        # Small data should default to local
        assert proxy.execution_mode in [ExecutionMode.LOCAL, ExecutionMode.AUTO]

    def test_explicit_execution_mode(self):
        """Test explicit execution mode."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(df, execution_mode="distributed")
        assert proxy.execution_mode == ExecutionMode.DISTRIBUTED

    @patch("parquetframe.core.proxy.NARWHALS_AVAILABLE", True)
    @patch("parquetframe.core.proxy.nw")
    def test_narwhals_initialization(self, mock_nw):
        """Test narwhals wrapper initialization."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        mock_nw.from_native.return_value = MagicMock()

        proxy = DataFrameProxy(df)
        mock_nw.from_native.assert_called_once()


class TestDataFrameProxyOperations:
    """Test DataFrameProxy operations."""

    def test_native_access(self):
        """Test accessing native DataFrame."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(df)
        assert proxy.native is df

    def test_backend_property(self):
        """Test backend property."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(df)
        assert proxy.backend == "pandas"

    def test_set_execution_mode(self):
        """Test changing execution mode."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(df, execution_mode="local")

        proxy.set_execution_mode("distributed")
        assert proxy.execution_mode == ExecutionMode.DISTRIBUTED

    @patch("parquetframe.core.proxy.NARWHALS_AVAILABLE", True)
    @patch("parquetframe.core.proxy.nw")
    def test_filter_with_narwhals(self, mock_nw):
        """Test filter operation using narwhals."""
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})

        # Mock narwhals behavior
        mock_result = MagicMock()
        mock_result.to_native.return_value = pd.DataFrame({"a": [4, 5]})
        mock_nw_df = MagicMock()
        mock_nw_df.filter.return_value = mock_result
        mock_nw.from_native.return_value = mock_nw_df

        proxy = DataFrameProxy(df)
        result = proxy.filter("a > 3")

        assert isinstance(result, DataFrameProxy)
        assert len(result.native) == 2

    def test_repr(self):
        """Test string representation."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(df)
        repr_str = repr(proxy)

        assert "DataFrameProxy" in repr_str
        assert "pandas" in repr_str


class TestDataFrameProxyRust:
    """Test Rust-accelerated operations."""

    @patch("parquetframe.core.proxy.DataFrameProxy._check_rust_available")
    @patch("parquetframe.pf_py.filter_parallel")
    def test_filter_rust_local(self, mock_filter, mock_rust_check):
        """Test Rust filter in local mode."""
        mock_rust_check.return_value = True
        mock_filter.return_value = pd.DataFrame({"a": [4, 5]})

        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        ctx = ExecutionContext(mode=ExecutionMode.LOCAL, rust_threads=4)
        proxy = DataFrameProxy(df, execution_ctx=ctx)

        result = proxy.filter_rust("a > 3")

        mock_filter.assert_called_once()
        assert isinstance(result, DataFrameProxy)


class TestDataFrameProxyFallback:
    """Test fallback behavior when dependencies missing."""

    @patch("parquetframe.core.proxy.NARWHALS_AVAILABLE", False)
    def test_filter_without_narwhals(self):
        """Test that filter raises error without narwhals."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(df)

        with pytest.raises(RuntimeError, match="Narwhals not available"):
            proxy.filter("a > 2")

    @patch("parquetframe.core.proxy.DataFrameProxy._check_rust_available")
    def test_filter_rust_fallback(self, mock_rust_check):
        """Test fallback when Rust not available."""
        mock_rust_check.return_value = False

        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(df)

        # Should fall back to narwhals filter
        # (will raise if narwhals also not available)
        with patch("parquetframe.core.proxy.NARWHALS_AVAILABLE", False):
            with pytest.raises(RuntimeError):
                proxy.filter_rust("a > 2")
