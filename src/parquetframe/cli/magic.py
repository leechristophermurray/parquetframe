"""
Magic command system for interactive REPL.

Provides IPython-style magic commands like %sql, %info, %help, etc.
"""

import logging
from collections.abc import Callable
from typing import Any

from .context import ExecutionContext
from .display import (
    console,
    display_error,
    display_info,
    display_sql,
    display_success,
)

logger = logging.getLogger(__name__)

# Magic command registry
MAGIC_REGISTRY: dict[str, Callable] = {}


def register_magic(name: str):
    """
    Decorator to register a magic command.

    Usage:
        @register_magic("sql")
        def magic_sql(context, args):
            ...
    """

    def decorator(func: Callable):
        MAGIC_REGISTRY[name] = func
        return func

    return decorator


@register_magic("help")
def magic_help(context: ExecutionContext, args: list[str]) -> None:
    """Show help for magic commands."""
    if not args:
        # Show all magics
        console.print("\n[bold cyan]Available Magic Commands:[/]\n")

        magics = {
            "%sql": "Execute SQL query on DataFrames",
            "%info": "Show DataFrame information",
            "%schema": "Display DataFrame schema",
            "%whos": "List all variables in context",
            "%clear": "Clear all variables",
            "%help": "Show this help message",
        }

        for magic, desc in magics.items():
            console.print(f"  [yellow]{magic:12}[/] - {desc}")

        console.print("\n[dim]Type '%help <command>' for detailed help[/]\n")
    else:
        # Show help for specific magic
        magic_name = args[0].lstrip("%")
        if magic_name in MAGIC_REGISTRY:
            func = MAGIC_REGISTRY[magic_name]
            console.print(f"\n[bold]%{magic_name}[/]")
            console.print(f"{func.__doc__ or 'No documentation available.'}\n")
        else:
            display_error(f"Unknown magic command: %{magic_name}")


@register_magic("sql")
def magic_sql(context: ExecutionContext, args: list[str]) -> Any:
    """
    Execute SQL query on DataFrames in context.

    Usage:
        %sql SELECT * FROM df WHERE age > 30
        %sql SELECT name, COUNT(*) as cnt FROM df GROUP BY name
    """
    if not args:
        display_error("No SQL query provided")
        return None

    query = " ".join(args)
    display_sql(query)

    try:
        # TODO: Implement SQL execution using datafusion or duckdb
        # For now, show a placeholder
        display_info("SQL execution not yet implemented")
        display_info("Will use DataFusion or DuckDB for querying DataFrames")

        return None

    except Exception as e:
        display_error(f"SQL execution failed: {e}")
        logger.error(f"SQL error: {e}")
        return None


@register_magic("info")
def magic_info(context: ExecutionContext, args: list[str]) -> None:
    """
    Show information about a DataFrame.

    Usage:
        %info df
        %info my_data
    """
    if not args:
        display_error("No variable name provided")
        return

    var_name = args[0]

    try:
        df = context.get_variable(var_name)

        # Check if it's a DataFrame
        if not hasattr(df, "columns"):
            display_warning(f"Variable '{var_name}' is not a DataFrame")
            console.print(f"Type: {type(df).__name__}")
            return

        # Display info
        console.print(f"\n[bold]DataFrame: {var_name}[/]")
        console.print(f"Rows: {len(df):,}")
        console.print(f"Columns: {len(df.columns)}")
        console.print(f"Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        # Show column types
        console.print("\n[bold]Column Types:[/]")
        for col, dtype in df.dtypes.items():
            console.print(f"  {col}: [cyan]{dtype}[/]")

        console.print()

    except NameError as e:
        display_error(str(e))
    except Exception as e:
        display_error(f"Failed to get info: {e}")
        logger.error(f"Info error: {e}")


@register_magic("schema")
def magic_schema(context: ExecutionContext, args: list[str]) -> None:
    """
    Display DataFrame schema.

    Usage:
        %schema df
    """
    if not args:
        display_error("No variable name provided")
        return

    var_name = args[0]

    try:
        df = context.get_variable(var_name)

        if not hasattr(df, "columns"):
            display_warning(f"Variable '{var_name}' is not a DataFrame")
            return

        console.print(f"\n[bold]Schema for: {var_name}[/]\n")

        for col in df.columns:
            dtype = df[col].dtype
            console.print(f"  [cyan]{col}[/]: {dtype}")

        console.print()

    except NameError as e:
        display_error(str(e))
    except Exception as e:
        display_error(f"Failed to get schema: {e}")


@register_magic("whos")
def magic_whos(context: ExecutionContext, args: list[str]) -> None:
    """
    List all variables in the current context.

    Usage:
        %whos
    """
    variables = context.list_variables()

    if not variables:
        display_info("No variables defined")
        return

    console.print("\n[bold]Variables:[/]\n")

    for name, type_name in variables.items():
        # Get value for size info
        try:
            value = context.get_variable(name)
            if hasattr(value, "__len__"):
                size_info = f" ({len(value)} items)"
            else:
                size_info = ""
        except Exception:
            size_info = ""

        console.print(f"  [yellow]{name:20}[/] [cyan]{type_name:15}[/]{size_info}")

    console.print()


@register_magic("clear")
def magic_clear(context: ExecutionContext, args: list[str]) -> None:
    """
    Clear all variables from the context.

    Usage:
        %clear
    """
    context.clear()
    display_success("All variables cleared")


def execute_magic(context: ExecutionContext, command: str) -> Any:
    """
    Execute a magic command.

    Args:
        context: Execution context
        command: Magic command string (e.g., "%sql SELECT * FROM df")

    Returns:
        Result of the magic command execution
    """
    # Remove leading %
    command = command.lstrip("%").strip()

    # Split into magic name and arguments
    parts = command.split(maxsplit=1)
    magic_name = parts[0]
    args = parts[1].split() if len(parts) > 1 else []

    # Look up and execute magic
    if magic_name in MAGIC_REGISTRY:
        try:
            return MAGIC_REGISTRY[magic_name](context, args)
        except Exception as e:
            display_error(f"Magic command failed: {e}")
            logger.error(f"Magic error in %{magic_name}: {e}")
            return None
    else:
        display_error(f"Unknown magic command: %{magic_name}")
        display_info("Type %help to see available commands")
        return None


__all__ = ["execute_magic", "register_magic", "MAGIC_REGISTRY"]
