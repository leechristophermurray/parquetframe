"""
Fluent SQL API for ParquetFrame.

Provides builder pattern and helper functions for SQL operations.
"""

import time

import pandas as pd

from .engine import SQLEngine

# Check if DuckDB is available
try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    duckdb = None
    DUCKDB_AVAILABLE = False


class QueryResult:
    """Result of a SQL query with profiling information."""

    def __init__(self, df: pd.DataFrame, execution_time: float = 0.0, query: str = ""):
        self._df = df
        self.data = df  # Alias for compatibility
        self.execution_time = execution_time
        self.row_count = len(df)
        self.query = query

    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return self._df

    def head(self, n: int = 5) -> pd.DataFrame:
        """Return first n rows."""
        return self._df.head(n)

    def count(self) -> int:
        """Return number of rows."""
        return self.row_count


class QueryContext:
    """
    Query optimization context with hints for SQL execution.

    Provides control over query optimization strategies like predicate pushdown,
    projection pushdown, parallelization, and memory limits.
    """

    def __init__(
        self,
        predicate_pushdown: bool = True,
        projection_pushdown: bool = True,
        enable_parallel: bool = True,
        memory_limit: str | None = None,
        custom_pragmas: dict | None = None,
    ):
        self.predicate_pushdown = predicate_pushdown
        self.projection_pushdown = projection_pushdown
        self.enable_parallel = enable_parallel
        self.memory_limit = memory_limit
        self.custom_pragmas = custom_pragmas or {}

    def to_duckdb_pragmas(self) -> list[str]:
        """
        Convert context settings to DuckDB PRAGMA statements.

        Returns:
            List of PRAGMA SQL statements
        """
        pragmas = []

        # Optimizer settings
        if not self.predicate_pushdown:
            pragmas.append("PRAGMA enable_optimizer=false")

        # Parallel execution
        if not self.enable_parallel:
            pragmas.append("PRAGMA threads=1")

        # Memory limit
        if self.memory_limit:
            pragmas.append(f"PRAGMA memory_limit='{self.memory_limit}'")

        # Custom pragmas
        for key, value in self.custom_pragmas.items():
            if isinstance(value, bool):
                val_str = "true" if value else "false"
            elif isinstance(value, str):
                val_str = f"'{value}'"
            else:
                val_str = str(value)
            pragmas.append(f"PRAGMA {key}={val_str}")

        return pragmas


class SQLBuilder:
    """Fluent builder for SQL queries with join support."""

    def __init__(self, table: str, engine: SQLEngine | None = None):
        self.table = table
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
        query = f"SELECT {', '.join(self._select)} FROM {self.table}"

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
            return QueryResult(df, execution_time=execution_time, query=sql)
        else:
            df = self.engine.query(sql)
            return QueryResult(df, query=sql)


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
    """Execute query on provided DataFrames."""
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
    "query_dataframes",
    "validate_sql_query",
    "build_join_query",
    "DUCKDB_AVAILABLE",
    "duckdb",
]
