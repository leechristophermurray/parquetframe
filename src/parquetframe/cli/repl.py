"""
Interactive REPL for ParquetFrame.

Provides a Jupyter-like command interface with magic commands,
rich display, and execution context management.
"""

import logging
import sys
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory

from .context import ExecutionContext
from .display import (
    console,
    display_error,
    display_result,
    display_success,
    display_warning,
    print_banner,
)
from .magic import execute_magic

logger = logging.getLogger(__name__)


class ParquetFrameREPL:
    """Interactive REPL for ParquetFrame."""

    def __init__(self):
        """Initialize the REPL."""
        self.context = ExecutionContext()
        self.session = PromptSession(
            history=FileHistory(".pf_history"),
            auto_suggest=AutoSuggestFromHistory(),
        )
        self.running = True

    def run(self):
        """Main REPL loop."""
        # Print banner
        print_banner()

        # Setup parquetframe in context
        try:
            import parquetframe as pf

            self.context.set_variable("pf", pf)
            display_success("ParquetFrame module loaded as 'pf'")
        except ImportError:
            display_warning("Could not import parquetframe module")

        console.print()

        # Main loop
        while self.running:
            try:
                # Get input with numbered prompt
                exec_count = self.context.get_execution_count() + 1
                prompt_str = f"pf[{exec_count}]> "

                code = self.session.prompt(prompt_str)

                # Skip empty input
                if not code.strip():
                    continue

                # Handle exit commands
                if code.strip().lower() in ("exit", "quit"):
                    self.handle_exit()
                    break

                # Add to history
                self.context.add_to_history(code)

                # Execute
                if code.strip().startswith("%"):
                    # Magic command
                    result = execute_magic(self.context, code)
                else:
                    # Python code
                    result = self.execute_python(code)

                # Display result
                if result is not None:
                    display_result(result)

            except KeyboardInterrupt:
                # Ctrl+C - cancel current line
                console.print()
                continue

            except EOFError:
                # Ctrl+D - exit
                self.handle_exit()
                break

            except Exception as e:
                display_error(f"Unexpected error: {e}")
                logger.exception("REPL error")

    def execute_python(self, code: str) -> Any:
        """
        Execute Python code in the context.

        Args:
            code: Python code to execute

        Returns:
            Result of the execution
        """
        try:
            # Build namespace from context
            namespace = self.context.variables.copy()

            # Try as expression first
            try:
                result = eval(code, namespace)  # noqa: S307
                return result
            except SyntaxError:
                # Not an expression, execute as statement
                exec(code, namespace)  # noqa: S102

                # Update context with new/modified variables
                for name, value in namespace.items():
                    if not name.startswith("_") and name not in ("pf",):
                        self.context.set_variable(name, value)

                return None

        except Exception as e:
            display_error(f"Python execution failed: {e}")
            logger.error(f"Execution error: {e}")
            return None

    def handle_exit(self):
        """Handle exit gracefully."""
        console.print("\n[cyan]Goodbye! 👋[/]\n")
        self.running = False


def start_repl():
    """Start the interactive REPL."""
    repl = ParquetFrameREPL()
    try:
        repl.run()
    except Exception as e:
        console.print(f"\n[red]REPL crashed: {e}[/]")
        logger.exception("REPL crash")
        sys.exit(1)


__all__ = ["ParquetFrameREPL", "start_repl"]
