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

        print("   ✓ pandas and dask imported successfully")

        import parquetframe as pqf

        print("   ✓ parquetframe imported successfully")

        # Test basic creation
        print("2. Testing basic creation...")
        empty_pf = pqf.create_empty()
        print(f"   ✓ Created empty ParquetFrame: {empty_pf}")

        # Test with sample data
        print("3. Testing with sample data...")
        sample_df = pd.DataFrame(
            {
                "id": range(5),
                "value": range(5, 10),
                "category": ["A", "B", "A", "B", "A"],
            }
        )

        pf = pqf.ParquetFrame(sample_df)
        print(f"   ✓ Created ParquetFrame with data: {pf.shape}")

        # Test basic operations
        print("4. Testing basic operations...")
        result = pf.groupby("category").sum()
        print(f"   ✓ GroupBy operation result shape: {result.shape}")

        # Test file I/O (in temp directory)
        print("5. Testing file I/O...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_data"

            # Save
            pf.save(temp_path)
            expected_file = Path(temp_dir) / "test_data.parquet"
            print(f"   ✓ Saved to {expected_file}")

            # Read back
            pf_loaded = pqf.read(temp_path)
            print(f"   ✓ Loaded from file: {pf_loaded.shape}")

            # Verify data integrity
            pd.testing.assert_frame_equal(
                pf._df.reset_index(drop=True), pf_loaded._df.reset_index(drop=True)
            )
            print("   ✓ Data integrity verified")

        print("🎉 All tests passed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
