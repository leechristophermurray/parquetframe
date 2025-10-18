"""
Tests for configuration system.
"""

from pathlib import Path

import pytest

from parquetframe.config import (
    Config,
    config_context,
    get_config,
    reset_config,
    set_config,
)


@pytest.fixture(autouse=True)
def clean_config():
    """Reset configuration before each test."""
    reset_config()
    yield
    reset_config()


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clean environment variables before each test."""
    env_vars = [
        "PARQUETFRAME_ENGINE",
        "PARQUETFRAME_PANDAS_THRESHOLD_MB",
        "PARQUETFRAME_POLARS_THRESHOLD_MB",
        "PARQUETFRAME_ENTITY_FORMAT",
        "PARQUETFRAME_ENTITY_BASE_PATH",
        "PARQUETFRAME_VERBOSE",
        "PARQUETFRAME_QUIET",
        "PARQUETFRAME_PROGRESS",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()

        assert config.default_engine is None
        assert config.pandas_threshold_mb == 100.0
        assert config.polars_threshold_mb == 10_000.0
        assert config.default_entity_format == "parquet"
        assert config.default_entity_base_path is None
        assert config.default_compression is None
        assert config.chunk_size == 10_000
        assert config.verbose is False
        assert config.show_warnings is True
        assert config.progress_bar is False
        assert config.parallel_read is True
        assert config.max_workers is None

    def test_get_config_singleton(self):
        """Test get_config returns singleton."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2


class TestConfigSetters:
    """Test configuration setters."""

    def test_set_single_value(self):
        """Test setting a single configuration value."""
        config = get_config()
        config.set(default_engine="polars")

        assert config.default_engine == "polars"

    def test_set_multiple_values(self):
        """Test setting multiple configuration values."""
        config = get_config()
        config.set(default_engine="dask", verbose=True, pandas_threshold_mb=200.0)

        assert config.default_engine == "dask"
        assert config.verbose is True
        assert config.pandas_threshold_mb == 200.0

    def test_set_invalid_key_raises_error(self):
        """Test setting invalid key raises ValueError."""
        config = get_config()

        with pytest.raises(ValueError, match="Unknown configuration key"):
            config.set(invalid_key="value")

    def test_set_config_function(self):
        """Test set_config function."""
        set_config(default_engine="polars", verbose=True)

        config = get_config()
        assert config.default_engine == "polars"
        assert config.verbose is True


class TestConfigEnvironment:
    """Test configuration from environment variables."""

    def test_engine_from_env(self, monkeypatch):
        """Test loading engine from environment."""
        monkeypatch.setenv("PARQUETFRAME_ENGINE", "polars")
        config = Config()

        assert config.default_engine == "polars"

    def test_thresholds_from_env(self, monkeypatch):
        """Test loading thresholds from environment."""
        monkeypatch.setenv("PARQUETFRAME_PANDAS_THRESHOLD_MB", "50")
        monkeypatch.setenv("PARQUETFRAME_POLARS_THRESHOLD_MB", "5000")
        config = Config()

        assert config.pandas_threshold_mb == 50.0
        assert config.polars_threshold_mb == 5000.0

    def test_invalid_threshold_ignored(self, monkeypatch):
        """Test invalid threshold value is ignored."""
        monkeypatch.setenv("PARQUETFRAME_PANDAS_THRESHOLD_MB", "invalid")
        config = Config()

        assert config.pandas_threshold_mb == 100.0  # Default value

    def test_entity_format_from_env(self, monkeypatch):
        """Test loading entity format from environment."""
        monkeypatch.setenv("PARQUETFRAME_ENTITY_FORMAT", "avro")
        config = Config()

        assert config.default_entity_format == "avro"

    def test_entity_base_path_from_env(self, monkeypatch):
        """Test loading entity base path from environment."""
        monkeypatch.setenv("PARQUETFRAME_ENTITY_BASE_PATH", "/tmp/entities")
        config = Config()

        assert config.default_entity_base_path == Path("/tmp/entities")

    def test_verbose_from_env(self, monkeypatch):
        """Test loading verbose setting from environment."""
        test_cases = [
            ("1", True),
            ("true", True),
            ("True", True),
            ("yes", True),
            ("0", False),
            ("false", False),
            ("", False),
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("PARQUETFRAME_VERBOSE", env_value)
            config = Config()
            assert config.verbose == expected, f"Failed for env_value={env_value}"

    def test_quiet_from_env(self, monkeypatch):
        """Test loading quiet setting from environment."""
        monkeypatch.setenv("PARQUETFRAME_QUIET", "true")
        config = Config()

        assert config.show_warnings is False

    def test_progress_from_env(self, monkeypatch):
        """Test loading progress setting from environment."""
        monkeypatch.setenv("PARQUETFRAME_PROGRESS", "1")
        config = Config()

        assert config.progress_bar is True


class TestConfigReset:
    """Test configuration reset."""

    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        config = get_config()
        config.set(default_engine="dask", verbose=True)

        config.reset()

        assert config.default_engine is None
        assert config.verbose is False

    def test_reset_config_function(self):
        """Test reset_config function."""
        set_config(default_engine="polars", verbose=True)
        reset_config()

        config = get_config()
        assert config.default_engine is None
        assert config.verbose is False


class TestConfigContext:
    """Test configuration context manager."""

    def test_config_context_temporary_change(self):
        """Test temporary configuration change."""
        config = get_config()
        config.set(default_engine="pandas")

        with config_context(default_engine="polars", verbose=True):
            assert config.default_engine == "polars"
            assert config.verbose is True

        # Values should be restored
        assert config.default_engine == "pandas"
        assert config.verbose is False

    def test_config_context_exception_restores(self):
        """Test configuration is restored even on exception."""
        config = get_config()
        config.set(default_engine="pandas")

        try:
            with config_context(default_engine="dask"):
                assert config.default_engine == "dask"
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should be restored despite exception
        assert config.default_engine == "pandas"


class TestConfigSerialization:
    """Test configuration serialization."""

    def test_to_dict(self):
        """Test exporting configuration to dictionary."""
        config = Config(
            default_engine="polars",
            pandas_threshold_mb=50.0,
            verbose=True,
        )

        config_dict = config.to_dict()

        assert config_dict["default_engine"] == "polars"
        assert config_dict["pandas_threshold_mb"] == 50.0
        assert config_dict["verbose"] is True
        assert "pandas_threshold_mb" in config_dict

    def test_from_dict(self):
        """Test creating configuration from dictionary."""
        config_dict = {
            "default_engine": "dask",
            "pandas_threshold_mb": 200.0,
            "verbose": True,
            "default_entity_base_path": "/tmp/test",
        }

        config = Config.from_dict(config_dict)

        assert config.default_engine == "dask"
        assert config.pandas_threshold_mb == 200.0
        assert config.verbose is True
        assert config.default_entity_base_path == Path("/tmp/test")

    def test_from_dict_ignores_invalid_keys(self):
        """Test from_dict ignores invalid keys."""
        config_dict = {
            "default_engine": "polars",
            "invalid_key": "value",
        }

        config = Config.from_dict(config_dict)

        assert config.default_engine == "polars"
        assert not hasattr(config, "invalid_key")

    def test_round_trip_serialization(self):
        """Test round-trip serialization."""
        original = Config(
            default_engine="polars",
            pandas_threshold_mb=75.0,
            verbose=True,
        )

        config_dict = original.to_dict()
        restored = Config.from_dict(config_dict)

        assert restored.default_engine == original.default_engine
        assert restored.pandas_threshold_mb == original.pandas_threshold_mb
        assert restored.verbose == original.verbose
