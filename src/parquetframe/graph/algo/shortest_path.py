"""
Shortest path algorithms for weighted and unweighted graphs.

This module implements shortest path algorithms including BFS for unweighted
graphs and Dijkstra's algorithm for weighted graphs with non-negative weights.
"""

from typing import Any, Literal

import pandas as pd


def shortest_path(
    graph: Any,  # GraphFrame type hint will be added after implementation
    sources: int | list[int],
    weight_column: str | None = None,
    directed: bool | None = None,
    backend: Literal["auto", "pandas", "dask"] | None = "auto",
    include_unreachable: bool = True,
) -> pd.DataFrame:
    """
    Find shortest paths from source vertices to all reachable vertices.

    For unweighted graphs (weight_column=None), uses BFS for optimal performance.
    For weighted graphs, uses Dijkstra's algorithm with non-negative weights.

    Args:
        graph: GraphFrame object containing the graph data
        sources: Starting vertex ID(s) for shortest path computation
        weight_column: Name of edge weight column. If None, treats as unweighted (uniform weight 1)
        directed: Whether to treat graph as directed. If None, uses graph.is_directed
        backend: Backend selection ('auto', 'pandas', 'dask')
        include_unreachable: Whether to include unreachable vertices with infinite distance

    Returns:
        DataFrame with columns:
            - vertex (int64): Vertex ID
            - distance (float64): Shortest distance from nearest source (inf for unreachable)
            - predecessor (int64): Previous vertex in shortest path (nullable)

    Raises:
        ValueError: If sources contain invalid vertex IDs, weight_column not found,
                   or negative weights detected (Dijkstra)
        NotImplementedError: If Dask backend requested for weighted shortest paths

    Examples:
        Unweighted shortest paths:
            >>> paths = shortest_path(graph, sources=[1, 2])
            >>> reachable = paths[paths['distance'] < float('inf')]

        Weighted shortest paths:
            >>> paths = shortest_path(graph, sources=[1], weight_column='cost')
            >>> print(paths.nsmallest(10, 'distance'))
    """
    # TODO: Phase 1.2 - Implement shortest path algorithm
    # 1. Validate inputs (sources, weight_column existence, non-negative weights)
    # 2. If unweighted (weight_column=None): delegate to BFS implementation
    # 3. If weighted: implement Dijkstra's algorithm using heapq
    # 4. Handle multi-source initialization for both cases
    # 5. Return DataFrame with vertex, distance, predecessor columns
    # 6. Handle unreachable vertices based on include_unreachable flag
    raise NotImplementedError(
        "Shortest path algorithm implementation pending - Phase 1.2"
    )


def dijkstra(
    graph: Any,  # GraphFrame type hint will be added after implementation
    sources: int | list[int],
    weight_column: str,
    directed: bool | None = None,
    include_unreachable: bool = True,
) -> pd.DataFrame:
    """
    Dijkstra's algorithm for single/multi-source shortest paths with non-negative weights.

    This is a specialized implementation of Dijkstra's algorithm optimized for
    pandas backend processing with CSRAdjacency neighbor lookups.

    Args:
        graph: GraphFrame object containing the graph data
        sources: Starting vertex ID(s)
        weight_column: Name of edge weight column (must exist and be numeric)
        directed: Whether to treat graph as directed. If None, uses graph.is_directed
        include_unreachable: Whether to include unreachable vertices

    Returns:
        DataFrame with shortest path results

    Raises:
        ValueError: If weight_column contains negative weights

    Examples:
        Single source Dijkstra:
            >>> result = dijkstra(graph, sources=1, weight_column='weight')
            >>> print(result.nsmallest(5, 'distance'))
    """
    # TODO: Phase 1.2 - Implement Dijkstra's algorithm
    # 1. Validate weight_column exists and contains non-negative numeric values
    # 2. Get CSRAdjacency and edge weights for efficient lookups
    # 3. Initialize priority queue (heapq) with sources at distance 0
    # 4. Main Dijkstra loop with relaxation and early termination
    # 5. Track predecessors for path reconstruction
    # 6. Return results as pandas DataFrame
    raise NotImplementedError("Dijkstra algorithm implementation pending - Phase 1.2")


def bfs_shortest_path(
    graph: Any,  # GraphFrame type hint will be added after implementation
    sources: int | list[int],
    directed: bool | None = None,
    include_unreachable: bool = True,
) -> pd.DataFrame:
    """
    BFS-based shortest paths for unweighted graphs (all edge weights = 1).

    Optimized implementation that delegates to the main BFS algorithm
    but returns results in shortest_path format for consistency.

    Args:
        graph: GraphFrame object containing the graph data
        sources: Starting vertex ID(s)
        directed: Whether to treat graph as directed
        include_unreachable: Whether to include unreachable vertices

    Returns:
        DataFrame with shortest path results (distance as float64 for consistency)

    Examples:
        Multi-source unweighted shortest paths:
            >>> result = bfs_shortest_path(graph, sources=[1, 10, 100])
            >>> print(result[result['distance'] <= 3])
    """
    # TODO: Phase 1.2 - Implement BFS shortest path wrapper
    # 1. Delegate to main bfs() function with appropriate parameters
    # 2. Convert integer distance to float64 for consistency with Dijkstra
    # 3. Rename 'layer' column to match shortest_path schema if needed
    # 4. Handle include_unreachable by filtering or adding unreachable vertices
    raise NotImplementedError("BFS shortest path implementation pending - Phase 1.2")
