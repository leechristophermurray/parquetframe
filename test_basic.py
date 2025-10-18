#!/usr/bin/env python3
"""
Basic integration test to verify ParquetFrame works correctly.
This can be used to debug CI issues locally.
"""

import sys
import tempfile
from pathlib import Path


def test_basic_functionality():
    """Test basic ParquetFrame functionality."""
    print("Testing basic ParquetFrame functionality...")

    try:
        # Test imports
        print("1. Testing imports...")
        import pandas as pd

        print("   [OK] pandas and dask imported successfully")

        import parquetframe as pqf

        print("   [OK] parquetframe imported successfully")

        # Test with sample data
        print("2. Testing with sample data...")
        sample_df = pd.DataFrame(
            {
                "id": range(5),
                "value": range(5, 10),
                "category": ["A", "B", "A", "B", "A"],
            }
        )

        # Create a temporary file to test read functionality
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "sample_data.csv"
            sample_df.to_csv(temp_path, index=False)

            # Test Phase 2 read with automatic engine selection
            df = pqf.read(temp_path)
            print(
                f"   [OK] Created DataFrameProxy with data using {df.engine_name} engine"
            )
            print(f"   [OK] DataFrame shape: {df.native.shape}")

        # Test basic operations
        print("3. Testing basic operations...")
        result = df.native.groupby("category").sum()
        print(f"   [OK] GroupBy operation result shape: {result.shape}")

        # Test file I/O (in temp directory)
        print("4. Testing file I/O...")
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test CSV read/write
            csv_path = Path(temp_dir) / "test_data.csv"
            sample_df.to_csv(csv_path, index=False)
            print(f"   [OK] Saved CSV to {csv_path}")

            # Read back
            df_loaded = pqf.read(csv_path)
            print(f"   [OK] Loaded from CSV: {df_loaded.native.shape}")
            print(f"   [OK] Engine used: {df_loaded.engine_name}")

            # Test Parquet read/write
            parquet_path = Path(temp_dir) / "test_data.parquet"
            sample_df.to_parquet(parquet_path)
            df_parquet = pqf.read(parquet_path)
            print(f"   [OK] Loaded from Parquet: {df_parquet.native.shape}")

            # Verify data integrity
            pd.testing.assert_frame_equal(
                sample_df.reset_index(drop=True),
                df_loaded.native.reset_index(drop=True),
            )
            print("   [OK] Data integrity verified")

        print("[SUCCESS] All tests passed successfully!")
        return True

    except Exception as e:
        print(f"[FAILED] Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
