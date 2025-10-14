"""
Tests for SQL functionality in ParquetFrame.
"""

from unittest.mock import patch

import dask.dataframe as dd
import pandas as pd
import pytest

from parquetframe.core import ParquetFrame
from parquetframe.sql import explain_query, query_dataframes, validate_sql_query

# Check if DuckDB is available for skip conditions
try:
    import duckdb  # noqa: F401

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False


class TestSQLModule:
    """Test the SQL module functions directly."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        df1 = pd.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "name": ["Alice", "Bob", "Charlie", "David"],
                "age": [25, 30, 35, 40],
            }
        )
        df2 = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "city": ["New York", "London", "Tokyo"],
                "country": ["USA", "UK", "Japan"],
            }
        )
        return df1, df2

    def test_sql_availability_check(self):
        """Test that SQL availability is properly checked."""
        try:
            import duckdb  # noqa: F401

            from parquetframe.sql import DUCKDB_AVAILABLE

            assert DUCKDB_AVAILABLE
        except ImportError:
            from parquetframe.sql import DUCKDB_AVAILABLE

            assert not DUCKDB_AVAILABLE

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_basic_sql_query(self, sample_data):
        """Test basic SQL query on a single DataFrame."""
        df1, _ = sample_data

        result = query_dataframes(df1, "SELECT * FROM df WHERE age > 30")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Charlie and David
        assert list(result["name"]) == ["Charlie", "David"]

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_sql_join(self, sample_data):
        """Test SQL JOIN operation between two DataFrames."""
        df1, df2 = sample_data

        query = """
        SELECT df.name, df.age, other.city
        FROM df
        JOIN other ON df.id = other.id
        """

        result = query_dataframes(df1, query, {"other": df2})

        assert len(result) == 3  # Only IDs 1, 2, 3 have matches
        assert "name" in result.columns
        assert "age" in result.columns
        assert "city" in result.columns
        assert list(result["city"]) == ["New York", "London", "Tokyo"]

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_sql_with_dask_dataframes(self, sample_data):
        """Test SQL operations with Dask DataFrames."""
        df1, df2 = sample_data
        ddf1 = dd.from_pandas(df1, npartitions=2)
        ddf2 = dd.from_pandas(df2, npartitions=2)

        # Use warnings.catch_warnings to capture specific warning
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Capture all warnings
            result = query_dataframes(
                ddf1, "SELECT * FROM df WHERE age > 25", {"other": ddf2}
            )

            # Check that our specific UserWarning was issued
            user_warnings = [
                warning for warning in w if issubclass(warning.category, UserWarning)
            ]
            assert len(user_warnings) > 0
            assert any(
                "SQL queries on Dask DataFrames" in str(warning.message)
                for warning in user_warnings
            )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # Bob, Charlie, David

    def test_sql_query_validation(self):
        """Test SQL query validation function."""
        # Valid queries
        assert validate_sql_query("SELECT * FROM df")
        assert validate_sql_query("SELECT id, name FROM df WHERE age > 25")
        assert validate_sql_query("  SELECT * FROM df  ")  # With whitespace

        # Invalid queries
        assert not validate_sql_query("")
        assert not validate_sql_query("   ")
        assert not validate_sql_query("INVALID QUERY")

        # Dangerous queries (should warn but still validate)
        with pytest.warns(UserWarning, match="potentially destructive"):
            assert not validate_sql_query("DROP TABLE df")

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_sql_error_handling(self, sample_data):
        """Test error handling in SQL queries."""
        df1, _ = sample_data

        # Invalid SQL syntax
        with pytest.raises(ValueError, match="SQL query execution failed"):
            query_dataframes(df1, "INVALID SQL SYNTAX")

        # Reference to non-existent table
        with pytest.raises(ValueError, match="SQL query execution failed"):
            query_dataframes(df1, "SELECT * FROM nonexistent_table")

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_explain_query(self, sample_data):
        """Test query explanation functionality."""
        df1, df2 = sample_data

        plan = explain_query(df1, "SELECT * FROM df WHERE age > 30", {"other": df2})

        assert isinstance(plan, str)
        assert len(plan) > 0
        # Should contain some execution plan information (DuckDB format may vary)
        plan_upper = plan.upper()
        assert (
            "FILTER" in plan_upper
            or "PROJECTION" in plan_upper
            or "PHYSICAL_PLAN" in plan_upper
            or "PLAN" in plan_upper
        )


class TestParquetFrameSQL:
    """Test SQL functionality integrated with ParquetFrame."""

    @pytest.fixture
    def sample_parquetframes(self):
        """Create sample ParquetFrame objects for testing."""
        df1 = pd.DataFrame(
            {
                "customer_id": [1, 2, 3, 4],
                "name": ["Alice", "Bob", "Charlie", "David"],
                "age": [25, 30, 35, 40],
            }
        )
        df2 = pd.DataFrame(
            {
                "order_id": [101, 102, 103, 104, 105],
                "customer_id": [1, 1, 2, 3, 4],
                "amount": [100.0, 150.0, 200.0, 75.0, 300.0],
            }
        )

        pf1 = ParquetFrame(df1, islazy=False)
        pf2 = ParquetFrame(df2, islazy=False)

        return pf1, pf2

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_parquetframe_sql_method(self, sample_parquetframes):
        """Test the .sql() method on ParquetFrame objects."""
        customers, orders = sample_parquetframes

        # Simple query on single ParquetFrame
        result = customers.sql("SELECT * FROM df WHERE age > 30")

        assert isinstance(result, ParquetFrame)
        assert not result.islazy  # SQL results are always pandas
        assert len(result) == 2  # Charlie and David

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_parquetframe_sql_join(self, sample_parquetframes):
        """Test SQL JOIN using ParquetFrame.sql() method."""
        customers, orders = sample_parquetframes

        query = """
        SELECT c.name, c.age, SUM(o.amount) as total_orders
        FROM df c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.name, c.age
        ORDER BY total_orders DESC
        """

        result = customers.sql(query, orders=orders)

        assert isinstance(result, ParquetFrame)
        assert len(result) == 4  # All customers have orders
        assert "total_orders" in result.columns

        # David should have highest total (300.0), then Alice (250.0)
        first_row = result._df.iloc[0]
        assert first_row["name"] == "David"
        assert first_row["total_orders"] == 300.0

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_parquetframe_sql_with_dask(self, sample_parquetframes):
        """Test SQL operations with Dask-backed ParquetFrame."""
        customers, orders = sample_parquetframes

        # Convert to Dask
        customers_dask = customers.to_dask()

        # Use warnings.catch_warnings to capture specific warning
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Capture all warnings
            result = customers_dask.sql("SELECT name FROM df WHERE age >= 30")

            # Check that our specific UserWarning was issued
            user_warnings = [
                warning for warning in w if issubclass(warning.category, UserWarning)
            ]
            assert len(user_warnings) > 0
            assert any(
                "SQL queries on Dask DataFrames" in str(warning.message)
                for warning in user_warnings
            )

        assert isinstance(result, ParquetFrame)
        assert not result.islazy  # SQL results are always pandas
        assert len(result) == 3  # Bob, Charlie, David

    def test_parquetframe_sql_no_dataframe(self):
        """Test SQL method behavior when no DataFrame is loaded."""
        pf = ParquetFrame()

        with pytest.raises(ValueError, match="No dataframe loaded for SQL query"):
            pf.sql("SELECT * FROM df")

    @pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
    def test_parquetframe_sql_error_handling(self, sample_parquetframes):
        """Test error handling in ParquetFrame SQL operations."""
        customers, _ = sample_parquetframes

        # Invalid SQL
        with pytest.raises(ValueError, match="SQL query execution failed"):
            customers.sql("INVALID SQL")

        # Reference to non-existent join table
        with pytest.raises(ValueError, match="SQL query execution failed"):
            customers.sql("SELECT * FROM df JOIN nonexistent ON df.id = nonexistent.id")


@pytest.mark.skipif(not DUCKDB_AVAILABLE, reason="DuckDB not available")
class TestSQLIntegration:
    """Test SQL functionality in real-world scenarios."""

    def test_complex_aggregation(self):
        """Test complex SQL aggregation query."""
        # Sales data
        sales_df = pd.DataFrame(
            {
                "product_id": [1, 1, 2, 2, 3, 3, 1, 2],
                "region": [
                    "North",
                    "South",
                    "North",
                    "South",
                    "North",
                    "South",
                    "East",
                    "West",
                ],
                "sales_amount": [100, 150, 200, 175, 90, 110, 120, 160],
                "quantity": [10, 15, 20, 18, 9, 11, 12, 16],
            }
        )

        # Product info
        products_df = pd.DataFrame(
            {
                "product_id": [1, 2, 3],
                "product_name": ["Widget A", "Widget B", "Widget C"],
                "category": ["Electronics", "Home", "Electronics"],
            }
        )

        sales_pf = ParquetFrame(sales_df)
        products_pf = ParquetFrame(products_df)

        # Complex aggregation with JOIN
        query = """
        SELECT
            p.product_name,
            p.category,
            COUNT(*) as num_sales,
            SUM(s.sales_amount) as total_revenue,
            AVG(s.sales_amount) as avg_sale,
            SUM(s.quantity) as total_quantity
        FROM df s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.product_name, p.category
        HAVING total_revenue > 200
        ORDER BY total_revenue DESC
        """

        result = sales_pf.sql(query, products=products_pf)

        assert len(result) >= 1
        assert all(
            col in result.columns
            for col in ["product_name", "category", "total_revenue"]
        )
        # All results should have revenue > 200 due to HAVING clause
        assert all(result._df["total_revenue"] > 200)

    def test_window_functions(self):
        """Test SQL window functions."""
        df = pd.DataFrame(
            {
                "employee": ["Alice", "Bob", "Charlie", "David", "Eve"],
                "department": ["Sales", "Sales", "Engineering", "Engineering", "Sales"],
                "salary": [50000, 55000, 70000, 65000, 48000],
            }
        )

        pf = ParquetFrame(df)

        query = """
        SELECT
            employee,
            department,
            salary,
            AVG(salary) OVER (PARTITION BY department) as dept_avg_salary,
            salary - AVG(salary) OVER (PARTITION BY department) as salary_diff
        FROM df
        ORDER BY department, salary DESC
        """

        result = pf.sql(query)

        assert len(result) == 5
        assert "dept_avg_salary" in result.columns
        assert "salary_diff" in result.columns

        # Check that department averages are calculated correctly
        sales_rows = result._df[result._df["department"] == "Sales"]
        engineering_rows = result._df[result._df["department"] == "Engineering"]

        # Sales dept average: (50000 + 55000 + 48000) / 3 = 51000
        assert all(abs(row - 51000) < 1 for row in sales_rows["dept_avg_salary"])

        # Engineering dept average: (70000 + 65000) / 2 = 67500
        assert all(abs(row - 67500) < 1 for row in engineering_rows["dept_avg_salary"])


@patch("parquetframe.sql.DUCKDB_AVAILABLE", False)
def test_sql_unavailable_error():
    """Test behavior when DuckDB is not available."""
    df = pd.DataFrame({"a": [1, 2, 3]})

    with pytest.raises(ImportError, match="DuckDB is required for SQL functionality"):
        query_dataframes(df, "SELECT * FROM df")

    pf = ParquetFrame(df)
    with pytest.raises(ImportError, match="DuckDB is required for SQL functionality"):
        pf.sql("SELECT * FROM df")
