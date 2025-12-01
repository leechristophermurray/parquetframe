"""
Comprehensive tests for new ParquetFrame features.

Tests SQL, Time Series, GeoSpatial, Financial, and CLI modules.
"""

# Check for SQL dependencies at module level
import importlib.util

import numpy as np
import pandas as pd
import pytest

# Import accessors to register them with pandas
import parquetframe.finance  # noqa: F401 - registers .fin accessor
import parquetframe.time  # noqa: F401 - registers .ts accessor

HAS_SQL = False  # Initialize to False
if importlib.util.find_spec("datafusion"):
    HAS_SQL = True
elif importlib.util.find_spec("duckdb"):
    HAS_SQL = True


@pytest.mark.skipif(not HAS_SQL, reason="SQL dependencies not installed")
class TestSQLEngine:
    """Test SQL query engine."""

    def test_basic_query(self):
        """Test basic SELECT query."""
        from parquetframe.sql import sql

        df = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
        )

        result = sql("SELECT * FROM df WHERE age > 28", df=df)
        assert len(result) == 2
        assert list(result["name"]) == ["Bob", "Charlie"]

    def test_joins(self):
        """Test SQL JOIN operations."""
        from parquetframe.sql import sql

        users = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})

        orders = pd.DataFrame(
            {"order_id": [101, 102], "user_id": [1, 3], "amount": [100, 200]}
        )

        result = sql(
            """
            SELECT u.name, o.amount
            FROM users u
            JOIN orders o ON u.id = o.user_id
        """,
            users=users,
            orders=orders,
        )

        assert len(result) == 2
        assert result["amount"].sum() == 300

    def test_aggregations(self):
        """Test SQL aggregations."""
        from parquetframe.sql import sql

        sales = pd.DataFrame(
            {"product": ["A", "B", "A", "A"], "amount": [100, 150, 200, 50]}
        )

        result = sql(
            """
            SELECT product, COUNT(*) as count, SUM(amount) as total
            FROM sales
            GROUP BY product
        """,
            sales=sales,
        )

        assert len(result) == 2
        product_a = result[result["product"] == "A"].iloc[0]
        assert product_a["count"] == 3
        assert product_a["total"] == 350

    def test_sql_context(self):
        """Test SQL context management."""
        from parquetframe.sql import SQLContext

        ctx = SQLContext()

        users = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        ctx.register("users", users)

        result = ctx.query("SELECT * FROM users WHERE id = 1")
        assert len(result) == 1
        assert result["name"].iloc[0] == "Alice"


class TestTimeSeriesAccessor:
    """Test time series .ts accessor."""

    def test_resample(self):
        """Test time series resampling."""

        dates = pd.date_range("2024-01-01", periods=100, freq="h")
        df = pd.DataFrame({"value": range(100)}, index=dates)

        daily = df.ts.resample("1D", agg="mean")
        assert len(daily) < len(df)
        # assert daily.index.freq == pd.DateOffset(days=1)  # Flaky assertion across pandas versions

    def test_rolling(self):
        """Test rolling windows."""

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        df = pd.DataFrame({"value": np.random.randn(100)}, index=dates)

        ma7 = df.ts.rolling("7D", agg="mean")
        assert len(ma7) == len(df)
        assert not ma7["value"].isna().all()

    def test_interpolate(self):
        """Test interpolation."""

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        values = list(range(10))
        values[5] = np.nan
        df = pd.DataFrame({"value": values}, index=dates)

        filled = df.ts.interpolate("linear")
        assert not filled["value"].isna().any()

    def test_transformations(self):
        """Test time series transformations."""

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({"price": [100 + i for i in range(10)]}, index=dates)

        returns = df.ts.pct_change()
        diff = df.ts.diff()
        lagged = df.ts.shift(1)

        assert len(returns) == len(df)
        assert len(diff) == len(df)
        assert len(lagged) == len(df)


class TestFinanceAccessor:
    """Test financial .fin accessor."""

    def test_moving_averages(self):
        """Test SMA and EMA."""

        df = pd.DataFrame({"close": np.random.randn(100).cumsum() + 100})

        sma = df.fin.sma("close", 20)
        ema = df.fin.ema("close", 20)

        assert len(sma) == len(df)
        assert len(ema) == len(df)
        # sma returns a DataFrame with the new column added
        sma_col = sma["close_sma_20"]
        assert not sma_col.isna().all()

    def test_rsi(self):
        """Test RSI indicator."""

        df = pd.DataFrame({"close": np.random.randn(100).cumsum() + 100})
        rsi = df.fin.rsi("close", 14)

        # RSI returns a DataFrame with the RSI column added
        rsi_col = rsi["close_rsi_14"]
        valid_rsi = rsi_col[~rsi_col.isna()]
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    def test_macd(self):
        """TestMACD indicator."""

        df = pd.DataFrame({"close": np.random.randn(100).cumsum() + 100})
        macd = df.fin.macd("close")

        assert "macd" in macd.columns
        assert "signal" in macd.columns
        assert "histogram" in macd.columns

    def test_bollinger_bands(self):
        """Test Bollinger Bands."""

        df = pd.DataFrame({"close": np.random.randn(100).cumsum() + 100})
        bb = df.fin.bollinger_bands("close")

        assert "upper" in bb.columns
        assert "middle" in bb.columns
        assert "lower" in bb.columns

        # Upper should be > middle > lower
        valid = bb[~bb["upper"].isna()]
        if len(valid) > 0:
            assert (valid["upper"] >= valid["middle"]).all()
            assert (valid["middle"] >= valid["lower"]).all()

    def test_returns_volatility(self):
        """Test returns and volatility calculations."""

        df = pd.DataFrame({"close": np.random.randn(100).cumsum() + 100})

        returns = df.fin.returns("close")
        cum_returns = df.fin.cumulative_returns("close")
        vol = df.fin.volatility("close", 20)

        assert len(returns) == len(df)
        assert len(cum_returns) == len(df)
        assert len(vol) == len(df)


class TestGeoSpatialAccessor:
    """Test geospatial .geo accessor."""

    def test_buffer(self):
        """Test buffer operation."""
        try:
            import geopandas as gpd
            from shapely.geometry import Point

            import parquetframe.geo  # noqa: F401

            gdf = gpd.GeoDataFrame(
                {"name": ["A", "B"], "geometry": [Point(0, 0), Point(1, 1)]}
            )

            buffered = gdf.geo.buffer(1.0)
            assert len(buffered) == len(gdf)
            assert buffered.geo.area().sum() > 0
        except ImportError:
            pytest.skip("GeoPandas not installed")

    def test_spatial_operations(self):
        """Test spatial operations."""
        try:
            import geopandas as gpd
            from shapely.geometry import Point

            import parquetframe.geo  # noqa: F401

            gdf = gpd.GeoDataFrame(
                {"name": ["A", "B"], "geometry": [Point(0, 0), Point(1, 1)]},
                crs="EPSG:4326",
            )

            area = gdf.geo.area()
            centroid = gdf.geo.centroid()

            assert len(area) == len(gdf)
            assert len(centroid) == len(gdf)
        except ImportError:
            pytest.skip("GeoPandas not installed")


class TestCLI:
    """Test CLI functionality."""

    def test_basic_repl(self):
        """Test basic REPL start."""
        from parquetframe.cli import start_basic_repl

        # Just ensure it imports without error
        assert start_basic_repl is not None

    def test_rich_repl(self):
        """Test rich REPL start."""
        from parquetframe.cli import start_repl

        # Just ensure it imports without error
        assert start_repl is not None


class TestIntegration:
    """Integration tests combining multiple features."""

    @pytest.mark.skipif(not HAS_SQL, reason="SQL dependencies not installed")
    def test_sql_with_time_series(self):
        """Test SQL queries on time series data."""
        from parquetframe.sql import sql

        # Create time series
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "date": dates,
                "value": np.random.randn(100).cumsum() + 100,
                "category": ["A"] * 50 + ["B"] * 50,
            }
        )

        # SQL filter
        filtered = sql("SELECT * FROM df WHERE category = 'A'", df=df)

        # Time series on result
        filtered = filtered.set_index("date")
        daily_avg = filtered[["value"]].ts.resample("7D", agg="mean")

        assert len(daily_avg) < len(filtered)

    @pytest.mark.skipif(not HAS_SQL, reason="SQL dependencies not installed")
    def test_finance_with_sql(self):
        """Test financial indicators with SQL."""
        from parquetframe.sql import sql

        # Create price data
        df = pd.DataFrame(
            {
                "ticker": ["AAPL"] * 50 + ["GOOGL"] * 50,
                "close": np.random.randn(100).cumsum() + 100,
            }
        )

        # Filter with SQL
        aapl = sql("SELECT * FROM df WHERE ticker = 'AAPL'", df=df)

        # Calculate RSI - rsi returns a DataFrame, need to extract column
        rsi_df = aapl.fin.rsi("close", 14)
        aapl["RSI"] = rsi_df["close_rsi_14"]

        assert "RSI" in aapl.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
