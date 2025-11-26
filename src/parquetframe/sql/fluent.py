"""
Fluent SQL API for ParquetFrame.

Provides builder pattern and helper functions for SQL operations.
"""

import time
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .engine import SQLEngine

# Check if DuckDB is available
try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    duckdb = None
    DUCKDB_AVAILABLE = False


@dataclass
class QueryResult:
    """
    Enhanced query result with execution metadata and profiling information.

    Attributes:
        data: The pandas DataFrame result
        execution_time: Query execution time in seconds
        row_count: Number of rows in the result
        column_count: Number of columns in the result
        query: The original SQL query
        from_cache: Whether the result came from cache
        memory_usage: Approximate memory usage in MB
        duckdb_profile: Optional DuckDB query profiling information
        query_plan: Optional query execution plan
    """

    data: pd.DataFrame
    execution_time: float = 0.0
    row_count: int = 0
    column_count: int = 0
    query: str = ""
    from_cache: bool = False
    memory_usage: float | None = None
    duckdb_profile: dict | None = None
    query_plan: str | None = None

    def __post_init__(self):
        """Calculate memory usage after initialization."""
        if self.memory_usage is None:
            try:
                # Estimate memory usage in MB
                self.memory_usage = self.data.memory_usage(deep=True).sum() / (
                    1024 * 1024
                )
            except Exception:
                self.memory_usage = 0.0

        # Backwards compatibility aliases
        self._df = self.data
        self.row_count = len(self.data)
        self.column_count = len(self.data.columns)

    # Convenience properties for easier access
    @property
    def rows(self) -> int:
        """Number of rows in the result."""
        return self.row_count

    @property
    def columns(self) -> int:
        """Number of columns in the result."""
        return self.column_count

    @property
    def cached(self) -> bool:
        """Whether the result came from cache."""
        return self.from_cache

    @property
    def dataframe(self):
        """The result data as a ParquetFrame."""
        from ..core.frame import DataFrameProxy

        return DataFrameProxy(data=self.data, engine="pandas")

    @property
    def memory_usage_mb(self) -> float:
        """Memory usage in MB."""
        return self.memory_usage or 0.0

    def summary(self) -> str:
        """Get a summary of the query execution."""
        cache_info = " (from cache)" if self.from_cache else ""
        return (
            f"Query executed in {self.execution_time:.3f}s{cache_info}\n"
            f"Result: {self.row_count} rows × {self.column_count} columns\n"
            f"Memory usage: {self.memory_usage:.2f} MB"
        )

    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return self.data

    def head(self, n: int = 5) -> pd.DataFrame:
        """Return first n rows."""
        return self.data.head(n)

    def count(self) -> int:
        """Return number of rows."""
        return self.row_count


@dataclass
class QueryContext:
    """
    Context object for SQL query execution with optimization hints.

    Attributes:
        format_hints: Format hints for file reading (e.g., {'df': 'csv'})
        predicate_pushdown: Enable predicate pushdown optimization
        projection_pushdown: Enable projection pushdown optimization
        enable_parallel: Enable parallel query execution
        memory_limit: Memory limit for query execution (e.g., '1GB')
        temp_directory: Directory for temporary files
        enable_statistics: Enable query statistics collection
        custom_pragmas: Additional DuckDB PRAGMA statements
    """

    format_hints: dict[str, str] = field(default_factory=dict)
    predicate_pushdown: bool = True
    projection_pushdown: bool = True
    enable_parallel: bool = True
    memory_limit: str | None = None
    temp_directory: str | None = None
    enable_statistics: bool = False
    custom_pragmas: dict[str, Any] = field(default_factory=dict)

    def to_duckdb_pragmas(self) -> list[str]:
        """Convert context to DuckDB PRAGMA statements."""
        pragmas = []

        if not self.predicate_pushdown:
            pragmas.append("PRAGMA enable_optimizer=false")

        if not self.enable_parallel:
            pragmas.append("PRAGMA threads=1")

        if self.memory_limit:
            pragmas.append(f"PRAGMA memory_limit='{self.memory_limit}'")

        if self.temp_directory:
            pragmas.append(f"PRAGMA temp_directory='{self.temp_directory}'")

        if self.enable_statistics:
            pragmas.append("PRAGMA enable_profiling=true")
            pragmas.append("PRAGMA profiling_output='query_profiling.json'")

        # Add custom pragmas
        for pragma, value in self.custom_pragmas.items():
            if value is True:
                pragmas.append(f"PRAGMA {pragma}=true")
            elif value is False:
                pragmas.append(f"PRAGMA {pragma}=false")
            elif value is not None:
                pragmas.append(f"PRAGMA {pragma}='{value}'")

        return pragmas


class SQLBuilder:
    """Fluent builder for SQL queries with join support."""

    def __init__(self, table: Any, engine: SQLEngine | None = None):
        self.table = table  # Can be str or DataFrameProxy/ParquetFrame
        self.engine = engine or SQLEngine()
        self._select = ["*"]
        self._where = []
        self._joins = []
        self._group_by = []
        self._having = []
        self._order_by = []
        self._limit = None
        self._context = None
        self._profile = False

    def select(self, *columns: str) -> "SQLBuilder":
        """Select columns."""
        self._select = list(columns)
        return self

    def where(self, condition: str) -> "SQLBuilder":
        """Add WHERE clause."""
        self._where.append(condition)
        return self

    def inner_join(self, table: str, on: str) -> "SQLBuilder":
        """Add INNER JOIN."""
        self._joins.append(("INNER", table, on))
        return self

    def left_join(self, table: str, on: str) -> "SQLBuilder":
        """Add LEFT JOIN."""
        self._joins.append(("LEFT", table, on))
        return self

    def right_join(self, table: str, on: str) -> "SQLBuilder":
        """Add RIGHT JOIN."""
        self._joins.append(("RIGHT", table, on))
        return self

    def full_join(self, table: str, on: str) -> "SQLBuilder":
        """Add FULL OUTER JOIN."""
        self._joins.append(("FULL OUTER", table, on))
        return self

    def group_by(self, *columns: str) -> "SQLBuilder":
        """Add GROUP BY clause."""
        self._group_by = list(columns)
        return self

    def having(self, condition: str) -> "SQLBuilder":
        """Add HAVING clause."""
        self._having.append(condition)
        return self

    def order_by(self, *columns: str) -> "SQLBuilder":
        """Add ORDER BY clause."""
        self._order_by = list(columns)
        return self

    def limit(self, n: int) -> "SQLBuilder":
        """Add LIMIT clause."""
        self._limit = n
        return self

    def hint(self, **kwargs) -> "SQLBuilder":
        """Add optimization hints."""
        self._context = QueryContext(**kwargs)
        return self

    def profile(self, enable: bool = True) -> "SQLBuilder":
        """Enable query profiling."""
        self._profile = enable
        return self

    def build(self) -> str:
        """Build SQL query string."""
        # Handle table name if it's a proxy object
        table_name = str(self.table)
        if hasattr(self.table, "engine_name"):  # Proxy object
            # We assume it will be registered as 'df' during execute
            if self.table == getattr(self, "_execution_table_obj", None):
                table_name = "df"
            else:
                table_name = "df"

        query = f"SELECT {', '.join(self._select)} FROM {table_name}"

        # Add joins
        for join_type, table, condition in self._joins:
            query += f" {join_type} JOIN {table} ON {condition}"

        # Add WHERE
        if self._where:
            query += f" WHERE {' AND '.join(self._where)}"

        # Add GROUP BY
        if self._group_by:
            query += f" GROUP BY {', '.join(self._group_by)}"

        # Add HAVING
        if self._having:
            query += f" HAVING {' AND '.join(self._having)}"

        # Add ORDER BY
        if self._order_by:
            query += f" ORDER BY {', '.join(self._order_by)}"

        # Add LIMIT
        if self._limit is not None:
            query += f" LIMIT {self._limit}"

        return query

    def execute(self) -> QueryResult:
        """Execute query and return result with optional profiling."""
        # Handle DataFrameProxy/ParquetFrame input
        table_name = "df"

        # Store object for build() context
        self._execution_table_obj = self.table

        # Check if self.table is a proxy/frame object
        is_frame_obj = (
            hasattr(self.table, "pandas_df")
            or hasattr(self.table, "native")
            or hasattr(self.table, "_df")
        )

        if is_frame_obj:
            # It's a frame object, register it
            # Convert to pandas if needed (for now, as per existing implementation)
            if hasattr(self.table, "to_pandas"):
                df = self.table.to_pandas()
                if hasattr(df, "native"):  # If to_pandas returned a proxy
                    df = df.native
            elif hasattr(self.table, "pandas_df"):
                df = self.table.pandas_df
            elif hasattr(self.table, "_df"):
                df = self.table._df
            else:
                df = self.table

            # Unwrap dask if needed
            if hasattr(df, "compute"):
                df = df.compute()

            self.engine.register_dataframe(table_name, df)
        else:
            # It's likely a string table name already registered
            table_name = str(self.table)

        # Build query
        sql = self.build()

        # Apply context/hints if set
        if self._context and DUCKDB_AVAILABLE:
            import warnings

            pragmas = self._context.to_duckdb_pragmas()
            for pragma in pragmas:
                try:
                    self.engine.query(pragma)
                except Exception as e:
                    warnings.warn(
                        f"Failed to apply optimization hint: {pragma}. {e}",
                        UserWarning,
                        stacklevel=2,
                    )

        # Execute with profiling if enabled
        if self._profile:
            start_time = time.time()
            df = self.engine.query(sql)
            execution_time = time.time() - start_time
            return QueryResult(
                df,
                execution_time=execution_time,
                query=sql,
                row_count=len(df),
                column_count=len(df.columns),
            )
        else:
            df = self.engine.query(sql)
            return QueryResult(
                df, query=sql, row_count=len(df), column_count=len(df.columns)
            )


def explain_query(query: str, engine: SQLEngine | None = None) -> str:
    """Explain query execution plan."""
    engine = engine or SQLEngine()
    # Simple explain implementation
    if DUCKDB_AVAILABLE:
        try:
            result = engine.query(f"EXPLAIN {query}")
            return result.to_string()
        except Exception:
            pass
    return f"EXPLAIN {query}"


def query_dataframes(query: str, **tables) -> pd.DataFrame:
    """
    Execute query on provided DataFrames.

    DEPRECATED: Use parquetframe.sql.engine.query_dataframes instead.
    """
    engine = SQLEngine()
    for name, df in tables.items():
        engine.register_dataframe(name, df)
    return engine.query(query)


def validate_sql_query(query: str) -> bool:
    """Validate SQL syntax (basic check)."""
    return bool(query and isinstance(query, str) and "SELECT" in query.upper())


def build_join_query(
    left_table: str,
    right_table: str,
    on: str,
    join_type: str = "INNER",
    columns: list[str] | None = None,
) -> str:
    """Build a JOIN query string."""
    cols = "*" if not columns else ", ".join(columns)
    return f"SELECT {cols} FROM {left_table} {join_type} JOIN {right_table} ON {on}"


__all__ = [
    "QueryResult",
    "QueryContext",
    "SQLBuilder",
    "explain_query",
    "validate_sql_query",
    "build_join_query",
    "query_dataframes",
    "DUCKDB_AVAILABLE",
    "duckdb",
]
