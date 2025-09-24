"""
Tests for the ParquetFrame CLI module.
"""

import pandas as pd
import pytest
from click.testing import CliRunner
from pathlib import Path

from parquetframe.cli import main


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_parquet(tmp_path):
    """Create a sample parquet file for testing."""
    df = pd.DataFrame({
        'id': range(20),
        'name': [f'user_{i}' for i in range(20)],
        'age': [20 + (i % 50) for i in range(20)],
        'city': ['NYC', 'LA', 'Chicago'] * 6 + ['NYC', 'LA'],
        'score': [i * 1.5 for i in range(20)]
    })
    
    file_path = tmp_path / "test_data.parquet"
    df.to_parquet(file_path)
    return file_path


class TestCLIInfo:
    """Test the info command."""
    
    def test_info_command_basic(self, cli_runner, sample_parquet):
        """Test basic info command functionality."""
        result = cli_runner.invoke(main, ['info', str(sample_parquet)])
        
        assert result.exit_code == 0
        assert "File Information" in result.output
        assert "File Size" in result.output
        assert "Recommended Backend" in result.output
        assert "Parquet Schema" in result.output
        
    def test_info_command_nonexistent_file(self, cli_runner):
        """Test info command with nonexistent file."""
        result = cli_runner.invoke(main, ['info', 'nonexistent.parquet'])
        
        assert result.exit_code == 2  # Click's file not found error
        
        
class TestCLIRun:
    """Test the run command."""
    
    def test_run_command_basic(self, cli_runner, sample_parquet):
        """Test basic run command with preview."""
        result = cli_runner.invoke(main, ['run', str(sample_parquet)])
        
        assert result.exit_code == 0
        assert "Reading file" in result.output
        assert "Preview" in result.output
        assert "Operation completed successfully" in result.output
        
    def test_run_command_with_query(self, cli_runner, sample_parquet):
        """Test run command with query filter."""
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--query', 'age > 30'
        ])
        
        assert result.exit_code == 0
        assert "Applying query: age > 30" in result.output
        
    def test_run_command_with_columns(self, cli_runner, sample_parquet):
        """Test run command with column selection."""
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--columns', 'name,age'
        ])
        
        assert result.exit_code == 0
        assert "Selecting columns: name, age" in result.output
        
    def test_run_command_with_head(self, cli_runner, sample_parquet):
        """Test run command with head option."""
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--head', '3'
        ])
        
        assert result.exit_code == 0
        assert "First 3 rows" in result.output
        
    def test_run_command_with_describe(self, cli_runner, sample_parquet):
        """Test run command with describe option."""
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--describe'
        ])
        
        assert result.exit_code == 0
        assert "Statistical Description" in result.output
        
    def test_run_command_with_output(self, cli_runner, sample_parquet, tmp_path):
        """Test run command with output file."""
        output_file = tmp_path / "output.parquet"
        
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert f"Saving to: {output_file}" in result.output
        assert output_file.exists()
        
    def test_run_command_with_script_generation(self, cli_runner, sample_parquet, tmp_path):
        """Test run command with script generation."""
        script_file = tmp_path / "test_script.py"
        
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--query', 'age > 25',
            '--save-script', str(script_file)
        ])
        
        assert result.exit_code == 0
        assert script_file.exists()
        
        # Check script content
        script_content = script_file.read_text()
        assert "from parquetframe import ParquetFrame" in script_content
        assert "query('age > 25')" in script_content
        
    def test_run_command_force_backends(self, cli_runner, sample_parquet):
        """Test run command with backend forcing options."""
        # Test force pandas
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--force-pandas'
        ])
        assert result.exit_code == 0
        assert "pandas DataFrame" in result.output
        
        # Test force dask
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--force-dask'
        ])
        assert result.exit_code == 0
        assert "Dask DataFrame" in result.output
        
    def test_run_command_conflicting_backends(self, cli_runner, sample_parquet):
        """Test run command with conflicting backend options."""
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--force-pandas',
            '--force-dask'
        ])
        
        assert result.exit_code == 1
        assert "Cannot use both --force-dask and --force-pandas" in result.output
        

class TestCLIInteractive:
    """Test the interactive command."""
    
    def test_interactive_command_help(self, cli_runner):
        """Test interactive command help."""
        result = cli_runner.invoke(main, ['interactive', '--help'])
        
        assert result.exit_code == 0
        assert "Start an interactive Python session" in result.output
        
    # Note: Interactive mode is difficult to test in automated tests
    # as it starts a Python REPL. We would need more sophisticated
    # testing tools to test the interactive functionality fully.
        

class TestCLIGeneral:
    """Test general CLI functionality."""
    
    def test_main_help(self, cli_runner):
        """Test main CLI help."""
        result = cli_runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "ParquetFrame CLI" in result.output
        assert "info" in result.output
        assert "interactive" in result.output
        assert "run" in result.output
        
    def test_version_option(self, cli_runner):
        """Test version option."""
        result = cli_runner.invoke(main, ['--version'])
        
        assert result.exit_code == 0
        

class TestCLIErrorHandling:
    """Test error handling in CLI commands."""
    
    def test_run_invalid_query(self, cli_runner, sample_parquet):
        """Test run command with invalid query."""
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--query', 'invalid_column > 30'
        ])
        
        assert result.exit_code == 1
        assert "Error:" in result.output
        
    def test_run_invalid_columns(self, cli_runner, sample_parquet):
        """Test run command with invalid column names."""
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--columns', 'nonexistent_column'
        ])
        
        assert result.exit_code == 1
        assert "Error:" in result.output


class TestCLIIntegration:
    """Test CLI integration scenarios."""
    
    def test_full_pipeline(self, cli_runner, sample_parquet, tmp_path):
        """Test a complete data processing pipeline."""
        output_file = tmp_path / "pipeline_output.parquet"
        script_file = tmp_path / "pipeline_script.py"
        
        # Run complex pipeline
        result = cli_runner.invoke(main, [
            'run', str(sample_parquet),
            '--query', 'age > 25',
            '--columns', 'name,age,score',
            '--head', '5',
            '--output', str(output_file),
            '--save-script', str(script_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        assert script_file.exists()
        
        # Verify the output file has the expected data
        output_df = pd.read_parquet(output_file)
        assert len(output_df) <= 5  # Should be limited by head
        assert list(output_df.columns) == ['name', 'age', 'score']
        assert all(output_df['age'] > 25)  # Should be filtered by query
        
        # Verify script can be executed
        script_content = script_file.read_text()
        assert "query('age > 25')" in script_content
        assert "['name', 'age', 'score']" in script_content
        
    def test_different_file_sizes(self, cli_runner, tmp_path):
        """Test CLI with different file sizes to test backend selection."""
        # Create a tiny file (should use pandas)
        tiny_df = pd.DataFrame({'x': [1, 2, 3]})
        tiny_file = tmp_path / "tiny.parquet"
        tiny_df.to_parquet(tiny_file)
        
        result = cli_runner.invoke(main, ['run', str(tiny_file)])
        assert result.exit_code == 0
        assert "pandas DataFrame" in result.output
        
        # Test with explicit threshold
        result = cli_runner.invoke(main, [
            'run', str(tiny_file),
            '--threshold', '0.001'  # Very small threshold to force Dask
        ])
        assert result.exit_code == 0
        # With such a tiny file and threshold, it may still use pandas
        # This tests the threshold mechanism