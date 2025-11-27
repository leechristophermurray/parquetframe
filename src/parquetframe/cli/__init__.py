"""
CLI utilities for ParquetFrame.
"""

from ..exceptions import BENCHMARK_AVAILABLE, check_dependencies
from .commands import console, main
from .repl import start_basic_repl, start_repl

__all__ = [
    "start_repl",
    "start_basic_repl",
    "main",
    "console",
    "check_dependencies",
    "BENCHMARK_AVAILABLE",
]
