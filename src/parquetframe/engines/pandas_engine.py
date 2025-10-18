"""
Pandas engine implementation for ParquetFrame Phase 2.

Provides pandas DataFrame engine with consistent interface and optimizations
for small to medium-scale datasets.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from ..core_v2.base import DataFrameLike, Engine


class PandasEngine(Engine):
    """Pandas DataFrame engine implementation."""

    @property
    def name(self) -> str:
        """Engine name."""
        return "pandas"

    @property
    def is_lazy(self) -> bool:
        """Pandas is eager by default."""
        return False

    @property
    def is_available(self) -> bool:
        """Check if pandas is available."""
        try:
            import importlib.util

            return importlib.util.find_spec("pandas") is not None
        except Exception:
            return False

    def read_parquet(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        """Read Parquet file using pandas."""
        return pd.read_parquet(path, **kwargs)

    def read_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        """Read CSV file using pandas."""
        return pd.read_csv(path, **kwargs)

    def to_pandas(self, df: DataFrameLike) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        if isinstance(df, pd.DataFrame):
            return df

        # If it's another engine's DataFrame, try to convert
        if hasattr(df, "to_pandas"):
            return df.to_pandas()

        # Fallback: assume it has pandas-compatible interface
        return pd.DataFrame(df)

    def compute_if_lazy(self, df: DataFrameLike) -> DataFrameLike:
        """No-op for pandas (always eager)."""
        return df

    def estimate_memory_usage(self, df: pd.DataFrame) -> int:
        """Estimate memory usage in bytes."""
        try:
            return int(df.memory_usage(deep=True).sum())
        except Exception:
            # Fallback estimation
            return len(df) * len(df.columns) * 8  # Assume 8 bytes per value

    def from_pandas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert from pandas (no-op)."""
        return df
