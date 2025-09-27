"""
ParquetFrame: A universal wrapper for working with dataframes in Python.

This package provides seamless switching between pandas and Dask DataFrames
based on file size thresholds, with automatic file extension handling for
parquet files.

Examples:
    Basic usage:
        >>> import parquetframe as pqf
        >>> df = pqf.read("data")  # Auto-detects backend and extension
        >>> result = df.groupby("column").sum()
        >>> result.save("output")  # Saves as output.parquet

    Manual control:
        >>> df = pqf.read("large_data", islazy=True)  # Force Dask
        >>> df.to_pandas()  # Convert to pandas
        >>> print(df.islazy)  # False
"""

from pathlib import Path
from typing import Optional, Union

from .core import ParquetFrame

# Make ParquetFrame available as 'pf' for convenience
pf = ParquetFrame


# Convenience functions for more ergonomic usage
def read(
    file: Union[str, Path],
    threshold_mb: Optional[float] = None,
    islazy: Optional[bool] = None,
    **kwargs,
) -> ParquetFrame:
    """
    Read a parquet file into a ParquetFrame.

    This is a convenience function that wraps ParquetFrame.read().

    Args:
        file: Path to the parquet file (extension optional).
        threshold_mb: Size threshold in MB for backend selection. Defaults to 10MB.
        islazy: Force backend selection (True=Dask, False=pandas, None=auto).
        **kwargs: Additional keyword arguments for read_parquet methods.

    Returns:
        ParquetFrame instance with loaded data.

    Examples:
        >>> import parquetframe as pqf
        >>> df = pqf.read("data")  # Auto-detect extension and backend
        >>> df = pqf.read("data.parquet", threshold_mb=50)
        >>> df = pqf.read("data", islazy=True)  # Force Dask
    """
    return ParquetFrame.read(file, threshold_mb=threshold_mb, islazy=islazy, **kwargs)


def create_empty(islazy: bool = False) -> ParquetFrame:
    """
    Create an empty ParquetFrame.

    Args:
        islazy: Whether to initialize as Dask (True) or pandas (False).

    Returns:
        Empty ParquetFrame instance.

    Examples:
        >>> import parquetframe as pqf
        >>> empty_pf = pqf.create_empty()
        >>> empty_pf = pqf.create_empty(islazy=True)
    """
    return ParquetFrame(islazy=islazy)


__version__ = "0.2.3.2"
__all__ = ["ParquetFrame", "pf", "read", "create_empty"]
