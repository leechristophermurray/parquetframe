"""
Core multi-engine DataFrame framework for ParquetFrame Phase 2.

This module provides the unified DataFrame abstraction layer with intelligent
backend selection across pandas, Polars, and Dask engines.
"""

from .base import DataFrameLike, Engine, EngineCapabilities
from .frame import DataFrameProxy
from .heuristics import EngineHeuristics
from .reader import read, read_avro, read_csv, read_json, read_orc, read_parquet
from .registry import EngineRegistry

__all__ = [
    # Base types
    "DataFrameLike",
    "Engine",
    "EngineCapabilities",
    # Core classes
    "DataFrameProxy",
    "EngineRegistry",
    "EngineHeuristics",
    # Reader functions
    "read",
    "read_parquet",
    "read_csv",
    "read_json",
    "read_orc",
    "read_avro",
]
