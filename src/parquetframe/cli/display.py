"""
Rich display utilities for interactive REPL.

Provides beautiful terminal output using the rich library.
"""

import logging
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

logger = logging.getLogger(__name__)

# Global console instance
console = Console()


def print_banner():
    """Print the ParquetFrame interactive banner."""
    banner = """
╔════════════════════════════════════════╗
║  [bold cyan]ParquetFrame Interactive Shell[/]    ║
║  [dim]v0.1.0[/]                              ║
║  Type [yellow]%help[/] for magic commands     ║
╚════════════════════════════════════════╝
"""
    console.print(banner)


def display_dataframe(df: Any, max_rows: int = 10, title: str | None = None):
    """
    Display a DataFrame as a rich table.

    Args:
        df: DataFrame to display (pandas or similar)
        max_rows: Maximum rows to show
        title: Optional table title
    """
    try:
        # Get basic info
        num_rows = len(df)
        columns = list(df.columns)

        # Create table
        table_title = title or f"DataFrame ({num_rows} rows)"
        table = Table(title=table_title, show_header=True, header_style="bold cyan")

        # Add columns
        for col in columns:
            table.add_column(str(col), style="white")

        # Add rows (limited to max_rows)
        display_rows = min(max_rows, num_rows)
        for idx in range(display_rows):
            row_data = df.iloc[idx]
            table.add_row(*[str(val) for val in row_data])

        # Add ellipsis if truncated
        if num_rows > max_rows:
            table.add_row(*["..." for _ in columns], style="dim")

        console.print(table)

        # Show row count if truncated
        if num_rows > max_rows:
            console.print(
                f"[dim]Showing {display_rows} of {num_rows} rows[/]", style="dim"
            )

    except Exception as e:
        console.print(f"[red]Error displaying DataFrame: {e}[/]")
        logger.error(f"Failed to display DataFrame: {e}")


def display_sql(query: str):
    """Display SQL query with syntax highlighting."""
    syntax = Syntax(query, "sql", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="[cyan]SQL Query[/]", border_style="cyan"))


def display_python(code: str):
    """Display Python code with syntax highlighting."""
    syntax = Syntax(code, "python", theme="monokai", line_numbers=False)
    console.print(syntax)


def display_success(message: str):
    """Display a success message."""
    console.print(f"✓ [green]{message}[/]")


def display_error(message: str):
    """Display an error message."""
    console.print(f"✗ [red]{message}[/]")


def display_warning(message: str):
    """Display a warning message."""
    console.print(f"⚠ [yellow]{message}[/]")


def display_info(message: str):
    """Display an info message."""
    console.print(f"ℹ [blue]{message}[/]")


def display_result(result: Any):
    """
    Display a result value with appropriate formatting.

    Args:
        result: The result to display
    """
    if result is None:
        return

    # Check if it's a DataFrame
    if hasattr(result, "columns") and hasattr(result, "iloc"):
        display_dataframe(result)
    else:
        # Default: print with rich
        console.print(result)


__all__ = [
    "console",
    "print_banner",
    "display_dataframe",
    "display_sql",
    "display_python",
    "display_success",
    "display_error",
    "display_warning",
    "display_info",
    "display_result",
]
