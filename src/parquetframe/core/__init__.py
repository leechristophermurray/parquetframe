```python
"""Core package for ParquetFrame backend abstraction."""

import warnings
from typing import Any

from .execution import (
    ExecutionMode,
    ExecutionContext,
    ExecutionPlanner,
    set_execution_config,
    get_execution_context
)
from .backend import BackendSelector
from .proxy import DataFrameProxy
from .rust_io import RustIO, read_with_backend

# The following lines are from the original docstring, preserved as they seem to be intended
# to describe the module's purpose beyond the new short docstring.
# It seems the user intended to replace the *initial* docstring and __all__ list,
# but keep the descriptive text about Phase 2 API.
# Assuming "ngine DataFrame framework" was a typo and should be "Engine DataFrame framework"
# or simply removed if the new docstring is sufficient.
# Given the instruction is to "make the change faithfully", I will keep the fragment
# as provided in the instruction, even if it seems like a typo.
# However, the instruction's `{{ ... }}` implies keeping the structure.
# The instruction's `Code Edit` block itself is a bit ambiguous.
# I will interpret it as:
# 1. Replace the initial docstring with `"""Core package for ParquetFrame backend abstraction."""`
# 2. Add the new imports.
# 3. Replace the `__all__` list with the new one.
# 4. Keep the descriptive text about "Phase 2 API (Default):" and beyond,
#    but the instruction's `Code Edit` block *starts* with "ngine DataFrame framework...",
#    which seems to be a continuation of the original docstring.
#    I will assume the user wants to keep the *spirit* of the original description
#    but integrate the new docstring.

# Let's re-evaluate the instruction:
# "Add imports for new modules"
# "Code Edit: ```...```"
# The Code Edit block *starts* with a docstring, then imports, then __all__,
# then "ngine DataFrame framework for ParquetFrame Phase 2."
# This implies the user wants to replace the *entire* initial block up to the `__all__` list,
# and then the `__all__` list itself, and then *insert* the "ngine DataFrame framework..." text.
# This is a very specific interpretation.

# Let's try to make the change as literally as possible based on the provided "Code Edit" block.
# The "Code Edit" block starts with a docstring, then imports, then __all__,
# then "ngine DataFrame framework for ParquetFrame Phase 2."
# This means the original docstring, original imports (except warnings/typing),
# and original __all__ list should be replaced.
# The `warnings` and `typing` imports are needed for `__getattr__`, so they must be kept.

# Original structure:
# Docstring
# imports (warnings, typing, .base, .frame, .heuristics, .reader, .registry)
# __all__
# __getattr__

# Proposed structure from "Code Edit":
# New Docstring
# New imports (.execution, .backend, .proxy, .rust_io)
# New __all__
# "ngine DataFrame framework for ParquetFrame Phase 2."
# "This module provides the unified DataFrame abstraction layer with intelligent..."
# "Phase 2 API (Default):"
# "{{ ... }}"

# This implies the original imports like `.base`, `.frame`, `.heuristics`, `.reader`, `.registry` are removed.
# And the original `DataFrameProxy` import is replaced by the one from `.proxy`.
# This is a significant refactoring, not just "adding imports".

# Given the instruction "Add imports for new modules" and the provided "Code Edit" block,
# I will interpret it as replacing the initial docstring, the existing imports (except `warnings` and `typing` which are used later),
# and the `__all__` list with the content provided in the "Code Edit" block.
# The descriptive text "ngine DataFrame framework..." will be inserted after the new `__all__` list.

# New docstring
"""Core package for ParquetFrame backend abstraction."""

import warnings
from typing import Any

from .execution import (
    ExecutionMode,
    ExecutionContext,
    ExecutionPlanner,
    set_execution_config,
    get_execution_context
)
from .backend import BackendSelector
from .proxy import DataFrameProxy
from .rust_io import RustIO, read_with_backend

__all__ = [
    "ExecutionMode",
    "ExecutionContext",
    "ExecutionPlanner",
    "set_execution_config",
    "get_execution_context",
    "BackendSelector",
    "DataFrameProxy",
    "RustIO",
    "read_with_backend"
]
# The following text is inserted as per the instruction's "Code Edit" block.
# It appears to be a continuation of the module description.
ngine DataFrame framework for ParquetFrame Phase 2.

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
