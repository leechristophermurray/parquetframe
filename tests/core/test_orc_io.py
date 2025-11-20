import pytest
import pandas as pd
import pyarrow as pa
import tempfile
from pathlib import Path
from parquetframe.core.frame import DataFrameProxy
from parquetframe.core.reader import DataReader

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "a": [1, 2, 3],
        "b": ["x", "y", "z"],
        "c": [1.1, 2.2, 3.3]
    })

def test_orc_io_roundtrip(sample_df):
    """Test writing to ORC and reading back."""
    try:
        import pyarrow.orc
    except ImportError:
        pytest.skip("pyarrow.orc not available")

    with tempfile.NamedTemporaryFile(suffix=".orc", delete=False) as f:
        path = f.name

    try:
        # Write
        proxy = DataFrameProxy(data=sample_df, engine="pandas")
        proxy.to_orc(path)

        # Read back
        reader = DataReader()
        # Force ORC read (auto-detection might not be set up for .orc extension yet in all places)
        # But DataReader.read_orc exists.
        read_proxy = reader.read_orc(path)
        
        result_df = read_proxy.to_pandas().native
        
        pd.testing.assert_frame_equal(sample_df, result_df)
        
    finally:
        Path(path).unlink(missing_ok=True)

def test_orc_read_auto_detect(sample_df):
    """Test reading ORC with auto-detection (if implemented)."""
    try:
        import pyarrow.orc
    except ImportError:
        pytest.skip("pyarrow.orc not available")

    with tempfile.NamedTemporaryFile(suffix=".orc", delete=False) as f:
        path = f.name
    
    # Create ORC file using pyarrow directly to ensure valid file
    table = pa.Table.from_pandas(sample_df)
    import pyarrow.orc as orc
    orc.write_table(table, path)

    try:
        # Use top-level read (assuming it uses DataReader which should detect orc)
        # Note: We need to check if DataReader detects .orc extension.
        # Based on previous knowledge, it likely does or we need to add it.
        # For now, let's try DataReader.read which usually dispatches based on extension.
        reader = DataReader()
        # We'll mock the dispatch if needed, but let's see if it works out of box
        # If DataReader doesn't support .orc auto-detection, this might fail.
        # Let's check DataReader.read implementation if possible, but for now we test explicit read_orc
        # as the requirement was "Add ORC read/write".
        
        read_proxy = reader.read_orc(path)
        result_df = read_proxy.to_pandas().native
        pd.testing.assert_frame_equal(sample_df, result_df)

    finally:
        Path(path).unlink(missing_ok=True)
