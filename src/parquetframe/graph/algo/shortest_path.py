"""
Shortest path algorithms for weighted and unweighted graphs.

This module implements shortest path algorithms including BFS for unweighted
graphs and Dijkstra's algorithm for weighted graphs with non-negative weights.
"""

import heapq
from typing import Any, Literal

import numpy as np
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
    # 1. Validate inputs
    if graph.num_vertices == 0:
        raise ValueError("Cannot compute shortest paths on empty graph")

    # Normalize sources to list
    if isinstance(sources, int):
        sources = [sources]
    else:
        sources = list(sources)

    if not sources:
        raise ValueError("At least one source vertex must be specified")

    # Validate source vertices exist
    for src in sources:
        if src < 0 or src >= graph.num_vertices:
            raise ValueError(
                f"Source vertex {src} out of range [0, {graph.num_vertices})"
            )

    # Handle directed parameter
    if directed is None:
        directed = graph.is_directed

    # 2. Choose algorithm based on whether weights are provided
    if weight_column is None:
        # Unweighted graph - use BFS
        return bfs_shortest_path(graph, sources, directed, include_unreachable)
    else:
        # Weighted graph - use Dijkstra's algorithm
        if backend == "dask":
            raise NotImplementedError(
                "Dask backend for weighted shortest paths not yet implemented. "
                "Use backend='pandas' for Dijkstra's algorithm."
            )
        return dijkstra(graph, sources, weight_column, directed, include_unreachable)


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
    # 1. Validate weight_column exists and contains non-negative numeric values
    if weight_column not in graph.edges.columns:
        raise ValueError(f"Weight column '{weight_column}' not found in graph edges")

    # Get edge weights and check for negative values
    edge_weights = graph.edges[weight_column]
    if hasattr(edge_weights, "pandas_df"):
        edge_weights = edge_weights.pandas_df  # Handle ParquetFrame
    elif hasattr(edge_weights, "compute"):
        edge_weights = edge_weights.compute()  # Handle Dask

    if edge_weights.min() < 0:
        raise ValueError("Dijkstra's algorithm requires non-negative edge weights")

    # Normalize sources to list
    if isinstance(sources, int):
        sources = [sources]
    else:
        sources = list(sources)

    # Handle directed parameter
    if directed is None:
        directed = graph.is_directed

    # 2. Get adjacency structures and edge data for efficient lookups
    if directed:
        adj = graph.csr_adjacency  # Outgoing edges only
    else:
        # For undirected graphs, we need both directions
        adj = graph.csr_adjacency
        adj_reverse = graph.csc_adjacency

    # Get edge data for weight lookups
    edges_df = graph.edges
    if hasattr(edges_df, "pandas_df"):
        edges_df = edges_df.pandas_df
    elif hasattr(edges_df, "compute"):
        edges_df = edges_df.compute()

    # Create edge weight lookup dictionary for efficient access
    # Format: {(src, dst): weight}
    from ..data import EdgeSet

    edge_set = EdgeSet(
        data=graph.edges, edge_type="default", properties={}, schema=None
    )
    src_col = edge_set.src_column or "src"
    dst_col = edge_set.dst_column or "dst"

    edge_weights_dict = {}
    for _, row in edges_df.iterrows():
        src, dst, weight = row[src_col], row[dst_col], row[weight_column]
        edge_weights_dict[(src, dst)] = weight
        if not directed:
            # Add reverse edge for undirected graphs
            edge_weights_dict[(dst, src)] = weight

    # 3. Initialize Dijkstra's data structures
    num_vertices = graph.num_vertices
    distances = np.full(num_vertices, np.inf, dtype=np.float64)
    predecessors = np.full(num_vertices, -1, dtype=np.int64)
    visited = np.full(num_vertices, False, dtype=bool)

    # Priority queue: (distance, vertex)
    pq = []

    # Initialize sources
    for src in sources:
        distances[src] = 0.0
        predecessors[src] = -1  # Sources have no predecessor
        heapq.heappush(pq, (0.0, src))

    # 4. Main Dijkstra loop
    while pq:
        current_dist, current_vertex = heapq.heappop(pq)

        # Skip if we've already processed this vertex with a better distance
        if visited[current_vertex] or current_dist > distances[current_vertex]:
            continue

        visited[current_vertex] = True

        # Get neighbors based on graph directionality
        if directed:
            neighbors = adj.neighbors(current_vertex)
        else:
            # For undirected graphs, get both outgoing and incoming neighbors
            out_neighbors = adj.neighbors(current_vertex)
            if current_vertex < adj_reverse.num_vertices:
                in_neighbors = adj_reverse.predecessors(current_vertex)
                neighbors = np.unique(np.concatenate([out_neighbors, in_neighbors]))
            else:
                neighbors = out_neighbors

        # Relax edges to neighbors
        for neighbor in neighbors:
            if visited[neighbor]:
                continue

            # Get edge weight
            edge_weight = edge_weights_dict.get((current_vertex, neighbor))
            if edge_weight is None:
                continue  # Skip if edge weight not found

            new_distance = distances[current_vertex] + edge_weight

            # Relaxation step
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                predecessors[neighbor] = current_vertex
                heapq.heappush(pq, (new_distance, neighbor))

    # 5. Create result DataFrame
    result_data = {"vertex": [], "distance": [], "predecessor": []}

    for vertex in range(num_vertices):
        vertex_distance = distances[vertex]

        # Include vertex if:
        # - It was reached (distance != inf), OR
        # - include_unreachable is True
        if vertex_distance != np.inf or include_unreachable:
            result_data["vertex"].append(vertex)
            result_data["distance"].append(vertex_distance)
            result_data["predecessor"].append(
                predecessors[vertex] if predecessors[vertex] != -1 else None
            )

    # Create DataFrame with proper dtypes
    result_df = pd.DataFrame(result_data)
    if not result_df.empty:
        result_df["vertex"] = result_df["vertex"].astype("int64")
        result_df["distance"] = result_df["distance"].astype("float64")
        result_df["predecessor"] = result_df["predecessor"].astype(
            "Int64"
        )  # Nullable int
    else:
        # Handle empty result case
        result_df = pd.DataFrame(
            {
                "vertex": pd.Series([], dtype="int64"),
                "distance": pd.Series([], dtype="float64"),
                "predecessor": pd.Series([], dtype="Int64"),
            }
        )

    return result_df


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
    # 1. Delegate to main BFS function
    from .traversal import bfs

    # Call BFS with include_unreachable to get consistent behavior
    bfs_result = bfs(
        graph=graph,
        sources=sources,
        directed=directed,
        include_unreachable=include_unreachable,
        backend="pandas",  # Always use pandas for consistency with Dijkstra
    )

    # 2. Convert BFS result to shortest_path format
    result_df = bfs_result[["vertex", "distance", "predecessor"]].copy()

    # Convert distance from int64 to float64 for consistency with Dijkstra
    result_df["distance"] = result_df["distance"].astype("float64")

    # Handle unreachable vertices (BFS uses -1 for unreachable, we want inf)
    if include_unreachable:
        result_df.loc[result_df["distance"] == -1.0, "distance"] = np.inf
    else:
        # Filter out unreachable vertices (those with distance -1)
        result_df = result_df[result_df["distance"] != -1.0]

    return result_df
