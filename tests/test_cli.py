"""
Tests for CLI functionality.

This module provides comprehensive testing for the command-line interface, including:
- Command parsing and argument validation
- Different command modes (interactive, query, deps)
- Error handling and user feedback
- Integration with underlying components
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from src.parquetframe.cli import cli
from src.parquetframe.exceptions import DataSourceError, DependencyError


class TestCLICommandParsing:
    """Test CLI command parsing and argument validation."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_help_command(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "ParquetFrame" in result.output
        assert "query" in result.output
        assert "interactive" in result.output
        assert "deps" in result.output

    def test_version_command(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_query_command_help(self):
        """Test query subcommand help."""
        result = self.runner.invoke(cli, ["query", "--help"])

        assert result.exit_code == 0
        assert "Execute SQL query" in result.output
        assert "--path" in result.output
        assert "--db-uri" in result.output

    def test_interactive_command_help(self):
        """Test interactive subcommand help."""
        result = self.runner.invoke(cli, ["interactive", "--help"])

        assert result.exit_code == 0
        assert "Start interactive" in result.output
        assert "--path" in result.output
        assert "--db-uri" in result.output

    def test_deps_command_help(self):
        """Test deps subcommand help."""
        result = self.runner.invoke(cli, ["deps", "--help"])

        assert result.exit_code == 0
        assert "Check dependencies" in result.output


class TestQueryCommand:
    """Test query command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_query_command_missing_arguments(self):
        """Test query command with missing required arguments."""
        result = self.runner.invoke(cli, ["query", "SELECT * FROM users"])

        assert result.exit_code != 0
        assert "specify either --path or --db-uri" in result.output

    def test_query_command_conflicting_arguments(self, temp_parquet_dir):
        """Test query command with conflicting path and db-uri arguments."""
        result = self.runner.invoke(
            cli,
            [
                "query",
                "--path",
                str(temp_parquet_dir),
                "--db-uri",
                "sqlite:///test.db",
                "SELECT * FROM users",
            ],
        )

        assert result.exit_code != 0
        assert "Cannot specify both" in result.output

    def test_query_command_invalid_path(self):
        """Test query command with invalid path."""
        result = self.runner.invoke(
            cli, ["query", "--path", "/nonexistent/path", "SELECT * FROM users"]
        )

        assert result.exit_code != 0
        assert "does not exist" in result.output

    @patch("src.parquetframe.cli.DataContextFactory")
    def test_query_command_success(self, mock_factory, temp_parquet_dir):
        """Test successful query command execution."""
        # Mock DataContext
        mock_context = MagicMock()
        mock_context.initialize = AsyncMock()
        mock_context.execute = AsyncMock(return_value=MagicMock())
        mock_context.close = MagicMock()
        mock_factory.create_from_path.return_value = mock_context

        result = self.runner.invoke(
            cli, ["query", "--path", str(temp_parquet_dir), "SELECT * FROM users"]
        )

        assert result.exit_code == 0
        mock_factory.create_from_path.assert_called_once_with(str(temp_parquet_dir))
        mock_context.initialize.assert_called_once()
        mock_context.execute.assert_called_once_with("SELECT * FROM users")
        mock_context.close.assert_called_once()

    @patch("src.parquetframe.cli.DataContextFactory")
    def test_query_command_with_database_uri(self, mock_factory):
        """Test query command with database URI."""
        # Mock DataContext
        mock_context = MagicMock()
        mock_context.initialize = AsyncMock()
        mock_context.execute = AsyncMock(return_value=MagicMock())
        mock_context.close = MagicMock()
        mock_factory.create_from_db_uri.return_value = mock_context

        result = self.runner.invoke(
            cli, ["query", "--db-uri", "sqlite:///test.db", "SELECT * FROM users"]
        )

        assert result.exit_code == 0
        mock_factory.create_from_db_uri.assert_called_once_with("sqlite:///test.db")

    @patch("src.parquetframe.cli.DataContextFactory")
    def test_query_command_initialization_error(self, mock_factory, temp_parquet_dir):
        """Test query command with context initialization error."""
        # Mock DataContext that fails initialization
        mock_context = MagicMock()
        mock_context.initialize = AsyncMock(
            side_effect=DataSourceError("Initialization failed", "path")
        )
        mock_context.close = MagicMock()
        mock_factory.create_from_path.return_value = mock_context

        result = self.runner.invoke(
            cli, ["query", "--path", str(temp_parquet_dir), "SELECT * FROM users"]
        )

        assert result.exit_code != 0
        assert "Initialization failed" in result.output

    @patch("src.parquetframe.cli.DataContextFactory")
    def test_query_command_query_execution_error(self, mock_factory, temp_parquet_dir):
        """Test query command with query execution error."""
        # Mock DataContext that fails query execution
        mock_context = MagicMock()
        mock_context.initialize = AsyncMock()
        mock_context.execute = AsyncMock(side_effect=Exception("Query failed"))
        mock_context.close = MagicMock()
        mock_factory.create_from_path.return_value = mock_context

        result = self.runner.invoke(
            cli, ["query", "--path", str(temp_parquet_dir), "SELECT * FROM users"]
        )

        assert result.exit_code != 0
        assert "Query failed" in result.output

    @patch("src.parquetframe.cli.DataContextFactory")
    def test_query_command_with_ai_flag(
        self, mock_factory, temp_parquet_dir, mock_ollama_module, mock_ollama_client
    ):
        """Test query command with AI flag enabled."""
        # Mock DataContext
        mock_context = MagicMock()
        mock_context.initialize = AsyncMock()
        mock_context.close = MagicMock()
        mock_factory.create_from_path.return_value = mock_context

        # Mock successful AI response
        mock_ollama_client.chat.return_value = {
            "message": {"content": "SELECT * FROM users;"}
        }

        # Mock AI agent
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.query = "SELECT * FROM users;"
        mock_result.result = MagicMock()

        with patch("src.parquetframe.cli.LLMAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.generate_query = AsyncMock(return_value=mock_result)
            mock_agent_class.return_value = mock_agent

            result = self.runner.invoke(
                cli,
                ["query", "--path", str(temp_parquet_dir), "--ai", "show me all users"],
            )

            assert result.exit_code == 0
            mock_agent.generate_query.assert_called_once()

    def test_query_command_ai_without_ollama(self, temp_parquet_dir):
        """Test query command with AI flag when ollama is not available."""
        with patch(
            "src.parquetframe.cli.LLMAgent",
            side_effect=DependencyError("ollama", "AI queries"),
        ):
            result = self.runner.invoke(
                cli,
                ["query", "--path", str(temp_parquet_dir), "--ai", "show me all users"],
            )

            assert result.exit_code != 0
            assert "Missing dependency" in result.output


class TestInteractiveCommand:
    """Test interactive command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_interactive_command_missing_arguments(self):
        """Test interactive command with missing required arguments."""
        result = self.runner.invoke(cli, ["interactive"])

        assert result.exit_code != 0
        assert "specify either --path or --db-uri" in result.output

    def test_interactive_command_conflicting_arguments(self, temp_parquet_dir):
        """Test interactive command with conflicting arguments."""
        result = self.runner.invoke(
            cli,
            [
                "interactive",
                "--path",
                str(temp_parquet_dir),
                "--db-uri",
                "sqlite:///test.db",
            ],
        )

        assert result.exit_code != 0
        assert "Cannot specify both" in result.output

    @patch("src.parquetframe.cli.InteractiveShell")
    def test_interactive_command_success(self, mock_shell_class, temp_parquet_dir):
        """Test successful interactive command execution."""
        # Mock InteractiveShell
        mock_shell = MagicMock()
        mock_shell.run = AsyncMock()
        mock_shell_class.return_value = mock_shell

        result = self.runner.invoke(
            cli, ["interactive", "--path", str(temp_parquet_dir)]
        )

        assert result.exit_code == 0
        mock_shell_class.assert_called_once_with(str(temp_parquet_dir), ai_enabled=True)
        mock_shell.run.assert_called_once()

    @patch("src.parquetframe.cli.InteractiveShell")
    def test_interactive_command_with_database_uri(self, mock_shell_class):
        """Test interactive command with database URI."""
        # Mock InteractiveShell
        mock_shell = MagicMock()
        mock_shell.run = AsyncMock()
        mock_shell_class.return_value = mock_shell

        result = self.runner.invoke(
            cli, ["interactive", "--db-uri", "sqlite:///test.db"]
        )

        assert result.exit_code == 0
        mock_shell_class.assert_called_once_with("sqlite:///test.db", ai_enabled=True)

    @patch("src.parquetframe.cli.InteractiveShell")
    def test_interactive_command_ai_disabled(self, mock_shell_class, temp_parquet_dir):
        """Test interactive command with AI disabled."""
        # Mock InteractiveShell
        mock_shell = MagicMock()
        mock_shell.run = AsyncMock()
        mock_shell_class.return_value = mock_shell

        result = self.runner.invoke(
            cli, ["interactive", "--path", str(temp_parquet_dir), "--no-ai"]
        )

        assert result.exit_code == 0
        mock_shell_class.assert_called_once_with(
            str(temp_parquet_dir), ai_enabled=False
        )

    @patch("src.parquetframe.cli.InteractiveShell")
    def test_interactive_command_initialization_error(
        self, mock_shell_class, temp_parquet_dir
    ):
        """Test interactive command with initialization error."""
        # Mock InteractiveShell that fails
        mock_shell_class.side_effect = DataSourceError("Invalid path", "path")

        result = self.runner.invoke(
            cli, ["interactive", "--path", str(temp_parquet_dir)]
        )

        assert result.exit_code != 0
        assert "Invalid path" in result.output

    @patch("src.parquetframe.cli.InteractiveShell")
    def test_interactive_command_runtime_error(
        self, mock_shell_class, temp_parquet_dir
    ):
        """Test interactive command with runtime error."""
        # Mock InteractiveShell that fails during run
        mock_shell = MagicMock()
        mock_shell.run = AsyncMock(side_effect=Exception("Runtime error"))
        mock_shell_class.return_value = mock_shell

        result = self.runner.invoke(
            cli, ["interactive", "--path", str(temp_parquet_dir)]
        )

        assert result.exit_code != 0
        assert "Runtime error" in result.output


class TestDepsCommand:
    """Test deps command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @patch("src.parquetframe.cli.check_dependencies")
    def test_deps_command_success(self, mock_check_deps):
        """Test successful deps command execution."""
        # Mock dependency check results
        mock_check_deps.return_value = {
            "pandas": {"available": True, "version": "1.5.0"},
            "pyarrow": {"available": True, "version": "10.0.0"},
            "duckdb": {"available": False, "install_cmd": "pip install duckdb"},
            "ollama": {"available": False, "install_cmd": "pip install ollama"},
        }

        result = self.runner.invoke(cli, ["deps"])

        assert result.exit_code == 0
        assert "pandas" in result.output
        assert "pyarrow" in result.output
        assert "duckdb" in result.output
        assert "ollama" in result.output
        assert "✓" in result.output  # Available dependencies
        assert "✗" in result.output  # Missing dependencies

    @patch("src.parquetframe.cli.check_dependencies")
    def test_deps_command_all_available(self, mock_check_deps):
        """Test deps command when all dependencies are available."""
        # Mock all dependencies as available
        mock_check_deps.return_value = {
            "pandas": {"available": True, "version": "1.5.0"},
            "pyarrow": {"available": True, "version": "10.0.0"},
            "duckdb": {"available": True, "version": "0.8.0"},
            "polars": {"available": True, "version": "0.18.0"},
            "ollama": {"available": True, "version": "0.1.7"},
        }

        result = self.runner.invoke(cli, ["deps"])

        assert result.exit_code == 0
        assert "All dependencies are available" in result.output

    @patch("src.parquetframe.cli.check_dependencies")
    def test_deps_command_missing_core_dependencies(self, mock_check_deps):
        """Test deps command when core dependencies are missing."""
        # Mock core dependencies as missing
        mock_check_deps.return_value = {
            "pandas": {"available": False, "install_cmd": "pip install pandas"},
            "pyarrow": {"available": False, "install_cmd": "pip install pyarrow"},
        }

        result = self.runner.invoke(cli, ["deps"])

        assert result.exit_code == 0
        assert "Missing core dependencies" in result.output
        assert "pip install pandas" in result.output
        assert "pip install pyarrow" in result.output

    @patch("src.parquetframe.cli.check_dependencies")
    def test_deps_command_with_error(self, mock_check_deps):
        """Test deps command when dependency check fails."""
        mock_check_deps.side_effect = Exception("Dependency check failed")

        result = self.runner.invoke(cli, ["deps"])

        assert result.exit_code != 0
        assert "Error checking dependencies" in result.output


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.mark.integration
    def test_full_query_workflow(self, temp_parquet_dir):
        """Test complete query workflow through CLI."""
        # This test requires actual dependencies and data
        result = self.runner.invoke(
            cli,
            [
                "query",
                "--path",
                str(temp_parquet_dir),
                "SELECT COUNT(*) as count FROM parquet_data",
            ],
        )

        # May fail due to missing dependencies, but should handle gracefully
        if result.exit_code != 0:
            assert any(
                phrase in result.output
                for phrase in [
                    "PyArrow is required",
                    "No query engine available",
                    "does not exist",
                ]
            )

    @pytest.mark.integration
    @patch("builtins.input", side_effect=["\\quit"])
    def test_full_interactive_workflow(self, mock_input, temp_parquet_dir):
        """Test complete interactive workflow through CLI."""
        result = self.runner.invoke(
            cli, ["interactive", "--path", str(temp_parquet_dir)]
        )

        # May fail due to missing dependencies or immediate quit
        if result.exit_code != 0:
            assert any(
                phrase in result.output
                for phrase in [
                    "PyArrow is required",
                    "No query engine available",
                    "does not exist",
                ]
            )

    def test_cli_error_handling(self):
        """Test CLI error handling for various scenarios."""
        # Test with completely invalid command
        result = self.runner.invoke(cli, ["invalid_command"])
        assert result.exit_code != 0

        # Test with invalid subcommand options
        result = self.runner.invoke(cli, ["query", "--invalid-option"])
        assert result.exit_code != 0


class TestCLIUtilities:
    """Test CLI utility functions and helpers."""

    def test_format_dependency_status(self):
        """Test dependency status formatting."""
        from src.parquetframe.cli import format_dependency_status

        # Test available dependency
        status = {"available": True, "version": "1.5.0"}
        formatted = format_dependency_status("pandas", status)
        assert "✓" in formatted
        assert "pandas" in formatted
        assert "1.5.0" in formatted

        # Test missing dependency
        status = {"available": False, "install_cmd": "pip install pandas"}
        formatted = format_dependency_status("pandas", status)
        assert "✗" in formatted
        assert "pandas" in formatted
        assert "pip install pandas" in formatted

    def test_validate_exclusive_options(self):
        """Test option validation utility."""
        from src.parquetframe.cli import validate_exclusive_options

        # Should pass with one option
        validate_exclusive_options("/path/to/data", None)
        validate_exclusive_options(None, "sqlite:///db.db")

        # Should raise with both options
        with pytest.raises(SystemExit):
            validate_exclusive_options("/path/to/data", "sqlite:///db.db")

        # Should raise with neither option
        with pytest.raises(SystemExit):
            validate_exclusive_options(None, None)

    def test_create_console_output(self):
        """Test console output creation."""
        from src.parquetframe.cli import create_console

        console = create_console()
        assert console is not None
        # Console should have basic printing capability
        assert hasattr(console, "print")

    @patch("sys.exit")
    def test_error_exit_handling(self, mock_exit):
        """Test error exit handling utilities."""
        from src.parquetframe.cli import handle_error_and_exit

        error = DataSourceError("Test error", "path")
        handle_error_and_exit(error)

        mock_exit.assert_called_once_with(1)


class TestCLIErrorScenarios:
    """Test various CLI error scenarios and edge cases."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_keyboard_interrupt_handling(self, temp_parquet_dir):
        """Test handling of keyboard interrupt during execution."""
        with patch("src.parquetframe.cli.DataContextFactory") as mock_factory:
            # Mock context that hangs on initialization to simulate long operation
            mock_context = MagicMock()
            mock_context.initialize = AsyncMock(side_effect=KeyboardInterrupt())
            mock_factory.create_from_path.return_value = mock_context

            result = self.runner.invoke(
                cli, ["query", "--path", str(temp_parquet_dir), "SELECT * FROM users"]
            )

            # Should handle gracefully
            assert result.exit_code != 0

    def test_system_exit_handling(self, temp_parquet_dir):
        """Test handling of system exit during execution."""
        with patch("src.parquetframe.cli.DataContextFactory") as mock_factory:
            # Mock context that raises SystemExit
            mock_context = MagicMock()
            mock_context.initialize = AsyncMock(side_effect=SystemExit(1))
            mock_factory.create_from_path.return_value = mock_context

            result = self.runner.invoke(
                cli, ["query", "--path", str(temp_parquet_dir), "SELECT * FROM users"]
            )

            # Should handle gracefully
            assert result.exit_code != 0

    def test_unexpected_exception_handling(self, temp_parquet_dir):
        """Test handling of unexpected exceptions."""
        with patch("src.parquetframe.cli.DataContextFactory") as mock_factory:
            # Mock context that raises unexpected exception
            mock_context = MagicMock()
            mock_context.initialize = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )
            mock_factory.create_from_path.return_value = mock_context

            result = self.runner.invoke(
                cli, ["query", "--path", str(temp_parquet_dir), "SELECT * FROM users"]
            )

            assert result.exit_code != 0
            assert "Unexpected error" in result.output

    def test_empty_query_handling(self, temp_parquet_dir):
        """Test handling of empty query string."""
        result = self.runner.invoke(
            cli,
            ["query", "--path", str(temp_parquet_dir), ""],  # Empty query
        )

        # Should handle gracefully or provide meaningful error
        assert result.exit_code != 0

    def test_very_long_query_handling(self, temp_parquet_dir):
        """Test handling of very long query strings."""
        # Create a very long query (more than typical command line limits)
        long_query = (
            "SELECT " + ", ".join([f"col_{i}" for i in range(1000)]) + " FROM users;"
        )

        result = self.runner.invoke(
            cli, ["query", "--path", str(temp_parquet_dir), long_query]
        )

        # Should either process or fail gracefully
        if result.exit_code != 0:
            # Acceptable failure modes
            assert any(
                phrase in result.output
                for phrase in [
                    "does not exist",
                    "PyArrow is required",
                    "No query engine available",
                ]
            )


class TestCLIPerformance:
    """Performance-related tests for CLI operations."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @pytest.mark.slow
    def test_cli_startup_time(self):
        """Test that CLI starts up in reasonable time."""
        import time

        start_time = time.time()
        result = self.runner.invoke(cli, ["--help"])
        startup_time = time.time() - start_time

        assert result.exit_code == 0
        assert startup_time < 2.0, f"CLI startup took {startup_time:.2f} seconds"

    @pytest.mark.slow
    def test_deps_command_performance(self):
        """Test that deps command completes in reasonable time."""
        import time

        start_time = time.time()
        result = self.runner.invoke(cli, ["deps"])
        deps_time = time.time() - start_time

        # Deps command should complete quickly
        assert deps_time < 5.0, f"Deps command took {deps_time:.2f} seconds"
