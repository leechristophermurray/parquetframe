"""
CLI utilities for ParquetFrame.
"""

from ..exceptions import check_dependencies
from .commands import BENCHMARK_AVAILABLE, console, main
from .repl import start_basic_repl, start_repl

__all__ = [
    "start_repl",
    "start_basic_repl",
    "main",
    "console",
    "check_dependencies",
    "BENCHMARK_AVAILABLE",
]
