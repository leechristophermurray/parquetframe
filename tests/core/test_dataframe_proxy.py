"""
Tests for DataFrameProxy functionality.

Tests cover:
- Proxy initialization with different engines
- Method delegation and wrapping
- Engine switching
- DataFrame operations
"""

import pandas as pd
import pytest

from parquetframe.core import DataFrameProxy


class TestDataFrameProxyInit:
    """Test DataFrameProxy initialization."""

    def test_init_empty(self):
        """Test initializing empty DataFrameProxy."""
        proxy = DataFrameProxy()
        assert proxy.engine_name in ("pandas", "polars", "dask")
        assert proxy.native is None

    def test_init_with_pandas_df(self):
        """Test initializing with pandas DataFrame."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert proxy.engine_name == "pandas"
        assert isinstance(proxy.native, pd.DataFrame)
        pd.testing.assert_frame_equal(proxy.native, df)

    def test_init_with_engine_string(self):
        """Test initialization with engine name."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert proxy.engine_name == "pandas"

    def test_init_auto_selection(self):
        """Test automatic engine selection."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df)

        # Should select an available engine
        assert proxy.engine_name in ("pandas", "polars", "dask")


class TestDataFrameProxyProperties:
    """Test DataFrameProxy properties."""

    def test_engine_name(self):
        """Test engine_name property."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert proxy.engine_name == "pandas"

    def test_is_lazy_pandas(self):
        """Test is_lazy property for pandas."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert proxy.is_lazy is False

    @pytest.mark.skipif(
        not pytest.importorskip("polars", reason="Polars not available"),
        reason="Polars not available",
    )
    def test_is_lazy_polars(self):
        """Test is_lazy property for Polars."""
        import polars as pl

        df = pl.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df.lazy(), engine="polars")

        assert proxy.is_lazy is True

    def test_shape(self):
        """Test shape property."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert proxy.shape == (3, 2)

    def test_columns(self):
        """Test columns property."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert proxy.columns == ["a", "b"]

    def test_native(self):
        """Test native property returns underlying DataFrame."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert proxy.native is df


class TestDataFrameProxyMethods:
    """Test DataFrameProxy basic methods."""

    def test_head(self):
        """Test head method."""
        df = pd.DataFrame({"a": range(10)})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy.head(3)

        assert isinstance(result, DataFrameProxy)
        assert len(result) == 3
        pd.testing.assert_frame_equal(result.native, df.head(3))

    def test_tail(self):
        """Test tail method."""
        df = pd.DataFrame({"a": range(10)})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy.tail(3)

        assert isinstance(result, DataFrameProxy)
        assert len(result) == 3
        pd.testing.assert_frame_equal(result.native, df.tail(3))

    def test_len(self):
        """Test __len__ method."""
        df = pd.DataFrame({"a": range(10)})
        proxy = DataFrameProxy(data=df, engine="pandas")

        assert len(proxy) == 10

    def test_repr(self):
        """Test string representation."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        repr_str = repr(proxy)
        assert "DataFrameProxy" in repr_str
        assert "pandas" in repr_str
        assert "3 rows" in repr_str


class TestDataFrameProxyDelegation:
    """Test method delegation to underlying DataFrame."""

    def test_getattr_pandas_method(self):
        """Test calling pandas methods through delegation."""
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 2, 3, 3, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        # Test method that returns DataFrame
        result = proxy.groupby("b").sum()

        assert isinstance(result, DataFrameProxy)
        assert result.engine_name == "pandas"

    def test_getattr_returns_scalar(self):
        """Test methods that return scalar values."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        # Test scalar return
        mean_val = proxy["a"].mean()
        assert isinstance(mean_val, int | float)
        assert mean_val == 2.0

    def test_getitem_column(self):
        """Test column access via __getitem__."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy["a"]

        # Should return wrapped Series
        assert hasattr(result, "engine_name")

    def test_getitem_multiple_columns(self):
        """Test multiple column access."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy[["a", "c"]]

        assert isinstance(result, DataFrameProxy)
        assert list(result.columns) == ["a", "c"]

    def test_attribute_error_empty_proxy(self):
        """Test AttributeError for empty proxy."""
        proxy = DataFrameProxy()

        with pytest.raises(AttributeError, match="empty"):
            _ = proxy.nonexistent_method()


class TestDataFrameProxyCompute:
    """Test compute functionality for lazy engines."""

    def test_compute_pandas(self):
        """Test compute is no-op for pandas."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy.compute()

        assert isinstance(result, DataFrameProxy)
        pd.testing.assert_frame_equal(result.native, df)

    @pytest.mark.skipif(
        not pytest.importorskip("polars", reason="Polars not available"),
        reason="Polars not available",
    )
    def test_compute_polars(self):
        """Test compute for Polars LazyFrame."""
        import polars as pl

        df = pl.DataFrame({"a": [1, 2, 3]})
        lazy_df = df.lazy()
        proxy = DataFrameProxy(data=lazy_df, engine="polars")

        result = proxy.compute()

        assert isinstance(result, DataFrameProxy)
        assert isinstance(result.native, pl.DataFrame)


class TestDataFrameProxyEngineConversion:
    """Test engine conversion methods."""

    def test_to_pandas_from_pandas(self):
        """Test to_pandas when already pandas."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy.to_pandas()

        assert isinstance(result, DataFrameProxy)
        assert result.engine_name == "pandas"

    @pytest.mark.skipif(
        not pytest.importorskip("polars", reason="Polars not available"),
        reason="Polars not available",
    )
    def test_to_polars_from_pandas(self):
        """Test converting pandas to Polars."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy.to_polars()

        assert isinstance(result, DataFrameProxy)
        assert result.engine_name == "polars"

    @pytest.mark.skipif(
        not pytest.importorskip("dask", reason="Dask not available"),
        reason="Dask not available",
    )
    def test_to_dask_from_pandas(self):
        """Test converting pandas to Dask."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        result = proxy.to_dask()

        assert isinstance(result, DataFrameProxy)
        assert result.engine_name == "dask"

    def test_to_engine_invalid(self):
        """Test conversion to invalid engine."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        proxy = DataFrameProxy(data=df, engine="pandas")

        with pytest.raises(KeyError, match="Engine .* not found"):
            proxy.to_engine("invalid_engine")
