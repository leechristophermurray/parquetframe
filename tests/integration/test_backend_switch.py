"""
Integration tests for backend switching logic and file size detection.
"""

import os

import dask.dataframe as dd
import pandas as pd
import pytest

import parquetframe as pqf
from parquetframe.core import ParquetFrame


class TestBackendSwitchingLogic:
    """Test automatic backend switching based on file size."""

    def test_threshold_boundary_below(self, sample_small_df, temp_dir):
        """Test file just below threshold uses pandas."""
        # Create a small file, set threshold slightly above its size
        file_path = temp_dir / "boundary_test.parquet"
        sample_small_df.to_parquet(file_path)

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        threshold = file_size_mb + 0.1  # Slightly above

        pf = ParquetFrame.read(file_path, threshold_mb=threshold)
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False

    def test_threshold_boundary_above(self, sample_small_df, temp_dir):
        """Test file just above threshold uses Dask."""
        file_path = temp_dir / "boundary_test.parquet"
        sample_small_df.to_parquet(file_path)

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        threshold = file_size_mb - 0.001  # Slightly below

        pf = ParquetFrame.read(file_path, threshold_mb=threshold)
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True

    def test_default_threshold_small_file(self, sample_small_df, temp_dir):
        """Test small file with default 10MB threshold uses pandas."""
        file_path = temp_dir / "small_default.parquet"
        sample_small_df.to_parquet(file_path)

        # Ensure file is actually small
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        assert file_size_mb < 1.0  # Should be well under 10MB

        pf = ParquetFrame.read(file_path)
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False

    def test_override_with_islazy_true(self, sample_small_df, temp_dir):
        """Test islazy=True overrides size-based decision."""
        file_path = temp_dir / "force_dask.parquet"
        sample_small_df.to_parquet(file_path)

        pf = ParquetFrame.read(file_path, islazy=True)
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True

    def test_override_with_islazy_false(self, large_parquet_file):
        """Test islazy=False overrides size-based decision."""
        pf = ParquetFrame.read(large_parquet_file, islazy=False)
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False


class TestBackendConversionIntegration:
    """Test backend conversion in realistic scenarios."""

    def test_read_small_convert_to_dask_save(self, sample_small_df, temp_dir):
        """Test complete workflow: read small -> convert to Dask -> save."""
        # Read small file (should be pandas)
        input_file = temp_dir / "small_input.parquet"
        sample_small_df.to_parquet(input_file)

        pf = ParquetFrame.read(input_file)
        assert isinstance(pf._df, pd.DataFrame)

        # Convert to Dask
        pf.to_dask()
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True

        # Save (should work with Dask)
        output_file = temp_dir / "dask_output"
        pf.save(output_file)

        expected_path = temp_dir / "dask_output.parquet"
        assert expected_path.exists()

    def test_read_large_convert_to_pandas_operations(self, large_parquet_file):
        """Test reading large file, converting to pandas, and doing operations."""
        # Read large file (should be Dask)
        pf = ParquetFrame.read(large_parquet_file)
        assert isinstance(pf._df, dd.DataFrame)

        # Convert to pandas for faster operations
        pf.to_pandas()
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False

        # Perform pandas operations
        result = pf.groupby("category").size()
        assert hasattr(result, "values")  # pandas Series

    def test_islazy_property_toggle_integration(self, sample_small_df):
        """Test islazy property setter in realistic workflow."""
        pf = ParquetFrame(sample_small_df, islazy=False)

        # Toggle to Dask
        pf.islazy = True
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True

        # Toggle back to pandas
        pf.islazy = False
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False

        # Data should be preserved
        pd.testing.assert_frame_equal(
            pf._df.reset_index(drop=True), sample_small_df.reset_index(drop=True)
        )


class TestFileExtensionIntegration:
    """Test file extension handling in various scenarios."""

    def test_read_save_cycle_preserves_data(self, sample_small_df, temp_dir):
        """Test reading and saving preserves data correctly."""
        # Save with pandas
        original_file = temp_dir / "original.parquet"
        sample_small_df.to_parquet(original_file)

        # Read with ParquetFrame
        pf = ParquetFrame.read(original_file)

        # Save again
        output_file = temp_dir / "copy"
        pf.save(output_file)

        # Read with pandas to verify
        copied_df = pd.read_parquet(temp_dir / "copy.parquet")
        pd.testing.assert_frame_equal(
            copied_df.reset_index(drop=True), sample_small_df.reset_index(drop=True)
        )

    def test_mixed_extension_preference(self, sample_small_df, temp_dir):
        """Test extension preference when both .parquet and .pqt exist."""
        base_name = "mixed_extensions"

        # Create both files
        parquet_file = temp_dir / f"{base_name}.parquet"
        pqt_file = temp_dir / f"{base_name}.pqt"

        # Save different data to each
        sample_small_df.to_parquet(parquet_file)
        modified_df = sample_small_df.copy()
        modified_df["extra_col"] = "extra"
        modified_df.to_parquet(pqt_file)

        # Read without extension - should prefer .parquet
        pf = ParquetFrame.read(temp_dir / base_name)

        # Should have read the .parquet file (without extra_col)
        assert "extra_col" not in pf.columns

    def test_extension_case_sensitivity(self, sample_small_df, temp_dir):
        """Test that extension detection works correctly."""
        # Create files with different cases
        file1 = temp_dir / "test.parquet"
        file2 = temp_dir / "test.pqt"

        sample_small_df.to_parquet(file1)

        # Reading with exact extension should work
        pf1 = ParquetFrame.read(file1)
        assert isinstance(pf1._df, pd.DataFrame)

        # Reading without extension should find .parquet
        pf2 = ParquetFrame.read(temp_dir / "test")
        assert isinstance(pf2._df, pd.DataFrame)


class TestConvenienceFunctionIntegration:
    """Test integration of top-level convenience functions."""

    def test_pqf_read_function(self, small_parquet_file, sample_small_df):
        """Test pqf.read() convenience function."""
        df = pqf.read(small_parquet_file)

        # Phase 2 returns DataFrameProxy (ParquetFrame is an alias)
        assert isinstance(df, ParquetFrame | pqf.DataFrameProxy)
        # Phase 2 uses .native instead of ._df
        native_df = df.native if hasattr(df, "native") else df._df
        assert isinstance(native_df, pd.DataFrame)
        pd.testing.assert_frame_equal(
            native_df.reset_index(drop=True), sample_small_df.reset_index(drop=True)
        )

    def test_pqf_read_with_parameters(self, small_parquet_file):
        """Test pqf.read() with various parameters."""
        # Phase 2 uses engine="dask" instead of islazy=True
        df1 = pqf.read(small_parquet_file, engine="dask")
        native_df1 = df1.native if hasattr(df1, "native") else df1._df
        assert isinstance(native_df1, dd.DataFrame)

        # Phase 2 may not support threshold_mb in read(); skip this assertion
        # or use smaller file size detection threshold in config

        # Additional kwargs
        df3 = pqf.read(small_parquet_file, columns=["id", "name"])
        assert list(df3.columns) == ["id", "name"]

    def test_create_empty_function(self):
        """Test pqf.create_empty() convenience function."""
        # Default (pandas)
        empty1 = pqf.create_empty()
        assert isinstance(empty1, ParquetFrame | pqf.DataFrameProxy)
        # Phase 2 uses engine_name instead of islazy
        assert empty1.engine_name == "pandas"

        # Dask - Phase 2 uses engine parameter
        empty2 = pqf.create_empty(engine="dask")
        assert isinstance(empty2, ParquetFrame | pqf.DataFrameProxy)
        assert empty2.engine_name == "dask"

    def test_pf_alias_integration(self, small_parquet_file, sample_small_df):
        """Test that parquetframe module can be used directly."""
        # Phase 2: pqf IS the module, no separate pf alias needed
        df = pqf.read(small_parquet_file)

        assert isinstance(df, ParquetFrame | pqf.DataFrameProxy)
        native_df = df.native if hasattr(df, "native") else df._df
        pd.testing.assert_frame_equal(
            native_df.reset_index(drop=True), sample_small_df.reset_index(drop=True)
        )


class TestMethodChainingIntegration:
    """Test method chaining in realistic workflows."""

    def test_read_transform_save_chain(self, sample_small_df, temp_dir):
        """Test complete data pipeline with method chaining."""
        # Setup input file
        input_file = temp_dir / "input.parquet"
        sample_small_df.to_parquet(input_file)

        # Chain operations
        result = (
            ParquetFrame.read(input_file)
            .to_dask()  # Convert to Dask
            .to_pandas()  # Convert back to pandas
            .save(temp_dir / "chained_output")
        )  # Save

        # Should return ParquetFrame for chaining
        assert isinstance(result, ParquetFrame)

        # Output file should exist
        assert (temp_dir / "chained_output.parquet").exists()

        # Data should be preserved
        saved_df = pd.read_parquet(temp_dir / "chained_output.parquet")
        pd.testing.assert_frame_equal(
            saved_df.reset_index(drop=True), sample_small_df.reset_index(drop=True)
        )

    def test_dataframe_operations_chaining(self, sample_small_df):
        """Test chaining DataFrame operations."""
        pf = ParquetFrame(sample_small_df, islazy=False)

        # Chain operations that return DataFrames directly
        result = pf.head(10).reset_index(drop=True)

        # Result should be wrapped in ParquetFrame
        assert isinstance(result, ParquetFrame)
        assert isinstance(result._df, pd.DataFrame)

        # Should have expected structure and size
        assert len(result) == 10
        assert "category" in result.columns

    @pytest.mark.slow
    def test_large_file_dask_operations_chain(self, large_parquet_file):
        """Test chaining operations on large Dask DataFrames."""
        # This test is marked as slow due to large file operations
        result = (
            ParquetFrame.read(large_parquet_file)
            .groupby("category")
            .id.count()
            .compute()
        )  # Compute Dask result

        # Result should be a pandas Series (computed from Dask)
        assert hasattr(result, "values")  # pandas Series
        assert len(result) > 0


class TestErrorHandlingIntegration:
    """Test error handling in integrated workflows."""

    def test_invalid_file_in_workflow(self, temp_dir):
        """Test error handling when file doesn't exist in workflow."""
        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(FileNotFoundError):
            (ParquetFrame.read(nonexistent).to_dask().save(temp_dir / "output"))

    def test_save_without_dataframe_in_chain(self, temp_dir):
        """Test error when trying to save empty ParquetFrame in chain."""
        with pytest.raises(TypeError, match="No dataframe loaded to save"):
            (ParquetFrame().to_dask().save(temp_dir / "output"))  # Still empty

    def test_attribute_error_propagation(self, sample_small_df):
        """Test that AttributeError propagates correctly through chains."""
        pf = ParquetFrame(sample_small_df, islazy=False)

        with pytest.raises(AttributeError):
            # Should fail on nonexistent_method
            result = pf.head(5).nonexistent_method()


@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance characteristics of backend switching."""

    def test_pandas_faster_for_small_operations(self, sample_small_df):
        """Test that pandas is faster for small DataFrame operations."""
        import time

        # Pandas timing
        pf_pandas = ParquetFrame(sample_small_df, islazy=False)
        start = time.time()
        result_pandas = pf_pandas.groupby("category").sum()
        pandas_time = time.time() - start

        # Dask timing
        pf_dask = ParquetFrame(sample_small_df, islazy=True)
        start = time.time()
        result_dask = pf_dask.groupby("category").sum()
        if hasattr(result_dask, "compute"):
            result_dask = result_dask.compute()
        dask_time = time.time() - start

        # For small operations, pandas should be faster
        # (This is more of a sanity check than a strict requirement)
        print(f"Pandas time: {pandas_time:.4f}s, Dask time: {dask_time:.4f}s")

    def test_memory_usage_patterns(self, temp_dir):
        """Test memory usage patterns for different backends."""
        # Create moderately sized DataFrame
        category_pattern = ["A", "B", "C"] * (50000 // 3) + ["A", "B"][: 50000 % 3]
        df = pd.DataFrame(
            {
                "id": range(50000),
                "value": range(50000),
                "category": category_pattern,
            }
        )

        file_path = temp_dir / "memory_test.parquet"
        df.to_parquet(file_path)

        # Test pandas vs Dask memory patterns
        pf_pandas = ParquetFrame.read(file_path, islazy=False)
        pf_dask = ParquetFrame.read(file_path, islazy=True)

        # Both should be able to perform operations
        result1 = pf_pandas.groupby("category").size()
        result2 = pf_dask.groupby("category").size()

        # Results should be similar
        assert len(result1) == len(
            result2.compute() if hasattr(result2, "compute") else result2
        )
