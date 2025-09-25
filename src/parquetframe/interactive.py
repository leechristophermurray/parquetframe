"""
Interactive CLI session for parquetframe.

This module provides an interactive REPL interface that integrates DataContext
for data source management and LLM for natural language queries.
"""

from __future__ import annotations

import asyncio
import logging
import pickle
import sys
import time
from pathlib import Path
from typing import Any

from .ai import LLMAgent, LLMError
from .datacontext import DataContext, DataContextFactory

logger = logging.getLogger(__name__)

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.shortcuts import confirm
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    INTERACTIVE_AVAILABLE = True
except ImportError:
    INTERACTIVE_AVAILABLE = False


class InteractiveSession:
    """
    Interactive CLI session for parquetframe.

    Provides a REPL interface with meta-commands for exploring data sources,
    executing queries, and using LLM-powered natural language queries.
    """

    def __init__(self, data_context: DataContext, enable_ai: bool = True):
        """
        Initialize interactive session.

        Args:
            data_context: DataContext for data source interaction
            enable_ai: Whether to enable LLM functionality
        """
        if not INTERACTIVE_AVAILABLE:
            raise ImportError(
                "Interactive mode requires additional dependencies. "
                "Install with: pip install parquetframe[ai,cli]"
            )

        self.data_context = data_context
        self.console = Console()
        self.history = InMemoryHistory()

        # Initialize LLM agent if available
        self.llm_agent: LLMAgent | None = None
        self.ai_enabled = False

        if enable_ai:
            try:
                self.llm_agent = LLMAgent()
                self.ai_enabled = True
                logger.info("AI functionality enabled")
            except LLMError as e:
                logger.warning(f"AI functionality disabled: {e}")
                self.ai_enabled = False

        # Session state
        self.query_history: list[dict[str, Any]] = []
        self.session_id = self._generate_session_id()

        # Setup command completions
        meta_commands = [
            "\\help",
            "\\h",
            "\\?",
            "\\list",
            "\\l",
            "\\tables",
            "\\describe",
            "\\d",
            "\\ai",
            "\\llm",
            "\\history",
            "\\hist",
            "\\save-session",
            "\\load-session",
            "\\quit",
            "\\q",
            "\\exit",
        ]

        self.completer = WordCompleter(meta_commands, ignore_case=True)
        self.session = PromptSession(history=self.history, completer=self.completer)

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{int(time.time())}"

    async def start(self) -> None:
        """Start the interactive session."""
        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold blue]ParquetFrame Interactive Mode[/bold blue]\n"
                f"Data source: [green]{self.data_context.source_location}[/green]\n"
                f"Type: [yellow]{self.data_context.source_type.value}[/yellow]\n"
                f"AI enabled: [{'green' if self.ai_enabled else 'red'}]"
                f"{'Yes' if self.ai_enabled else 'No'}[/]\n\n"
                "Type [cyan]\\help[/cyan] for available commands",
                title="🚀 Welcome",
                border_style="blue",
            )
        )

        # Initialize data context
        try:
            await self.data_context.initialize()
            table_count = len(self.data_context.get_table_names())
            self.console.print(
                f"✅ Connected! Found [bold]{table_count}[/bold] table(s)"
            )
        except Exception as e:
            self.console.print(f"❌ Connection failed: {e}", style="red")
            return

        # Main REPL loop
        while True:
            try:
                # Create prompt with context info
                prompt_text = self._create_prompt()

                # Get user input
                user_input = await asyncio.to_thread(self.session.prompt, prompt_text)

                if not user_input.strip():
                    continue

                # Handle meta-commands vs SQL queries
                if user_input.strip().startswith("\\"):
                    should_continue = await self._handle_meta_command(
                        user_input.strip()
                    )
                    if not should_continue:
                        break
                else:
                    await self._handle_query(user_input.strip())

            except (EOFError, KeyboardInterrupt):
                self.console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                self.console.print(f"❌ Error: {e}", style="red")
                logger.exception("Unexpected error in interactive session")

    def _create_prompt(self) -> HTML:
        """Create the interactive prompt."""
        source_type = self.data_context.source_type.value
        ai_indicator = "🤖" if self.ai_enabled else ""

        return HTML(
            f"<ansigreen>pframe</ansigreen>:"
            f"<ansiblue>{source_type}</ansiblue>"
            f"{ai_indicator}> "
        )

    async def _handle_meta_command(self, command: str) -> bool:
        """
        Handle meta-commands (starting with \\).

        Returns:
            True to continue session, False to exit
        """
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in ["\\help", "\\h", "\\?"]:
            await self._show_help()

        elif cmd in ["\\list", "\\l", "\\tables"]:
            await self._list_tables()

        elif cmd in ["\\describe", "\\d"]:
            if args:
                await self._describe_table(args[0])
            else:
                self.console.print("Usage: \\describe <table_name>", style="yellow")

        elif cmd in ["\\ai", "\\llm"]:
            await self._handle_ai_command(args)

        elif cmd in ["\\history", "\\hist"]:
            await self._show_history()

        elif cmd == "\\save-session":
            if args:
                await self._save_session(args[0])
            else:
                self.console.print("Usage: \\save-session <filename>", style="yellow")

        elif cmd == "\\load-session":
            if args:
                await self._load_session(args[0])
            else:
                self.console.print("Usage: \\load-session <filename>", style="yellow")

        elif cmd in ["\\quit", "\\q", "\\exit"]:
            return False

        else:
            self.console.print(
                f"Unknown command: {cmd}. Type \\help for help.", style="yellow"
            )

        return True

    async def _handle_query(self, query: str) -> None:
        """Handle SQL query execution."""
        try:
            # Execute the query
            start_time = time.time()

            result = await self.data_context.execute(query)
            execution_time = (time.time() - start_time) * 1000

            # Display results
            self._display_query_result(result, execution_time)

            # Log to history
            self.query_history.append(
                {
                    "query": query,
                    "timestamp": time.time(),
                    "execution_time_ms": execution_time,
                    "success": True,
                    "error": None,
                }
            )

        except Exception as e:
            self.console.print(f"❌ Query failed: {e}", style="red")

            # Log failed query to history
            self.query_history.append(
                {
                    "query": query,
                    "timestamp": time.time(),
                    "execution_time_ms": None,
                    "success": False,
                    "error": str(e),
                }
            )

    async def _handle_ai_command(self, args: list[str]) -> None:
        """Handle AI/LLM commands."""
        if not self.ai_enabled:
            self.console.print("❌ AI functionality not available", style="red")
            return

        if not args:
            self.console.print(
                "Usage: \\ai <natural language question>", style="yellow"
            )
            return

        natural_query = " ".join(args)

        try:
            self.console.print(f"🤖 Processing: [italic]{natural_query}[/italic]")

            with self.console.status("[bold green]Thinking..."):
                result = await self.llm_agent.generate_query(
                    natural_query, self.data_context
                )

            if result.success:
                # Show generated query and ask for approval
                self.console.print("\n📝 Generated Query:", style="bold")
                self.console.print(
                    Panel(result.query, expand=False, border_style="green")
                )

                # Ask for approval
                if confirm("\n🚀 Execute this query?", default=True):
                    self._display_query_result(result.result, result.execution_time_ms)

                    # Log to history
                    self.query_history.append(
                        {
                            "query": result.query,
                            "natural_language": natural_query,
                            "timestamp": time.time(),
                            "execution_time_ms": result.execution_time_ms,
                            "success": True,
                            "ai_generated": True,
                            "attempts": result.attempts,
                        }
                    )
                else:
                    self.console.print("❌ Query cancelled", style="yellow")
            else:
                self.console.print(
                    f"❌ Failed to generate query: {result.error}", style="red"
                )
                if result.query:
                    self.console.print(f"Last attempted query: {result.query}")

        except Exception as e:
            self.console.print(f"❌ AI error: {e}", style="red")
            logger.exception("AI command failed")

    def _display_query_result(
        self, result: Any, execution_time_ms: float | None
    ) -> None:
        """Display query results in a formatted table."""
        try:
            # Handle pandas DataFrame
            if hasattr(result, "head"):
                df = result

                # Limit display rows
                display_rows = min(20, len(df))
                display_df = df.head(display_rows)

                # Create Rich table
                table = Table(show_header=True, header_style="bold blue")

                # Add columns
                for col in display_df.columns:
                    table.add_column(str(col))

                # Add rows
                for _, row in display_df.iterrows():
                    table.add_row(*[str(val) for val in row])

                self.console.print()
                self.console.print(table)

                # Show summary
                time_info = (
                    f" in {execution_time_ms:.2f}ms" if execution_time_ms else ""
                )
                if len(df) > display_rows:
                    self.console.print(
                        f"📊 Showing {display_rows} of {len(df)} rows{time_info}",
                        style="dim",
                    )
                else:
                    self.console.print(f"📊 {len(df)} rows{time_info}", style="dim")

            else:
                # Handle other result types
                self.console.print(f"Result: {result}")
                if execution_time_ms:
                    self.console.print(
                        f"Execution time: {execution_time_ms:.2f}ms", style="dim"
                    )

        except Exception as e:
            self.console.print(f"Error displaying results: {e}", style="red")
            self.console.print(f"Raw result: {result}")

    async def _show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold blue]ParquetFrame Interactive Commands[/bold blue]

[bold]Data Exploration:[/bold]
  \\list, \\l, \\tables     List all available tables
  \\describe <table>       Show detailed table schema

[bold]Querying:[/bold]
  <SQL query>             Execute SQL query directly
  \\ai <question>          Ask question in natural language 🤖

[bold]Session Management:[/bold]
  \\history                Show query history
  \\save-session <file>    Save current session
  \\load-session <file>    Load saved session

[bold]Other:[/bold]
  \\help, \\h, \\?           Show this help
  \\quit, \\q, \\exit        Exit interactive mode

[bold]Examples:[/bold]
  SELECT * FROM users LIMIT 10;
  \\ai how many users are there?
  \\describe users
"""
        self.console.print(Panel(help_text, title="📚 Help", border_style="blue"))

    async def _list_tables(self) -> None:
        """List all available tables."""
        try:
            table_names = self.data_context.get_table_names()

            if not table_names:
                self.console.print("No tables found", style="yellow")
                return

            # Create table listing
            table = Table(
                title="📋 Available Tables", show_header=True, header_style="bold blue"
            )
            table.add_column("Table Name")
            table.add_column("Type")

            for name in table_names:
                source_type = (
                    "Virtual"
                    if self.data_context.source_type.value == "parquet"
                    else "Database"
                )
                table.add_row(name, source_type)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"❌ Error listing tables: {e}", style="red")

    async def _describe_table(self, table_name: str) -> None:
        """Describe a specific table."""
        try:
            schema_info = self.data_context.get_table_schema(table_name)

            # Create schema table
            table = Table(
                title=f"🔍 Table Schema: {table_name}",
                show_header=True,
                header_style="bold blue",
            )
            table.add_column("Column")
            table.add_column("Type")
            table.add_column("Nullable")

            if "columns" in schema_info:
                for col in schema_info["columns"]:
                    nullable = "✓" if col.get("nullable", True) else "✗"
                    table.add_row(
                        col["name"],
                        col.get("sql_type", col.get("type", "UNKNOWN")),
                        nullable,
                    )

            self.console.print(table)

            # Show additional info
            if "file_count" in schema_info:
                self.console.print(
                    f"📁 Files: {schema_info['file_count']}", style="dim"
                )
            if "source_location" in schema_info:
                self.console.print(
                    f"📍 Source: {schema_info['source_location']}", style="dim"
                )

        except Exception as e:
            self.console.print(
                f"❌ Error describing table '{table_name}': {e}", style="red"
            )

    async def _show_history(self) -> None:
        """Show query history."""
        if not self.query_history:
            self.console.print("No query history", style="yellow")
            return

        table = Table(
            title="📚 Query History", show_header=True, header_style="bold blue"
        )
        table.add_column("#", justify="right", style="dim")
        table.add_column("Query")
        table.add_column("Status")
        table.add_column("Time (ms)", justify="right")

        for i, entry in enumerate(self.query_history[-10:], 1):  # Show last 10
            query = (
                entry["query"][:60] + "..."
                if len(entry["query"]) > 60
                else entry["query"]
            )
            status = "✅" if entry["success"] else "❌"
            time_str = (
                f"{entry['execution_time_ms']:.1f}"
                if entry.get("execution_time_ms")
                else "N/A"
            )

            style = None if entry["success"] else "red"
            table.add_row(str(i), query, status, time_str, style=style)

        self.console.print(table)

    async def _save_session(self, filename: str) -> None:
        """Save current session to file."""
        try:
            session_data = {
                "session_id": self.session_id,
                "data_context_config": {
                    "source_location": self.data_context.source_location,
                    "source_type": self.data_context.source_type.value,
                },
                "query_history": self.query_history,
                "ai_enabled": self.ai_enabled,
            }

            # Ensure sessions directory exists
            sessions_dir = Path.home() / ".parquetframe" / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            session_file = sessions_dir / f"{filename}.pkl"

            with open(session_file, "wb") as f:
                pickle.dump(session_data, f)

            self.console.print(f"💾 Session saved to: {session_file}", style="green")

        except Exception as e:
            self.console.print(f"❌ Error saving session: {e}", style="red")

    async def _load_session(self, filename: str) -> None:
        """Load session from file."""
        try:
            sessions_dir = Path.home() / ".parquetframe" / "sessions"
            session_file = sessions_dir / f"{filename}.pkl"

            if not session_file.exists():
                self.console.print(
                    f"❌ Session file not found: {session_file}", style="red"
                )
                return

            with open(session_file, "rb") as f:
                session_data = pickle.load(f)

            # Restore query history
            self.query_history = session_data.get("query_history", [])

            self.console.print(
                f"📂 Loaded session: {len(self.query_history)} queries in history",
                style="green",
            )

        except Exception as e:
            self.console.print(f"❌ Error loading session: {e}", style="red")


async def start_interactive_session(
    path: str | None = None, db_uri: str | None = None, enable_ai: bool = True
) -> None:
    """
    Start an interactive parquetframe session.

    Args:
        path: Path to parquet directory
        db_uri: Database connection URI
        enable_ai: Whether to enable AI functionality
    """
    try:
        # Create DataContext
        data_context = DataContextFactory.create_context(path=path, db_uri=db_uri)

        # Create and start interactive session
        session = InteractiveSession(data_context, enable_ai=enable_ai)
        await session.start()

    except Exception as e:
        from rich.console import Console

        console = Console()
        console.print(f"❌ Failed to start interactive session: {e}", style="red")
        sys.exit(1)
    finally:
        # Clean up DataContext
        if "data_context" in locals():
            data_context.close()
