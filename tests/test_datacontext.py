"""
Tests for DataContext architecture and implementations.

This module tests the core DataContext abstraction, factory patterns,
and the specific implementations for parquet and database sources.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from src.parquetframe.datacontext import (
    DataContext,
    DataContextError,
    DataContextFactory,
    SourceType,
)


class TestDataContextFactory:
    """Test the DataContextFactory and its dependency injection patterns."""

    def test_create_context_with_path(self):
        """Test factory creation with valid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy parquet file
            test_df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
            parquet_path = Path(temp_dir) / "test.parquet"
            test_df.to_parquet(parquet_path)

            context = DataContextFactory.create_from_path(temp_dir)

            assert context.source_type == SourceType.PARQUET
            assert context.source_location == str(Path(temp_dir).resolve())
            assert not context.is_initialized

    def test_create_context_with_nonexistent_path(self):
        """Test factory creation with nonexistent path raises error."""
        with pytest.raises(DataContextError, match="Path does not exist"):
            DataContextFactory.create_from_path("/nonexistent/path")

    def test_create_context_with_file_not_directory(self):
        """Test factory creation with file path instead of directory raises error."""
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(DataContextError, match="Path must be a directory"):
                DataContextFactory.create_from_path(temp_file.name)

    def test_create_context_with_db_uri(self):
        """Test factory creation with database URI."""
        db_uri = "sqlite:///test.db"
        context = DataContextFactory.create_from_db_uri(db_uri)

        assert context.source_type == SourceType.DATABASE
        assert context.source_location == db_uri
        assert not context.is_initialized

    def test_create_context_with_empty_db_uri(self):
        """Test factory creation with empty DB URI raises error."""
        with pytest.raises(
            DataContextError, match="Database URI must be a non-empty string"
        ):
            DataContextFactory.create_from_db_uri("")

        with pytest.raises(
            DataContextError, match="Database URI must be a non-empty string"
        ):
            DataContextFactory.create_from_db_uri(None)

    def test_create_context_mutual_exclusion(self):
        """Test that specifying both path and db_uri raises error."""
        with pytest.raises(
            DataContextError, match="Cannot specify both path and db_uri"
        ):
            DataContextFactory.create_context(path="/some/path", db_uri="sqlite:///db")

    def test_create_context_requires_one_parameter(self):
        """Test that specifying neither path nor db_uri raises error."""
        with pytest.raises(
            DataContextError, match="Must specify either path or db_uri"
        ):
            DataContextFactory.create_context()

    def test_create_context_chooses_correct_implementation(self):
        """Test that factory chooses the right implementation based on parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create dummy parquet file
            test_df = pd.DataFrame({"a": [1, 2, 3]})
            parquet_path = Path(temp_dir) / "test.parquet"
            test_df.to_parquet(parquet_path)

            # Test path-based creation
            parquet_context = DataContextFactory.create_context(path=temp_dir)
            assert parquet_context.source_type == SourceType.PARQUET

            # Test URI-based creation
            db_context = DataContextFactory.create_context(db_uri="sqlite:///test.db")
            assert db_context.source_type == SourceType.DATABASE


class TestDataContextInterface:
    """Test the DataContext abstract interface contracts."""

    def test_abstract_methods_must_be_implemented(self):
        """Test that DataContext cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DataContext("test", SourceType.PARQUET)

    def test_context_manager_protocol(self):
        """Test that DataContext implementations support context manager."""
        # We'll use a mock since DataContext is abstract
        mock_context = Mock(spec=DataContext)
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.close = Mock()

        with mock_context as ctx:
            assert ctx == mock_context

        mock_context.close.assert_called_once()


@pytest.mark.asyncio
class TestParquetDataContextIntegration:
    """Integration tests for ParquetDataContext."""

    async def test_initialization_with_single_parquet_file(self):
        """Test ParquetDataContext initialization with a single parquet file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test parquet file
            test_df = pd.DataFrame(
                {
                    "id": [1, 2, 3, 4],
                    "name": ["Alice", "Bob", "Charlie", "Diana"],
                    "age": [25, 30, 35, 28],
                    "city": ["New York", "London", "Tokyo", "Paris"],
                }
            )
            parquet_path = Path(temp_dir) / "users.parquet"
            test_df.to_parquet(parquet_path, index=False)

            # Test context creation and initialization
            context = DataContextFactory.create_from_path(temp_dir)

            # Check dependencies are available for this test
            try:
                await context.initialize()
            except DataContextError as e:
                if "PyArrow is required" in str(e):
                    pytest.skip("PyArrow not available for testing")
                elif "No query engine available" in str(e):
                    pytest.skip("No query engine (DuckDB/Polars) available for testing")
                else:
                    raise

            assert context.is_initialized

            # Test schema methods
            table_names = context.get_table_names()
            assert len(table_names) == 1
            assert table_names[0] == "parquet_data"

            schema_text = context.get_schema_as_text()
            assert "CREATE TABLE parquet_data" in schema_text
            assert "id" in schema_text
            assert "name" in schema_text
            assert "age" in schema_text
            assert "city" in schema_text

            table_schema = context.get_table_schema("parquet_data")
            assert table_schema["table_name"] == "parquet_data"
            assert table_schema["file_count"] == 1
            assert len(table_schema["columns"]) == 4

            # Test context manager
            context.close()

    async def test_initialization_with_multiple_parquet_files(self):
        """Test ParquetDataContext with multiple parquet files in subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple parquet files in different subdirectories
            (temp_path / "year=2023").mkdir()
            (temp_path / "year=2024").mkdir()

            # First file
            df1 = pd.DataFrame(
                {
                    "id": [1, 2],
                    "value": [10, 20],
                    "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02"]),
                }
            )
            df1.to_parquet(temp_path / "year=2023" / "data.parquet", index=False)

            # Second file with slightly different schema
            df2 = pd.DataFrame(
                {
                    "id": [3, 4],
                    "value": [30, 40],
                    "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                    "new_column": ["A", "B"],  # Additional column
                }
            )
            df2.to_parquet(temp_path / "year=2024" / "data.parquet", index=False)

            context = DataContextFactory.create_from_path(temp_dir)

            try:
                await context.initialize()
            except DataContextError as e:
                if "PyArrow is required" in str(
                    e
                ) or "No query engine available" in str(e):
                    pytest.skip("Required dependencies not available for testing")
                else:
                    raise

            assert context.is_initialized

            # Should discover both files
            table_schema = context.get_table_schema("parquet_data")
            assert table_schema["file_count"] == 2

            # Schema should include all columns (unified)
            column_names = [col["name"] for col in table_schema["columns"]]
            assert "id" in column_names
            assert "value" in column_names
            assert "timestamp" in column_names
            assert "new_column" in column_names  # From schema unification

            context.close()

    async def test_no_parquet_files_raises_error(self):
        """Test that empty directory raises appropriate error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            context = DataContextFactory.create_from_path(temp_dir)

            with pytest.raises(DataContextError, match="No parquet files found"):
                await context.initialize()


@pytest.mark.asyncio
class TestDatabaseDataContextIntegration:
    """Integration tests for DatabaseDataContext."""

    async def test_sqlite_initialization(self):
        """Test DatabaseDataContext with SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            db_path = temp_db.name

        try:
            # Create a simple SQLite database
            import sqlite3

            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    age INTEGER
                )
            """
            )
            conn.execute(
                "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                ("Alice", "alice@example.com", 25),
            )
            conn.execute(
                "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                ("Bob", "bob@example.com", 30),
            )
            conn.commit()
            conn.close()

            # Test DatabaseDataContext
            db_uri = f"sqlite:///{db_path}"
            context = DataContextFactory.create_from_db_uri(db_uri)

            try:
                await context.initialize()
            except DataContextError as e:
                if "SQLAlchemy is required" in str(e) or "Pandas is required" in str(e):
                    pytest.skip("Required dependencies not available for testing")
                else:
                    raise

            assert context.is_initialized

            # Test schema methods
            table_names = context.get_table_names()
            assert "users" in table_names

            schema_text = context.get_schema_as_text()
            assert "CREATE TABLE users" in schema_text
            assert "id INTEGER" in schema_text
            assert "name VARCHAR" in schema_text

            table_schema = context.get_table_schema("users")
            assert table_schema["table_name"] == "users"
            assert table_schema["source_type"] == "database"

            # Test query execution
            result = await context.execute("SELECT COUNT(*) as user_count FROM users")
            assert len(result) == 1
            assert result.iloc[0]["user_count"] == 2

            # Test query validation
            is_valid = await context.validate_query(
                "SELECT * FROM users WHERE age > 20"
            )
            assert is_valid

            is_invalid = await context.validate_query("SELECT * FROM nonexistent_table")
            assert not is_invalid

            context.close()

        finally:
            # Clean up
            Path(db_path).unlink(missing_ok=True)

    async def test_invalid_connection_uri_raises_error(self):
        """Test that invalid connection URI raises appropriate error."""
        context = DataContextFactory.create_from_db_uri("invalid://connection/string")

        with pytest.raises(DataContextError, match="Database initialization failed"):
            await context.initialize()


class TestErrorHandling:
    """Test error handling across the DataContext architecture."""

    def test_datacontext_error_inheritance(self):
        """Test that DataContextError is properly structured."""
        error = DataContextError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_factory_validation(self):
        """Test factory input validation."""
        # Test invalid path types
        with pytest.raises(DataContextError):
            DataContextFactory.create_from_path(123)  # Wrong type

        with pytest.raises(DataContextError):
            DataContextFactory.create_from_db_uri(123)  # Wrong type


if __name__ == "__main__":
    pytest.main([__file__])
