"""
ParquetFrame: A universal wrapper for working with dataframes in Python.

This package provides seamless switching between pandas and Dask DataFrames
based on file size thresholds, with automatic file extension handling for
parquet files.
"""

from .core import ParquetFrame

# Make ParquetFrame available as 'pf' for convenience
pf = ParquetFrame

__version__ = "0.1.0"
__all__ = ["ParquetFrame", "pf"]