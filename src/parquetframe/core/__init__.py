"""
Core multi-engine DataFrame framework for ParquetFrame Phase 2.

This module provides the unified DataFrame abstraction layer with intelligent
backend selection across pandas, Polars, and Dask engines.

Phase 2 API (Default):
    - DataFrameProxy: Unified DataFrame interface
    - read(), read_parquet(), read_csv(), etc.: Format-specific readers
    - EngineRegistry: Engine management
    - EngineHeuristics: Intelligent engine selection

Phase 1 API (Deprecated):
    - ParquetFrame: Original DataFrame wrapper (deprecated, use DataFrameProxy)
    - Access via: from parquetframe.core import ParquetFrame (triggers warning)
"""

import warnings
from typing import Any

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


def __getattr__(name: str) -> Any:
    """
    Provide deprecated access to Phase 1 features.

    This function is called when an attribute is not found in the module's
    normal namespace. It allows Phase 1 features to remain accessible with
    deprecation warnings.

    Args:
        name: Attribute name being accessed

    Returns:
        The requested Phase 1 attribute

    Raises:
        AttributeError: If the attribute doesn't exist in Phase 1 either
    """
    # Import Phase 1 module lazily to avoid circular imports
    from .. import core_legacy

    # Map of Phase 1 exports that should trigger deprecation warnings
    phase1_exports = {
        "ParquetFrame": core_legacy.ParquetFrame,
        "FileFormat": core_legacy.FileFormat,
        "detect_format": core_legacy.detect_format,
        "IOHandler": core_legacy.IOHandler,
        "ParquetHandler": core_legacy.ParquetHandler,
        "CsvHandler": core_legacy.CsvHandler,
        "JsonHandler": core_legacy.JsonHandler,
        "OrcHandler": core_legacy.OrcHandler,
        "FORMAT_HANDLERS": core_legacy.FORMAT_HANDLERS,
    }

    if name in phase1_exports:
        warnings.warn(
            "\n"
            "=" * 80 + "\n"
            f"DEPRECATION WARNING: '{name}' (Phase 1 API)\n"
            f"=" * 80 + "\n"
            f"\n"
            f"The Phase 1 API is deprecated as of version 1.0.0 and will be removed\n"
            f"in version 2.0.0 (approximately 6-12 months).\n"
            f"\n"
            f"You are importing '{name}' from 'parquetframe.core', which is now\n"
            f"the Phase 2 multi-engine API. Please migrate to Phase 2:\n"
            f"\n"
            f"  Phase 1 (Deprecated):\n"
            f"    from parquetframe.core import {name}\n"
            f"\n"
            f"  Phase 2 (Recommended):\n"
            f"    from parquetframe.core import DataFrameProxy, read\n"
            f"    # Or from parquetframe import read, DataFrameProxy\n"
            f"\n"
            f"Key API changes:\n"
            f"  - ParquetFrame        →  DataFrameProxy\n"
            f"  - df.islazy          →  df.engine_name\n"
            f"  - df.df              →  df.native\n"
            f"  - islazy=True/False  →  engine='pandas'/'polars'/'dask'\n"
            f"\n"
            f"For detailed migration guide, see:\n"
            f"  - BREAKING_CHANGES.md\n"
            f"  - docs/phase2/MIGRATION_GUIDE.md\n"
            f"\n"
            f"=" * 80 + "\n",
            DeprecationWarning,
            stacklevel=2,
        )
        return phase1_exports[name]

    raise AttributeError(f"module 'parquetframe.core' has no attribute '{name}'")
