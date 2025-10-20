"""Tests for shortest path algorithms (BFS for unweighted, Dijkstra for weighted)."""

import numpy as np
import pandas as pd
import pytest

from parquetframe.core import ParquetFrame
from parquetframe.graph import GraphFrame
from parquetframe.graph.algo.shortest_path import (
    bfs_shortest_path,
    dijkstra,
    shortest_path,
)


@pytest.fixture
def simple_chain_graph():
    """Create a simple chain graph: 0->1->2->3->4."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})

    # Edges
    edge_data = pd.DataFrame({"src": [0, 1, 2, 3], "dst": [1, 2, 3, 4]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def weighted_chain_graph():
    """Create a weighted chain graph: 0--(2)->1--(3)->2--(1)->3--(4)->4."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})

    # Edges with weights
    edge_data = pd.DataFrame(
        {"src": [0, 1, 2, 3], "dst": [1, 2, 3, 4], "weight": [2.0, 3.0, 1.0, 4.0]}
    )

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def weighted_diamond_graph():
    """Create a diamond graph with different path costs: 0->1->3 vs 0->2->3."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3]})

    # Edges: two paths from 0 to 3
    # Path 1: 0->1->3 (cost 1 + 5 = 6)
    # Path 2: 0->2->3 (cost 10 + 1 = 11)
    edge_data = pd.DataFrame(
        {"src": [0, 0, 1, 2], "dst": [1, 2, 3, 3], "weight": [1.0, 10.0, 5.0, 1.0]}
    )

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def disconnected_weighted_graph():
    """Create disconnected components with weights: 0->1, 2->3, 4 (isolated)."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})

    # Edges - two components plus isolated vertex
    edge_data = pd.DataFrame({"src": [0, 2], "dst": [1, 3], "weight": [2.5, 1.5]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.mark.graph
class TestShortestPath:
    """Test the main shortest_path function (delegates to BFS or Dijkstra)."""

    def test_unweighted_shortest_path(self, simple_chain_graph):
        """Test unweighted shortest path (should delegate to BFS)."""
        result = shortest_path(simple_chain_graph, sources=0)

        # Should have all vertices with correct distances
        assert len(result) == 5
        assert list(result.sort_values("vertex")["distance"]) == [
            0.0,
            1.0,
            2.0,
            3.0,
            4.0,
        ]

        # Check dtypes are correct (distance as float64)
        assert result["distance"].dtype == "float64"
        assert result["vertex"].dtype == "int64"
        assert result["predecessor"].dtype == "Int64"

    def test_weighted_shortest_path(self, weighted_chain_graph):
        """Test weighted shortest path (should delegate to Dijkstra)."""
        result = shortest_path(weighted_chain_graph, sources=0, weight_column="weight")

        # Should have all vertices with cumulative weighted distances
        expected_distances = [0.0, 2.0, 5.0, 6.0, 10.0]  # 0, 2, 2+3, 2+3+1, 2+3+1+4
        assert len(result) == 5
        actual_distances = list(result.sort_values("vertex")["distance"])
        assert actual_distances == expected_distances

    def test_multi_source_unweighted(self, simple_chain_graph):
        """Test multi-source unweighted shortest paths."""
        result = shortest_path(simple_chain_graph, sources=[0, 4])

        # Sources should have distance 0
        source_results = result[result["vertex"].isin([0, 4])]
        assert all(source_results["distance"] == 0.0)

        # Middle vertices should be reached from nearest source
        middle = result[result["vertex"] == 2].iloc[0]
        assert middle["distance"] == 2.0  # From either source

    def test_multi_source_weighted(self, weighted_chain_graph):
        """Test multi-source weighted shortest paths."""
        result = shortest_path(
            weighted_chain_graph, sources=[0, 4], weight_column="weight"
        )

        # Sources should have distance 0
        source_results = result[result["vertex"].isin([0, 4])]
        assert all(source_results["distance"] == 0.0)

    def test_shortest_path_with_better_route(self, weighted_diamond_graph):
        """Test that shortest path finds the optimal route."""
        result = shortest_path(
            weighted_diamond_graph, sources=0, weight_column="weight"
        )

        # Vertex 3 should be reached via the shorter path (0->1->3 = 6, not 0->2->3 = 11)
        vertex_3_result = result[result["vertex"] == 3].iloc[0]
        assert vertex_3_result["distance"] == 6.0
        assert vertex_3_result["predecessor"] == 1  # Came from vertex 1

    def test_include_unreachable_weighted(self, disconnected_weighted_graph):
        """Test include_unreachable with weighted graph."""
        result = shortest_path(
            disconnected_weighted_graph,
            sources=0,
            weight_column="weight",
            include_unreachable=True,
        )

        # Should include all vertices
        assert len(result) == 5

        # Reachable vertices have finite distances
        reachable = result[result["vertex"].isin([0, 1])]
        assert list(reachable.sort_values("vertex")["distance"]) == [0.0, 2.5]

        # Unreachable vertices have infinite distances
        unreachable = result[result["vertex"].isin([2, 3, 4])]
        assert all(unreachable["distance"] == np.inf)

    def test_shortest_path_empty_graph(self):
        """Test shortest path on empty graph."""
        empty_vertices = pd.DataFrame({"vertex_id": []})
        empty_edges = pd.DataFrame({"src": [], "dst": [], "weight": []})
        empty_graph = GraphFrame(
            vertices=ParquetFrame(empty_vertices),
            edges=ParquetFrame(empty_edges),
            metadata={"directed": True},
        )

        with pytest.raises(
            ValueError, match="Cannot compute shortest paths on empty graph"
        ):
            shortest_path(empty_graph, sources=0)

    def test_invalid_source_vertex(self, simple_chain_graph):
        """Test shortest path with invalid source."""
        with pytest.raises(ValueError, match="Source vertex 10 out of range"):
            shortest_path(simple_chain_graph, sources=10)

    def test_invalid_weight_column(self, simple_chain_graph):
        """Test shortest path with non-existent weight column."""
        with pytest.raises(ValueError, match="Weight column 'nonexistent' not found"):
            shortest_path(simple_chain_graph, sources=0, weight_column="nonexistent")

    def test_dask_backend_not_supported_weighted(self, weighted_chain_graph):
        """Test that Dask backend raises NotImplementedError for weighted graphs."""
        with pytest.raises(
            NotImplementedError,
            match="Dask backend for weighted shortest paths not yet implemented",
        ):
            shortest_path(
                weighted_chain_graph, sources=0, weight_column="weight", backend="dask"
            )


@pytest.mark.graph
class TestDijkstra:
    """Test Dijkstra's algorithm implementation."""

    def test_dijkstra_single_source(self, weighted_chain_graph):
        """Test Dijkstra from single source."""
        result = dijkstra(weighted_chain_graph, sources=0, weight_column="weight")

        # Check correct shortest distances
        expected_distances = [0.0, 2.0, 5.0, 6.0, 10.0]
        actual_distances = list(result.sort_values("vertex")["distance"])
        assert actual_distances == expected_distances

        # Check predecessors form a valid shortest path tree
        vertex_4_result = result[result["vertex"] == 4].iloc[0]
        assert vertex_4_result["predecessor"] == 3

        vertex_3_result = result[result["vertex"] == 3].iloc[0]
        assert vertex_3_result["predecessor"] == 2

    def test_dijkstra_multi_source(self, weighted_chain_graph):
        """Test Dijkstra with multiple sources."""
        result = dijkstra(weighted_chain_graph, sources=[0, 2], weight_column="weight")

        # Both sources should have distance 0
        source_results = result[result["vertex"].isin([0, 2])]
        assert all(source_results["distance"] == 0.0)

        # Vertex 1 should be reached from source 0 (distance 2)
        vertex_1_result = result[result["vertex"] == 1].iloc[0]
        assert vertex_1_result["distance"] == 2.0
        assert vertex_1_result["predecessor"] == 0

        # Vertex 3 should be reached from source 2 (distance 1)
        vertex_3_result = result[result["vertex"] == 3].iloc[0]
        assert vertex_3_result["distance"] == 1.0
        assert vertex_3_result["predecessor"] == 2

    def test_dijkstra_optimal_path_selection(self, weighted_diamond_graph):
        """Test that Dijkstra selects the optimal path."""
        result = dijkstra(weighted_diamond_graph, sources=0, weight_column="weight")

        # Should choose path 0->1->3 (cost 6) over 0->2->3 (cost 11)
        vertex_3_result = result[result["vertex"] == 3].iloc[0]
        assert vertex_3_result["distance"] == 6.0
        assert vertex_3_result["predecessor"] == 1

    def test_dijkstra_negative_weights_error(self):
        """Test that Dijkstra raises error for negative weights."""
        # Create graph with negative weight
        vertex_data = pd.DataFrame({"vertex_id": [0, 1]})
        edge_data = pd.DataFrame({"src": [0], "dst": [1], "weight": [-1.0]})
        negative_graph = GraphFrame(
            vertices=ParquetFrame(vertex_data),
            edges=ParquetFrame(edge_data),
            metadata={"directed": True},
        )

        with pytest.raises(
            ValueError, match="Dijkstra's algorithm requires non-negative edge weights"
        ):
            dijkstra(negative_graph, sources=0, weight_column="weight")

    def test_dijkstra_missing_weight_column(self, simple_chain_graph):
        """Test Dijkstra with missing weight column."""
        with pytest.raises(
            ValueError, match="Weight column 'weight' not found in graph edges"
        ):
            dijkstra(simple_chain_graph, sources=0, weight_column="weight")

    def test_dijkstra_result_dtypes(self, weighted_chain_graph):
        """Test that Dijkstra result has correct dtypes."""
        result = dijkstra(weighted_chain_graph, sources=0, weight_column="weight")

        assert result["vertex"].dtype == "int64"
        assert result["distance"].dtype == "float64"
        assert result["predecessor"].dtype == "Int64"  # Nullable int


@pytest.mark.graph
class TestBFSShortestPath:
    """Test BFS shortest path wrapper."""

    def test_bfs_shortest_path_single_source(self, simple_chain_graph):
        """Test BFS shortest path from single source."""
        result = bfs_shortest_path(simple_chain_graph, sources=0)

        # Should match BFS results but with float64 distances
        assert len(result) == 5
        expected_distances = [0.0, 1.0, 2.0, 3.0, 4.0]
        actual_distances = list(result.sort_values("vertex")["distance"])
        assert actual_distances == expected_distances

        # Check dtypes
        assert result["distance"].dtype == "float64"

    def test_bfs_shortest_path_multi_source(self, simple_chain_graph):
        """Test BFS shortest path with multiple sources."""
        result = bfs_shortest_path(simple_chain_graph, sources=[0, 4])

        # Sources should have distance 0.0
        source_results = result[result["vertex"].isin([0, 4])]
        assert all(source_results["distance"] == 0.0)

    def test_bfs_shortest_path_disconnected_include_unreachable(self):
        """Test BFS shortest path on disconnected graph with unreachable vertices."""
        # Create disconnected graph
        vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})
        edge_data = pd.DataFrame({"src": [0, 2], "dst": [1, 3]})
        disconnected_graph = GraphFrame(
            vertices=ParquetFrame(vertex_data),
            edges=ParquetFrame(edge_data),
            metadata={"directed": True},
        )

        result = bfs_shortest_path(
            disconnected_graph, sources=0, include_unreachable=True
        )

        # Should include all vertices
        assert len(result) == 5

        # Reachable vertices have finite distances
        reachable = result[result["vertex"].isin([0, 1])]
        assert list(reachable.sort_values("vertex")["distance"]) == [0.0, 1.0]

        # Unreachable vertices have infinite distances
        unreachable = result[result["vertex"].isin([2, 3, 4])]
        assert all(unreachable["distance"] == np.inf)

    def test_bfs_shortest_path_exclude_unreachable(self):
        """Test BFS shortest path excluding unreachable vertices."""
        # Create disconnected graph
        vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})
        edge_data = pd.DataFrame({"src": [0, 2], "dst": [1, 3]})
        disconnected_graph = GraphFrame(
            vertices=ParquetFrame(vertex_data),
            edges=ParquetFrame(edge_data),
            metadata={"directed": True},
        )

        result = bfs_shortest_path(
            disconnected_graph, sources=0, include_unreachable=False
        )

        # Should only include reachable vertices
        assert len(result) == 2
        assert set(result["vertex"]) == {0, 1}
        assert all(result["distance"] < np.inf)


@pytest.mark.graph
class TestDijkstraRustBackend:
    """Test Rust backend integration for Dijkstra shortest path algorithm."""

    def test_dijkstra_rust_backend_when_available(self, weighted_chain_graph):
        """Test that Rust backend works when explicitly requested and available."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Explicitly request Rust backend
        result = shortest_path(
            weighted_chain_graph, sources=0, weight_column="weight", backend="rust"
        )

        # Should have correct basic properties
        assert len(result) == 5
        expected_distances = [0.0, 2.0, 5.0, 6.0, 10.0]
        actual_distances = list(result.sort_values("vertex")["distance"])
        assert actual_distances == expected_distances

    def test_dijkstra_rust_backend_unavailable_error(self, weighted_chain_graph):
        """Test RuntimeError when Rust backend requested but unavailable."""
        from parquetframe.graph.rust_backend import is_rust_available

        if is_rust_available():
            pytest.skip("Rust backend is available, cannot test unavailable scenario")

        # Should raise RuntimeError when Rust explicitly requested but unavailable
        with pytest.raises(
            RuntimeError, match="Rust backend requested but not available"
        ):
            shortest_path(
                weighted_chain_graph, sources=0, weight_column="weight", backend="rust"
            )

    def test_dijkstra_auto_prefers_rust(self, weighted_chain_graph):
        """Test that backend='auto' prefers Rust when available."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Auto should prefer Rust
        result = shortest_path(
            weighted_chain_graph, sources=0, weight_column="weight", backend="auto"
        )

        # Should succeed and return valid results
        assert len(result) == 5
        expected_distances = [0.0, 2.0, 5.0, 6.0, 10.0]
        actual_distances = list(result.sort_values("vertex")["distance"])
        assert actual_distances == expected_distances

    def test_dijkstra_rust_parity_with_pandas(self, weighted_diamond_graph):
        """Test that Rust results match pandas implementation."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Run both implementations
        rust_result = dijkstra(
            weighted_diamond_graph, sources=0, weight_column="weight", backend="rust"
        )
        pandas_result = dijkstra(
            weighted_diamond_graph, sources=0, weight_column="weight", backend="pandas"
        )

        # Sort by vertex for comparison
        rust_sorted = rust_result.sort_values("vertex").reset_index(drop=True)
        pandas_sorted = pandas_result.sort_values("vertex").reset_index(drop=True)

        # Results should match exactly
        for i in range(len(rust_sorted)):
            assert rust_sorted.iloc[i]["distance"] == pandas_sorted.iloc[i]["distance"]

            # Handle pandas NA values properly in predecessor comparison
            rust_pred = rust_sorted.iloc[i]["predecessor"]
            pandas_pred = pandas_sorted.iloc[i]["predecessor"]

            if pd.isna(rust_pred) and pd.isna(pandas_pred):
                # Both are NA, considered equal
                continue
            elif pd.isna(rust_pred) or pd.isna(pandas_pred):
                pytest.fail(
                    f"Predecessor mismatch at vertex {i}: "
                    f"rust={rust_pred}, pandas={pandas_pred}"
                )
            else:
                assert rust_pred == pandas_pred

    def test_dijkstra_rust_multi_source(self, weighted_chain_graph):
        """Test Rust Dijkstra with multiple sources."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        result = shortest_path(
            weighted_chain_graph, sources=[0, 4], weight_column="weight", backend="rust"
        )

        # Sources should have distance 0
        source_results = result[result["vertex"].isin([0, 4])]
        assert all(source_results["distance"] == 0.0)

    def test_dijkstra_rust_unreachable_vertices(self, disconnected_weighted_graph):
        """Test Rust Dijkstra with unreachable vertices."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        result = shortest_path(
            disconnected_weighted_graph,
            sources=0,
            weight_column="weight",
            backend="rust",
            include_unreachable=True,
        )

        # Should include all vertices
        assert len(result) == 5

        # Reachable vertices have finite distances
        reachable = result[result["vertex"].isin([0, 1])]
        assert list(reachable.sort_values("vertex")["distance"]) == [0.0, 2.5]

        # Unreachable vertices have infinite distances
        unreachable = result[result["vertex"].isin([2, 3, 4])]
        assert all(unreachable["distance"] == np.inf)

    def test_dijkstra_rust_negative_weights_error(self):
        """Test that Rust Dijkstra raises error on negative weights."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Create graph with negative weight
        vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2]})
        edge_data = pd.DataFrame({"src": [0, 1], "dst": [1, 2], "weight": [1.0, -2.0]})
        neg_graph = GraphFrame(
            vertices=ParquetFrame(vertex_data),
            edges=ParquetFrame(edge_data),
            metadata={"directed": True},
        )

        # Should raise ValueError for negative weights
        with pytest.raises(ValueError, match="non-negative edge weights"):
            shortest_path(neg_graph, sources=0, weight_column="weight", backend="rust")

    def test_dijkstra_rust_single_vertex(self):
        """Test Rust Dijkstra on single vertex graph."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Single vertex with no edges
        vertex_data = pd.DataFrame({"vertex_id": [0]})
        edge_data = pd.DataFrame({"src": [], "dst": [], "weight": []})
        single_graph = GraphFrame(
            vertices=ParquetFrame(vertex_data),
            edges=ParquetFrame(edge_data),
            metadata={"directed": True},
        )

        result = shortest_path(
            single_graph, sources=0, weight_column="weight", backend="rust"
        )

        # Single source vertex should have distance 0
        assert len(result) == 1
        assert result.iloc[0]["distance"] == 0.0
