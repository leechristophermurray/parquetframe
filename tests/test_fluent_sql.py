"""Tests for fluent SQL API functionality."""

import pandas as pd
import pytest

from parquetframe import ParquetFrame
from parquetframe.sql import QueryResult, SQLBuilder


class TestFluentSQL:
    """Test fluent SQL API functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        data = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "age": [25, 30, 35, 28, 32],
                "salary": [50000, 60000, 75000, 55000, 70000],
                "department": [
                    "Engineering",
                    "Sales",
                    "Engineering",
                    "Sales",
                    "Engineering",
                ],
            }
        )
        return ParquetFrame(data)

    def test_select_where_chain(self, sample_data):
        """Test basic SELECT and WHERE chaining."""
        result = (
            sample_data.select("name", "age", "salary")
            .where("age > 28")
            .order_by("salary")
            .execute()
        )

        assert isinstance(result, ParquetFrame)
        df = result.pandas_df
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "salary"]
        assert df["name"].tolist() == ["Bob", "Eve", "Charlie"]

    def test_where_select_chain(self, sample_data):
        """Test starting with WHERE condition."""
        result = (
            sample_data.where("salary >= 60000")
            .select("name", "department", "salary")
            .order_by("name")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 3
        assert df["name"].tolist() == ["Bob", "Charlie", "Eve"]

    def test_group_by_aggregation(self, sample_data):
        """Test GROUP BY with aggregation."""
        result = (
            sample_data.select(
                "department", "COUNT(*) as count", "AVG(salary) as avg_salary"
            )
            .group_by("department")
            .having("count >= 2")
            .order_by("avg_salary", "DESC")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 2
        assert df.iloc[0]["department"] == "Engineering"
        assert df.iloc[0]["count"] == 3

    def test_order_by_limit(self, sample_data):
        """Test ORDER BY with LIMIT."""
        result = (
            sample_data.order_by("age", "DESC").select("name", "age").limit(2).execute()
        )

        df = result.pandas_df
        assert len(df) == 2
        assert df.iloc[0]["name"] == "Charlie"  # Age 35
        assert df.iloc[1]["name"] == "Eve"  # Age 32

    def test_group_by_entry_point(self, sample_data):
        """Test starting query with GROUP BY."""
        result = (
            sample_data.group_by("department")
            .select("department", "COUNT(*) as employee_count")
            .order_by("employee_count", "DESC")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 2
        assert df.iloc[0]["department"] == "Engineering"
        assert df.iloc[0]["employee_count"] == 3

    def test_profiling_and_caching(self, sample_data):
        """Test profiling and caching functionality."""
        # First query with profiling and caching
        result1 = (
            sample_data.select("name", "salary")
            .where("age BETWEEN 25 AND 32")
            .order_by("salary", "DESC")
            .profile(True)
            .cache(True)
            .execute()
        )

        assert isinstance(result1, QueryResult)
        assert result1.rows == 4
        assert result1.columns == 2
        assert not result1.cached  # First time, not from cache
        assert result1.execution_time > 0

        # Same query again should be cached
        result2 = (
            sample_data.select("name", "salary")
            .where("age BETWEEN 25 AND 32")
            .order_by("salary", "DESC")
            .profile(True)
            .cache(True)
            .execute()
        )

        assert result2.cached  # Should be from cache now
        assert result2.rows == 4
        assert result2.columns == 2

        # Check that dataframes are equivalent
        pd.testing.assert_frame_equal(
            result1.dataframe.pandas_df, result2.dataframe.pandas_df
        )

    def test_multiple_where_conditions(self, sample_data):
        """Test multiple WHERE conditions."""
        result = (
            sample_data.select("name", "age", "salary")
            .where("age > 25")
            .where("salary < 70000")
            .order_by("age")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 2  # Diana (28, 55000) and Bob (30, 60000)
        assert df.iloc[0]["name"] == "Diana"
        assert df.iloc[1]["name"] == "Bob"

    def test_join_capability(self, sample_data):
        """Test JOIN capability with fluent API."""
        # Create second dataset
        data2 = pd.DataFrame(
            {
                "department": ["Engineering", "Sales", "Marketing"],
                "budget": [1000000, 500000, 300000],
            }
        )
        pf2 = ParquetFrame(data2)

        result = (
            sample_data.select("df.name", "df.department", "other.budget")
            .join(pf2, "df.department = other.department", join_type="INNER")
            .where("other.budget > 400000")
            .order_by("df.name")
            .execute()
        )

        df = result.pandas_df
        assert len(df) > 0
        assert "budget" in df.columns

    def test_sql_builder_direct(self, sample_data):
        """Test using SQLBuilder directly."""
        builder = SQLBuilder(sample_data)
        result = (
            builder.select("name", "age")
            .where("age > 30")
            .order_by("age", "DESC")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 2  # Charlie (35) and Eve (32)
        assert df.iloc[0]["name"] == "Charlie"
        assert df.iloc[1]["name"] == "Eve"

    def test_query_result_properties(self, sample_data):
        """Test QueryResult convenience properties."""
        result = sample_data.select("*").profile(True).execute()

        assert isinstance(result, QueryResult)
        assert result.rows == 5
        assert result.columns == 4
        assert result.memory_usage_mb >= 0
        assert not result.cached
        assert isinstance(result.dataframe, ParquetFrame)

        # Test summary method
        summary = result.summary()
        assert "Query executed" in summary
        assert "rows × 4 columns" in summary
        assert "Memory usage" in summary

    def test_empty_result(self, sample_data):
        """Test handling of empty query results."""
        result = (
            sample_data.select("*")
            .where("age > 100")  # No one is older than 100
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 0
        assert list(df.columns) == ["name", "age", "salary", "department"]

    def test_complex_aggregation_chain(self, sample_data):
        """Test complex aggregation chain."""
        result = (
            sample_data.select(
                "department",
                "COUNT(*) as employee_count",
                "AVG(salary) as avg_salary",
                "MIN(age) as min_age",
                "MAX(age) as max_age",
            )
            .group_by("department")
            .having("employee_count > 1")
            .order_by("avg_salary", "DESC")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 2
        assert all(
            col in df.columns
            for col in [
                "department",
                "employee_count",
                "avg_salary",
                "min_age",
                "max_age",
            ]
        )

        # Engineering should have higher average salary
        eng_row = df[df["department"] == "Engineering"].iloc[0]
        sales_row = df[df["department"] == "Sales"].iloc[0]
        assert eng_row["avg_salary"] > sales_row["avg_salary"]
