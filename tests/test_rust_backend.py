"""Tests for Rust backend detection and fallback logic."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from parquetframe.config import reset_config, set_config
from parquetframe.io.io_backend import (
    get_backend_info,
    is_rust_io_available,
    try_get_row_count_fast,
)


@pytest.fixture(autouse=True)
def clean_config():
    """Reset configuration before each test."""
    reset_config()
    yield
    reset_config()


class TestRustBackendDetection:
    """Test Rust backend detection and availability."""

    def test_is_rust_io_available_returns_bool(self):
        """Test is_rust_io_available returns boolean."""
        result = is_rust_io_available()
        assert isinstance(result, bool)

    def test_get_backend_info_returns_dict(self):
        """Test get_backend_info returns comprehensive status."""
        info = get_backend_info()

        assert isinstance(info, dict)
        assert "rust_compiled" in info
        assert "rust_io_enabled" in info
        assert "rust_io_available" in info

        # All values should be booleans
        for key, value in info.items():
            assert isinstance(value, bool), f"{key} should be bool, got {type(value)}"

    def test_backend_info_consistency(self):
        """Test backend info values are consistent."""
        info = get_backend_info()

        # If rust_io_available is True, both compiled and enabled must be True
        if info["rust_io_available"]:
            assert info["rust_compiled"], "Available requires compiled"
            assert info["rust_io_enabled"], "Available requires enabled"

        # If not compiled, cannot be available
        if not info["rust_compiled"]:
            assert not info["rust_io_available"], "Cannot be available if not compiled"


class TestRustBackendConfiguration:
    """Test Rust backend configuration integration."""

    def test_disable_rust_io_via_config(self):
        """Test disabling Rust I/O via configuration."""
        initial_info = get_backend_info()
        initial_compiled = initial_info["rust_compiled"]

        # Disable via config
        set_config(rust_io_enabled=False)

        # Check it's disabled
        assert not is_rust_io_available()

        info_after = get_backend_info()
        assert (
            info_after["rust_compiled"] == initial_compiled
        )  # Compile state unchanged
        assert not info_after["rust_io_enabled"]
        assert not info_after["rust_io_available"]

    def test_enable_rust_io_via_config(self):
        """Test enabling Rust I/O via configuration."""
        # Disable first
        set_config(rust_io_enabled=False)
        assert not is_rust_io_available()

        # Re-enable
        set_config(rust_io_enabled=True)

        info = get_backend_info()
        assert info["rust_io_enabled"]

        # Available depends on whether Rust is compiled
        if info["rust_compiled"]:
            assert is_rust_io_available()


class TestRustBackendFallback:
    """Test Rust backend fallback mechanisms."""

    def test_try_get_row_count_fast_returns_none_when_disabled(self):
        """Test try_get_row_count_fast returns None when Rust disabled."""
        # Create a test parquet file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            test_file = Path(tmp.name)

        try:
            # Create test data
            df = pd.DataFrame({"a": range(100), "b": range(100, 200)})
            df.to_parquet(test_file)

            # Disable Rust
            set_config(rust_io_enabled=False)

            # Should return None (fallback)
            result = try_get_row_count_fast(test_file)
            assert result is None

        finally:
            test_file.unlink(missing_ok=True)

    def test_try_get_row_count_fast_works_when_enabled(self):
        """Test try_get_row_count_fast works when Rust enabled and available."""
        info = get_backend_info()

        if not info["rust_compiled"]:
            pytest.skip("Rust backend not compiled")

        # Create a test parquet file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            test_file = Path(tmp.name)

        try:
            # Create test data
            df = pd.DataFrame({"a": range(100), "b": range(100, 200)})
            df.to_parquet(test_file)

            # Ensure Rust is enabled
            set_config(rust_io_enabled=True)

            # Should return row count
            result = try_get_row_count_fast(test_file)
            assert result == 100

        finally:
            test_file.unlink(missing_ok=True)

    def test_disabled_rust_does_not_break_functionality(self):
        """Test that disabling Rust doesn't break overall functionality."""
        # This is a smoke test - ensures graceful fallback
        set_config(rust_io_enabled=False)

        # Should not raise errors
        assert not is_rust_io_available()
        info = get_backend_info()
        assert not info["rust_io_available"]


class TestRustBackendEnvironment:
    """Test Rust backend environment variable integration."""

    def test_disable_rust_env_var(self, monkeypatch):
        """Test PARQUETFRAME_DISABLE_RUST environment variable."""
        from parquetframe.config import Config

        monkeypatch.setenv("PARQUETFRAME_DISABLE_RUST", "1")
        config = Config()

        assert not config.use_rust_backend
        assert not config.rust_io_enabled
        assert not config.rust_graph_enabled

    def test_disable_rust_io_env_var(self, monkeypatch):
        """Test PARQUETFRAME_DISABLE_RUST_IO environment variable."""
        from parquetframe.config import Config

        monkeypatch.setenv("PARQUETFRAME_DISABLE_RUST_IO", "1")
        config = Config()

        assert config.use_rust_backend  # General flag still on
        assert not config.rust_io_enabled
        assert config.rust_graph_enabled
