"""
Core multi-engine DataFrame framework for ParquetFrame Phase 2.

This module provides the unified DataFrame abstraction layer with intelligent
backend selection across pandas, Polars, and Dask engines.
"""

from .base import DataFrameLike, Engine
from .frame import DataFrameProxy
from .heuristics import EngineHeuristics
from .registry import EngineRegistry

__all__ = [
    "DataFrameLike",
    "Engine",
    "DataFrameProxy",
    "EngineRegistry",
    "EngineHeuristics",
]
