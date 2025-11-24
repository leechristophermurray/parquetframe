"""Core package for ParquetFrame backend abstraction."""

from .backend import BackendSelector
from .execution import (
    ExecutionContext,
    ExecutionMode,
    ExecutionPlanner,
    get_execution_context,
    set_execution_config,
)
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
    "read_with_backend",
]
