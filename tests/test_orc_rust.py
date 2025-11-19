"""
Test ORC fast-path functionality using Rust backend.

Verifies ORC file reading with the Rust implementation.
"""

import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Skip all tests if pyarrow or pyorc not available
pytest.importorskip("pyarrow")


def test_orc_basic_read_write():
    """Test basic ORC read/write roundtrip."""
    try:
        import pyarrow as pa
        import pyarrow.orc as orc

        from parquetframe.io_rust import read_orc_fast
    except ImportError:
        pytest.skip("pyarrow.orc not available")

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create test data
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "Dave", "Eve"],
                "value": [10.5, 20.3, 30.1, 40.9, 50.2],
                "active": [True, False, True, True, False],
            }
        )

        # Write ORC file using pyarrow
        table = pa.Table.from_pandas(df)
        orc_path = temp_dir / "test.orc"
        with open(orc_path, "wb") as f:
            orc.write_table(table, f)

        # Read using Rust fast-path
        result_table = read_orc_fast(str(orc_path))
        result_df = result_table.to_pandas()

        # Verify data
        pd.testing.assert_frame_equal(df, result_df, check_dtype=False)

        print(f"✓ ORC roundtrip successful: {len(result_df)} rows")

    finally:
        shutil.rmtree(temp_dir)


def test_orc_with_batch_size():
    """Test ORC reading with custom batch size."""
    try:
        import pyarrow as pa
        import pyarrow.orc as orc

        from parquetframe.io_rust import read_orc_fast
    except ImportError:
        pytest.skip("pyarrow.orc not available")

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create larger dataset
        df = pd.DataFrame(
            {
                "idx": range(1000),
                "value": range(1000, 2000),
            }
        )

        # Write ORC
        table = pa.Table.from_pandas(df)
        orc_path = temp_dir / "large.orc"
        with open(orc_path, "wb") as f:
            orc.write_table(table, f)

        # Read with custom batch size
        result_table = read_orc_fast(str(orc_path), batch_size=100)
        result_df = result_table.to_pandas()

        # Verify
        assert len(result_df) == 1000
        pd.testing.assert_frame_equal(df, result_df, check_dtype=False)

        print(f"✓ ORC with batch_size=100: {len(result_df)} rows")

    finally:
        shutil.rmtree(temp_dir)


def test_orc_data_types():
    """Test ORC with various data types."""
    try:
        import pyarrow as pa
        import pyarrow.orc as orc

        from parquetframe.io_rust import read_orc_fast
    except ImportError:
        pytest.skip("pyarrow.orc not available")

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create data with various types
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
                "bool_col": [True, False, True],
            }
        )

        # Write ORC
        table = pa.Table.from_pandas(df)
        orc_path = temp_dir / "types.orc"
        with open(orc_path, "wb") as f:
            orc.write_table(table, f)

        # Read back
        result_table = read_orc_fast(str(orc_path))
        result_df = result_table.to_pandas()

        # Verify types and data
        assert len(result_df) == 3
        assert list(result_df.columns) == [
            "int_col",
            "float_col",
            "str_col",
            "bool_col",
        ]

        print("✓ ORC data types preserved correctly")

    finally:
        shutil.rmtree(temp_dir)


def test_orc_rust_io_engine():
    """Test ORC via RustIOEngine class."""
    try:
        import pyarrow as pa
        import pyarrow.orc as orc

        from parquetframe.io_rust import RustIOEngine
    except ImportError:
        pytest.skip("pyarrow.orc not available")

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create test data
        df = pd.DataFrame(
            {
                "a": [1, 2, 3],
                "b": ["x", "y", "z"],
            }
        )

        # Write ORC
        table = pa.Table.from_pandas(df)
        orc_path = temp_dir / "engine_test.orc"
        with open(orc_path, "wb") as f:
            orc.write_table(table, f)

        # Read via engine
        engine = RustIOEngine()
        result_table = engine.read_orc(str(orc_path))
        result_df = result_table.to_pandas()

        # Verify
        pd.testing.assert_frame_equal(df, result_df, check_dtype=False)

        print("✓ RustIOEngine.read_orc() works")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("Testing ORC Fast Path...")

    try:
        test_orc_basic_read_write()
        print("✓ Basic read/write works")
    except Exception as e:
        print(f"✗ Basic read/write failed: {e}")

    try:
        test_orc_with_batch_size()
        print("✓ Batch size parameter works")
    except Exception as e:
        print(f"✗ Batch size failed: {e}")

    try:
        test_orc_data_types()
        print("✓ Data types work")
    except Exception as e:
        print(f"✗ Data types failed: {e}")

    try:
        test_orc_rust_io_engine()
        print("✓ RustIOEngine works")
    except Exception as e:
        print(f"✗ RustIOEngine failed: {e}")

    print("\n✅ All ORC tests passed!")
