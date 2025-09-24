"""
Unit tests for the core ParquetFrame functionality.
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import dask.dataframe as dd
import pytest

from parquetframe.core import ParquetFrame


class TestParquetFrameInit:
    """Test ParquetFrame initialization."""
    
    def test_init_empty(self):
        """Test initializing empty ParquetFrame."""
        pf = ParquetFrame()
        assert pf._df is None
        assert pf.islazy is False
        assert pf.DEFAULT_THRESHOLD_MB == 10
        
    def test_init_with_pandas_df(self, sample_small_df):
        """Test initializing with pandas DataFrame."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False
        
    def test_init_with_dask_df(self, sample_small_df):
        """Test initializing with Dask DataFrame."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True


class TestParquetFrameProperties:
    """Test ParquetFrame properties and setters."""
    
    def test_islazy_property_getter(self, sample_small_df):
        """Test islazy property getter."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        assert pf.islazy is False
        
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        assert pf.islazy is True
        
    def test_islazy_property_setter_to_dask(self, sample_small_df):
        """Test setting islazy to True converts to Dask."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        assert isinstance(pf._df, pd.DataFrame)
        
        with patch.object(pf, 'to_dask') as mock_to_dask:
            pf.islazy = True
            mock_to_dask.assert_called_once()
            
    def test_islazy_property_setter_to_pandas(self, sample_small_df):
        """Test setting islazy to False converts to pandas."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        assert isinstance(pf._df, dd.DataFrame)
        
        with patch.object(pf, 'to_pandas') as mock_to_pandas:
            pf.islazy = False
            mock_to_pandas.assert_called_once()
            
    def test_islazy_property_setter_no_change(self, sample_small_df):
        """Test setting islazy to same value doesn't trigger conversion."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        with patch.object(pf, 'to_pandas') as mock_to_pandas:
            with patch.object(pf, 'to_dask') as mock_to_dask:
                pf.islazy = False  # Same value
                mock_to_pandas.assert_not_called()
                mock_to_dask.assert_not_called()


class TestParquetFrameRepresentation:
    """Test ParquetFrame string representation."""
    
    def test_repr_empty(self):
        """Test repr of empty ParquetFrame."""
        pf = ParquetFrame()
        repr_str = repr(pf)
        assert "ParquetFrame(type=pandas, df=None)" in repr_str
        
    def test_repr_with_pandas_df(self, sample_small_df):
        """Test repr with pandas DataFrame."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        repr_str = repr(pf)
        assert "ParquetFrame(type=pandas" in repr_str
        
    def test_repr_with_dask_df(self, sample_small_df):
        """Test repr with Dask DataFrame."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        repr_str = repr(pf)
        assert "ParquetFrame(type=Dask" in repr_str


class TestParquetFrameRead:
    """Test ParquetFrame read functionality."""
    
    def test_read_small_file_auto(self, small_parquet_file, sample_small_df):
        """Test reading small file automatically selects pandas."""
        pf = ParquetFrame.read(small_parquet_file)
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False
        pd.testing.assert_frame_equal(pf._df.reset_index(drop=True), 
                                    sample_small_df.reset_index(drop=True))
        
    def test_read_large_file_auto(self, large_parquet_file):
        """Test reading large file automatically selects Dask."""
        pf = ParquetFrame.read(large_parquet_file)
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True
        
    def test_read_force_pandas(self, large_parquet_file):
        """Test forcing pandas backend."""
        pf = ParquetFrame.read(large_parquet_file, islazy=False)
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False
        
    def test_read_force_dask(self, small_parquet_file):
        """Test forcing Dask backend."""
        pf = ParquetFrame.read(small_parquet_file, islazy=True)
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True
        
    def test_read_custom_threshold(self, small_parquet_file):
        """Test custom size threshold."""
        # Set threshold very low to force Dask
        pf = ParquetFrame.read(small_parquet_file, threshold_mb=0.001)
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True
        
    def test_read_pqt_extension(self, small_pqt_file, sample_small_df):
        """Test reading .pqt files."""
        pf = ParquetFrame.read(small_pqt_file)
        assert isinstance(pf._df, pd.DataFrame)
        pd.testing.assert_frame_equal(pf._df.reset_index(drop=True), 
                                    sample_small_df.reset_index(drop=True))
        
    def test_read_without_extension(self, small_parquet_file, sample_small_df):
        """Test reading file without extension."""
        base_path = small_parquet_file.with_suffix('')
        pf = ParquetFrame.read(str(base_path))
        assert isinstance(pf._df, pd.DataFrame)
        pd.testing.assert_frame_equal(pf._df.reset_index(drop=True), 
                                    sample_small_df.reset_index(drop=True))
        
    def test_read_with_kwargs(self, small_parquet_file):
        """Test reading with additional kwargs."""
        pf = ParquetFrame.read(small_parquet_file, columns=['id', 'name'])
        assert isinstance(pf._df, pd.DataFrame)
        assert list(pf._df.columns) == ['id', 'name']
        
    def test_read_nonexistent_file(self, nonexistent_file_path):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            ParquetFrame.read(nonexistent_file_path)
            
    def test_read_no_extension_variants(self, temp_dir):
        """Test reading file with no extension when no variants exist."""
        nonexistent_base = temp_dir / "nonexistent"
        with pytest.raises(FileNotFoundError, match="No parquet file found"):
            ParquetFrame.read(nonexistent_base)


class TestParquetFrameSave:
    """Test ParquetFrame save functionality."""
    
    def test_save_pandas_df(self, sample_small_df, temp_dir):
        """Test saving pandas DataFrame."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        output_path = temp_dir / "output_pandas"
        
        result = pf.save(output_path)
        
        # Check method chaining
        assert result is pf
        
        # Check file was created
        expected_path = temp_dir / "output_pandas.parquet"
        assert expected_path.exists()
        
        # Check file contents
        saved_df = pd.read_parquet(expected_path)
        pd.testing.assert_frame_equal(saved_df.reset_index(drop=True), 
                                    sample_small_df.reset_index(drop=True))
        
    def test_save_dask_df(self, sample_small_df, temp_dir):
        """Test saving Dask DataFrame."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        output_path = temp_dir / "output_dask"
        
        result = pf.save(output_path)
        
        # Check method chaining
        assert result is pf
        
        # Check file was created (might be a directory for Dask)
        expected_path = temp_dir / "output_dask.parquet"
        assert expected_path.exists()
        
    def test_save_with_extension(self, sample_small_df, temp_dir):
        """Test saving with explicit extension."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        output_path = temp_dir / "output_with_ext.parquet"
        
        pf.save(output_path)
        
        assert output_path.exists()
        
    def test_save_empty_df_raises_error(self):
        """Test saving empty ParquetFrame raises error."""
        pf = ParquetFrame()
        
        with pytest.raises(TypeError, match="No dataframe loaded to save"):
            pf.save("output")
            
    def test_save_with_kwargs(self, sample_small_df, temp_dir):
        """Test saving with additional kwargs."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        output_path = temp_dir / "output_compressed"
        
        pf.save(output_path, compression='snappy')
        
        expected_path = temp_dir / "output_compressed.parquet"
        assert expected_path.exists()


class TestParquetFrameConversion:
    """Test ParquetFrame conversion methods."""
    
    def test_to_pandas_from_dask(self, sample_small_df):
        """Test converting from Dask to pandas."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        
        result = pf.to_pandas()
        
        # Check method chaining
        assert result is pf
        
        # Check conversion
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False
        pd.testing.assert_frame_equal(pf._df.reset_index(drop=True), 
                                    sample_small_df.reset_index(drop=True))
        
    def test_to_pandas_already_pandas(self, sample_small_df):
        """Test to_pandas when already pandas."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        result = pf.to_pandas()
        
        # Check method chaining
        assert result is pf
        
        # Should still be pandas
        assert isinstance(pf._df, pd.DataFrame)
        assert pf.islazy is False
        
    def test_to_dask_from_pandas(self, sample_small_df):
        """Test converting from pandas to Dask."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        result = pf.to_dask()
        
        # Check method chaining
        assert result is pf
        
        # Check conversion
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True
        
    def test_to_dask_already_dask(self, sample_small_df):
        """Test to_dask when already Dask."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        
        result = pf.to_dask()
        
        # Check method chaining
        assert result is pf
        
        # Should still be Dask
        assert isinstance(pf._df, dd.DataFrame)
        assert pf.islazy is True
        
    def test_to_dask_custom_partitions(self, sample_small_df):
        """Test to_dask with custom partition count."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        pf.to_dask(npartitions=4)
        
        assert isinstance(pf._df, dd.DataFrame)
        assert pf._df.npartitions == 4


class TestParquetFrameAttributeDelegation:
    """Test ParquetFrame attribute delegation."""
    
    def test_getattr_pandas_method(self, sample_small_df):
        """Test calling pandas methods through delegation."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        # Test method that returns DataFrame
        result = pf.head(5)
        assert isinstance(result, ParquetFrame)
        assert len(result._df) == 5
        
    def test_getattr_pandas_attribute(self, sample_small_df):
        """Test accessing pandas attributes through delegation."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        # Test attribute access
        shape = pf.shape
        assert shape == sample_small_df.shape
        
        columns = pf.columns
        pd.testing.assert_index_equal(columns, sample_small_df.columns)
        
    def test_getattr_dask_method(self, sample_small_df):
        """Test calling Dask methods through delegation."""
        dask_df = dd.from_pandas(sample_small_df, npartitions=2)
        pf = ParquetFrame(dask_df, islazy=True)
        
        # Test method that returns DataFrame
        result = pf.head(5)
        assert isinstance(result, ParquetFrame)
        
    def test_getattr_method_returns_scalar(self, sample_small_df):
        """Test methods that return scalar values."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        # Test aggregation method
        mean_value = pf['id'].mean()
        assert isinstance(mean_value, (int, float))
        
    def test_getattr_nonexistent_attribute(self, sample_small_df):
        """Test accessing nonexistent attribute raises error."""
        pf = ParquetFrame(sample_small_df, islazy=False)
        
        with pytest.raises(AttributeError):
            _ = pf.nonexistent_attribute
            
    def test_getattr_empty_df_raises_error(self):
        """Test accessing attribute on empty ParquetFrame raises error."""
        pf = ParquetFrame()
        
        with pytest.raises(AttributeError, match="'ParquetFrame' object has no attribute"):
            _ = pf.shape


class TestStaticMethods:
    """Test ParquetFrame static methods."""
    
    def test_resolve_file_path_with_extension(self, small_parquet_file):
        """Test _resolve_file_path with existing extension."""
        result = ParquetFrame._resolve_file_path(small_parquet_file)
        assert result == small_parquet_file
        
    def test_resolve_file_path_without_extension(self, small_parquet_file):
        """Test _resolve_file_path without extension."""
        base_path = small_parquet_file.with_suffix('')
        result = ParquetFrame._resolve_file_path(base_path)
        assert result == small_parquet_file
        
    def test_resolve_file_path_pqt_extension(self, small_pqt_file):
        """Test _resolve_file_path finds .pqt files."""
        base_path = small_pqt_file.with_suffix('')
        result = ParquetFrame._resolve_file_path(base_path)
        assert result == small_pqt_file
        
    def test_resolve_file_path_nonexistent(self, temp_dir):
        """Test _resolve_file_path with nonexistent file."""
        nonexistent = temp_dir / "nonexistent.parquet"
        with pytest.raises(FileNotFoundError, match="File not found"):
            ParquetFrame._resolve_file_path(nonexistent)
            
    def test_resolve_file_path_no_variants(self, temp_dir):
        """Test _resolve_file_path with no extension variants."""
        nonexistent = temp_dir / "nonexistent"
        with pytest.raises(FileNotFoundError, match="No parquet file found"):
            ParquetFrame._resolve_file_path(nonexistent)
            
    def test_ensure_parquet_extension_no_extension(self):
        """Test _ensure_parquet_extension adds .parquet."""
        result = ParquetFrame._ensure_parquet_extension("test")
        assert result == Path("test.parquet")
        
    def test_ensure_parquet_extension_with_parquet(self):
        """Test _ensure_parquet_extension with .parquet."""
        result = ParquetFrame._ensure_parquet_extension("test.parquet")
        assert result == Path("test.parquet")
        
    def test_ensure_parquet_extension_with_pqt(self):
        """Test _ensure_parquet_extension with .pqt."""
        result = ParquetFrame._ensure_parquet_extension("test.pqt")
        assert result == Path("test.pqt")
        
    def test_ensure_parquet_extension_with_other(self):
        """Test _ensure_parquet_extension replaces other extensions."""
        result = ParquetFrame._ensure_parquet_extension("test.csv")
        assert result == Path("test.parquet")