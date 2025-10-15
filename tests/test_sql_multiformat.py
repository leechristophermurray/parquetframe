"""
Tests for enhanced SQL functionality with multi-format support and optimization hints.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

import parquetframe as pqf
from parquetframe.sql import (
    QueryContext,
    parameterize_query,
    query_dataframes_from_files,
)


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "users": pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "age": [25, 30, 35, 28, 32],
                "city": ["NYC", "LA", "Chicago", "NYC", "LA"],
                "salary": [50000, 75000, 60000, 55000, 80000],
            }
        ),
        "orders": pd.DataFrame(
            {
                "id": [101, 102, 103, 104, 105],
                "user_id": [1, 2, 1, 3, 2],
                "product": ["laptop", "phone", "tablet", "laptop", "phone"],
                "amount": [1200, 800, 400, 1200, 900],
                "date": [
                    "2023-01-15",
                    "2023-01-20",
                    "2023-02-01",
                    "2023-02-15",
                    "2023-03-01",
                ],
            }
        ),
    }


@pytest.fixture
def temp_files(sample_data):
    """Create temporary files in various formats."""
    temp_dir = tempfile.mkdtemp()
    files = {}

    # Create files in different formats
    formats = {
        "csv": (".csv", lambda df, path: df.to_csv(path, index=False)),
        "json": (".json", lambda df, path: df.to_json(path, orient="records")),
        "jsonl": (
            ".jsonl",
            lambda df, path: df.to_json(path, orient="records", lines=True),
        ),
        "parquet": (".parquet", lambda df, path: df.to_parquet(path)),
        "tsv": (".tsv", lambda df, path: df.to_csv(path, index=False, sep="\t")),
    }

    # Skip ORC tests unless pyarrow with ORC is available
    try:
        import pyarrow.orc as orc

        formats["orc"] = (
            ".orc",
            lambda df, path: orc.write_table(df.to_pyarrow(), path),
        )
    except ImportError:
        pass

    for table_name, df in sample_data.items():
        files[table_name] = {}
        for format_name, (ext, writer) in formats.items():
            file_path = Path(temp_dir) / f"{table_name}{ext}"
            try:
                if format_name == "orc":
                    # Special handling for ORC
                    import pyarrow as pa

                    table = pa.Table.from_pandas(df)
                    orc.write_table(table, file_path)
                else:
                    writer(df, file_path)
                files[table_name][format_name] = file_path
            except ImportError:
                continue  # Skip formats that aren't available

    yield temp_dir, files

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


class TestQueryContext:
    """Test QueryContext optimization hints."""

    def test_default_context(self):
        """Test default QueryContext creation."""
        ctx = QueryContext()
        assert ctx.predicate_pushdown is True
        assert ctx.projection_pushdown is True
        assert ctx.enable_parallel is True
        assert ctx.memory_limit is None
        assert ctx.custom_pragmas == {}

    def test_custom_context(self):
        """Test custom QueryContext with hints."""
        ctx = QueryContext(
            predicate_pushdown=False,
            memory_limit="1GB",
            custom_pragmas={"enable_optimizer": False},
        )
        assert ctx.predicate_pushdown is False
        assert ctx.memory_limit == "1GB"
        assert ctx.custom_pragmas == {"enable_optimizer": False}

    def test_to_duckdb_pragmas(self):
        """Test converting QueryContext to DuckDB PRAGMA statements."""
        ctx = QueryContext(
            predicate_pushdown=False,
            enable_parallel=False,
            memory_limit="2GB",
            custom_pragmas={"enable_optimizer": True, "threads": 4},
        )
        pragmas = ctx.to_duckdb_pragmas()

        assert "PRAGMA enable_optimizer=false" in pragmas
        assert "PRAGMA threads=1" in pragmas
        assert "PRAGMA memory_limit='2GB'" in pragmas
        assert "PRAGMA enable_optimizer=true" in pragmas
        assert "PRAGMA threads='4'" in pragmas


class TestMultiFormatSQL:
    """Test SQL operations on different file formats."""

    @pytest.mark.parametrize("format_name", ["csv", "json", "jsonl", "parquet", "tsv"])
    def test_sql_on_different_formats(self, temp_files, format_name):
        """Test SQL queries on different file formats."""
        temp_dir, files = temp_files

        # Skip if format not available
        if format_name not in files["users"]:
            pytest.skip(f"Format {format_name} not available")

        # Test basic SQL query
        file_path = files["users"][format_name]
        pf = pqf.read(file_path)

        # Simple query
        result = pf.sql("SELECT name, age FROM df WHERE age > 30")
        assert isinstance(result, pqf.ParquetFrame)
        assert (
            len(result) == 2
        )  # Bob (30), Charlie (35), Eve (32) - but > 30, so Bob excluded
        assert set(result.pandas_df.columns) == {"name", "age"}

    def test_multi_format_join(self, temp_files):
        """Test JOIN operations between different formats."""
        temp_dir, files = temp_files

        # Skip if required formats not available
        if "csv" not in files["users"] or "json" not in files["orders"]:
            pytest.skip("Required formats not available")

        # Load files in different formats
        users_pf = pqf.read(files["users"]["csv"])
        orders_pf = pqf.read(files["orders"]["json"])

        # JOIN query
        result = users_pf.sql(
            """
            SELECT u.name, u.age, o.product, o.amount
            FROM df u
            JOIN orders o ON u.id = o.user_id
            WHERE u.age > 25
            ORDER BY o.amount DESC
        """,
            orders=orders_pf,
        )

        assert len(result) > 0
        expected_cols = {"name", "age", "product", "amount"}
        assert set(result.pandas_df.columns) == expected_cols

    def test_orc_format_sql(self, temp_files):
        """Test SQL operations on ORC files."""
        temp_dir, files = temp_files

        if "orc" not in files["users"]:
            pytest.skip("ORC format not available")

        file_path = files["users"]["orc"]
        pf = pqf.read(file_path)

        result = pf.sql("SELECT COUNT(*) as user_count FROM df")
        assert result.pandas_df.iloc[0]["user_count"] == 5


class TestQueryOptimizationHints:
    """Test SQL optimization hints and QueryContext integration."""

    def test_sql_hint_method(self, sample_data):
        """Test the sql_hint method on ParquetFrame."""
        pf = pqf.ParquetFrame(sample_data["users"])

        # Create context with hints
        ctx = pf.sql_hint(memory_limit="1GB", enable_parallel=False)
        assert isinstance(ctx, QueryContext)
        assert ctx.memory_limit == "1GB"
        assert ctx.enable_parallel is False

    def test_sql_with_context(self, sample_data):
        """Test SQL execution with QueryContext."""
        pf = pqf.ParquetFrame(sample_data["users"])

        # Create optimization context
        ctx = QueryContext(predicate_pushdown=True, memory_limit="512MB")

        # Execute query with context
        result = pf.sql("SELECT name, age FROM df WHERE age > 25", context=ctx)

        assert len(result) == 5  # All users are > 25
        assert isinstance(result, pqf.ParquetFrame)

    @patch("parquetframe.sql.duckdb")
    def test_pragma_application(self, mock_duckdb, sample_data):
        """Test that optimization hints are properly applied as PRAGMAs."""
        # Create mock connection
        mock_conn = mock_duckdb.connect.return_value
        mock_conn.execute.return_value.fetchdf.return_value = sample_data["users"]

        pf = pqf.ParquetFrame(sample_data["users"])
        ctx = QueryContext(
            enable_parallel=False,
            memory_limit="1GB",
            custom_pragmas={"enable_optimizer": True},
        )

        # Execute query with context
        result = pf.sql("SELECT * FROM df", context=ctx)

        # Verify PRAGMA statements were executed
        pragma_calls = [
            call[0][0]
            for call in mock_conn.execute.call_args_list
            if call[0][0].startswith("PRAGMA")
        ]

        assert "PRAGMA threads=1" in pragma_calls
        assert "PRAGMA memory_limit='1GB'" in pragma_calls
        assert "PRAGMA enable_optimizer=true" in pragma_calls


class TestSQLBuilder:
    """Test enhanced SQLBuilder functionality."""

    def test_sql_builder_with_hints(self, sample_data):
        """Test SQLBuilder with optimization hints."""
        pf = pqf.ParquetFrame(sample_data["users"])

        result = (
            pf.select("name", "age", "salary")
            .where("age > 25")
            .hint(memory_limit="1GB", enable_parallel=False)
            .order_by("salary DESC")
            .execute()
        )

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 5
        assert list(result.pandas_df.columns) == ["name", "age", "salary"]

    def test_fluent_api_with_profiling(self, sample_data):
        """Test fluent API with profiling enabled."""
        pf = pqf.ParquetFrame(sample_data["users"])

        result = (
            pf.select("city", "COUNT(*) as user_count", "AVG(salary) as avg_salary")
            .group_by("city")
            .having("user_count >= 1")
            .order_by("avg_salary DESC")
            .profile(True)
            .execute()
        )

        from parquetframe.sql import QueryResult

        assert isinstance(result, QueryResult)
        assert result.row_count > 0
        assert result.execution_time >= 0


class TestParameterizedQueries:
    """Test parameterized SQL queries."""

    def test_parameterize_query_function(self):
        """Test the parameterize_query utility function."""
        query_template = (
            "SELECT * FROM df WHERE age > {min_age} AND salary < {max_salary}"
        )

        result = parameterize_query(query_template, min_age=25, max_salary=70000)

        expected = "SELECT * FROM df WHERE age > 25 AND salary < 70000"
        assert result == expected

    def test_parameterized_query_execution(self, sample_data):
        """Test executing parameterized queries."""
        pf = pqf.ParquetFrame(sample_data["users"])

        result = pf.sql_with_params(
            "SELECT name, age, salary FROM df WHERE age > {min_age} AND salary < {max_salary}",
            min_age=25,
            max_salary=70000,
        )

        assert len(result) == 2  # Should match Alice (25, 50000) and Diana (28, 55000)
        assert all(age >= 25 for age in result.pandas_df["age"])
        assert all(salary < 70000 for salary in result.pandas_df["salary"])

    def test_missing_parameter_error(self, sample_data):
        """Test error handling for missing parameters."""
        pf = pqf.ParquetFrame(sample_data["users"])

        with pytest.raises(ValueError, match="Missing required parameter"):
            pf.sql_with_params(
                "SELECT * FROM df WHERE age > {min_age}",
                # min_age parameter missing
            )


class TestSQLErrorHandling:
    """Test enhanced SQL error handling."""

    def test_invalid_sql_query(self, sample_data):
        """Test handling of invalid SQL queries."""
        pf = pqf.ParquetFrame(sample_data["users"])

        with pytest.raises(ValueError, match="SQL query execution failed"):
            pf.sql("INVALID SQL QUERY")

    def test_pragma_warning_on_failure(self, sample_data):
        """Test that invalid PRAGMAs generate warnings but don't fail."""
        pf = pqf.ParquetFrame(sample_data["users"])

        ctx = QueryContext(custom_pragmas={"invalid_pragma": "invalid_value"})

        # Should generate warning but not fail
        with pytest.warns(UserWarning, match="Failed to apply optimization hint"):
            result = pf.sql("SELECT COUNT(*) FROM df", context=ctx)
            assert isinstance(result, pqf.ParquetFrame)


class TestDirectFileQuerying:
    """Test querying files directly without loading into ParquetFrame first."""

    def test_query_dataframes_from_files(self, temp_files):
        """Test querying files directly using query_dataframes_from_files."""
        temp_dir, files = temp_files

        if "csv" not in files["users"]:
            pytest.skip("CSV format not available")

        result = query_dataframes_from_files(
            files["users"]["csv"], "SELECT name, age FROM df WHERE age > 30"
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Charlie (35) and Eve (32)

    def test_direct_file_join(self, temp_files):
        """Test JOIN operations directly on files."""
        temp_dir, files = temp_files

        if "csv" not in files["users"] or "json" not in files["orders"]:
            pytest.skip("Required formats not available")

        result = query_dataframes_from_files(
            files["users"]["csv"],
            """
            SELECT u.name, o.product, o.amount
            FROM df u
            JOIN orders o ON u.id = o.user_id
            WHERE o.amount > 800
            ORDER BY o.amount DESC
            """,
            other_files={"orders": files["orders"]["json"]},
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert set(result.columns) == {"name", "product", "amount"}


@pytest.mark.integration
class TestSQLIntegration:
    """Integration tests for the complete SQL enhancement functionality."""

    def test_end_to_end_workflow(self, temp_files):
        """Test complete workflow with multiple formats and optimizations."""
        temp_dir, files = temp_files

        if "csv" not in files["users"] or "json" not in files["orders"]:
            pytest.skip("Required formats not available")

        # Load different formats
        users = pqf.read(files["users"]["csv"])
        orders = pqf.read(files["orders"]["json"])

        # Create optimization context
        ctx = users.sql_hint(
            memory_limit="512MB", predicate_pushdown=True, enable_parallel=True
        )

        # Complex query with profiling
        result = users.sql(
            """
            WITH user_stats AS (
                SELECT
                    u.city,
                    COUNT(u.id) as user_count,
                    AVG(u.age) as avg_age,
                    AVG(u.salary) as avg_salary
                FROM df u
                GROUP BY u.city
            ),
            order_stats AS (
                SELECT
                    u.city,
                    COUNT(o.id) as order_count,
                    SUM(o.amount) as total_amount
                FROM df u
                JOIN orders o ON u.id = o.user_id
                GROUP BY u.city
            )
            SELECT
                us.city,
                us.user_count,
                us.avg_age,
                us.avg_salary,
                os.order_count,
                os.total_amount
            FROM user_stats us
            JOIN order_stats os ON us.city = os.city
            ORDER BY os.total_amount DESC
        """,
            profile=True,
            context=ctx,
            orders=orders,
        )

        from parquetframe.sql import QueryResult

        assert isinstance(result, QueryResult)
        assert result.execution_time >= 0
        assert result.row_count > 0

        # Verify results make sense
        df = result.data
        assert "city" in df.columns
        assert "user_count" in df.columns
        assert "total_amount" in df.columns


if __name__ == "__main__":
    pytest.main([__file__])
