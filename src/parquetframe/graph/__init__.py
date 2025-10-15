"""
Graph processing functionality for ParquetFrame.

This module provides graph data processing capabilities, including:
- Apache GraphAr format support for large-scale graph data
- Graph data structures with vertex/edge property access
- CSR/CSC adjacency list representations for efficient traversal
- Integration with pandas/Dask backends for scalable processing

Examples:
    Basic graph loading:
        >>> import parquetframe as pf
        >>> graph = pf.graph.read_graph("my_social_network/")
        >>> print(graph.num_vertices, graph.num_edges)
        (1000000, 5000000)

    Graph property access:
        >>> users = graph.vertices  # Vertex properties as ParquetFrame
        >>> follows = graph.edges   # Edge properties as ParquetFrame
        >>> degree_out = graph.degree(vertex_id=123, mode="out")

    Graph traversal preparation:
        >>> adj_out = graph.out_adjacency  # CSR adjacency for outgoing edges
        >>> neighbors = adj_out.neighbors(vertex_id=123)
"""

from pathlib import Path
from typing import Any, Literal

from ..core import ParquetFrame


class GraphFrame:
    """
    A graph data structure built on top of ParquetFrame.

    GraphFrame represents a graph with vertex and edge data stored in
    columnar format (Parquet), enabling scalable graph processing using
    pandas or Dask backends.

    The graph follows the Apache GraphAr specification for standardized
    graph data organization and metadata.

    Attributes:
        vertices: ParquetFrame containing vertex data and properties
        edges: ParquetFrame containing edge data and properties
        metadata: Dict containing graph metadata from GraphAr format
        num_vertices: Number of vertices in the graph
        num_edges: Number of edges in the graph

    Examples:
        Access graph components:
            >>> graph = read_graph("social_network/")
            >>> print(f"Graph has {graph.num_vertices} vertices, {graph.num_edges} edges")
            >>> users = graph.vertices  # Access vertex data
            >>> connections = graph.edges  # Access edge data

        Vertex/edge property queries:
            >>> active_users = graph.vertices.query("last_login > '2024-01-01'")
            >>> strong_ties = graph.edges.query("weight > 0.8")

        Degree calculations:
            >>> out_degree = graph.degree(vertex_id=123, mode="out")
            >>> in_degree = graph.degree(vertex_id=123, mode="in")
            >>> total_degree = graph.degree(vertex_id=123, mode="all")
    """

    def __init__(
        self,
        vertices: ParquetFrame,
        edges: ParquetFrame,
        metadata: dict[str, Any],
        adjacency_data: dict[str, Any] | None = None,
    ):
        """
        Initialize a GraphFrame.

        Args:
            vertices: ParquetFrame containing vertex data
            edges: ParquetFrame containing edge data
            metadata: Graph metadata dictionary from GraphAr format
            adjacency_data: Optional precomputed adjacency structures

        Note:
            This constructor is typically not called directly. Use read_graph()
            to load graphs from GraphAr directories.
        """
        self.vertices = vertices
        self.edges = edges
        self.metadata = metadata
        self._adjacency_data = adjacency_data or {}

    @property
    def num_vertices(self) -> int:
        """Number of vertices in the graph."""
        if hasattr(self.vertices.data, "__len__"):
            return len(self.vertices.data)
        return self.vertices.data.index.max() + 1  # Fallback for lazy evaluation

    @property
    def num_edges(self) -> int:
        """Number of edges in the graph."""
        if hasattr(self.edges.data, "__len__"):
            return len(self.edges.data)
        return len(self.edges.data.index)  # For lazy evaluation

    @property
    def is_directed(self) -> bool:
        """Whether the graph is directed."""
        return self.metadata.get("directed", True)

    @property
    def vertex_properties(self) -> list[str]:
        """List of vertex property column names."""
        return [col for col in self.vertices.columns if col not in ("vertex_id", "id")]

    @property
    def edge_properties(self) -> list[str]:
        """List of edge property column names."""
        return [
            col
            for col in self.edges.columns
            if col not in ("src", "dst", "source", "target")
        ]

    def degree(self, vertex_id: int, mode: Literal["in", "out", "all"] = "all") -> int:
        """
        Calculate vertex degree.

        Args:
            vertex_id: The vertex ID to calculate degree for
            mode: Type of degree ("in", "out", "all")

        Returns:
            Vertex degree count

        Examples:
            >>> graph.degree(123)  # Total degree
            15
            >>> graph.degree(123, mode="out")  # Outgoing edges only
            8
            >>> graph.degree(123, mode="in")   # Incoming edges only
            7
        """
        # This is a placeholder implementation - will be properly implemented
        # when adjacency structures are built
        if mode == "out" or mode == "all":
            out_count = len(self.edges.query(f"src == {vertex_id}"))
            if mode == "out":
                return out_count

        if mode == "in" or mode == "all":
            in_count = len(self.edges.query(f"dst == {vertex_id}"))
            if mode == "in":
                return in_count

        if mode == "all":
            return out_count + in_count

        return 0

    def neighbors(
        self, vertex_id: int, mode: Literal["in", "out", "all"] = "out"
    ) -> list[int]:
        """
        Get neighboring vertex IDs.

        Args:
            vertex_id: The vertex to find neighbors for
            mode: Direction to traverse ("in", "out", "all")

        Returns:
            List of neighboring vertex IDs

        Examples:
            >>> graph.neighbors(123)  # Outgoing neighbors
            [456, 789, 101112]
            >>> graph.neighbors(123, mode="in")  # Incoming neighbors
            [13, 14, 15]
        """
        # Placeholder implementation - will be optimized with adjacency structures
        neighbors = []

        if mode in ("out", "all"):
            out_edges = self.edges.query(f"src == {vertex_id}")
            neighbors.extend(out_edges["dst"].tolist())

        if mode in ("in", "all"):
            in_edges = self.edges.query(f"dst == {vertex_id}")
            neighbors.extend(in_edges["src"].tolist())

        return list(set(neighbors))  # Remove duplicates for "all" mode

    def subgraph(self, vertex_ids: list[int]) -> "GraphFrame":
        """
        Extract a subgraph containing only the specified vertices.

        Args:
            vertex_ids: List of vertex IDs to include in subgraph

        Returns:
            New GraphFrame containing the subgraph

        Examples:
            >>> important_nodes = [1, 5, 10, 23, 45]
            >>> subgraph = graph.subgraph(important_nodes)
            >>> print(subgraph.num_vertices, subgraph.num_edges)
            (5, 12)
        """
        # Filter vertices
        vertex_mask = self.vertices["vertex_id"].isin(vertex_ids)
        filtered_vertices = self.vertices[vertex_mask]

        # Filter edges (only edges between selected vertices)
        edge_mask = self.edges["src"].isin(vertex_ids) & self.edges["dst"].isin(
            vertex_ids
        )
        filtered_edges = self.edges[edge_mask]

        # Create new GraphFrame with filtered data
        return GraphFrame(
            vertices=filtered_vertices,
            edges=filtered_edges,
            metadata={**self.metadata, "subgraph": True},
        )

    def __repr__(self) -> str:
        """String representation of the GraphFrame."""
        directed_str = "directed" if self.is_directed else "undirected"
        return (
            f"GraphFrame({self.num_vertices:,} vertices, {self.num_edges:,} edges, "
            f"{directed_str})"
        )

    def __str__(self) -> str:
        """User-friendly string representation."""
        return self.__repr__()


def read_graph(
    path: str | Path,
    *,
    threshold_mb: float | None = None,
    islazy: bool | None = None,
    validate_schema: bool = True,
    load_adjacency: bool = False,
) -> GraphFrame:
    """
    Read a graph from GraphAr format directory.

    GraphAr is a columnar format for graph data that organizes vertices
    and edges in Parquet files with standardized metadata and schema files.

    Args:
        path: Path to GraphAr directory containing graph data
        threshold_mb: Size threshold in MB for pandas/Dask backend selection
        islazy: Force backend selection (True=Dask, False=pandas, None=auto)
        validate_schema: Whether to validate GraphAr schema compliance
        load_adjacency: Whether to preload adjacency structures for fast traversal

    Returns:
        GraphFrame object containing the loaded graph

    Raises:
        FileNotFoundError: If GraphAr directory or required files are missing
        ValueError: If GraphAr schema validation fails
        ImportError: If required dependencies for format are missing

    Examples:
        Basic usage:
            >>> graph = read_graph("my_social_network/")
            >>> print(f"Loaded {graph.num_vertices} vertices, {graph.num_edges} edges")

        Force Dask backend for large graphs:
            >>> large_graph = read_graph("web_graph/", islazy=True)
            >>> print(f"Using Dask: {large_graph.vertices.islazy}")
            True

        Skip schema validation for performance:
            >>> graph = read_graph("trusted_graph/", validate_schema=False)

        Preload adjacency for traversal algorithms:
            >>> graph = read_graph("social_net/", load_adjacency=True)
            >>> neighbors = graph.neighbors(vertex_id=123)  # Fast lookup
    """
    # This is a placeholder - actual implementation will be in the GraphArReader
    from .io.graphar import GraphArReader

    reader = GraphArReader()
    return reader.read(
        path=path,
        threshold_mb=threshold_mb,
        islazy=islazy,
        validate_schema=validate_schema,
        load_adjacency=load_adjacency,
    )


__all__ = [
    "GraphFrame",
    "read_graph",
]
