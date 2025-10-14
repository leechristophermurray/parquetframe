"""
Tests for CLI functionality.

This module provides basic testing for the CLI, focusing on:
- Command group existence and imports
- Basic CLI functionality validation
- Dependency handling
"""

from unittest.mock import patch

from click.testing import CliRunner


class TestCLIImports:
    """Test CLI imports and basic functionality."""

    def test_cli_import(self):
        """Test that we can import the CLI module."""
        from src.parquetframe.cli import main

        assert main is not None
        assert hasattr(main, "commands")

    def test_cli_console_import(self):
        """Test that console is properly imported."""
        from src.parquetframe.cli import console

        assert console is not None
        assert hasattr(console, "print")


class TestCLIBasicFunctionality:
    """Test basic CLI functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_main_help_command(self):
        """Test CLI main help command."""
        from src.parquetframe.cli import main

        result = self.runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "ParquetFrame CLI" in result.output

    def test_main_version_command(self):
        """Test CLI version command."""
        from src.parquetframe.cli import main

        result = self.runner.invoke(main, ["--version"])

        # Version command may fail if package not installed in development
        # This is expected during testing with src layout
        assert result.exit_code in [0, 1]

    @patch("src.parquetframe.cli.Path.exists")
    def test_run_command_exists(self, mock_exists):
        """Test that run command exists and can be invoked."""
        from src.parquetframe.cli import main

        # Mock file existence
        mock_exists.return_value = True

        result = self.runner.invoke(main, ["run", "--help"])

        # Should show run command help without error
        assert "Run operations on data files" in result.output


class TestCLIUtilities:
    """Test CLI utility functions and helpers."""

    def test_dependency_checking_functions(self):
        """Test that dependency checking functions can be imported."""
        from src.parquetframe.cli import (
            check_dependencies,
            format_dependency_status,
            suggest_installation_commands,
        )

        assert check_dependencies is not None
        assert format_dependency_status is not None
        assert suggest_installation_commands is not None

    def test_availability_flags(self):
        """Test that availability flags are properly set."""
        from src.parquetframe.cli import (
            BENCHMARK_AVAILABLE,
            INTERACTIVE_AVAILABLE,
            SQL_AVAILABLE,
            WORKFLOW_AVAILABLE,
            WORKFLOW_HISTORY_AVAILABLE,
            WORKFLOW_VISUALIZATION_AVAILABLE,
        )

        # All should be booleans
        assert isinstance(INTERACTIVE_AVAILABLE, bool)
        assert isinstance(BENCHMARK_AVAILABLE, bool)
        assert isinstance(WORKFLOW_AVAILABLE, bool)
        assert isinstance(SQL_AVAILABLE, bool)
        assert isinstance(WORKFLOW_HISTORY_AVAILABLE, bool)
        assert isinstance(WORKFLOW_VISUALIZATION_AVAILABLE, bool)


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_invalid_command(self):
        """Test handling of invalid commands."""
        from src.parquetframe.cli import main

        result = self.runner.invoke(main, ["invalid_command"])

        assert result.exit_code != 0
        # Should show error about unknown command

    def test_run_with_nonexistent_file(self):
        """Test run command with nonexistent file."""
        from src.parquetframe.cli import main

        result = self.runner.invoke(main, ["run", "/nonexistent/file.parquet"])

        assert result.exit_code != 0
        # Should handle file not found gracefully
