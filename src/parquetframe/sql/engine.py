"""
SQL Engine for ParquetFrame using DataFusion.

Enables SQL queries on DataFrames with high performance.
"""

from typing import Any, Dict, Optional
import pandas as pd


class SQLEngine:
    """
    Execute SQL queries on DataFrames using DataFusion.

    Example:
        >>> engine = SQLEngine()
        >>> engine.register_dataframe("users", users_df)
        >>> result = engine.query("SELECT * FROM users WHERE age > 25")
    """

    def __init__(self):
        """Initialize SQL engine with DataFusion context."""
        try:
            import datafusion

            self.ctx = datafusion.SessionContext()
            self.tables = {}
            self._datafusion_available = True
        except ImportError:
            # Fallback: Use DuckDB if DataFusion not available
            try:
                import duckdb

                self.ctx = duckdb.connect(":memory:")
                self.tables = {}
                self._datafusion_available = False
                self._use_duckdb = True
            except ImportError:
                raise ImportError(
                    "SQL engine requires either 'datafusion' or 'duckdb'. "
                    "Install with: pip install datafusion or pip install duckdb"
                ) from ImportError

    def register_dataframe(self, name: str, df: Any) -> None:
        """
        Register DataFrame as SQL table.

        Args:
            name: Table name for SQL queries
            df: pandas or polars DataFrame
        """
        # Convert to pandas if needed
        if hasattr(df, "to_pandas"):
            df = df.to_pandas()

        if self._datafusion_available:
            # Convert to Arrow for DataFusion
            import pyarrow as pa

            arrow_table = pa.Table.from_pandas(df)
            self.ctx.register_record_batches(name, [[arrow_table.to_batches()[0]]])
        else:
            # DuckDB can work directly with pandas
            self.ctx.register(name, df)

        self.tables[name] = df

    def query(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query and return result as DataFrame.

        Args:
            sql: SQL query string

        Returns:
            Query result as pandas DataFrame
        """
        if self._datafusion_available:
            result = self.ctx.sql(sql)
            # Convert back to pandas
            return result.to_pandas()
        else:
            # DuckDB
            result = self.ctx.execute(sql).fetchdf()
            return result

    def list_tables(self) -> list[str]:
        """List all registered tables."""
        return list(self.tables.keys())

    def unregister(self, name: str) -> None:
        """Remove table from catalog."""
        if name in self.tables:
            del self.tables[name]
            # Note: DataFusion/DuckDB don't have direct unregister


__all__ = ["SQLEngine"]
