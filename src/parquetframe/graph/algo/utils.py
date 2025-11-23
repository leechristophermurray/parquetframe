"""
Utility functions shared across graph algorithms.

This module provides common functionality used by multiple graph algorithms
including backend selection, parameter validation, and result formatting.
"""

from typing import Any, Literal

import pandas as pd


def select_backend(
    graph: Any,  # GraphFrame type hint will be added after implementation
    backend: Literal["auto", "pandas", "dask"] | None = "auto",
    algorithm: str = "unknown",
) -> Literal["pandas", "dask"]:
    """
    Select the optimal backend for graph algorithm execution.

    Makes intelligent backend selection based on graph size, current data backend,
    user preference, and algorithm capabilities.

    Args:
        graph: GraphFrame object
        backend: User backend preference ('auto', 'pandas', 'dask')
        algorithm: Algorithm name for backend capability checking

    Returns:
        Selected backend ('pandas' or 'dask')

    Raises:
        NotImplementedError: If requested backend is not available for algorithm

    Examples:
        Automatic selection:
            >>> backend = select_backend(graph, 'auto', 'bfs')
            >>> print(f"Selected {backend} backend for BFS")
    """
    # 1. If backend explicitly specified, validate and return
    if backend == "pandas":
        return "pandas"
    elif backend == "dask":
        return "dask"

    # 2. Auto-select based on graph characteristics
    # Check if graph uses Dask backend
    is_lazy = getattr(graph.vertices, "islazy", False) or getattr(
        graph.edges, "islazy", False
    )

    # 3. Consider graph size (heuristic: > 1M edges suggests Dask)
    try:
        edge_count = len(graph.edges)
        if edge_count > 1_000_000:
            return "dask"
    except:
        pass  # Fall through to default

    # 4. Default: use pandas for better algorithm support
    return "pandas"


def validate_sources(
    graph: Any,  # GraphFrame type hint will be added after implementation
    sources: int | list[int] | None,
) -> list[int]:
    """
    Validate and normalize source vertex specification.

    Ensures source vertices exist in the graph and returns a consistent
    list format for algorithm processing.

    Args:
        graph: GraphFrame object
        sources: Source vertex specification (int, list, or None)

    Returns:
        List of validated source vertex IDs

    Raises:
        ValueError: If sources contain invalid vertex IDs or graph is empty

    Examples:
        Validate single source:
            >>> sources = validate_sources(graph, 42)
            >>> print(sources)  # [42]

        Validate multiple sources:
            >>> sources = validate_sources(graph, [1, 10, 100])
            >>> print(f"Validated {len(sources)} source vertices")
    """
    # 1. Handle None case - default to first vertex
    if sources is None:
        vertices_df = (
            graph.vertices._df if hasattr(graph.vertices, "_df") else graph.vertices
        )
        if len(vertices_df) == 0:
            raise ValueError("Cannot validate sources: graph has no vertices")
        first_id = vertices_df.iloc[0]["id"] if "id" in vertices_df.columns else 0
        return [first_id]

    # 2. Convert single int to list
    if isinstance(sources, int):
        sources = [sources]

    # 3. Validate all source IDs exist in graph
    vertices_df = (
        graph.vertices._df if hasattr(graph.vertices, "_df") else graph.vertices
    )
    if "id" in vertices_df.columns:
        valid_ids = set(vertices_df["id"].values)
        invalid_sources = [s for s in sources if s not in valid_ids]
        if invalid_sources:
            raise ValueError(f"Invalid source vertices: {invalid_sources}")

    # 4. Remove duplicates while preserving order
    seen = set()
    unique_sources = []
    for s in sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    # 5. Ensure at least one valid source
    if not unique_sources:
        raise ValueError("At least one valid source vertex required")

    return unique_sources


def create_result_dataframe(
    data: dict[str, list],
    columns: list[str],
    dtypes: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Create a standardized result DataFrame with proper column types.

    Ensures consistent column naming and data types across all algorithm results.

    Args:
        data: Dictionary mapping column names to value lists
        columns: Expected column order for the result
        dtypes: Optional dtype specifications for columns

    Returns:
        Formatted pandas DataFrame with correct types

    Examples:
        Create BFS result DataFrame:
            >>> data = {
            ...     'vertex': [0, 1, 2],
            ...     'distance': [0, 1, 2],
            ...     'predecessor': [None, 0, 1]
            ... }
            >>> result = create_result_dataframe(data, ['vertex', 'distance', 'predecessor'])
    """
    # 1. Create DataFrame from data dict
    df = pd.DataFrame(data)

    # 2. Reorder columns according to expected order
    if columns:
        # Only reorder columns that exist
        existing_cols = [c for c in columns if c in df.columns]
        df = df[existing_cols]

    # 3. Apply proper dtypes if specified
    if dtypes:
        for col, dtype in dtypes.items():
            if col in df.columns:
                try:
                    if dtype in ("Int64", "Int32"):  # Nullable integer
                        df[col] = pd.array(df[col], dtype=dtype)
                    else:
                        df[col] = df[col].astype(dtype)
                except (ValueError, TypeError):
                    pass  # Skip if conversion fails

    return df


def symmetrize_edges(
    graph: Any,  # GraphFrame type hint will be added after implementation
    directed: bool | None = None,
) -> Any:  # Return type will be EdgeSet or similar
    """
    Create symmetrized edge set for undirected graph algorithms.

    For directed graphs that need to be treated as undirected (e.g., weak components),
    adds reverse edges to make the graph symmetric.

    Args:
        graph: GraphFrame object
        directed: Whether to treat graph as directed (None = use graph.is_directed)

    Returns:
        EdgeSet with potentially symmetrized edges

    Examples:
        Symmetrize directed graph:
            >>> undirected_edges = symmetrize_edges(graph, directed=False)
            >>> print(f"Original: {len(graph.edges)} edges")
            >>> print(f"Symmetrized: {len(undirected_edges)} edges")
    """
    # 1. Check if symmetrization is needed
    is_directed = graph.is_directed if hasattr(graph, "is_directed") else True
    if directed is not None:
        is_directed = directed

    if not is_directed:
        # Already undirected, return as-is
        return graph.edges

    # 2. Get original edges DataFrame
    edges_df = graph.edges._df if hasattr(graph.edges, "_df") else graph.edges

    # 3. Create reverse edges (swap src/dst columns)
    if "src" in edges_df.columns and "dst" in edges_df.columns:
        reverse_edges = edges_df.copy()
        reverse_edges["src"], reverse_edges["dst"] = (
            edges_df["dst"].copy(),
            edges_df["src"].copy(),
        )

        # 4. Concatenate original and reverse edges
        symmetrized = pd.concat([edges_df, reverse_edges], ignore_index=True)

        # 5. Remove duplicate edges
        symmetrized = symmetrized.drop_duplicates(subset=["src", "dst"], keep="first")

        # 6. Return the symmetrized edge data
        # Note: Caller should wrap this in appropriate EdgeSet if needed
        return symmetrized
    else:
        # If columns not named src/dst, return original
        return graph.edges


def check_convergence(
    old_values: pd.Series | Any,  # Could be Dask Series
    new_values: pd.Series | Any,  # Could be Dask Series
    tol: float,
    metric: Literal["l1", "l2", "max"] = "l1",
) -> bool:
    """
    Check convergence between old and new algorithm values.

    Computes difference metric between iterations to determine if
    algorithm has converged within tolerance.

    Args:
        old_values: Previous iteration values
        new_values: Current iteration values
        tol: Convergence tolerance threshold
        metric: Distance metric ('l1', 'l2', 'max')

    Returns:
        True if converged (difference < tolerance)

    Examples:
        Check PageRank convergence:
            >>> converged = check_convergence(old_ranks, new_ranks, tol=1e-6)
            >>> if converged:
            ...     print("Algorithm converged!")
    """
    import numpy as np

    # 1. Handle pandas vs Dask Series appropriately
    # Compute values if Dask
    if hasattr(old_values, "compute"):
        old_values = old_values.compute()
    if hasattr(new_values, "compute"):
        new_values = new_values.compute()

    # 4. Handle edge cases
    if len(old_values) == 0 or len(new_values) == 0:
        return False

    # Fill NaN values with 0 for comparison
    old_clean = old_values.fillna(0)
    new_clean = new_values.fillna(0)

    # 2. Compute difference based on specified metric
    diff = np.abs(new_clean - old_clean)

    if metric == "l1":
        distance = diff.sum()
    elif metric == "l2":
        distance = np.sqrt((diff**2).sum())
    elif metric == "max":
        distance = diff.max()
    else:
        raise ValueError(f"Unknown metric: {metric}")

    # 3. Return boolean convergence status
    return distance < tol
