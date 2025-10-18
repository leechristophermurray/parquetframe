"""
Tests for multi-format IO functionality in ParquetFrame.

Tests the new multi-format architecture including CSV, JSON, and ORC support
with both pandas and Dask backends.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from parquetframe.core import FORMAT_HANDLERS, FileFormat, detect_format
from parquetframe.legacy import ParquetFrame


class TestFormatDetection:
    """Test format detection functionality."""

    def test_detect_format_by_extension(self):
        """Test format detection from file extensions."""
        assert detect_format("data.csv") == FileFormat.CSV
        assert detect_format("data.tsv") == FileFormat.CSV
        assert detect_format("data.json") == FileFormat.JSON
        assert detect_format("data.jsonl") == FileFormat.JSON
        assert detect_format("data.ndjson") == FileFormat.JSON
        assert detect_format("data.parquet") == FileFormat.PARQUET
        assert detect_format("data.pqt") == FileFormat.PARQUET
        assert detect_format("data.orc") == FileFormat.ORC

    def test_detect_format_explicit(self):
        """Test explicit format specification overrides extension."""
        assert detect_format("data.txt", explicit_format="csv") == FileFormat.CSV
        assert detect_format("data.unknown", explicit_format="JSON") == FileFormat.JSON
        assert (
            detect_format("data.csv", explicit_format="parquet") == FileFormat.PARQUET
        )

    def test_detect_format_case_insensitive(self):
        """Test case-insensitive format detection."""
        assert detect_format("data.CSV") == FileFormat.CSV
        assert detect_format("data.JSON") == FileFormat.JSON
        assert detect_format("data.PARQUET") == FileFormat.PARQUET

    def test_detect_format_unknown_defaults_to_parquet(self):
        """Test unknown extensions default to parquet for backwards compatibility."""
        assert detect_format("data.unknown") == FileFormat.PARQUET
        assert detect_format("data") == FileFormat.PARQUET

    def test_detect_format_invalid_explicit_format(self):
        """Test invalid explicit format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported format: invalid"):
            detect_format("data.txt", explicit_format="invalid")


class TestFormatHandlers:
    """Test individual format handlers."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "score": [85.5, 92.0, 78.5],
            }
        )

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files with Windows-compatible cleanup."""
        import os
        import shutil
        import time

        tmpdir = tempfile.mkdtemp()
        try:
            yield Path(tmpdir)
        finally:
            # Windows-compatible cleanup with retry logic
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    if os.name == "nt":
                        # On Windows, force garbage collection and wait briefly
                        import gc

                        gc.collect()
                        time.sleep(0.1)
                    shutil.rmtree(tmpdir)
                    break
                except (PermissionError, OSError) as e:
                    if attempt == max_attempts - 1:
                        # On final attempt, try to make files writable and retry
                        try:
                            for root, _dirs, files in os.walk(tmpdir):
                                for fname in files:
                                    file_path = os.path.join(root, fname)
                                    try:
                                        os.chmod(file_path, 0o777)
                                    except OSError:
                                        pass
                            time.sleep(0.2)
                            shutil.rmtree(tmpdir)
                        except (PermissionError, OSError):
                            # If we still can't delete, log and continue
                            # The OS will clean up temp files eventually
                            pass
                    else:
                        time.sleep(0.1)

    def test_csv_handler_roundtrip_pandas(self, sample_data, temp_dir):
        """Test CSV handler with pandas backend."""
        handler = FORMAT_HANDLERS[FileFormat.CSV]
        csv_path = temp_dir / "test.csv"

        # Write and read back
        handler.write(sample_data, csv_path)
        result = handler.read(csv_path, use_dask=False)

        assert isinstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result.reset_index(drop=True), sample_data)

    def test_csv_handler_roundtrip_dask(self, sample_data, temp_dir):
        """Test CSV handler with Dask backend."""
        pytest.importorskip("dask")

        handler = FORMAT_HANDLERS[FileFormat.CSV]
        csv_path = temp_dir / "test.csv"

        # Write and read back with Dask
        handler.write(sample_data, csv_path)
        result = handler.read(csv_path, use_dask=True)

        # Convert Dask to pandas for comparison
        import dask.dataframe as dd

        assert isinstance(result, dd.DataFrame)
        result_pandas = result.compute().reset_index(drop=True)

        # Compare more flexibly due to possible dtype differences with Dask
        assert len(result_pandas) == len(sample_data)
        assert list(result_pandas.columns) == list(sample_data.columns)
        # Compare values rather than dtypes
        for col in sample_data.columns:
            if sample_data[col].dtype == "object":
                # For string columns, compare as strings
                assert (
                    result_pandas[col].astype(str).tolist()
                    == sample_data[col].astype(str).tolist()
                )
            else:
                # For numeric columns, use approximate comparison
                pd.testing.assert_series_equal(
                    result_pandas[col], sample_data[col], check_dtype=False
                )

    def test_csv_handler_tsv_support(self, sample_data, temp_dir):
        """Test TSV support with automatic delimiter detection."""
        handler = FORMAT_HANDLERS[FileFormat.CSV]
        tsv_path = temp_dir / "test.tsv"

        # Write and read back TSV
        handler.write(sample_data, tsv_path)
        result = handler.read(tsv_path, use_dask=False)

        assert isinstance(result, pd.DataFrame)
        # Check that the file was written with tab delimiter
        with open(tsv_path) as f:
            first_line = f.readline()
            assert "\t" in first_line

    def test_json_handler_roundtrip_pandas(self, sample_data, temp_dir):
        """Test JSON handler with pandas backend."""
        handler = FORMAT_HANDLERS[FileFormat.JSON]
        json_path = temp_dir / "test.json"

        # Write and read back
        handler.write(sample_data, json_path)
        result = handler.read(json_path, use_dask=False)

        assert isinstance(result, pd.DataFrame)
        # JSON may change column order and dtypes, so compare more flexibly
        assert set(result.columns) == set(sample_data.columns)
        assert len(result) == len(sample_data)

    def test_json_handler_jsonl_format(self, sample_data, temp_dir):
        """Test JSON Lines format handling."""
        handler = FORMAT_HANDLERS[FileFormat.JSON]
        jsonl_path = temp_dir / "test.jsonl"

        # Write and read back JSONL
        handler.write(sample_data, jsonl_path)
        result = handler.read(jsonl_path, use_dask=False)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data)

        # Verify file format is JSON Lines
        with open(jsonl_path) as f:
            lines = f.readlines()
            assert len(lines) == len(sample_data)
            # Each line should be valid JSON
            for line in lines:
                json.loads(line.strip())

    def test_parquet_handler_roundtrip(self, sample_data, temp_dir):
        """Test Parquet handler maintains existing functionality."""
        handler = FORMAT_HANDLERS[FileFormat.PARQUET]
        parquet_path = temp_dir / "test.parquet"

        # Write and read back
        handler.write(sample_data, parquet_path)
        result = handler.read(parquet_path, use_dask=False)

        assert isinstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result, sample_data)

    @pytest.mark.skipif(
        not pytest.importorskip("pyarrow", reason="pyarrow required for ORC support"),
        reason="pyarrow not available",
    )
    def test_orc_handler_basic_functionality(self, sample_data, temp_dir):
        """Test ORC handler basic functionality if pyarrow is available."""
        import os

        # Skip ORC tests on Windows due to timezone database issues with Arrow
        if os.name == "nt":
            pytest.skip("ORC tests skipped on Windows due to timezone database issues")

        try:
            # Use simplified data without potential datetime/timezone issues
            simple_data = pd.DataFrame(
                {
                    "id": [1, 2, 3],
                    "value": [10.5, 20.5, 30.5],
                    "category": ["A", "B", "C"],
                }
            )

            handler = FORMAT_HANDLERS[FileFormat.ORC]
            orc_path = temp_dir / "test.orc"

            # Write and read back
            handler.write(simple_data, orc_path)

            # Ensure file handle is closed before reading
            import gc

            gc.collect()

            result = handler.read(orc_path, use_dask=False)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(simple_data)
            assert set(result.columns) == set(simple_data.columns)

        except (ImportError, Exception) as e:
            if "pyarrow" in str(e).lower():
                pytest.skip("pyarrow with ORC support not available")
            elif "time zone" in str(e).lower() or "tzdata" in str(e).lower():
                pytest.skip(f"ORC timezone issue on this platform: {e}")
            else:
                raise

    def test_handler_path_resolution(self, temp_dir):
        """Test path resolution with extension detection."""
        # Create test files
        csv_path = temp_dir / "test.csv"
        pd.DataFrame({"a": [1, 2]}).to_csv(csv_path, index=False)

        handler = FORMAT_HANDLERS[FileFormat.CSV]

        # Should find file with extension
        resolved = handler.resolve_file_path(temp_dir / "test.csv")
        assert resolved == csv_path

        # Should find file without extension
        resolved = handler.resolve_file_path(temp_dir / "test")
        assert resolved == csv_path

        # Should raise FileNotFoundError for non-existent file
        with pytest.raises(FileNotFoundError):
            handler.resolve_file_path(temp_dir / "nonexistent")


class TestParquetFrameMultiformat:
    """Test ParquetFrame with multi-format support."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "name": ["Alice", "Bob", "Charlie", "David"],
                "age": [25, 30, 35, 40],
                "active": [True, False, True, True],
            }
        )

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files with Windows-compatible cleanup."""
        import os
        import shutil
        import time

        tmpdir = tempfile.mkdtemp()
        try:
            yield Path(tmpdir)
        finally:
            # Windows-compatible cleanup with retry logic
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    if os.name == "nt":
                        # On Windows, force garbage collection and wait briefly
                        import gc

                        gc.collect()
                        time.sleep(0.1)
                    shutil.rmtree(tmpdir)
                    break
                except (PermissionError, OSError) as e:
                    if attempt == max_attempts - 1:
                        # On final attempt, try to make files writable and retry
                        try:
                            for root, _dirs, files in os.walk(tmpdir):
                                for fname in files:
                                    file_path = os.path.join(root, fname)
                                    try:
                                        os.chmod(file_path, 0o777)
                                    except OSError:
                                        pass
                            time.sleep(0.2)
                            shutil.rmtree(tmpdir)
                        except (PermissionError, OSError):
                            # If we still can't delete, log and continue
                            # The OS will clean up temp files eventually
                            pass
                    else:
                        time.sleep(0.1)

    def test_read_csv_auto_detection(self, sample_data, temp_dir):
        """Test reading CSV with automatic format detection."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        # Read with format auto-detection
        pf = ParquetFrame.read(csv_path)

        assert isinstance(pf._df, pd.DataFrame)
        assert len(pf) == len(sample_data)
        assert set(pf._df.columns) == set(sample_data.columns)

    def test_read_json_auto_detection(self, sample_data, temp_dir):
        """Test reading JSON with automatic format detection."""
        json_path = temp_dir / "test.json"
        # Write as regular JSON (not lines format)
        sample_data.to_json(json_path, orient="records")

        # Read with format auto-detection
        pf = ParquetFrame.read(json_path)

        assert isinstance(pf._df, pd.DataFrame)
        assert len(pf) == len(sample_data)

    def test_read_with_explicit_format(self, sample_data, temp_dir):
        """Test reading with explicit format specification."""
        # Create CSV file with .txt extension
        txt_path = temp_dir / "test.txt"
        sample_data.to_csv(txt_path, index=False)

        # Read as CSV despite .txt extension
        pf = ParquetFrame.read(txt_path, format="csv")

        assert isinstance(pf._df, pd.DataFrame)
        assert len(pf) == len(sample_data)

    def test_read_with_dask_backend(self, sample_data, temp_dir):
        """Test reading with forced Dask backend."""
        csv_path = temp_dir / "test.csv"
        sample_data.to_csv(csv_path, index=False)

        # Force Dask backend
        pf = ParquetFrame.read(csv_path, islazy=True)

        import dask.dataframe as dd

        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True

    def test_read_backend_selection_by_size(self, temp_dir):
        """Test automatic backend selection based on file size."""
        # Create small CSV file (should use pandas)
        small_data = pd.DataFrame({"x": range(10)})
        small_csv = temp_dir / "small.csv"
        small_data.to_csv(small_csv, index=False)

        pf_small = ParquetFrame.read(small_csv, threshold_mb=1)
        assert pf_small.islazy is False

        # For large files, we'd need to create a file >threshold, but that's
        # impractical in tests. The logic is tested in the implementation.

    def test_save_format_detection(self, temp_dir):
        """Test saving with format detection from file extension."""
        # Create a ParquetFrame
        data = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        pf = ParquetFrame(data)

        # Save as different formats
        csv_path = temp_dir / "output.csv"
        json_path = temp_dir / "output.json"

        # The save method needs to be updated to use format handlers
        # For now, this tests the current functionality
        # TODO: Update save method to use format handlers

    def test_multiformat_error_handling(self):
        """Test error handling for multi-format functionality."""
        # Test invalid format
        with pytest.raises(ValueError, match="Unsupported format"):
            ParquetFrame.read("test.txt", format="invalid")

        # Test missing file
        with pytest.raises(FileNotFoundError):
            ParquetFrame.read("nonexistent.csv")

    def test_backward_compatibility(self, sample_data, temp_dir):
        """Test that existing parquet functionality still works."""
        parquet_path = temp_dir / "test.parquet"
        sample_data.to_parquet(parquet_path)

        # Should still work without extension
        pf = ParquetFrame.read(temp_dir / "test")
        assert isinstance(pf._df, pd.DataFrame)
        assert len(pf) == len(sample_data)

        # Should work with explicit .parquet
        pf2 = ParquetFrame.read(parquet_path)
        assert isinstance(pf2._df, pd.DataFrame)
        assert len(pf2) == len(sample_data)


class TestOrcHandlerEdgeCases:
    """Test ORC handler edge cases and error conditions."""

    def test_orc_handler_import_error(self):
        """Test ORC handler gracefully handles missing pyarrow."""
        handler = FORMAT_HANDLERS[FileFormat.ORC]

        # Patch the specific import inside the ORC handler methods
        with patch.dict("sys.modules", {"pyarrow.orc": None}):
            with pytest.raises(ImportError, match="ORC support requires pyarrow"):
                handler.read("dummy.orc")

        with patch.dict("sys.modules", {"pyarrow": None, "pyarrow.orc": None}):
            with pytest.raises(ImportError, match="ORC support requires pyarrow"):
                handler.write(pd.DataFrame({"a": [1]}), "dummy.orc")


@pytest.mark.integration
class TestMultiFormatIntegration:
    """Integration tests for multi-format functionality."""

    def test_format_conversion_workflow(self):
        """Test converting between different formats."""
        # This would test a complete workflow:
        # 1. Read CSV
        # 2. Process data
        # 3. Save as JSON
        # 4. Read JSON back
        # 5. Save as Parquet
        # This tests the round-trip compatibility between formats

        data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2023-01-01", periods=5),
                "value": [10.5, 15.2, 8.7, 12.1, 9.8],
                "category": ["A", "B", "A", "C", "B"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create initial CSV
            csv_path = tmpdir / "data.csv"
            data.to_csv(csv_path, index=False)

            # Read CSV -> Process -> Save as JSON
            pf = ParquetFrame.read(csv_path)
            processed = pf.query("value > 10")  # Simple processing

            # Note: Currently save() method only supports parquet
            # This test documents the expected future functionality
            # TODO: Implement multi-format save() method
