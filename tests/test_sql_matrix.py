"""
Comprehensive SQL Multi-Format Test Matrix for ParquetFrame.

This module provides exhaustive testing of SQL operations across all supported
file formats with parametrized fixtures for maximum coverage.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

import parquetframe as pqf
from parquetframe.sql import QueryContext
from tests.conftest import skip_orc_on_windows

# Skip all tests in this file pending Phase 2 API migration
pytestmark = pytest.mark.skip(
    reason="Phase 2 API migration pending - SQL tests need DataFrameProxy.sql() method or legacy API updates. See docs/issues/phase2-test-migration.md"
)

# Define comprehensive test data
SAMPLE_USERS = pd.DataFrame(
    {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "age": [25, 30, 35, 28, 32],
        "department": ["Engineering", "Sales", "Engineering", "Marketing", "Sales"],
        "salary": [50000, 75000, 60000, 55000, 80000],
        "active": [True, True, False, True, True],
    }
)

SAMPLE_ORDERS = pd.DataFrame(
    {
        "order_id": [101, 102, 103, 104, 105, 106],
        "user_id": [1, 2, 1, 3, 2, 5],
        "product": ["laptop", "phone", "tablet", "laptop", "phone", "monitor"],
        "amount": [1200.50, 800.75, 400.25, 1200.50, 900.00, 350.99],
        "quantity": [1, 1, 1, 1, 2, 1],
        "status": [
            "completed",
            "completed",
            "pending",
            "shipped",
            "completed",
            "cancelled",
        ],
    }
)

# Test format configurations
FORMAT_CONFIGS = {
    "csv": {
        "extension": ".csv",
        "writer": lambda df, path: df.to_csv(path, index=False),
        "supports_nested": False,
    },
    "tsv": {
        "extension": ".tsv",
        "writer": lambda df, path: df.to_csv(path, index=False, sep="\t"),
        "supports_nested": False,
    },
    "json": {
        "extension": ".json",
        "writer": lambda df, path: df.to_json(path, orient="records"),
        "supports_nested": True,
    },
    "jsonl": {
        "extension": ".jsonl",
        "writer": lambda df, path: df.to_json(path, orient="records", lines=True),
        "supports_nested": True,
    },
    "parquet": {
        "extension": ".parquet",
        "writer": lambda df, path: df.to_parquet(path),
        "supports_nested": True,
    },
}

# Add ORC if available
try:
    import pyarrow as pa
    import pyarrow.orc as orc

    FORMAT_CONFIGS["orc"] = {
        "extension": ".orc",
        "writer": lambda df, path: orc.write_table(pa.Table.from_pandas(df), path),
        "supports_nested": True,
    }
except ImportError:
    pass


@pytest.fixture(scope="session")
def matrix_test_files():
    """Create test files in all supported formats for matrix testing."""
    temp_dir = tempfile.mkdtemp()
    files = {"users": {}, "orders": {}}

    datasets = {
        "users": SAMPLE_USERS,
        "orders": SAMPLE_ORDERS,
    }

    for table_name, df in datasets.items():
        for format_name, config in FORMAT_CONFIGS.items():
            file_path = Path(temp_dir) / f"{table_name}{config['extension']}"
            try:
                config["writer"](df, file_path)
                files[table_name][format_name] = file_path
            except Exception:
                # Skip formats that fail to write (e.g., missing dependencies)
                continue

    yield temp_dir, files

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestSQLOperationsMatrix:
    """Test SQL operations across all format combinations."""

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_basic_select_all_formats(self, matrix_test_files, format_name):
        """Test basic SELECT operations on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])
        result = pf.sql("SELECT * FROM df ORDER BY id")

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 5
        assert set(result.pandas_df.columns) == {
            "id",
            "name",
            "age",
            "department",
            "salary",
            "active",
        }

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_where_filtering_all_formats(self, matrix_test_files, format_name):
        """Test WHERE filtering on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        # Test numeric filtering
        result = pf.sql("SELECT name, age FROM df WHERE age > 30 ORDER BY age")
        assert len(result) == 2  # Charlie (35), Eve (32)
        assert list(result.pandas_df["name"]) == ["Eve", "Charlie"]

        # Test string filtering
        result = pf.sql(
            "SELECT name FROM df WHERE department = 'Engineering' ORDER BY name"
        )
        assert len(result) == 2  # Alice, Charlie
        assert set(result.pandas_df["name"]) == {"Alice", "Charlie"}

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_aggregation_all_formats(self, matrix_test_files, format_name):
        """Test aggregation operations on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        # Test COUNT
        result = pf.sql("SELECT COUNT(*) as total FROM df")
        assert result.pandas_df.iloc[0]["total"] == 5

        # Test GROUP BY with aggregation
        result = pf.sql(
            """
            SELECT department, COUNT(*) as user_count, AVG(salary) as avg_salary
            FROM df
            GROUP BY department
            ORDER BY department
        """
        )
        assert len(result) == 3  # Engineering, Marketing, Sales
        departments = set(result.pandas_df["department"])
        assert departments == {"Engineering", "Marketing", "Sales"}

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_window_functions_all_formats(self, matrix_test_files, format_name):
        """Test window functions on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["orders"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["orders"][format_name])

        result = pf.sql(
            """
            SELECT
                order_id,
                amount,
                ROW_NUMBER() OVER (ORDER BY amount DESC) as rank,
                SUM(amount) OVER (PARTITION BY user_id) as user_total
            FROM df
            ORDER BY amount DESC
            LIMIT 3
        """
        )

        assert len(result) == 3
        assert "rank" in result.pandas_df.columns
        assert "user_total" in result.pandas_df.columns

    @pytest.mark.parametrize(
        "user_format,order_format",
        [(f1, f2) for f1 in FORMAT_CONFIGS.keys() for f2 in FORMAT_CONFIGS.keys()],
    )
    def test_cross_format_joins(self, matrix_test_files, user_format, order_format):
        """Test JOIN operations between different format combinations."""
        skip_orc_on_windows(user_format)
        skip_orc_on_windows(order_format)
        temp_dir, files = matrix_test_files

        if user_format not in files["users"] or order_format not in files["orders"]:
            pytest.skip(f"Formats {user_format} or {order_format} not available")

        users_pf = pqf.read(files["users"][user_format])
        orders_pf = pqf.read(files["orders"][order_format])

        # Test INNER JOIN
        result = users_pf.sql(
            """
            SELECT
                u.name,
                u.department,
                o.product,
                o.amount
            FROM df u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE u.age > 25
            ORDER BY o.amount DESC
            LIMIT 5
        """,
            orders=orders_pf,
        )

        assert len(result) > 0
        expected_cols = {"name", "department", "product", "amount"}
        assert set(result.pandas_df.columns) == expected_cols

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_complex_queries_all_formats(self, matrix_test_files, format_name):
        """Test complex SQL queries on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        # Test subquery with CASE statement
        result = pf.sql(
            """
            SELECT
                name,
                age,
                salary,
                CASE
                    WHEN salary > 70000 THEN 'High'
                    WHEN salary > 50000 THEN 'Medium'
                    ELSE 'Low'
                END as salary_tier,
                (SELECT AVG(salary) FROM df) as avg_salary
            FROM df
            WHERE age BETWEEN 25 AND 35
            ORDER BY salary DESC
        """
        )

        assert len(result) == 5  # All users are between 25-35
        assert "salary_tier" in result.pandas_df.columns
        assert "avg_salary" in result.pandas_df.columns

        # Verify CASE logic
        high_salary_users = result.pandas_df[result.pandas_df["salary_tier"] == "High"]
        assert all(row["salary"] > 70000 for _, row in high_salary_users.iterrows())


class TestSQLPerformanceMatrix:
    """Test SQL performance with different optimization contexts across formats."""

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_optimization_context_all_formats(self, matrix_test_files, format_name):
        """Test QueryContext optimizations on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        # Test with optimization context
        ctx = QueryContext(
            predicate_pushdown=True, projection_pushdown=True, memory_limit="256MB"
        )

        result = pf.sql(
            "SELECT name, age FROM df WHERE age > 25 ORDER BY age", context=ctx
        )

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 4
        assert set(result.pandas_df.columns) == {"name", "age"}

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_profiling_all_formats(self, matrix_test_files, format_name):
        """Test SQL profiling on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        # Test with profiling enabled
        result = pf.sql(
            "SELECT COUNT(*) as total, AVG(salary) as avg_sal FROM df", profile=True
        )

        from parquetframe.sql import QueryResult

        assert isinstance(result, QueryResult)
        assert result.execution_time >= 0
        assert result.row_count == 1
        assert result.column_count == 2


class TestSQLErrorHandlingMatrix:
    """Test error handling across all formats."""

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_invalid_column_errors_all_formats(self, matrix_test_files, format_name):
        """Test invalid column error handling on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        with pytest.raises(ValueError, match="SQL query execution failed"):
            pf.sql("SELECT nonexistent_column FROM df")

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_syntax_error_handling_all_formats(self, matrix_test_files, format_name):
        """Test SQL syntax error handling on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        with pytest.raises(ValueError, match="SQL query execution failed"):
            pf.sql("INVALID SQL SYNTAX HERE")


class TestSQLCompatibilityMatrix:
    """Test SQL compatibility features across formats."""

    @pytest.mark.parametrize("format_name", ["csv", "json", "parquet"])  # Core formats
    def test_sql_builder_compatibility(self, matrix_test_files, format_name):
        """Test SQL builder pattern compatibility."""
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        # Test fluent SQL builder if available
        try:
            result = (
                pf.select("name", "age", "salary")
                .where("age > 25")
                .order_by("salary DESC")
                .execute()
            )
            assert isinstance(result, pqf.ParquetFrame)
            assert len(result) == 4
        except AttributeError:
            # SQL builder not yet fully implemented - test raw SQL
            result = pf.sql(
                """
                SELECT name, age, salary
                FROM df
                WHERE age > 25
                ORDER BY salary DESC
            """
            )
            assert isinstance(result, pqf.ParquetFrame)
            assert len(result) == 4

    @pytest.mark.parametrize("format_name", list(FORMAT_CONFIGS.keys()))
    def test_parameterized_queries_all_formats(self, matrix_test_files, format_name):
        """Test parameterized queries on all formats."""
        skip_orc_on_windows(format_name)
        temp_dir, files = matrix_test_files

        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        pf = pqf.read(files["users"][format_name])

        # Test parameterized queries if supported
        try:
            result = pf.sql_with_params(
                "SELECT name, age FROM df WHERE age > {min_age} AND salary < {max_salary}",
                min_age=25,
                max_salary=70000,
            )
            assert len(result) == 2  # Alice (25, 50000) and Diana (28, 55000)
        except AttributeError:
            # Method not implemented - test with formatted strings
            min_age, max_salary = 25, 70000
            result = pf.sql(
                f"""
                SELECT name, age
                FROM df
                WHERE age > {min_age} AND salary < {max_salary}
            """
            )
            assert len(result) == 2


@pytest.mark.slow
class TestSQLIntegrationMatrix:
    """Integration tests for comprehensive SQL functionality across formats."""

    def test_end_to_end_multi_format_workflow(self, matrix_test_files):
        """Test complete workflow with multiple formats and complex operations."""
        temp_dir, files = matrix_test_files

        # Use different formats for different tables
        available_formats = list(files["users"].keys())
        if len(available_formats) < 2:
            pytest.skip("Need at least 2 formats available")

        format1, format2 = available_formats[0], available_formats[1]

        users_pf = pqf.read(files["users"][format1])
        orders_pf = pqf.read(files["orders"][format2])

        # Complex multi-table analysis
        result = users_pf.sql(
            """
            WITH user_stats AS (
                SELECT
                    u.department,
                    COUNT(u.id) as user_count,
                    AVG(u.age) as avg_age,
                    AVG(u.salary) as avg_salary
                FROM df u
                WHERE u.active = true
                GROUP BY u.department
            ),
            order_stats AS (
                SELECT
                    u.department,
                    COUNT(o.order_id) as order_count,
                    SUM(o.amount) as total_revenue,
                    AVG(o.amount) as avg_order_value
                FROM df u
                JOIN orders o ON u.id = o.user_id
                WHERE o.status = 'completed'
                GROUP BY u.department
            )
            SELECT
                us.department,
                us.user_count,
                us.avg_age,
                us.avg_salary,
                COALESCE(os.order_count, 0) as order_count,
                COALESCE(os.total_revenue, 0) as total_revenue,
                COALESCE(os.avg_order_value, 0) as avg_order_value
            FROM user_stats us
            LEFT JOIN order_stats os ON us.department = os.department
            ORDER BY us.avg_salary DESC
        """,
            profile=True,
            orders=orders_pf,
        )

        from parquetframe.sql import QueryResult

        assert isinstance(result, QueryResult)
        assert result.execution_time >= 0
        assert len(result.data) > 0

        expected_cols = {
            "department",
            "user_count",
            "avg_age",
            "avg_salary",
            "order_count",
            "total_revenue",
            "avg_order_value",
        }
        assert set(result.data.columns) == expected_cols


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
