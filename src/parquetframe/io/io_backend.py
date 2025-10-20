"""
Rust backend integration for I/O operations.

This module provides utilities for using the Rust backend for fast Parquet
metadata reading when available, with automatic fallback to Python implementations.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Attempt to import Rust backend
try:
    from parquetframe import _rustic

    RUST_IO_AVAILABLE = True
except ImportError:
    RUST_IO_AVAILABLE = False
    _rustic = None


def is_rust_io_available() -> bool:
    """Check if Rust I/O backend is available."""
    return RUST_IO_AVAILABLE


def read_parquet_metadata_fast(path: str | Path) -> dict[str, Any]:
    """
    Read Parquet file metadata using Rust backend.

    This is significantly faster than pyarrow for metadata-only operations.

    Args:
        path: Path to Parquet file

    Returns:
        Dictionary with metadata:
            - num_rows: Number of rows
            - num_row_groups: Number of row groups
            - num_columns: Number of columns
            - file_size_bytes: File size in bytes (if available)
            - version: Parquet version
            - column_names: List of column names
            - column_types: List of column types

    Raises:
        RuntimeError: If Rust backend not available
        ValueError: If file doesn't exist or is invalid
    """
    if not RUST_IO_AVAILABLE:
        raise RuntimeError(
            "Rust I/O backend not available. Install with: pip install parquetframe[rust]"
        )

    path_str = str(path)
    return _rustic.read_parquet_metadata_rust(path_str)


def get_parquet_row_count_fast(path: str | Path) -> int:
    """
    Get row count from Parquet file (very fast).

    Reads only the file footer, typically completing in milliseconds
    even for multi-GB files.

    Args:
        path: Path to Parquet file

    Returns:
        Number of rows in the file

    Raises:
        RuntimeError: If Rust backend not available
        ValueError: If file doesn't exist or is invalid
    """
    if not RUST_IO_AVAILABLE:
        raise RuntimeError(
            "Rust I/O backend not available. Install with: pip install parquetframe[rust]"
        )

    path_str = str(path)
    return _rustic.get_parquet_row_count_rust(path_str)


def get_parquet_column_names_fast(path: str | Path) -> list[str]:
    """
    Get column names from Parquet file.

    Args:
        path: Path to Parquet file

    Returns:
        List of column names

    Raises:
        RuntimeError: If Rust backend not available
        ValueError: If file doesn't exist or is invalid
    """
    if not RUST_IO_AVAILABLE:
        raise RuntimeError(
            "Rust I/O backend not available. Install with: pip install parquetframe[rust]"
        )

    path_str = str(path)
    return _rustic.get_parquet_column_names_rust(path_str)


def get_parquet_column_stats_fast(path: str | Path) -> list[dict[str, Any]]:
    """
    Get column statistics from Parquet file.

    Extracts statistics from metadata including null counts and min/max values.

    Args:
        path: Path to Parquet file

    Returns:
        List of dictionaries with statistics for each column:
            - name: Column name
            - null_count: Number of nulls (if available)
            - distinct_count: Number of distinct values (if available)
            - min_value: Minimum value as string (if available)
            - max_value: Maximum value as string (if available)

    Raises:
        RuntimeError: If Rust backend not available
        ValueError: If file doesn't exist or is invalid
    """
    if not RUST_IO_AVAILABLE:
        raise RuntimeError(
            "Rust I/O backend not available. Install with: pip install parquetframe[rust]"
        )

    path_str = str(path)
    return _rustic.get_parquet_column_stats_rust(path_str)


def try_read_metadata_fast(path: str | Path) -> dict[str, Any] | None:
    """
    Try to read Parquet metadata using Rust backend.

    Returns None if Rust backend is unavailable or if there's an error.
    Use this for optional fast-path optimizations.

    Args:
        path: Path to Parquet file

    Returns:
        Metadata dictionary or None if unavailable
    """
    if not RUST_IO_AVAILABLE:
        return None

    try:
        return read_parquet_metadata_fast(path)
    except Exception as e:
        logger.debug(f"Rust metadata read failed, falling back: {e}")
        return None


def try_get_row_count_fast(path: str | Path) -> int | None:
    """
    Try to get row count using Rust backend.

    Returns None if Rust backend is unavailable or if there's an error.

    Args:
        path: Path to Parquet file

    Returns:
        Row count or None if unavailable
    """
    if not RUST_IO_AVAILABLE:
        return None

    try:
        return get_parquet_row_count_fast(path)
    except Exception as e:
        logger.debug(f"Rust row count read failed, falling back: {e}")
        return None
