"""
Graph traversal algorithms: Breadth-First Search (BFS) and Depth-First Search (DFS).

This module implements core graph traversal algorithms with support for both
pandas and Dask backends, multi-source traversal, and flexible output formats.
"""

from collections import deque
from typing import Any, Literal

import numpy as np
import pandas as pd


def bfs(
    graph: Any,  # GraphFrame type hint will be added after implementation
    sources: int | list[int] | None = None,
    max_depth: int | None = None,
    directed: bool | None = None,
    backend: Literal["auto", "pandas", "dask"] | None = "auto",
    include_unreachable: bool = False,
) -> pd.DataFrame:
    """
    Perform Breadth-First Search (BFS) traversal of a graph.

    BFS explores vertices in order of their distance from the source(s),
    visiting all vertices at distance k before any vertices at distance k+1.

    Args:
        graph: GraphFrame object containing the graph data
        sources: Starting vertex ID(s). If None, uses vertex 0 or first available vertex
        max_depth: Maximum depth to traverse. If None, explores entire reachable component
        directed: Whether to treat graph as directed. If None, uses graph.is_directed
        backend: Backend selection ('auto', 'pandas', 'dask')
        include_unreachable: Whether to include unreachable vertices with infinite distance

    Returns:
        DataFrame with columns:
            - vertex (int64): Vertex ID
            - distance (int64): Distance from nearest source vertex
            - predecessor (int64): Previous vertex in BFS tree (nullable)
            - layer (int64): BFS layer/level (same as distance)

    Raises:
        ValueError: If sources contain invalid vertex IDs or graph is empty
        NotImplementedError: If Dask backend is requested but not available

    Examples:
        Single source BFS:
            >>> result = bfs(graph, sources=1, max_depth=3)
            >>> print(result[result['distance'] <= 2])

        Multi-source BFS:
            >>> result = bfs(graph, sources=[1, 5, 10])
            >>> print(result.groupby('distance').size())
    """
    # 1. Validate inputs
    if graph.num_vertices == 0:
        raise ValueError("Cannot perform BFS on empty graph")

    # Normalize sources to list
    if sources is None:
        # Default to vertex 0 if it exists, otherwise first available vertex
        sources = [0] if graph.num_vertices > 0 else []
    elif isinstance(sources, int):
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

    # Validate parameters
    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be non-negative")

    # Handle directed parameter
    if directed is None:
        directed = graph.is_directed

    # Select backend (for Phase 1.2, only pandas is implemented)
    if backend == "dask":
        raise NotImplementedError("Dask backend for BFS not yet implemented")

    # 2. Get adjacency structure for efficient neighbor lookups
    if directed:
        adj = graph.csr_adjacency  # Outgoing edges only
    else:
        # For undirected graphs, we need both directions
        # Use CSR but will need to check both directions
        adj = graph.csr_adjacency
        adj_reverse = graph.csc_adjacency  # For incoming edges

    # 3. Initialize BFS data structures
    num_vertices = graph.num_vertices
    distance = np.full(num_vertices, -1, dtype=np.int64)  # -1 = unvisited
    predecessor = np.full(num_vertices, -1, dtype=np.int64)  # -1 = no predecessor

    # Initialize queue with source vertices
    queue = deque()
    for src in sources:
        distance[src] = 0
        predecessor[src] = -1  # Sources have no predecessor
        queue.append(src)

    # 4. Main BFS loop
    current_depth = 0
    while queue:
        # Process all vertices at current depth level
        level_size = len(queue)

        # Check depth limit
        if max_depth is not None and current_depth >= max_depth:
            break

        for _ in range(level_size):
            current = queue.popleft()
            current_dist = distance[current]

            # Get neighbors based on graph directionality
            if directed:
                neighbors = adj.neighbors(current)
            else:
                # For undirected graphs, get both outgoing and incoming neighbors
                out_neighbors = adj.neighbors(current)
                in_neighbors = adj_reverse.predecessors(current)
                neighbors = np.unique(np.concatenate([out_neighbors, in_neighbors]))

            # Visit unvisited neighbors
            for neighbor in neighbors:
                if distance[neighbor] == -1:  # Unvisited
                    distance[neighbor] = current_dist + 1
                    predecessor[neighbor] = current
                    queue.append(neighbor)

        current_depth += 1

    # 5. Create result DataFrame
    result_data = {"vertex": [], "distance": [], "predecessor": [], "layer": []}

    for vertex in range(num_vertices):
        vertex_distance = distance[vertex]

        # Include vertex if:
        # - It was visited (distance != -1), OR
        # - include_unreachable is True
        if vertex_distance != -1 or include_unreachable:
            result_data["vertex"].append(vertex)

            # For unreachable vertices, use a large sentinel value instead of infinity
            if vertex_distance != -1:
                result_data["distance"].append(vertex_distance)
                result_data["layer"].append(vertex_distance)
            else:
                # Use -1 to indicate unreachable (will be handled in result processing)
                result_data["distance"].append(-1)
                result_data["layer"].append(-1)

            result_data["predecessor"].append(
                predecessor[vertex] if predecessor[vertex] != -1 else None
            )

    # Create DataFrame with proper dtypes
    result_df = pd.DataFrame(result_data)
    if not result_df.empty:
        result_df["vertex"] = result_df["vertex"].astype("int64")
        result_df["distance"] = result_df["distance"].astype("int64")
        result_df["predecessor"] = result_df["predecessor"].astype(
            "Int64"
        )  # Nullable int
        result_df["layer"] = result_df["layer"].astype("int64")
    else:
        # Handle empty result case
        result_df = pd.DataFrame(
            {
                "vertex": pd.Series([], dtype="int64"),
                "distance": pd.Series([], dtype="int64"),
                "predecessor": pd.Series([], dtype="Int64"),
                "layer": pd.Series([], dtype="int64"),
            }
        )

    return result_df


def dfs(
    graph: Any,  # GraphFrame type hint will be added after implementation
    sources: int | list[int] | None = None,
    max_depth: int | None = None,
    directed: bool | None = None,
    backend: Literal["auto", "pandas", "dask"] | None = "auto",
    forest: bool = False,
) -> pd.DataFrame:
    """
    Perform Depth-First Search (DFS) traversal of a graph.

    DFS explores vertices by going as deep as possible along each branch
    before backtracking. Uses iterative implementation to avoid recursion limits.

    Args:
        graph: GraphFrame object containing the graph data
        sources: Starting vertex ID(s). If None and forest=False, uses vertex 0
        max_depth: Maximum depth to traverse. If None, explores until leaf nodes
        directed: Whether to treat graph as directed. If None, uses graph.is_directed
        backend: Backend selection ('auto', 'pandas', 'dask')
        forest: If True, performs DFS forest traversal over all components

    Returns:
        DataFrame with columns:
            - vertex (int64): Vertex ID
            - predecessor (int64): Previous vertex in DFS tree (nullable)
            - discovery_time (int64): Timestamp when vertex was first discovered
            - finish_time (int64): Timestamp when vertex processing completed
            - component_id (int64): Connected component ID (for forest traversal)

    Raises:
        ValueError: If sources contain invalid vertex IDs or graph is empty
        NotImplementedError: If Dask backend is requested (falls back to pandas)

    Examples:
        Single source DFS:
            >>> result = dfs(graph, sources=1)
            >>> print(result[['vertex', 'discovery_time', 'finish_time']])

        DFS forest (all components):
            >>> result = dfs(graph, forest=True)
            >>> print(result.groupby('component_id').size())
    """
    # TODO: Phase 1.2 - Implement DFS algorithm
    # 1. Validate inputs and handle forest vs single-source modes
    # 2. Get CSRAdjacency structure for neighbor lookups
    # 3. Implement iterative stack-based DFS
    # 4. Track discovery/finish times and component IDs
    # 5. Handle multi-component traversal for forest mode
    # 6. Return pandas DataFrame with required columns
    raise NotImplementedError("DFS algorithm implementation pending - Phase 1.2")
