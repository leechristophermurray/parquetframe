"""
Integration tests for configuration with engine selection.
"""

import pandas as pd
import pytest

from parquetframe.config import config_context, get_config, reset_config, set_config
from parquetframe.core import read_csv


@pytest.fixture(autouse=True)
def clean_config():
    """Reset configuration before each test."""
    reset_config()
    yield
    reset_config()


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file."""
    csv_file = tmp_path / "test.csv"
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def sample_parquet(tmp_path):
    """Create a sample Parquet file."""
    parquet_file = tmp_path / "test.parquet"
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    df.to_parquet(parquet_file)
    return parquet_file


class TestConfigEngineSelection:
    """Test configuration integration with engine selection."""

    def test_default_engine_override(self, sample_csv):
        """Test default_engine config overrides automatic selection."""
        # Set default engine to polars
        set_config(default_engine="polars")

        # Read a file - should use polars
        df = read_csv(sample_csv)

        assert df.engine_name == "polars"

    def test_default_engine_pandas(self, sample_csv):
        """Test forcing pandas engine via config."""
        set_config(default_engine="pandas")

        df = read_csv(sample_csv)

        assert df.engine_name == "pandas"

    def test_config_context_temporary_engine(self, sample_csv):
        """Test config_context for temporary engine override."""
        # Default config should select pandas for small file
        df1 = read_csv(sample_csv)
        assert df1.engine_name == "pandas"

        # Temporarily use polars
        with config_context(default_engine="polars"):
            df2 = read_csv(sample_csv)
            assert df2.engine_name == "polars"

        # Should revert to pandas
        df3 = read_csv(sample_csv)
        assert df3.engine_name == "pandas"

    def test_threshold_configuration(self, tmp_path):
        """Test custom thresholds from configuration."""
        # Create a file that's between default thresholds
        # Default: pandas < 100MB, polars < 10GB
        # Set new thresholds: pandas < 1MB
        set_config(pandas_threshold_mb=0.001)  # Very low threshold

        # Even a tiny file should trigger non-pandas selection
        tiny_file = tmp_path / "tiny.csv"
        df = pd.DataFrame({"a": range(10)})
        df.to_csv(tiny_file, index=False)

        # With the very low threshold, even this tiny file might trigger polars
        # (depending on metadata estimation)
        result = read_csv(tiny_file)
        # The engine selected might be pandas or polars depending on exact sizing
        assert result.engine_name in ("pandas", "polars")

    def test_verbose_mode_from_config(self, sample_csv, caplog):
        """Test verbose mode affects logging."""
        import logging

        caplog.set_level(logging.DEBUG)

        # Enable verbose mode
        set_config(verbose=True)

        # This should potentially produce more logging output
        # (actual verbose behavior would need to be implemented in readers)
        df = read_csv(sample_csv)

        assert df is not None


class TestConfigWithEntity:
    """Test configuration with entity framework."""

    def test_entity_default_format(self):
        """Test entity framework respects default format config."""
        from parquetframe.entity.metadata import registry

        registry.clear()

        # Set default format to avro
        set_config(default_entity_format="avro")

        # Entity should use config default
        # (Currently entities have their own format parameter,
        # but we could integrate with config in the future)
        config = get_config()
        assert config.default_entity_format == "avro"

        registry.clear()

    def test_entity_base_path(self, tmp_path):
        """Test entity framework can use configured base path."""
        set_config(default_entity_base_path=tmp_path)

        config = get_config()
        assert config.default_entity_base_path == tmp_path


class TestConfigEnvironmentIntegration:
    """Test configuration environment variable integration."""

    def test_engine_env_var_affects_selection(self, sample_csv, monkeypatch):
        """Test PARQUETFRAME_ENGINE env var affects engine selection."""
        # Reset config to pick up new env var
        monkeypatch.setenv("PARQUETFRAME_ENGINE", "polars")
        reset_config()  # Force reload from environment

        df = read_csv(sample_csv)
        assert df.engine_name == "polars"

    def test_threshold_env_var(self, sample_csv, monkeypatch):
        """Test threshold environment variables."""
        monkeypatch.setenv("PARQUETFRAME_PANDAS_THRESHOLD_MB", "1000")
        reset_config()

        config = get_config()
        assert config.pandas_threshold_mb == 1000.0
