"""
Edge case tests and error handling scenarios.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import dask.dataframe as dd
import pytest

from parquetframe.core import ParquetFrame
import parquetframe as pqf


class TestFileNotFoundErrors:
    """Test file not found error scenarios."""
    
    def test_read_nonexistent_file_with_extension(self, temp_dir):
        """Test reading nonexistent file with explicit extension."""
        nonexistent = temp_dir / "nonexistent.parquet"
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            ParquetFrame.read(nonexistent)
            
    def test_read_nonexistent_file_without_extension(self, temp_dir):
        """Test reading nonexistent file without extension."""
        nonexistent = temp_dir / "nonexistent"
        
        with pytest.raises(FileNotFoundError, match="No parquet file found"):
            ParquetFrame.read(nonexistent)
            
    def test_read_empty_directory_path(self, temp_dir):
        """Test reading from a directory path instead of file."""
        empty_dir = temp_dir / "empty_dir"
        empty_dir.mkdir()
        
        with pytest.raises(FileNotFoundError):
            ParquetFrame.read(empty_dir)
            
    def test_read_with_permission_denied(self, temp_dir, sample_small_df):
        """Test reading file with permission issues."""
        file_path = temp_dir / "readonly.parquet"
        sample_small_df.to_parquet(file_path)
        
        # Make file unreadable (on systems that support this)
        try:
            file_path.chmod(0o000)
            
            with pytest.raises(PermissionError):
                ParquetFrame.read(file_path)
                
        except (OSError, AttributeError):
            # Skip on systems that don't support chmod or permission errors
            pytest.skip("Permission testing not supported on this system")
        finally:
            try:
                file_path.chmod(0o644)  # Restore permissions for cleanup
            except (OSError, AttributeError):
                pass


class TestSaveErrors:
    """Test save operation error scenarios."""
    
    def test_save_empty_parquetframe(self, temp_dir):
        """Test saving ParquetFrame with no dataframe."""
        pf = ParquetFrame()
        
        with pytest.raises(TypeError, match="No dataframe loaded to save"):
            pf.save(temp_dir / "output")
            
    def test_save_to_readonly_directory(self, sample_small_df, temp_dir):
        """Test saving to readonly directory."""
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        
        try:
            readonly_dir.chmod(0o444)  # Make readonly
            
            pf = ParquetFrame(sample_small_df, islazy=False)
            
            with pytest.raises(PermissionError):
                pf.save(readonly_dir / "output")
                
        except (OSError, AttributeError):
            pytest.skip("Permission testing not supported on this system")
        finally:
            try:
                readonly_dir.chmod(0o755)  # Restore permissions
            except (OSError, AttributeError):
                pass
                
    def test_save_invalid_file_name(self, sample_small_df):
        """Test saving with invalid file names."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        # Test various invalid file names (platform dependent)
        invalid_names = []
        if os.name == 'nt':  # Windows
            invalid_names = ['CON', 'PRN', 'AUX', 'NUL']
        else:  # Unix-like
            invalid_names = ['']  # Empty string
            
        for invalid_name in invalid_names:
            if invalid_name:  # Skip empty string test for now
                try:
                    with pytest.raises(OSError):
                        pf.save(invalid_name)
                except OSError:
                    # Expected behavior
                    pass
                    
    def test_save_disk_full_simulation(self, sample_small_df, temp_dir):
        """Test save operation when disk is full (simulated)."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        # Mock the to_parquet method to raise OSError (disk full)
        with patch.object(pd.DataFrame, 'to_parquet', side_effect=OSError("No space left on device")):
            with pytest.raises(OSError, match="No space left on device"):
                pf.save(temp_dir / "output")


class TestCorruptedFileHandling:
    """Test handling of corrupted or invalid parquet files."""
    
    def test_read_empty_file(self, temp_dir):
        """Test reading empty file with .parquet extension."""
        empty_file = temp_dir / "empty.parquet"
        empty_file.touch()  # Create empty file
        
        with pytest.raises((pd.errors.EmptyDataError, Exception)):
            ParquetFrame.read(empty_file)
            
    def test_read_text_file_with_parquet_extension(self, temp_dir):
        """Test reading text file with .parquet extension."""
        fake_parquet = temp_dir / "fake.parquet"
        fake_parquet.write_text("This is not a parquet file")
        
        with pytest.raises(Exception):  # Various exceptions possible
            ParquetFrame.read(fake_parquet)
            
    def test_read_truncated_parquet_file(self, temp_dir, sample_small_df):
        """Test reading truncated parquet file."""
        file_path = temp_dir / "truncated.parquet"
        sample_small_df.to_parquet(file_path)
        
        # Truncate the file
        with open(file_path, 'r+b') as f:
            f.truncate(100)  # Keep only first 100 bytes
            
        with pytest.raises(Exception):  # Various exceptions possible
            ParquetFrame.read(file_path)


class TestMemoryLimitErrors:
    """Test behavior when hitting memory limits."""
    
    @pytest.mark.slow
    def test_large_file_memory_warning(self, temp_dir):
        """Test handling very large files that might cause memory issues."""
        # Create a large DataFrame that would use significant memory
        try:
            large_df = pd.DataFrame({
                'id': range(5_000_000),  # 5M rows
                'value': range(5_000_000),
                'text': ['test_string'] * 5_000_000
            })
            
            file_path = temp_dir / "very_large.parquet"
            large_df.to_parquet(file_path)
            
            # Reading with Dask should work
            pf = ParquetFrame.read(file_path, islazy=True)
            assert isinstance(pf._df, dd.DataFrame)
            
            # Force pandas might cause memory issues (but shouldn't crash)
            try:
                pf_pandas = ParquetFrame.read(file_path, islazy=False)
                assert isinstance(pf_pandas._df, pd.DataFrame)
            except MemoryError:
                # This is acceptable for very large files
                pytest.skip("Not enough memory for large pandas DataFrame")
                
        except MemoryError:
            pytest.skip("Not enough memory to create large test DataFrame")


class TestNetworkPathErrors:
    """Test errors related to network paths and remote files."""
    
    def test_read_invalid_url(self):
        """Test reading from invalid URL."""
        invalid_urls = [
            "http://nonexistent.domain/file.parquet",
            "https://invalid-url-12345.com/file.parquet",
            "ftp://invalid-ftp.com/file.parquet"
        ]
        
        for url in invalid_urls:
            with pytest.raises(Exception):  # Various network exceptions
                ParquetFrame.read(url)
                
    def test_read_network_timeout_simulation(self):
        """Test network timeout simulation."""
        # Mock network timeout
        with patch('pandas.read_parquet', side_effect=TimeoutError("Network timeout")):
            with pytest.raises(TimeoutError):
                ParquetFrame.read("http://example.com/file.parquet")


class TestTypeErrors:
    """Test type-related errors and edge cases."""
    
    def test_invalid_threshold_type(self, small_parquet_file):
        """Test invalid threshold types."""
        with pytest.raises(TypeError):
            ParquetFrame.read(small_parquet_file, threshold_mb="invalid")
            
    def test_invalid_islazy_type(self, small_parquet_file):
        """Test invalid islazy types."""
        with pytest.raises(TypeError):
            ParquetFrame.read(small_parquet_file, islazy="invalid")
            
    def test_invalid_npartitions_type(self, sample_small_df):
        """Test invalid npartitions type for to_dask."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        with pytest.raises(TypeError):
            pf.to_dask(npartitions="invalid")
            
    def test_negative_threshold(self, small_parquet_file):
        """Test negative threshold values."""
        # Negative threshold should still work (interpreted as 0)
        pf = ParquetFrame.read(small_parquet_file, threshold_mb=-1)
        # Should use Dask since any file size > -1MB
        assert isinstance(pf._df, dd.DataFrame)
        
    def test_negative_npartitions(self, sample_small_df):
        """Test negative npartitions values."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        with pytest.raises(ValueError):
            pf.to_dask(npartitions=-1)


class TestConcurrencyErrors:
    """Test concurrency and race condition scenarios."""
    
    def test_file_deleted_during_read(self, temp_dir, sample_small_df):
        """Test file being deleted during read operation."""
        file_path = temp_dir / "temp_file.parquet"
        sample_small_df.to_parquet(file_path)
        
        # Mock the file being deleted between resolution and reading
        original_read_parquet = pd.read_parquet
        
        def mock_read_parquet(path, **kwargs):
            # Delete the file before pandas tries to read it
            if Path(path).exists():
                Path(path).unlink()
            return original_read_parquet(path, **kwargs)
        
        with patch('pandas.read_parquet', side_effect=mock_read_parquet):
            with pytest.raises(FileNotFoundError):
                ParquetFrame.read(file_path)
                
    def test_concurrent_write_simulation(self, temp_dir, sample_small_df):
        """Test concurrent write operations."""
        file_path = temp_dir / "concurrent.parquet"
        
        pf1 = ParquetFrame(sample_small_df, islazy=False)
        pf2 = ParquetFrame(sample_small_df, islazy=False)
        
        # First write should succeed
        pf1.save(file_path)
        assert file_path.exists()
        
        # Second write should overwrite (this is expected behavior)
        pf2.save(file_path)
        assert file_path.exists()


class TestResourceCleanupErrors:
    """Test resource cleanup and file handle errors."""
    
    def test_file_handle_cleanup(self, temp_dir, sample_small_df):
        """Test that file handles are properly cleaned up."""
        file_path = temp_dir / "handle_test.parquet"
        sample_small_df.to_parquet(file_path)
        
        # Read file multiple times to test handle cleanup
        for _ in range(10):
            pf = ParquetFrame.read(file_path)
            assert len(pf) == len(sample_small_df)
            
        # File should still be deletable (no lingering handles)
        file_path.unlink()
        assert not file_path.exists()
        
    def test_temp_file_cleanup_on_error(self, temp_dir):
        """Test temporary file cleanup when operations fail."""
        # This is more of a documentation test since our library
        # doesn't create temp files directly
        pf = ParquetFrame()
        
        with pytest.raises(TypeError):
            pf.save(temp_dir / "should_fail")
            
        # No temporary files should be left behind
        temp_files = list(temp_dir.glob("*tmp*"))
        assert len(temp_files) == 0


class TestAttributeErrorPropagation:
    """Test that AttributeError propagates correctly from underlying DataFrames."""
    
    def test_invalid_pandas_method(self, sample_small_df):
        """Test calling invalid pandas methods."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        with pytest.raises(AttributeError):
            pf.nonexistent_method()
            
    def test_invalid_dask_method(self, sample_small_df):
        """Test calling invalid Dask methods."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        
        with pytest.raises(AttributeError):
            pf.nonexistent_method()
            
    def test_attribute_access_empty_frame(self):
        """Test attribute access on empty ParquetFrame."""
        pf = ParquetFrame()
        
        with pytest.raises(AttributeError):
            _ = pf.shape
            
        with pytest.raises(AttributeError):
            _ = pf.columns
            
    def test_method_call_empty_frame(self):
        """Test method calls on empty ParquetFrame."""
        pf = ParquetFrame()
        
        with pytest.raises(AttributeError):
            pf.head()
            
        with pytest.raises(AttributeError):
            pf.groupby('column')


class TestPlatformSpecificErrors:
    """Test platform-specific error scenarios."""
    
    def test_windows_path_length_limit(self, temp_dir, sample_small_df):
        """Test Windows path length limitations."""
        if os.name != 'nt':
            pytest.skip("Windows-specific test")
            
        # Create very long file path
        long_name = 'a' * 200  # Very long filename
        long_path = temp_dir / f"{long_name}.parquet"
        
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        try:
            pf.save(long_path)
            # If it succeeds, verify it works
            assert long_path.exists()
        except OSError:
            # Path too long error is acceptable
            pass
            
    def test_unix_special_characters(self, temp_dir, sample_small_df):
        """Test Unix special characters in filenames."""
        if os.name == 'nt':
            pytest.skip("Unix-specific test")
            
        special_chars = ['file with spaces', 'file:with:colons', 'file*with*stars']
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        for char_name in special_chars:
            try:
                file_path = temp_dir / f"{char_name}.parquet"
                pf.save(file_path)
                
                if file_path.exists():
                    # Verify it can be read back
                    pf_read = ParquetFrame.read(file_path)
                    assert len(pf_read) == len(sample_small_df)
                    
            except OSError:
                # Some special characters may not be supported
                pass


class TestRecoveryScenarios:
    """Test error recovery and graceful degradation."""
    
    def test_fallback_to_pandas_on_dask_error(self, temp_dir, sample_small_df):
        """Test fallback behavior when Dask operations fail."""
        file_path = temp_dir / "fallback_test.parquet"
        sample_small_df.to_parquet(file_path)
        
        # Mock Dask read to fail
        with patch('dask.dataframe.read_parquet', side_effect=Exception("Dask error")):
            # Should still be able to force pandas
            pf = ParquetFrame.read(file_path, islazy=False)
            assert isinstance(pf._df, pd.DataFrame)
            
    def test_conversion_error_recovery(self, sample_small_df):
        """Test recovery from conversion errors."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        # Mock conversion to fail
        with patch.object(dd, 'from_pandas', side_effect=Exception("Conversion error")):
            with pytest.raises(Exception):
                pf.to_dask()
                
            # Original data should still be intact
            assert isinstance(pf._df, pd.DataFrame)
            assert len(pf) == len(sample_small_df)
            
    def test_partial_operation_recovery(self, sample_small_df):
        """Test recovery from partial operation failures."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        # Test that failed operations don't corrupt the object
        try:
            # This should fail
            _ = pf.nonexistent_method()
        except AttributeError:
            pass
            
        # Object should still be usable
        assert isinstance(pf._df, pd.DataFrame)
        assert len(pf) == len(sample_small_df)
        
        # Operations should still work
        result = pf.head(3)
        assert len(result) == 3