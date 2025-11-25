"""
Fluent SQL API for ParquetFrame.

Provides builder pattern and helper functions for SQL operations.
"""

from typing import Any, Dict, List, Optional, Union

import pandas as pd

from .engine import SQLEngine


class QueryResult:
    """Result of a SQL query."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return self._df

    def head(self, n: int = 5) -> pd.DataFrame:
        """Return first n rows."""
        return self._df.head(n)

    def count(self) -> int:
        """Return number of rows."""
        return len(self._df)


class SQLBuilder:
    """Fluent builder for SQL queries."""

    def __init__(self, table: str, engine: Optional[SQLEngine] = None):
        self.table = table
        self.engine = engine or SQLEngine()
        self._select = ["*"]
        self._where = []
        self._group_by = []
        self._order_by = []
        self._limit = None

    def select(self, *columns: str) -> "SQLBuilder":
        """Select columns."""
        self._select = list(columns)
        return self

    def where(self, condition: str) -> "SQLBuilder":
        """Add WHERE clause."""
        self._where.append(condition)
        return self

    def group_by(self, *columns: str) -> "SQLBuilder":
        """Add GROUP BY clause."""
        self._group_by = list(columns)
        return self

    def order_by(self, *columns: str) -> "SQLBuilder":
        """Add ORDER BY clause."""
        self._order_by = list(columns)
        return self

    def limit(self, n: int) -> "SQLBuilder":
        """Add LIMIT clause."""
        self._limit = n
        return self

    def build(self) -> str:
        """Build SQL query string."""
        query = f"SELECT {', '.join(self._select)} FROM {self.table}"

        if self._where:
            query += f" WHERE {' AND '.join(self._where)}"

        if self._group_by:
            query += f" GROUP BY {', '.join(self._group_by)}"

        if self._order_by:
            query += f" ORDER BY {', '.join(self._order_by)}"

        if self._limit is not None:
            query += f" LIMIT {self._limit}"

        return query

    def execute(self) -> QueryResult:
        """Execute query and return result."""
        sql = self.build()
        df = self.engine.query(sql)
        return QueryResult(df)


class QueryContext:
    """Context for executing multiple queries."""

    def __init__(self):
        self.engine = SQLEngine()

    def register(self, name: str, df: Any) -> None:
        """Register DataFrame as table."""
        self.engine.register_dataframe(name, df)

    def sql(self, query: str) -> QueryResult:
        """Execute SQL query."""
        df = self.engine.query(query)
        return QueryResult(df)

    def table(self, name: str) -> SQLBuilder:
        """Get builder for table."""
        return SQLBuilder(name, self.engine)


def explain_query(query: str, engine: Optional[SQLEngine] = None) -> str:
    """Explain query execution plan."""
    engine = engine or SQLEngine()
    # Simple explain implementation
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
    columns: Optional[List[str]] = None,
) -> str:
    """Build a JOIN query string."""
    cols = "*" if not columns else ", ".join(columns)
    return f"SELECT {cols} FROM {left_table} {join_type} JOIN {right_table} ON {on}"
