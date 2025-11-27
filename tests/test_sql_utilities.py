"""Tests for SQL query utilities and builder patterns."""

import pandas as pd
import pytest

from parquetframe.legacy import ParquetFrame
from parquetframe.sql import build_join_query, parameterize_query


class TestSQLUtilities:
    """Test SQL utility functions and patterns."""

    def test_parameterize_query_basic(self):
        """Test basic parameter substitution."""
        query = "SELECT * FROM df WHERE age > {min_age}"
        result = parameterize_query(query, min_age=25)
        assert result == "SELECT * FROM df WHERE age > 25"

    def test_parameterize_query_multiple_params(self):
        """Test multiple parameter substitution."""
        query = "SELECT * FROM df WHERE age > {min_age} AND salary < {max_salary}"
        result = parameterize_query(query, min_age=25, max_salary=100000)
        expected = "SELECT * FROM df WHERE age > 25 AND salary < 100000"
        assert result == expected

    def test_parameterize_query_string_params(self):
        """Test string parameter substitution."""
        query = "SELECT * FROM df WHERE name = '{name}' AND dept = '{dept}'"
        result = parameterize_query(query, name="John", dept="Engineering")
        expected = "SELECT * FROM df WHERE name = 'John' AND dept = 'Engineering'"
        assert result == expected

    def test_parameterize_query_missing_param(self):
        """Test error handling for missing parameters."""
        query = "SELECT * FROM df WHERE age > {min_age}"
        with pytest.raises(ValueError, match="Missing required parameter: min_age"):
            parameterize_query(query)

    def test_build_join_query_simple(self):
        """Test simple JOIN query building."""
        joins = [
            {"table": "users", "condition": "df.user_id = users.id", "type": "LEFT"}
        ]
        result = build_join_query(select_cols=["df.name", "users.email"], joins=joins)
        expected = "SELECT df.name, users.email FROM df LEFT JOIN users ON df.user_id = users.id"
        assert result == expected

    def test_build_join_query_multiple_joins(self):
        """Test multiple JOIN query building."""
        joins = [
            {"table": "users", "condition": "df.user_id = users.id", "type": "LEFT"},
            {
                "table": "departments",
                "condition": "users.dept_id = departments.id",
                "type": "INNER",
            },
        ]
        result = build_join_query(
            select_cols=["df.name", "users.email", "departments.name as dept_name"],
            joins=joins,
        )
        expected = (
            "SELECT df.name, users.email, departments.name as dept_name FROM df "
            "LEFT JOIN users ON df.user_id = users.id "
            "INNER JOIN departments ON users.dept_id = departments.id"
        )
        assert result == expected

    def test_build_join_query_with_conditions(self):
        """Test JOIN query with WHERE, GROUP BY, etc."""
        joins = [{"table": "sales", "condition": "df.id = sales.product_id"}]
        result = build_join_query(
            select_cols=["df.name", "SUM(sales.amount) as total_sales"],
            joins=joins,
            where_conditions=["sales.date >= '2023-01-01'", "df.active = TRUE"],
            group_by=["df.name"],
            having_conditions=["SUM(sales.amount) > 1000"],
            order_by=["total_sales DESC"],
            limit=10,
        )
        expected = (
            "SELECT df.name, SUM(sales.amount) as total_sales FROM df "
            "INNER JOIN sales ON df.id = sales.product_id "
            "WHERE sales.date >= '2023-01-01' AND df.active = TRUE "
            "GROUP BY df.name "
            "HAVING SUM(sales.amount) > 1000 "
            "ORDER BY total_sales DESC "
            "LIMIT 10"
        )
        assert result == expected

    def test_build_join_query_defaults(self):
        """Test JOIN query with default values."""
        result = build_join_query()
        assert result == "SELECT * FROM df"

    def test_sql_with_params_integration(self):
        """Test parameterized queries through ParquetFrame."""
        data = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie", "Diana"],
                "age": [25, 30, 35, 28],
                "salary": [50000, 60000, 75000, 55000],
            }
        )
        pf = ParquetFrame(data)

        # Test parameterized query
        result = pf.sql_with_params(
            "SELECT * FROM df WHERE age > {min_age} AND salary < {max_salary}",
            min_age=26,
            max_salary=70000,
        )

        df = result.pandas_df
        assert len(df) == 2  # Bob (30, 60000) and Diana (28, 55000)
        assert df["name"].tolist() == ["Bob", "Diana"]

    def test_sql_with_params_profiling(self):
        """Test parameterized queries with profiling."""
        data = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
            }
        )
        pf = ParquetFrame(data)

        result = pf.sql_with_params(
            "SELECT COUNT(*) as count FROM df WHERE age >= {min_age}",
            min_age=30,
            profile=True,
        )

        assert result.rows == 1
        assert result.columns == 1
        assert result.dataframe.pandas_df.iloc[0]["count"] == 2


class TestSQLBuilderJoinMethods:
    """Test the enhanced JOIN methods in SQLBuilder."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        main_data = pd.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "name": ["Alice", "Bob", "Charlie", "Diana"],
                "dept_id": [1, 2, 1, 3],
            }
        )

        dept_data = pd.DataFrame(
            {"id": [1, 2, 3], "dept_name": ["Engineering", "Sales", "Marketing"]}
        )

        return ParquetFrame(main_data), ParquetFrame(dept_data)

    def test_left_join(self, sample_data):
        """Test LEFT JOIN convenience method."""
        main_pf, dept_pf = sample_data

        result = (
            main_pf.sql_builder()
            .select("df.name", "depts.dept_name")
            .left_join(dept_pf, "df.dept_id = depts.id", "depts")
            .order_by("df.name")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 4
        assert df["name"].tolist() == ["Alice", "Bob", "Charlie", "Diana"]
        assert df["dept_name"].tolist() == [
            "Engineering",
            "Sales",
            "Engineering",
            "Marketing",
        ]

    def test_inner_join(self, sample_data):
        """Test INNER JOIN convenience method."""
        main_pf, dept_pf = sample_data

        result = (
            main_pf.sql_builder()
            .select("df.name", "depts.dept_name")
            .inner_join(dept_pf, "df.dept_id = depts.id", "depts")
            .where("depts.dept_name = 'Engineering'")
            .execute()
        )

        df = result.pandas_df
        assert len(df) == 2
        engineering_names = df["name"].tolist()
        assert "Alice" in engineering_names
        assert "Charlie" in engineering_names

    def test_right_join(self, sample_data):
        """Test RIGHT JOIN convenience method."""
        main_pf, dept_pf = sample_data

        result = (
            main_pf.sql_builder()
            .select("df.name", "depts.dept_name")
            .right_join(dept_pf, "df.dept_id = depts.id", "depts")
            .order_by("depts.dept_name")
            .execute()
        )

        df = result.pandas_df
        # All departments should be present
        dept_names = df["dept_name"].tolist()
        assert "Engineering" in dept_names
        assert "Sales" in dept_names
        assert "Marketing" in dept_names

    def test_full_join(self, sample_data):
        """Test FULL JOIN convenience method."""
        main_pf, dept_pf = sample_data

        result = (
            main_pf.select("df.name", "depts.dept_name")
            .full_join(dept_pf, "df.dept_id = depts.id", "depts")
            .execute()
        )

        df = result.pandas_df
        # Should include all records from both tables
        assert len(df) >= 4  # At least 4 from the main table

    def test_multiple_joins(self, sample_data):
        """Test chaining multiple different JOIN types."""
        main_pf, dept_pf = sample_data

        # Create another table to join
        project_data = pd.DataFrame(
            {"dept_id": [1, 2], "project_name": ["Web App", "Sales Platform"]}
        )
        project_pf = ParquetFrame(project_data)

        result = (
            main_pf.sql_builder()
            .select("df.name", "depts.dept_name", "projects.project_name")
            .left_join(dept_pf, "df.dept_id = depts.id", "depts")
            .left_join(project_pf, "depts.id = projects.dept_id", "projects")
            .where("projects.project_name IS NOT NULL")
            .execute()
        )

        df = result.pandas_df
        # Should have employees with projects
        assert len(df) > 0
        assert "project_name" in df.columns
