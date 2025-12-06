"""
Test Schema Inference for Avro.

Verify that the automatic schema inference works correctly
when writing DataFrames to Avro files.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest


def test_schema_inference_basic():
    """Test basic schema inference for common data types."""
    import importlib.util

    if importlib.util.find_spec("parquetframe.io_new.avro"):
        from parquetframe.io_new.avro import (  # noqa: F401
            AvroReader,
            AvroWriter,
            infer_avro_schema,
        )
    else:
        pytest.skip("Avro module not available")

    # Create test DataFrame with various types
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.7],
            "active": [True, False, True],
        }
    )

    # Infer schema
    schema = infer_avro_schema(df, name="TestSchema")

    # Verify schema structure
    assert schema["type"] == "record"
    assert schema["name"] == "TestSchema"
    assert "fields" in schema
    assert len(schema["fields"]) == 4

    # Verify field types
    field_types = {f["name"]: f["type"] for f in schema["fields"]}
    assert field_types["id"] == "long"
    assert field_types["name"] == "string"
    assert field_types["value"] == "double"
    assert field_types["active"] == "boolean"

    print("✓ Basic schema inference works")


def test_schema_inference_nullable():
    """Test schema inference with nullable columns."""
    try:
        from parquetframe.io_new.avro import infer_avro_schema
    except ImportError:
        pytest.skip("Avro module not available")

    # Create DataFrame with nulls
    df = pd.DataFrame(
        {
            "id": [1, 2, None],
            "name": ["Alice", None, "Charlie"],
        }
    )

    schema = infer_avro_schema(df)

    # Verify nullable fields use unions
    field_types = {f["name"]: f["type"] for f in schema["fields"]}
    assert field_types["id"] == ["null", "long"]
    assert field_types["name"] == ["null", "string"]

    print("✓ Nullable schema inference works")


def test_to_avro_without_schema():
    """Test writing Avro file without specifying schema."""
    try:
        from parquetframe.io_new.avro import AvroReader, AvroWriter
    except ImportError:
        pytest.skip("Avro module not available")

    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.7],
        }
    )

    with tempfile.NamedTemporaryFile(suffix=".avro", delete=False) as f:
        avro_path = f.name

    try:
        # Write without schema (should auto-infer)
        writer = AvroWriter()
        writer.write(df, avro_path, schema=None, codec="deflate")

        # Read back
        reader = AvroReader()
        df_read = reader.read(avro_path, engine="pandas")

        # Verify data integrity
        assert len(df_read) == 3
        assert list(df_read["name"]) == ["Alice", "Bob", "Charlie"]

        print("✓ to_avro without schema works")

    finally:
        Path(avro_path).unlink()


if __name__ == "__main__":
    print("Testing Schema Inference for Avro...")

    test_schema_inference_basic()
    test_schema_inference_nullable()
    test_to_avro_without_schema()

    print("\n✅ All schema inference tests passed!")
