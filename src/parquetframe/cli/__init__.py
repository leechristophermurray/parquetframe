"""CLI module for interactive features."""

from .context import ExecutionContext
from .display import console, display_dataframe, display_result
from .magic import MAGIC_REGISTRY, execute_magic, register_magic
from .repl import ParquetFrameREPL, start_repl

__all__ = [
    "ExecutionContext",
    "console",
    "display_dataframe",
    "display_result",
    "execute_magic",
    "register_magic",
    "MAGIC_REGISTRY",
    "ParquetFrameREPL",
    "start_repl",
]
