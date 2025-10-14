"""
Tests for CLI multi-format functionality.

Tests the CLI commands with different file formats to ensure
multi-format support works correctly.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from parquetframe.cli import main


class TestCLIMultiFormat:
    """Test CLI commands with multiple file formats."""

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "score": [85.5, 92.0, 78.5],
                "active": [True, False, True],
            }
        )

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_cli_info_csv(self, runner, sample_data, temp_dir):
        """Test CLI info command with CSV file."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        result = runner.invoke(main, ["info", str(csv_path)])

        assert result.exit_code == 0
        assert "CSV" in result.output
        assert "File Details" in result.output
        assert "Data Schema" in result.output

    def test_cli_info_json(self, runner, sample_data, temp_dir):
        """Test CLI info command with JSON file."""
        json_path = temp_dir / "test.json"
        sample_data.to_json(json_path, orient="records")

        result = runner.invoke(main, ["info", str(json_path)])

        assert result.exit_code == 0
        assert "JSON" in result.output
        assert "File Details" in result.output

    def test_cli_info_explicit_format(self, runner, sample_data, temp_dir):
        """Test CLI info command with explicit format override."""
        # Create CSV file with .txt extension
        txt_path = temp_dir / "test.txt"
        sample_data.to_csv(txt_path, index=False)

        result = runner.invoke(main, ["info", str(txt_path), "--format", "csv"])

        assert result.exit_code == 0
        assert "CSV" in result.output

    def test_cli_run_csv(self, runner, sample_data, temp_dir):
        """Test CLI run command with CSV file."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        result = runner.invoke(main, ["run", str(csv_path), "--head", "2"])

        assert result.exit_code == 0
        assert "csv" in result.output.lower()
        assert "Alice" in result.output or "Bob" in result.output
        assert "SUCCESS" in result.output

    def test_cli_run_with_query(self, runner, sample_data, temp_dir):
        """Test CLI run command with query filtering."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        result = runner.invoke(
            main, ["run", str(csv_path), "--query", "age > 30", "--head", "1"]
        )

        assert result.exit_code == 0
        assert "SUCCESS" in result.output
        # Should only show records where age > 30

    def test_cli_run_json_lines(self, runner, sample_data, temp_dir):
        """Test CLI run command with JSON Lines file."""
        jsonl_path = temp_dir / "test.jsonl"
        sample_data.to_json(jsonl_path, orient="records", lines=True)

        result = runner.invoke(main, ["run", str(jsonl_path), "--info"])

        assert result.exit_code == 0
        assert "SUCCESS" in result.output

    def test_cli_run_explicit_format(self, runner, sample_data, temp_dir):
        """Test CLI run command with explicit format specification."""
        txt_path = temp_dir / "data.txt"
        sample_data.to_csv(txt_path, index=False)

        result = runner.invoke(
            main, ["run", str(txt_path), "--format", "csv", "--head", "1"]
        )

        assert result.exit_code == 0
        assert "format: csv" in result.output
        assert "SUCCESS" in result.output

    def test_cli_run_describe(self, runner, sample_data, temp_dir):
        """Test CLI run command with describe option."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        result = runner.invoke(main, ["run", str(csv_path), "--describe"])

        assert result.exit_code == 0
        assert "Statistical Description" in result.output
        assert "SUCCESS" in result.output

    def test_cli_run_columns_selection(self, runner, sample_data, temp_dir):
        """Test CLI run command with column selection."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        result = runner.invoke(
            main, ["run", str(csv_path), "--columns", "name,age", "--head", "2"]
        )

        assert result.exit_code == 0
        assert "name" in result.output
        assert "age" in result.output
        # Should not contain 'score' or 'active' columns
        assert "SUCCESS" in result.output

    def test_cli_error_handling(self, runner):
        """Test CLI error handling for non-existent files."""
        result = runner.invoke(main, ["info", "nonexistent.csv"])

        assert result.exit_code != 0

    def test_cli_format_validation(self, runner, sample_data, temp_dir):
        """Test CLI format validation for invalid formats."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        # This should still work because we handle invalid format gracefully
        # The command should auto-detect instead
        result = runner.invoke(
            main, ["run", str(csv_path), "--format", "invalid", "--head", "1"]
        )

        # The command may fail due to invalid format choice constraint
        # This tests that our click.Choice validation works
        assert "Invalid value for '--format'" in result.output or result.exit_code != 0

    def test_cli_multiple_formats_workflow(self, runner, sample_data, temp_dir):
        """Test a complete workflow with multiple formats."""
        # Create CSV input
        csv_path = temp_dir / "input.csv"
        sample_data.to_csv(csv_path, index=False)

        # Test info command
        info_result = runner.invoke(main, ["info", str(csv_path)])
        assert info_result.exit_code == 0

        # Test run command with processing
        run_result = runner.invoke(
            main,
            [
                "run",
                str(csv_path),
                "--query",
                "score > 80",
                "--columns",
                "name,score",
                "--head",
                "5",
            ],
        )
        assert run_result.exit_code == 0
        assert "SUCCESS" in run_result.output


class TestCLIFormatDetection:
    """Test CLI format detection edge cases."""

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    def test_cli_tsv_detection(self, runner):
        """Test CLI correctly handles TSV files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write TSV data
            f.write("name\tage\tscore\n")
            f.write("Alice\t25\t85.5\n")
            f.write("Bob\t30\t92.0\n")

            tsv_path = f.name

        try:
            result = runner.invoke(main, ["info", tsv_path])
            assert result.exit_code == 0
            assert "CSV" in result.output  # TSV is handled by CSV handler

        finally:
            Path(tsv_path).unlink()

    def test_cli_jsonl_detection(self, runner):
        """Test CLI correctly handles JSON Lines files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Write JSONL data
            f.write('{"name": "Alice", "age": 25, "score": 85.5}\n')
            f.write('{"name": "Bob", "age": 30, "score": 92.0}\n')

            jsonl_path = f.name

        try:
            result = runner.invoke(main, ["info", jsonl_path])
            assert result.exit_code == 0
            assert "JSON" in result.output

        finally:
            Path(jsonl_path).unlink()
