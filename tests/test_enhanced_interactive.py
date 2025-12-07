"""
Tests for enhanced interactive mode with Python execution and magic commands.
"""

from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest


@pytest.fixture
def mock_data_context():
    """Create a mock DataContext."""
    context = Mock()
    context.source_location = "./test_data"
    context.source_type = Mock(value="parquet")
    context.initialize = AsyncMock()
    context.execute = AsyncMock()
    context.get_table_names = Mock(return_value=["test_table"])
    context.get_table_schema = Mock(return_value={"columns": []})
    context.close = Mock()
    return context


@pytest.fixture
def interactive_session(mock_data_context):
    """Create an InteractiveSession for testing."""
    from parquetframe.interactive import InteractiveSession

    with (
        patch("parquetframe.interactive.PromptSession"),
        patch("parquetframe.interactive.Console"),
        patch("parquetframe.interactive.Panel"),
        patch("parquetframe.interactive.Table"),
        patch("parquetframe.interactive.HTML"),
        patch("parquetframe.interactive.InMemoryHistory"),
        patch("parquetframe.interactive.WordCompleter"),
        patch("parquetframe.interactive.INTERACTIVE_AVAILABLE", True),
    ):
        session = InteractiveSession(mock_data_context, enable_ai=False)
        yield session


class TestPythonExecution:
    """Test Python code execution in interactive mode."""

    def test_is_sql_query(self, interactive_session):
        """Test SQL detection."""
        assert interactive_session._is_sql_query("SELECT * FROM users")
        assert interactive_session._is_sql_query("INSERT INTO table VALUES")
        assert interactive_session._is_sql_query("UPDATE users SET name = 'test'")
        assert not interactive_session._is_sql_query("df = pf.read('file.parquet')")
        assert not interactive_session._is_sql_query("print('hello')")

    @pytest.mark.asyncio
    async def test_python_code_execution_expression(self, interactive_session):
        """Test Python expression evaluation."""
        # Skip if Python execution not available
        if not interactive_session.python_enabled:
            pytest.skip("Python execution not available")

        # Mock console
        interactive_session.console = Mock()

        # Execute simple expression
        await interactive_session._handle_python_code("2 + 2")

        # Should store result in _
        assert interactive_session.exec_context.has_variable("_")

    @pytest.mark.asyncio
    async def test_python_code_execution_statement(self, interactive_session):
        """Test Python statement execution."""
        if not interactive_session.python_enabled:
            pytest.skip("Python execution not available")

        interactive_session.console = Mock()

        # Execute assignment
        await interactive_session._handle_python_code("x = 42")

        # Variable should be stored
        assert interactive_session.exec_context.has_variable("x")
        assert interactive_session.exec_context.get_variable("x") == 42

    @pytest.mark.asyncio
    async def test_python_code_with_dataframe(self, interactive_session):
        """Test Python code with DataFrame."""
        if not interactive_session.python_enabled:
            pytest.skip("Python execution not available")

        interactive_session.console = Mock()

        # Create DataFrame
        code = "df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})"
        await interactive_session._handle_python_code(code)

        # Should have df variable
        assert interactive_session.exec_context.has_variable("df")
        df = interactive_session.exec_context.get_variable("df")
        assert len(df) == 3
        assert list(df.columns) == ["a", "b"]


class TestMagicCommands:
    """Test magic command functionality."""

    @pytest.mark.asyncio
    async def test_magic_info(self, interactive_session):
        """Test %info magic command."""
        if not interactive_session.python_enabled:
            pytest.skip("Python execution not available")

        interactive_session.console = Mock()

        # Create a test DataFrame
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        interactive_session.exec_context.set_variable("test_df", df)

        # Run %info
        await interactive_session._handle_magic_command("%info test_df")

        # Should have called console.print
        assert interactive_session.console.print.called

    @pytest.mark.asyncio
    async def test_magic_schema(self, interactive_session):
        """Test %schema magic command."""
        if not interactive_session.python_enabled:
            pytest.skip("Python execution not available")

        interactive_session.console = Mock()

        # Create test DataFrame
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        interactive_session.exec_context.set_variable("test_df", df)

        # Run %schema
        await interactive_session._handle_magic_command("%schema test_df")

        assert interactive_session.console.print.called

    @pytest.mark.asyncio
    async def test_magic_whos(self, interactive_session):
        """Test %whos magic command."""
        if not interactive_session.python_enabled:
            pytest.skip("Python execution not available")

        interactive_session.console = Mock()

        # Add some variables
        interactive_session.exec_context.set_variable("x", 42)
        interactive_session.exec_context.set_variable("y", "test")

        # Run %whos
        await interactive_session._handle_magic_command("%whos")

        assert interactive_session.console.print.called

    @pytest.mark.asyncio
    async def test_magic_clear(self, interactive_session):
        """Test %clear magic command."""
        if not interactive_session.python_enabled:
            pytest.skip("Python execution not available")

        interactive_session.console = Mock()

        # Add variables
        interactive_session.exec_context.set_variable("x", 42)
        interactive_session.exec_context.set_variable("y", "test")

        # Clear
        await interactive_session._handle_magic_command("%clear")

        # Variables should be gone
        assert len(interactive_session.exec_context.list_variables()) == 0

    @pytest.mark.asyncio
    async def test_magic_sql(self, interactive_session):
        """Test %sql magic command."""
        interactive_session.console = Mock()

        # Mock query handler
        interactive_session._handle_query = AsyncMock()

        # Run %sql
        await interactive_session._handle_magic_command("%sql SELECT * FROM users")

        # Should have called query handler
        interactive_session._handle_query.assert_called_once()


class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    @pytest.mark.asyncio
    async def test_meta_commands_still_work(self, interactive_session):
        r"""Test that \ meta-commands are preserved."""
        interactive_session.console = Mock()

        # Test help command
        await interactive_session._handle_meta_command("\\help")

        # Should have printed help
        assert interactive_session.console.print.called

    @pytest.mark.asyncio
    async def test_sql_queries_still_work(self, interactive_session):
        """Test that direct SQL queries still work."""
        interactive_session.console = Mock()
        interactive_session.data_context.execute = AsyncMock()

        # Execute SQL
        await interactive_session._handle_query("SELECT * FROM users")

        # Should have called data context
        interactive_session.data_context.execute.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
