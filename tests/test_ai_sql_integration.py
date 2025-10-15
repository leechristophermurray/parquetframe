"""
AI-powered SQL generation smoke tests for ParquetFrame.

This module provides smoke tests to verify that AI-generated SQL queries
work correctly with the SQL multi-format functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

import parquetframe as pqf


class TestAISQLIntegrationSmoke:
    """Smoke tests for AI-powered SQL generation integration."""

    @pytest.fixture
    def ai_test_data(self):
        """Create test data for AI SQL generation."""
        users = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "age": [25, 30, 35, 28, 32],
                "department": [
                    "Engineering",
                    "Sales",
                    "Engineering",
                    "Marketing",
                    "Sales",
                ],
                "salary": [70000, 60000, 85000, 55000, 65000],
                "active": [True, True, False, True, True],
            }
        )

        orders = pd.DataFrame(
            {
                "order_id": [101, 102, 103, 104, 105],
                "user_id": [1, 2, 1, 4, 5],
                "product": ["laptop", "mouse", "keyboard", "monitor", "headphones"],
                "amount": [1200.00, 50.00, 100.00, 350.00, 80.00],
                "order_date": pd.to_datetime(
                    [
                        "2023-01-15",
                        "2023-01-20",
                        "2023-02-01",
                        "2023-02-10",
                        "2023-02-15",
                    ]
                ),
            }
        )

        return {"users": users, "orders": orders}

    @pytest.fixture
    def ai_test_files(self, ai_test_data):
        """Create test files for AI SQL testing."""
        temp_dir = tempfile.mkdtemp()
        files = {}

        for table_name, df in ai_test_data.items():
            # Create multiple formats for comprehensive testing
            formats = {
                "parquet": lambda df, path: df.to_parquet(path),
                "csv": lambda df, path: df.to_csv(path, index=False),
                "json": lambda df, path: df.to_json(path, orient="records"),
            }

            files[table_name] = {}
            for format_name, writer in formats.items():
                file_path = Path(temp_dir) / f"{table_name}.{format_name}"
                writer(df, file_path)
                files[table_name][format_name] = file_path

        yield temp_dir, files

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_ai_agent(self):
        """Mock AI agent that returns deterministic SQL queries."""
        mock_agent = MagicMock()

        # Define deterministic query responses for different prompts
        query_responses = {
            "show all users": "SELECT * FROM df ORDER BY id",
            "count users by department": "SELECT department, COUNT(*) as user_count FROM df GROUP BY department ORDER BY user_count DESC",
            "find high salary users": "SELECT name, salary FROM df WHERE salary > 75000 ORDER BY salary DESC",
            "show user orders": """
                SELECT u.name, u.department, o.product, o.amount
                FROM df u
                JOIN orders o ON u.id = o.user_id
                ORDER BY o.amount DESC
            """,
            "average salary by department": "SELECT department, AVG(salary) as avg_salary FROM df GROUP BY department ORDER BY avg_salary DESC",
            "users without orders": """
                SELECT u.name, u.department
                FROM df u
                LEFT JOIN orders o ON u.id = o.user_id
                WHERE o.user_id IS NULL
            """,
        }

        def mock_query_generator(prompt, pf, **kwargs):
            """Generate SQL query based on prompt."""
            prompt_lower = prompt.lower().strip()

            # Find matching query response
            for key, sql in query_responses.items():
                if key in prompt_lower:
                    # Execute the query and return result
                    if "orders" in key and "orders" in kwargs:
                        result = pf.sql(sql.strip(), **kwargs)
                    else:
                        result = pf.sql(sql.strip())
                    return result

            # Default fallback query
            return pf.sql("SELECT COUNT(*) as total FROM df")

        mock_agent.query = mock_query_generator
        return mock_agent

    def test_ai_basic_query_generation_smoke(self, ai_test_files, mock_ai_agent):
        """Smoke test: AI generates basic SELECT query."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"]["parquet"])
        result = mock_ai_agent.query("show all users", pf)

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

        # Verify data is correctly ordered
        assert list(result.pandas_df["name"]) == [
            "Alice",
            "Bob",
            "Charlie",
            "Diana",
            "Eve",
        ]

    def test_ai_aggregation_query_smoke(self, ai_test_files, mock_ai_agent):
        """Smoke test: AI generates aggregation queries."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"]["csv"])  # Test with different format
        result = mock_ai_agent.query("count users by department", pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 3  # Engineering, Sales, Marketing
        assert "department" in result.pandas_df.columns
        assert "user_count" in result.pandas_df.columns

        # Verify aggregation worked correctly
        dept_counts = dict(
            zip(result.pandas_df["department"], result.pandas_df["user_count"])
        )
        assert dept_counts["Engineering"] == 2  # Charlie is inactive but still counted
        assert dept_counts["Sales"] == 2
        assert dept_counts["Marketing"] == 1

    def test_ai_filtering_query_smoke(self, ai_test_files, mock_ai_agent):
        """Smoke test: AI generates filtering queries."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"]["json"])  # Test with JSON format
        result = mock_ai_agent.query("find high salary users", pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 1  # Only Charlie has salary > 75000
        assert result.pandas_df.iloc[0]["name"] == "Charlie"
        assert result.pandas_df.iloc[0]["salary"] == 85000

    def test_ai_cross_format_join_smoke(self, ai_test_files, mock_ai_agent):
        """Smoke test: AI generates JOIN queries across different formats."""
        temp_dir, files = ai_test_files

        users_pf = pqf.read(files["users"]["parquet"])
        orders_pf = pqf.read(files["orders"]["csv"])  # Cross-format join

        result = mock_ai_agent.query("show user orders", users_pf, orders=orders_pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 5  # All orders
        assert set(result.pandas_df.columns) == {
            "name",
            "department",
            "product",
            "amount",
        }

        # Verify join worked correctly
        assert "Alice" in result.pandas_df["name"].values
        assert "laptop" in result.pandas_df["product"].values

    def test_ai_complex_analytics_smoke(self, ai_test_files, mock_ai_agent):
        """Smoke test: AI generates complex analytical queries."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"]["parquet"])
        result = mock_ai_agent.query("average salary by department", pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 3
        assert "department" in result.pandas_df.columns
        assert "avg_salary" in result.pandas_df.columns

        # Verify averages are calculated correctly
        dept_salaries = dict(
            zip(result.pandas_df["department"], result.pandas_df["avg_salary"])
        )
        assert dept_salaries["Engineering"] == 77500  # (70000 + 85000) / 2
        assert dept_salaries["Sales"] == 62500  # (60000 + 65000) / 2
        assert dept_salaries["Marketing"] == 55000

    def test_ai_left_join_analysis_smoke(self, ai_test_files, mock_ai_agent):
        """Smoke test: AI generates LEFT JOIN queries."""
        temp_dir, files = ai_test_files

        users_pf = pqf.read(files["users"]["csv"])
        orders_pf = pqf.read(files["orders"]["json"])  # Different format combination

        result = mock_ai_agent.query("users without orders", users_pf, orders=orders_pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 1  # Only Charlie has no orders (user_id = 3)
        assert result.pandas_df.iloc[0]["name"] == "Charlie"
        assert result.pandas_df.iloc[0]["department"] == "Engineering"

    @pytest.mark.skipif(
        os.getenv("OLLAMA_HOST") is None and os.getenv("OLLAMA_URL") is None,
        reason="Ollama not available - set OLLAMA_HOST or OLLAMA_URL to run real AI tests",
    )
    def test_real_ai_integration_smoke(self, ai_test_files):
        """Smoke test with real AI integration (requires Ollama)."""
        temp_dir, files = ai_test_files

        try:
            # Try to import and use real AI agent
            from parquetframe.ai import LLMAgent

            pf = pqf.read(files["users"]["parquet"])
            agent = LLMAgent(model_name="llama3.2")

            # Test simple query generation
            # Note: This is a smoke test - we just verify it doesn't crash
            # Real validation would require more complex setup

            # Mock the DataContext since we don't have a full database setup
            mock_context = MagicMock()
            mock_context.is_initialized = True
            mock_context.get_table_names.return_value = ["users"]
            mock_context.get_schema_as_text.return_value = """
                CREATE TABLE users (
                    id INTEGER,
                    name TEXT,
                    age INTEGER,
                    department TEXT,
                    salary REAL,
                    active BOOLEAN
                );
            """

            # Mock successful execution
            mock_context.execute = AsyncMock(return_value=pf._df.head())
            mock_context.validate_query = AsyncMock(return_value=True)

            # This would be the actual test in a full integration scenario
            # result = await agent.generate_query("Show me all users", mock_context)
            # assert result.success

            # For now, just verify the agent can be created
            assert agent is not None
            assert agent.model_name == "llama3.2"

        except ImportError:
            pytest.skip("LLMAgent not available")

    def test_ai_error_handling_smoke(self, ai_test_files, mock_ai_agent):
        """Smoke test: AI handles errors gracefully."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"]["parquet"])

        # Mock agent to return invalid SQL
        def error_query_generator(prompt, pf, **kwargs):
            try:
                # This should fail due to invalid column name
                return pf.sql("SELECT invalid_column FROM df")
            except Exception as e:
                # Return a fallback query
                return pf.sql("SELECT COUNT(*) as error_fallback FROM df")

        mock_ai_agent.query = error_query_generator

        result = mock_ai_agent.query("invalid query test", pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert "error_fallback" in result.pandas_df.columns
        assert result.pandas_df.iloc[0]["error_fallback"] == 5

    @pytest.mark.parametrize("format_name", ["parquet", "csv", "json"])
    def test_ai_format_independence_smoke(
        self, ai_test_files, mock_ai_agent, format_name
    ):
        """Smoke test: AI works consistently across file formats."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"][format_name])
        result = mock_ai_agent.query("count users by department", pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 3
        assert "department" in result.pandas_df.columns
        assert "user_count" in result.pandas_df.columns

        # Results should be consistent regardless of format
        total_users = result.pandas_df["user_count"].sum()
        assert total_users == 5


class TestAISQLEdgeCases:
    """Test AI SQL generation edge cases and error conditions."""

    @pytest.fixture
    def edge_case_data(self):
        """Create edge case data for testing."""
        # Data with NULL values and edge cases
        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", None, "Charlie", "", "Eve"],
                "value": [100, None, 300, 0, 500],
                "category": ["A", "B", None, "A", "B"],
                "active": [True, None, False, True, True],
            }
        )

    @pytest.fixture
    def edge_case_mock_ai_agent(self):
        """Mock AI agent for edge case testing."""
        mock_agent = MagicMock()

        # Default query generator for edge cases
        def default_query_generator(prompt, pf, **kwargs):
            return pf.sql("SELECT COUNT(*) as total FROM df")

        mock_agent.query = default_query_generator
        return mock_agent

    def test_ai_null_handling_smoke(self, edge_case_data, edge_case_mock_ai_agent):
        """Smoke test: AI handles NULL values correctly."""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "edge_case.parquet"
        edge_case_data.to_parquet(file_path)

        try:
            pf = pqf.read(file_path)

            # Mock query that handles NULLs
            def null_aware_query(prompt, pf, **kwargs):
                return pf.sql(
                    "SELECT COUNT(name) as non_null_names, COUNT(*) as total FROM df"
                )

            edge_case_mock_ai_agent.query = null_aware_query
            result = edge_case_mock_ai_agent.query("count non-null names", pf)

            assert isinstance(result, pqf.ParquetFrame)
            row = result.pandas_df.iloc[0]
            assert (
                row["non_null_names"] == 4
            )  # Alice, Charlie, "" (empty string), and Eve have non-null names
            assert row["total"] == 5  # Total count includes NULL values

        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ai_empty_result_handling_smoke(
        self, ai_test_files, edge_case_mock_ai_agent
    ):
        """Smoke test: AI handles queries with empty results."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"]["parquet"])

        def empty_result_query(prompt, pf, **kwargs):
            return pf.sql(
                "SELECT * FROM df WHERE salary > 1000000"
            )  # No users with salary > 1M

        edge_case_mock_ai_agent.query = empty_result_query
        result = edge_case_mock_ai_agent.query("find millionaire users", pf)

        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) == 0
        assert set(result.pandas_df.columns) == {
            "id",
            "name",
            "age",
            "department",
            "salary",
            "active",
        }

    def test_ai_performance_smoke(self, ai_test_files, edge_case_mock_ai_agent):
        """Smoke test: AI queries complete within reasonable time."""
        temp_dir, files = ai_test_files

        pf = pqf.read(files["users"]["parquet"])

        import time

        start_time = time.time()
        result = edge_case_mock_ai_agent.query("count users by department", pf)
        execution_time = time.time() - start_time

        # Should complete very quickly for small dataset
        assert execution_time < 1.0  # Less than 1 second
        assert isinstance(result, pqf.ParquetFrame)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
