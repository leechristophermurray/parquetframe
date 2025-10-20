"""
Rust backend integration for graph algorithms.

This module provides utilities for detecting and using the Rust backend
for graph algorithms when available, with automatic fallback to Python
implementations.
"""

import logging

import numpy as np

# Attempt to import Rust backend
try:
    from parquetframe import _rustic

    RUST_AVAILABLE = True
    RUST_VERSION = _rustic.rust_version()
except ImportError:
    RUST_AVAILABLE = False
    RUST_VERSION = None
    _rustic = None

logger = logging.getLogger(__name__)


def is_rust_available() -> bool:
    """Check if Rust backend is available."""
    return RUST_AVAILABLE


def get_rust_version() -> str | None:
    """Get Rust backend version if available."""
    return RUST_VERSION


def build_csr_rust(
    sources: np.ndarray,
    targets: np.ndarray,
    num_vertices: int,
    weights: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Build CSR adjacency structure using Rust backend.

    Args:
        sources: Source vertex IDs (int32)
        targets: Target vertex IDs (int32)
        num_vertices: Total number of vertices
        weights: Optional edge weights (float64)

    Returns:
        Tuple of (indptr, indices, weights) arrays

    Raises:
        RuntimeError: If Rust backend is not available
    """
    if not RUST_AVAILABLE:
        raise RuntimeError(
            "Rust backend not available. Install with: pip install parquetframe[rust]"
        )

    # Ensure correct dtypes
    sources = np.asarray(sources, dtype=np.int32)
    targets = np.asarray(targets, dtype=np.int32)
    if weights is not None:
        weights = np.asarray(weights, dtype=np.float64)

    # Call Rust function
    indptr, indices, rust_weights = _rustic.build_csr_rust(
        sources, targets, num_vertices, weights
    )

    # Convert to int64 for consistency with Python implementation
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)

    return indptr, indices, rust_weights


def build_csc_rust(
    sources: np.ndarray,
    targets: np.ndarray,
    num_vertices: int,
    weights: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Build CSC adjacency structure using Rust backend.

    Args:
        sources: Source vertex IDs (int32)
        targets: Target vertex IDs (int32)
        num_vertices: Total number of vertices
        weights: Optional edge weights (float64)

    Returns:
        Tuple of (indptr, indices, weights) arrays

    Raises:
        RuntimeError: If Rust backend is not available
    """
    if not RUST_AVAILABLE:
        raise RuntimeError(
            "Rust backend not available. Install with: pip install parquetframe[rust]"
        )

    # Ensure correct dtypes
    sources = np.asarray(sources, dtype=np.int32)
    targets = np.asarray(targets, dtype=np.int32)
    if weights is not None:
        weights = np.asarray(weights, dtype=np.float64)

    # Call Rust function
    indptr, indices, rust_weights = _rustic.build_csc_rust(
        sources, targets, num_vertices, weights
    )

    # Convert to int64 for consistency with Python implementation
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int64)

    return indptr, indices, rust_weights


def bfs_rust(
    indptr: np.ndarray,
    indices: np.ndarray,
    num_vertices: int,
    sources: list[int] | np.ndarray,
    max_depth: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perform BFS traversal using Rust backend.

    Args:
        indptr: CSR indptr array (int64)
        indices: CSR indices array (int64)
        num_vertices: Total number of vertices
        sources: Source vertex IDs
        max_depth: Maximum traversal depth (None for unlimited)

    Returns:
        Tuple of (distances, predecessors) arrays

    Raises:
        RuntimeError: If Rust backend is not available
    """
    if not RUST_AVAILABLE:
        raise RuntimeError(
            "Rust backend not available. Install with: pip install parquetframe[rust]"
        )

    # Ensure correct dtypes
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int32)  # Rust uses int32
    sources = np.asarray(sources, dtype=np.int32)

    # Call Rust function
    distances, predecessors = _rustic.bfs_rust(
        indptr, indices, num_vertices, sources, max_depth
    )

    # Convert to int64 for consistency
    distances = np.asarray(distances, dtype=np.int64)
    predecessors = np.asarray(predecessors, dtype=np.int64)

    return distances, predecessors


def dfs_rust(
    indptr: np.ndarray,
    indices: np.ndarray,
    num_vertices: int,
    source: int,
    max_depth: int | None = None,
) -> np.ndarray:
    """
    Perform DFS traversal using Rust backend.

    Args:
        indptr: CSR indptr array (int64)
        indices: CSR indices array (int64)
        num_vertices: Total number of vertices
        source: Source vertex ID
        max_depth: Maximum traversal depth (None for unlimited)

    Returns:
        Array of visited vertex IDs in DFS order

    Raises:
        RuntimeError: If Rust backend is not available
    """
    if not RUST_AVAILABLE:
        raise RuntimeError(
            "Rust backend not available. Install with: pip install parquetframe[rust]"
        )

    # Ensure correct dtypes
    indptr = np.asarray(indptr, dtype=np.int64)
    indices = np.asarray(indices, dtype=np.int32)  # Rust uses int32

    # Call Rust function
    visited = _rustic.dfs_rust(indptr, indices, num_vertices, source, max_depth)

    # Convert to int64 for consistency
    visited = np.asarray(visited, dtype=np.int64)

    return visited
