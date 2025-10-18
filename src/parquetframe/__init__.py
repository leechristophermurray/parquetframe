"""
ParquetFrame: A universal data processing framework with multi-format support.

This package provides seamless switching between pandas and Dask DataFrames
based on file size thresholds, with automatic format detection for multiple
file types including CSV, JSON, Parquet, and ORC.

Supported formats:
    - CSV (.csv, .tsv) - Comma or tab-separated values
    - JSON (.json, .jsonl, .ndjson) - Regular or JSON Lines format
    - Parquet (.parquet, .pqt) - Columnar format (optimal performance)
    - ORC (.orc) - Optimized Row Columnar format
    - GraphAr - Graph data in Apache GraphAr format (Phase 1.1+)

Examples:
    Multi-format data processing:
        >>> import parquetframe as pqf
        >>> csv_df = pqf.read("sales.csv")  # Auto-detects CSV
        >>> json_df = pqf.read("events.jsonl")  # Auto-detects JSON Lines
        >>> parquet_df = pqf.read("data.parquet")  # Auto-detects Parquet
        >>> result = csv_df.groupby("region").sum().save("output.parquet")

    Graph processing (Phase 1.1+):
        >>> import parquetframe as pqf
        >>> graph = pqf.graph.read_graph("social_network/")  # GraphAr format
        >>> print(f"Graph: {graph.num_vertices} vertices, {graph.num_edges} edges")
        >>> neighbors = graph.neighbors(vertex_id=123)

    Manual control:
        >>> df = pqf.read("data.txt", format="csv")  # Force CSV format
        >>> df = pqf.read("large_data.csv", islazy=True)  # Force Dask
        >>> print(df.islazy)  # True
"""

from pathlib import Path

from .core import ParquetFrame

# Import submodules
try:
    from . import graph
except ImportError:
    # Graph module not available - will be implemented in Phase 1.1
    graph = None

try:
    from . import permissions
except ImportError:
    # Permissions module not available
    permissions = None

# Make ParquetFrame available as 'pf' for convenience
pf = ParquetFrame


# Convenience functions for more ergonomic usage
def read(
    file: str | Path,
    threshold_mb: float | None = None,
    islazy: bool | None = None,
    **kwargs,
) -> ParquetFrame:
    """
    Read a data file into a ParquetFrame with automatic format detection.

    This is a convenience function that wraps ParquetFrame.read().
    Supports CSV, JSON, Parquet, and ORC formats with automatic detection.

    Args:
        file: Path to the data file. Format auto-detected from extension.
        threshold_mb: Size threshold in MB for backend selection. Defaults to 100MB.
        islazy: Force backend selection (True=Dask, False=pandas, None=auto).
        **kwargs: Additional keyword arguments (format="csv|json|parquet|orc", etc.).

    Returns:
        ParquetFrame instance with loaded data.

    Examples:
        >>> import parquetframe as pqf
        >>> df = pqf.read("sales.csv")  # Auto-detect CSV format and backend
        >>> df = pqf.read("events.jsonl")  # Auto-detect JSON Lines format
        >>> df = pqf.read("data.parquet", threshold_mb=50)  # Custom threshold
        >>> df = pqf.read("data.txt", format="csv")  # Manual format override
    """
    return ParquetFrame.read(file, threshold_mb=threshold_mb, islazy=islazy, **kwargs)


def create_empty(islazy: bool = False) -> ParquetFrame:
    """
    Create an empty ParquetFrame.

    Args:
        islazy: Whether to initialize as Dask (True) or pandas (False).

    Returns:
        Empty ParquetFrame instance.

    Examples:
        >>> import parquetframe as pqf
        >>> empty_pf = pqf.create_empty()
        >>> empty_pf = pqf.create_empty(islazy=True)
    """
    return ParquetFrame(islazy=islazy)


__version__ = "0.5.3"
__all__ = ["ParquetFrame", "pf", "read", "create_empty", "graph", "permissions"]
