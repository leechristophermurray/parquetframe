"""
I/O format tests for parquet file variants, compression options, and edge cases.
"""

import os
from pathlib import Path

import dask.dataframe as dd
import pandas as pd
import pytest

from parquetframe.core import ParquetFrame


class TestParquetFormatSupport:
    """Test support for various parquet formats and configurations."""

    def test_read_uncompressed_parquet(self, mixed_types_df, temp_dir):
        """Test reading uncompressed parquet files."""
        file_path = temp_dir / "uncompressed.parquet"
        mixed_types_df.to_parquet(file_path, compression=None)

        pf = ParquetFrame.read(file_path)
        assert isinstance(pf._df, pd.DataFrame)
        pd.testing.assert_frame_equal(
            pf._df.reset_index(drop=True), mixed_types_df.reset_index(drop=True)
        )

    def test_read_snappy_compressed(self, mixed_types_df, temp_dir):
        """Test reading snappy compressed parquet files."""
        file_path = temp_dir / "snappy.parquet"
        mixed_types_df.to_parquet(file_path, compression="snappy")

        pf = ParquetFrame.read(file_path)
        assert isinstance(pf._df, pd.DataFrame)
        pd.testing.assert_frame_equal(
            pf._df.reset_index(drop=True), mixed_types_df.reset_index(drop=True)
        )

    def test_read_gzip_compressed(self, mixed_types_df, temp_dir):
        """Test reading gzip compressed parquet files."""
        file_path = temp_dir / "gzip.parquet"
        mixed_types_df.to_parquet(file_path, compression="gzip")

        pf = ParquetFrame.read(file_path)
        assert isinstance(pf._df, pd.DataFrame)
        pd.testing.assert_frame_equal(
            pf._df.reset_index(drop=True), mixed_types_df.reset_index(drop=True)
        )

    def test_read_brotli_compressed(self, mixed_types_df, temp_dir):
        """Test reading brotli compressed parquet files."""
        try:
            file_path = temp_dir / "brotli.parquet"
            mixed_types_df.to_parquet(file_path, compression="brotli")

            pf = ParquetFrame.read(file_path)
            assert isinstance(pf._df, pd.DataFrame)
            pd.testing.assert_frame_equal(
                pf._df.reset_index(drop=True), mixed_types_df.reset_index(drop=True)
            )
        except ValueError:
            # Skip if brotli is not available
            pytest.skip("Brotli compression not available")


class TestDataTypePreservation:
    """Test that various data types are preserved correctly."""

    def test_mixed_data_types_preservation(self, mixed_types_df, temp_dir):
        """Test that mixed data types are preserved through read/save cycle."""
        file_path = temp_dir / "mixed_types.parquet"

        # Save with ParquetFrame
        pf = ParquetFrame(mixed_types_df, islazy=False)
        pf.save(file_path)

        # Read back
        pf_read = ParquetFrame.read(file_path)

        # Check data types are preserved
        for col in mixed_types_df.columns:
            original_dtype = mixed_types_df[col].dtype
            read_dtype = pf_read[col].dtype

            # Some minor type changes are acceptable (e.g., int64 -> int32)
            if original_dtype.kind == "i" and read_dtype.kind == "i":
                continue  # Integer types may change precision
            elif original_dtype.kind == "f" and read_dtype.kind == "f":
                continue  # Float types may change precision
            else:
                assert (
                    original_dtype == read_dtype
                ), f"Type mismatch for {col}: {original_dtype} vs {read_dtype}"

    def test_datetime_preservation(self, temp_dir):
        """Test that datetime columns are preserved correctly."""
        df = pd.DataFrame(
            {
                "date_col": pd.date_range("2023-01-01", periods=10),
                "timestamp_col": pd.date_range(
                    "2023-01-01 12:00:00", periods=10, freq="H"
                ),
                "value": range(10),
            }
        )

        file_path = temp_dir / "datetime_test.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)

        # Check datetime columns
        assert pf_read["date_col"].dtype.kind == "M"  # datetime64
        assert pf_read["timestamp_col"].dtype.kind == "M"  # datetime64

        pd.testing.assert_frame_equal(
            pf_read._df.reset_index(drop=True), df.reset_index(drop=True)
        )

    def test_categorical_data_preservation(self, temp_dir):
        """Test that categorical data is handled correctly."""
        df = pd.DataFrame(
            {
                "category_col": pd.Categorical(["A", "B", "C", "A", "B"]),
                "normal_col": [1, 2, 3, 4, 5],
            }
        )

        file_path = temp_dir / "categorical_test.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)

        # Categorical might be converted to string, which is acceptable
        assert len(pf_read) == len(df)
        assert list(pf_read["category_col"].unique()) == ["A", "B", "C"]

    def test_null_values_preservation(self, temp_dir):
        """Test that null values are preserved correctly."""
        df = pd.DataFrame(
            {
                "int_with_nulls": [1, 2, None, 4, 5],
                "str_with_nulls": ["a", None, "c", "d", None],
                "float_with_nulls": [1.1, 2.2, None, 4.4, 5.5],
            }
        )

        file_path = temp_dir / "nulls_test.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)

        # Check null counts are preserved
        for col in df.columns:
            original_nulls = df[col].isnull().sum()
            read_nulls = pf_read[col].isnull().sum()
            assert original_nulls == read_nulls, f"Null count mismatch for {col}"


class TestLargeFileHandling:
    """Test handling of large files with different backends."""

    @pytest.mark.slow
    def test_large_file_dask_backend(self, large_parquet_file):
        """Test that large files automatically use Dask backend."""
        pf = ParquetFrame.read(large_parquet_file)

        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True

        # Test basic operations work
        count = len(pf)  # This should work with Dask
        assert count > 0

    @pytest.mark.slow
    def test_large_file_forced_pandas(self, large_parquet_file):
        """Test forcing pandas backend on large files."""
        # This might consume significant memory
        pf = ParquetFrame.read(large_parquet_file, islazy=False)

        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False

        # Test basic operations work
        assert len(pf) > 0

    def test_chunked_reading_simulation(self, temp_dir):
        """Test behavior with moderately large files."""
        # Create a moderately large file (not huge, but larger than small test data)
        df = pd.DataFrame(
            {
                "id": range(10000),
                "value": range(10000),
                "category": ["A", "B", "C", "D"] * 2500,
            }
        )

        file_path = temp_dir / "moderate_size.parquet"
        df.to_parquet(file_path)

        # Test with different thresholds
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        # Should use pandas with high threshold
        pf1 = ParquetFrame.read(file_path, threshold_mb=file_size_mb + 1)
        assert isinstance(pf1._df, pd.DataFrame)

        # Should use Dask with low threshold
        pf2 = ParquetFrame.read(file_path, threshold_mb=file_size_mb - 0.1)
        assert isinstance(pf2._df, dd.DataFrame)


class TestSaveFormats:
    """Test saving in various formats and configurations."""

    def test_save_with_different_compressions(self, mixed_types_df, temp_dir):
        """Test saving with different compression options."""
        pf = ParquetFrame(mixed_types_df, islazy=False)

        # Test different compressions
        compressions = ["snappy", "gzip", "brotli", None]

        for compression in compressions:
            try:
                output_path = temp_dir / f"test_{compression or 'none'}.parquet"
                pf.save(output_path, compression=compression)

                assert output_path.exists()

                # Verify file can be read back
                pf_read = ParquetFrame.read(output_path)
                assert len(pf_read) == len(mixed_types_df)

            except ValueError as e:
                if compression == "brotli" and "brotli" in str(e).lower():
                    # Skip if compression not available
                    continue
                else:
                    raise

    def test_save_with_custom_options(self, mixed_types_df, temp_dir):
        """Test saving with custom parquet options."""
        pf = ParquetFrame(mixed_types_df, islazy=False)

        output_path = temp_dir / "custom_options.parquet"

        # Test with custom options (these should be passed through)
        pf.save(output_path, compression="snappy", index=False)

        assert output_path.exists()

        # Verify the file
        pf_read = ParquetFrame.read(output_path)
        assert len(pf_read) == len(mixed_types_df)

    def test_save_dask_multipart(self, sample_small_df, temp_dir):
        """Test saving Dask DataFrame (which may create multiple files)."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)

        output_path = temp_dir / "dask_multipart"
        pf.save(output_path)

        expected_path = temp_dir / "dask_multipart.parquet"
        # Dask may create a directory or a single file depending on the data
        assert expected_path.exists() or expected_path.is_dir()

        # Should be readable
        pf_read = ParquetFrame.read(expected_path)
        assert len(pf_read) == len(sample_small_df)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe_handling(self, temp_dir):
        """Test handling of empty DataFrames."""
        # Create a DataFrame with columns but no rows
        empty_df = pd.DataFrame(columns=["a", "b", "c"])

        file_path = temp_dir / "empty.parquet"
        empty_df.to_parquet(file_path)

        # Should be able to read it
        pf = ParquetFrame.read(file_path)
        assert isinstance(pf._df, pd.DataFrame)
        assert len(pf) == 0
        assert list(pf.columns) == ["a", "b", "c"]

    def test_single_row_dataframe(self, temp_dir):
        """Test handling of single-row DataFrames."""
        df = pd.DataFrame({"a": [1], "b": ["test"], "c": [3.14]})

        file_path = temp_dir / "single_row.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)
        assert len(pf_read) == 1
        pd.testing.assert_frame_equal(
            pf_read._df.reset_index(drop=True), df.reset_index(drop=True)
        )

    def test_single_column_dataframe(self, temp_dir):
        """Test handling of single-column DataFrames."""
        df = pd.DataFrame({"single_col": range(100)})

        file_path = temp_dir / "single_col.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)
        assert len(pf_read.columns) == 1
        assert pf_read.columns[0] == "single_col"

    def test_very_wide_dataframe(self, temp_dir):
        """Test handling of DataFrames with many columns."""
        # Create a DataFrame with many columns
        data = {f"col_{i}": [i] * 10 for i in range(100)}
        df = pd.DataFrame(data)

        file_path = temp_dir / "wide.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)
        assert len(pf_read.columns) == 100
        assert len(pf_read) == 10

    def test_special_characters_in_columns(self, temp_dir):
        """Test handling of column names with special characters."""
        df = pd.DataFrame(
            {
                "normal_col": [1, 2, 3],
                "col with spaces": [4, 5, 6],
                "col-with-dashes": [7, 8, 9],
                "col_with_underscores": [10, 11, 12],
                "col.with.dots": [13, 14, 15],
            }
        )

        file_path = temp_dir / "special_chars.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)

        # Column names should be preserved
        expected_cols = set(df.columns)
        actual_cols = set(pf_read.columns)
        assert expected_cols == actual_cols

    def test_unicode_data(self, temp_dir):
        """Test handling of Unicode data."""
        df = pd.DataFrame(
            {
                "unicode_col": ["Hello", "世界", "Ñiño", "Café", "🚀"],
                "value": [1, 2, 3, 4, 5],
            }
        )

        file_path = temp_dir / "unicode.parquet"
        pf = ParquetFrame(df, islazy=False)
        pf.save(file_path)

        pf_read = ParquetFrame.read(file_path)

        # Unicode should be preserved
        pd.testing.assert_frame_equal(
            pf_read._df.reset_index(drop=True), df.reset_index(drop=True)
        )


class TestFilePathEdgeCases:
    """Test edge cases related to file paths and extensions."""

    def test_nested_directory_creation(self, temp_dir):
        """Test saving to nested directories that don't exist."""
        nested_path = temp_dir / "nested" / "deep" / "path" / "file"

        df = pd.DataFrame({"a": [1, 2, 3]})
        pf = ParquetFrame(df, islazy=False)

        # This should create the nested directories
        pf.save(nested_path)

        expected_file = temp_dir / "nested" / "deep" / "path" / "file.parquet"
        assert expected_file.exists()

    def test_path_object_handling(self, mixed_types_df, temp_dir):
        """Test that Path objects are handled correctly."""
        file_path = Path(temp_dir) / "path_object.parquet"

        pf = ParquetFrame(mixed_types_df, islazy=False)
        pf.save(file_path)

        assert file_path.exists()

        # Should be able to read with Path object too
        pf_read = ParquetFrame.read(file_path)
        assert len(pf_read) == len(mixed_types_df)

    def test_relative_path_handling(self, mixed_types_df, temp_dir):
        """Test handling of relative paths."""
        # Change to temp directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            relative_path = "relative_test"
            pf = ParquetFrame(mixed_types_df, islazy=False)
            pf.save(relative_path)

            assert Path("relative_test.parquet").exists()

            # Should be able to read back
            pf_read = ParquetFrame.read(relative_path)
            assert len(pf_read) == len(mixed_types_df)

        finally:
            os.chdir(original_cwd)

    def test_file_extension_precedence(self, sample_small_df, temp_dir):
        """Test file extension precedence when multiple extensions exist."""
        base_name = "precedence_test"

        # Create .parquet file
        parquet_path = temp_dir / f"{base_name}.parquet"
        sample_small_df.to_parquet(parquet_path)

        # Create .pqt file with different data
        pqt_path = temp_dir / f"{base_name}.pqt"
        modified_df = sample_small_df.copy()
        modified_df["extra"] = "extra_data"
        modified_df.to_parquet(pqt_path)

        # Reading without extension should prefer .parquet
        pf = ParquetFrame.read(temp_dir / base_name)

        # Should have read the .parquet file (no extra column)
        assert "extra" not in pf.columns

        # But should be able to read .pqt explicitly
        pf_pqt = ParquetFrame.read(pqt_path)
        assert "extra" in pf_pqt.columns
