"""
Test engine contract compliance for all DataFrame engines.

Ensures all engines implement the required interface consistently
and provide equivalent behavior across different backends.
"""

import pytest


class TestEngineContract:
    """Test contract compliance for all engines."""

    @pytest.fixture(params=["pandas", "polars", "dask"])
    def engine_name(self, request):
        """Parameterized fixture for all engine names."""
        return request.param

    @pytest.fixture
    def engine(self, engine_name):
        """Create engine instance based on name."""
        # Will be implemented when engines are ready
        pytest.skip(f"Engine {engine_name} not yet implemented")

    def test_engine_properties(self, engine):
        """Test engine has required properties."""
        assert hasattr(engine, "name")
        assert hasattr(engine, "is_lazy")
        assert hasattr(engine, "is_available")

        # Properties should return expected types
        assert isinstance(engine.name, str)
        assert isinstance(engine.is_lazy, bool)
        assert isinstance(engine.is_available, bool)

    def test_engine_methods(self, engine):
        """Test engine has required methods."""
        assert hasattr(engine, "read_parquet")
        assert hasattr(engine, "read_csv")
        assert hasattr(engine, "to_pandas")
        assert hasattr(engine, "compute_if_lazy")
        assert hasattr(engine, "estimate_memory_usage")

    def test_engine_availability(self, engine):
        """Test engine availability detection."""
        # If engine is available, it should work
        if engine.is_available:
            # Basic functionality should work
            assert engine.name in ["pandas", "polars", "dask"]
        else:
            # Should raise ImportError for operations
            pytest.skip(f"Engine {engine.name} not available")
