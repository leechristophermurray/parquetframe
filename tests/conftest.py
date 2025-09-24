"""
Test fixtures and configuration for parquetframe tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Iterator

import pandas as pd
import pytest


@pytest.fixture
def sample_small_df() -> pd.DataFrame:
    """Create a small sample DataFrame for testing."""
    return pd.DataFrame({
        'id': range(100),
        'name': [f'item_{i}' for i in range(100)],
        'value': range(100, 200),
        'category': ['A', 'B', 'C'] * 33 + ['A']
    })


@pytest.fixture  
def sample_large_df() -> pd.DataFrame:
    """Create a large sample DataFrame for testing."""
    n_rows = 1_000_000  # 1M rows should be > 10MB when saved as parquet
    return pd.DataFrame({
        'id': range(n_rows),
        'name': [f'item_{i}' for i in range(n_rows)],
        'value': range(n_rows),
        'category': ['A', 'B', 'C', 'D'] * (n_rows // 4)
    })


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def small_parquet_file(sample_small_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a small parquet file for testing."""
    file_path = temp_dir / "small_test.parquet"
    sample_small_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def small_pqt_file(sample_small_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a small .pqt file for testing."""
    file_path = temp_dir / "small_test.pqt"
    sample_small_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def large_parquet_file(sample_large_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a large parquet file for testing (>10MB)."""
    file_path = temp_dir / "large_test.parquet"
    sample_large_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Create an empty DataFrame for testing."""
    return pd.DataFrame()


@pytest.fixture
def empty_parquet_file(empty_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create an empty parquet file for testing."""
    file_path = temp_dir / "empty_test.parquet"
    # pandas doesn't allow saving empty dataframes to parquet directly
    # so we create one with columns but no rows
    df_with_cols = pd.DataFrame(columns=['a', 'b', 'c'])
    df_with_cols.to_parquet(file_path)
    return file_path


@pytest.fixture
def nonexistent_file_path(temp_dir: Path) -> Path:
    """Return path to a file that doesn't exist."""
    return temp_dir / "nonexistent.parquet"


# Test data for various scenarios
@pytest.fixture
def mixed_types_df() -> pd.DataFrame:
    """DataFrame with mixed data types."""
    return pd.DataFrame({
        'int_col': [1, 2, 3, 4, 5],
        'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
        'str_col': ['a', 'b', 'c', 'd', 'e'],
        'bool_col': [True, False, True, False, True],
        'datetime_col': pd.date_range('2023-01-01', periods=5)
    })


@pytest.fixture
def compression_test_file(mixed_types_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a parquet file with compression for testing."""
    file_path = temp_dir / "compressed_test.parquet"
    mixed_types_df.to_parquet(file_path, compression='snappy')
    return file_path