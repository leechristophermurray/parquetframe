"""
Test Avro Fast Path implementation.

This test verifies:
1. The Rust apache-avro integration
2. Python wrapper functionality
3. End-to-end Avro reading
"""

import tempfile
from pathlib import Path

import pyarrow as pa
import pytest


# Create a simple Avro file for testing
def create_test_avro_file():
    """Create a test Avro file using fastavro."""
    try:
        import fastavro
    except ImportError:
        pytest.skip("fastavro not installed")

    schema = {
        "type": "record",
        "name": "Test",
        "fields": [
            {"name": "id", "type": "long"},
            {"name": "name", "type": "string"},
            {"name": "value", "type": "double"},
        ],
    }

    records = [
        {"id": 1, "name": "Alice", "value": 10.5},
        {"id": 2, "name": "Bob", "value": 20.3},
        {"id": 3, "name": "Charlie", "value": 30.7},
    ]

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".avro", delete=False) as f:
        fastavro.writer(f, schema, records)
        return f.name


def test_rust_avro_available():
    """Test that the Rust Avro function is available."""
    try:
        from parquetframe import _rustic

        assert hasattr(
            _rustic, "read_avro_fast"
        ), "read_avro_fast not exposed to Python"
    except ImportError:
        pytest.skip("Rust backend not available")


def test_read_avro_fast_basic():
    """Test reading an Avro file with the Rust fast-path."""
    try:
        from parquetframe import _rustic
    except ImportError:
        pytest.skip("Rust backend not available")

    avro_path = create_test_avro_file()

    try:
        # Read with Rust
        ipc_bytes = _rustic.read_avro_fast(avro_path, batch_size=None)
        assert isinstance(ipc_bytes, bytes)
        assert len(ipc_bytes) > 0

        # Reconstruct Arrow table
        buf = pa.py_buffer(ipc_bytes)
        with pa.ipc.open_stream(buf) as reader:
            table = reader.read_all()

        # Verify data
        assert table.num_rows == 3
        assert table.num_columns == 3
        assert table.column_names == ["id", "name", "value"]

        # Check values
        assert table.column("id").to_pylist() == [1, 2, 3]
        assert table.column("name").to_pylist() == ["Alice", "Bob", "Charlie"]
        assert table.column("value").to_pylist() == pytest.approx([10.5, 20.3, 30.7])

    finally:
        Path(avro_path).unlink()


def test_read_avro_engine():
    """Test reading via RustIOEngine.read_avro()."""
    try:
        from parquetframe.io_rust import RustIOEngine
    except ImportError:
        pytest.skip("Rust backend not available")

    avro_path = create_test_avro_file()

    try:
        engine = RustIOEngine()
        table = engine.read_avro(avro_path)

        assert table.num_rows == 3
        assert table.column_names == ["id", "name", "value"]

    finally:
        Path(avro_path).unlink()


def test_read_avro_fast_convenience():
    """Test convenience function read_avro_fast()."""
    try:
        from parquetframe.io_rust import read_avro_fast
    except ImportError:
        pytest.skip("Rust backend not available")

    avro_path = create_test_avro_file()

    try:
        table = read_avro_fast(avro_path)

        assert table.num_rows == 3
        assert table.column("name").to_pylist() == ["Alice", "Bob", "Charlie"]

    finally:
        Path(avro_path).unlink()


if __name__ == "__main__":
    print("Testing Avro Fast Path...")

    print("✓ Rust Avro available")
    test_rust_avro_available()

    print("✓ Basic Avro read")
    test_read_avro_fast_basic()

    print("✓ RustIOEngine.read_avro()")
    test_read_avro_engine()

    print("✓ read_avro_fast() convenience")
    test_read_avro_fast_convenience()

    print("\n✅ All tests passed!")
