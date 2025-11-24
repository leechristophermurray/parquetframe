"""
CLI utilities for ParquetFrame.
"""

from .repl import start_repl, start_basic_repl


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "repl":
        start_repl()
    else:
        start_basic_repl()


__all__ = ["start_repl", "start_basic_repl", "main"]
