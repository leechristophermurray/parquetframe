"""
Tests for intelligent backend switching optimization.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from parquetframe.core import ParquetFrame


class TestIntelligentBackendSwitching:
    """Test cases for intelligent backend switching logic."""
    
    def test_estimate_memory_usage_with_pyarrow(self):
        """Test memory estimation with pyarrow metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test parquet file
            test_data = pd.DataFrame({
                'A': range(1000),
                'B': ['test'] * 1000,
                'C': [1.5] * 1000
            })
            test_file = Path(temp_dir) / "test.parquet"
            test_data.to_parquet(test_file)
            
            # Test memory estimation
            estimated_mb = ParquetFrame._estimate_memory_usage(test_file)
            
            # Should return a positive value
            assert estimated_mb > 0
            # Should be reasonable (not too small or too large)
            assert 0.1 < estimated_mb < 100  # Between 0.1MB and 100MB
            
    @patch('pyarrow.parquet.ParquetFile')
    def test_estimate_memory_usage_fallback(self, mock_parquet_file):
        """Test memory estimation fallback when pyarrow fails."""
        # Mock pyarrow to raise an exception
        mock_parquet_file.side_effect = Exception("Mock error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file with known size
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (5 * 1024 * 1024))  # 5MB file
                
            estimated_mb = ParquetFrame._estimate_memory_usage(test_file)
            
            # Should use fallback estimation (file_size * 5)
            assert estimated_mb == 25.0  # 5MB * 5
            
    @patch('psutil.virtual_memory')
    def test_get_system_memory_with_psutil(self, mock_virtual_memory):
        """Test system memory detection with psutil."""
        # Mock psutil response
        mock_memory = MagicMock()
        mock_memory.available = 8 * 1024 * 1024 * 1024  # 8GB in bytes
        mock_virtual_memory.return_value = mock_memory
        
        available_mb = ParquetFrame._get_system_memory()
        
        assert available_mb == 8192.0  # 8GB in MB
        
    @patch('psutil.virtual_memory')
    def test_get_system_memory_fallback(self, mock_virtual_memory):
        """Test system memory fallback when psutil is not available."""
        # Mock ImportError to simulate psutil not available
        mock_virtual_memory.side_effect = ImportError("No module named 'psutil'")
        
        available_mb = ParquetFrame._get_system_memory()
        
        # Should return fallback value
        assert available_mb == 2048.0  # 2GB fallback
        
    def test_should_use_dask_explicit_islazy_true(self):
        """Test that explicit islazy=True always returns True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.parquet"
            test_file.touch()  # Create empty file
            
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=True
            )
            
            assert result is True
            
    def test_should_use_dask_explicit_islazy_false(self):
        """Test that explicit islazy=False always returns False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create large file
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (50 * 1024 * 1024))  # 50MB file
                
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=False
            )
            
            assert result is False
            
    def test_should_use_dask_basic_threshold_over(self):
        """Test basic threshold check - file over threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file larger than threshold
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (20 * 1024 * 1024))  # 20MB file
                
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=None
            )
            
            assert result is True
            
    def test_should_use_dask_basic_threshold_under(self):
        """Test basic threshold check - file under threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create small file
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (1024 * 1024))  # 1MB file
                
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=None
            )
            
            assert result is False
            
    @patch.object(ParquetFrame, '_estimate_memory_usage')
    @patch.object(ParquetFrame, '_get_system_memory')
    def test_should_use_dask_memory_pressure(self, mock_get_memory, mock_estimate_memory):
        """Test Dask selection based on memory pressure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file near threshold (8MB, threshold 10MB)
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (8 * 1024 * 1024))  # 8MB file
                
            # Mock high memory usage estimate and low available memory
            mock_estimate_memory.return_value = 3000  # 3GB estimated usage
            mock_get_memory.return_value = 4000  # 4GB available (usage > 50%)
            
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=None
            )
            
            assert result is True
            
    @patch.object(ParquetFrame, '_estimate_memory_usage')
    @patch.object(ParquetFrame, '_get_system_memory')
    def test_should_use_dask_low_memory_pressure(self, mock_get_memory, mock_estimate_memory):
        """Test pandas selection with low memory pressure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file near threshold
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (8 * 1024 * 1024))  # 8MB file
                
            # Mock low memory usage estimate and high available memory
            mock_estimate_memory.return_value = 100  # 100MB estimated usage
            mock_get_memory.return_value = 8000  # 8GB available (usage < 50%)
            
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=None
            )
            
            assert result is False
            
    @patch('pyarrow.parquet.ParquetFile')
    @patch.object(ParquetFrame, '_estimate_memory_usage')
    @patch.object(ParquetFrame, '_get_system_memory')
    def test_should_use_dask_many_row_groups(self, mock_get_memory, mock_estimate_memory, mock_parquet_file):
        """Test Dask selection based on many row groups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (8 * 1024 * 1024))  # 8MB file
                
            # Mock low memory pressure but many row groups
            mock_estimate_memory.return_value = 100  # Low memory usage
            mock_get_memory.return_value = 8000  # High available memory
            
            # Mock parquet metadata with many row groups
            mock_metadata = MagicMock()
            mock_metadata.num_row_groups = 15  # > 10 row groups
            mock_parquet_instance = MagicMock()
            mock_parquet_instance.metadata = mock_metadata
            mock_parquet_file.return_value = mock_parquet_instance
            
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=None
            )
            
            assert result is True
            
    @patch('pyarrow.parquet.ParquetFile')
    @patch.object(ParquetFrame, '_estimate_memory_usage')
    @patch.object(ParquetFrame, '_get_system_memory')
    def test_should_use_dask_few_row_groups(self, mock_get_memory, mock_estimate_memory, mock_parquet_file):
        """Test pandas selection with few row groups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (8 * 1024 * 1024))  # 8MB file
                
            # Mock low memory pressure and few row groups
            mock_estimate_memory.return_value = 100  # Low memory usage
            mock_get_memory.return_value = 8000  # High available memory
            
            # Mock parquet metadata with few row groups
            mock_metadata = MagicMock()
            mock_metadata.num_row_groups = 5  # <= 10 row groups
            mock_parquet_instance = MagicMock()
            mock_parquet_instance.metadata = mock_metadata
            mock_parquet_file.return_value = mock_parquet_instance
            
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=None
            )
            
            assert result is False
            
    @patch('pyarrow.parquet.ParquetFile')
    @patch.object(ParquetFrame, '_estimate_memory_usage')
    @patch.object(ParquetFrame, '_get_system_memory')
    def test_should_use_dask_metadata_error(self, mock_get_memory, mock_estimate_memory, mock_parquet_file):
        """Test behavior when parquet metadata reading fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.parquet"
            with open(test_file, 'wb') as f:
                f.write(b'0' * (8 * 1024 * 1024))  # 8MB file
                
            # Mock low memory pressure
            mock_estimate_memory.return_value = 100  # Low memory usage
            mock_get_memory.return_value = 8000  # High available memory
            
            # Mock parquet file to raise exception
            mock_parquet_file.side_effect = Exception("Mock error")
            
            result = ParquetFrame._should_use_dask(
                test_file, 
                threshold_mb=10, 
                islazy=None
            )
            
            # Should fall back to pandas when metadata reading fails
            assert result is False


class TestBackendSwitchingIntegration:
    """Integration tests for backend switching with real files."""
    
    def test_read_with_intelligent_switching(self):
        """Test that read method uses intelligent backend switching."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test parquet file
            test_data = pd.DataFrame({
                'A': range(100),
                'B': ['test'] * 100
            })
            test_file = Path(temp_dir) / "test.parquet"
            test_data.to_parquet(test_file)
            
            # Mock the intelligent switching to return True (use Dask)
            with patch.object(ParquetFrame, '_should_use_dask', return_value=True):
                pf = ParquetFrame.read(str(test_file))
                assert pf.islazy is True
                
            # Mock the intelligent switching to return False (use pandas)
            with patch.object(ParquetFrame, '_should_use_dask', return_value=False):
                pf = ParquetFrame.read(str(test_file))
                assert pf.islazy is False
                
    def test_read_explicit_override(self):
        """Test that explicit islazy parameter overrides intelligent switching."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = pd.DataFrame({'A': range(100)})
            test_file = Path(temp_dir) / "test.parquet"
            test_data.to_parquet(test_file)
            
            # Force pandas even if intelligent switching would choose Dask
            with patch.object(ParquetFrame, '_should_use_dask', return_value=True):
                pf = ParquetFrame.read(str(test_file), islazy=False)
                assert pf.islazy is False
                
            # Force Dask even if intelligent switching would choose pandas
            with patch.object(ParquetFrame, '_should_use_dask', return_value=False):
                pf = ParquetFrame.read(str(test_file), islazy=True)
                assert pf.islazy is True
                
    def test_threshold_parameter_passed_to_switching(self):
        """Test that threshold parameter is properly passed to switching logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = pd.DataFrame({'A': range(100)})
            test_file = Path(temp_dir) / "test.parquet"
            test_data.to_parquet(test_file)
            
            with patch.object(ParquetFrame, '_should_use_dask') as mock_should_use_dask:
                mock_should_use_dask.return_value = False
                
                # Test with custom threshold
                pf = ParquetFrame.read(str(test_file), threshold_mb=50)
                
                # Verify that _should_use_dask was called with correct threshold
                mock_should_use_dask.assert_called_once()
                args, kwargs = mock_should_use_dask.call_args
                assert args[1] == 50  # threshold_mb parameter
                
    @pytest.mark.slow
    def test_real_file_backend_selection(self):
        """Test backend selection with real files of different sizes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create small file (should use pandas)
            small_data = pd.DataFrame({'A': range(100), 'B': ['small'] * 100})
            small_file = Path(temp_dir) / "small.parquet"
            small_data.to_parquet(small_file)
            
            # Create larger file (might use Dask depending on system)
            large_data = pd.DataFrame({
                'A': range(10000), 
                'B': ['large'] * 10000,
                'C': list(range(10000)) * 1,  # More varied data
                'D': [f"item_{i}" for i in range(10000)]
            })
            large_file = Path(temp_dir) / "large.parquet"
            large_data.to_parquet(large_file)
            
            # Test small file - should prefer pandas
            small_pf = ParquetFrame.read(str(small_file), threshold_mb=5)
            # Small file should use pandas (unless system memory is very limited)
            
            # Test large file - behavior depends on system
            large_pf = ParquetFrame.read(str(large_file), threshold_mb=1)  # Low threshold
            # Large file with low threshold should use Dask
            
            # Verify both work correctly regardless of backend
            assert len(small_pf) == 100
            assert len(large_pf) == 10000
            
            # Test data access
            assert list(small_pf.columns) == ['A', 'B']
            assert list(large_pf.columns) == ['A', 'B', 'C', 'D']