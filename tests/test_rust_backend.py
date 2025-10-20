"""Tests for Rust backend detection and fallback logic."""


def test_rust_detection():
    """Test Rust backend detection."""
    # Import here to ensure clean state
    from parquetframe.backends.rust_backend import is_rust_available

    available = is_rust_available()
    assert isinstance(available, bool)


def test_rust_backend_returns_module_or_none():
    """Test that get_rust_backend returns module or None."""
    from parquetframe.backends.rust_backend import get_rust_backend

    backend = get_rust_backend()
    # Should return None if Rust not built, or module if available
    assert backend is None or hasattr(backend, "rust_available")


def test_rust_version_function():
    """Test rust version retrieval."""
    from parquetframe.backends.rust_backend import get_rust_version

    version = get_rust_version()
    # Should return None or a version string
    assert version is None or isinstance(version, str)


def test_rust_disable_env_var(monkeypatch):
    """Test disabling Rust via environment variable."""
    # Reset cached value
    import parquetframe.backends.rust_backend as rb

    rb._rust_available = None

    # Set environment variable
    monkeypatch.setenv("PARQUETFRAME_DISABLE_RUST", "1")

    from parquetframe.backends.rust_backend import is_rust_available

    assert not is_rust_available()


def test_rust_disable_env_var_variations(monkeypatch):
    """Test various environment variable values."""
    import parquetframe.backends.rust_backend as rb

    # Test "1" disables
    rb._rust_available = None
    monkeypatch.setenv("PARQUETFRAME_DISABLE_RUST", "1")
    from parquetframe.backends.rust_backend import is_rust_available

    assert not is_rust_available()

    # Test "0" doesn't disable (but may still be unavailable if not built)
    rb._rust_available = None
    monkeypatch.setenv("PARQUETFRAME_DISABLE_RUST", "0")
    # Result depends on whether Rust is actually available
    result = is_rust_available()
    assert isinstance(result, bool)
