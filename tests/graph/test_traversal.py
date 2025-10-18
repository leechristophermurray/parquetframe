"""Tests for graph traversal algorithms (BFS and DFS)."""

import pandas as pd
import pytest

from parquetframe.core import ParquetFrame
from parquetframe.graph import GraphFrame
from parquetframe.graph.algo.traversal import bfs
from parquetframe.graph.data import EdgeSet, VertexSet


@pytest.fixture
def simple_chain_graph():
    """Create a simple chain graph: 0->1->2->3->4."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})
    vertices = VertexSet(
        data=ParquetFrame(vertex_data), vertex_type="node", properties={}
    )

    # Edges
    edge_data = pd.DataFrame({"src": [0, 1, 2, 3], "dst": [1, 2, 3, 4]})
    edges = EdgeSet(data=ParquetFrame(edge_data), edge_type="edge", properties={})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def simple_star_graph():
    """Create a star graph: center (0) connected to 1,2,3,4."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})

    # Edges - star pattern with 0 as center
    edge_data = pd.DataFrame({"src": [0, 0, 0, 0], "dst": [1, 2, 3, 4]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def disconnected_graph():
    """Create a disconnected graph: 0->1, 2->3, 4 (isolated)."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})

    # Edges - two components plus isolated vertex
    edge_data = pd.DataFrame({"src": [0, 2], "dst": [1, 3]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.mark.graph
class TestBFS:
    """Test BFS (Breadth-First Search) implementation."""

    def test_bfs_single_source_chain(self, simple_chain_graph):
        """Test BFS from single source on chain graph."""
        result = bfs(simple_chain_graph, sources=0)

        # Verify all vertices reachable with correct distances
        assert len(result) == 5
        assert list(result["vertex"]) == [0, 1, 2, 3, 4]
        assert list(result["distance"]) == [0, 1, 2, 3, 4]
        assert list(result["layer"]) == [0, 1, 2, 3, 4]

        # Verify predecessor chain
        assert pd.isna(result.loc[result["vertex"] == 0, "predecessor"].iloc[0])
        assert result.loc[result["vertex"] == 1, "predecessor"].iloc[0] == 0
        assert result.loc[result["vertex"] == 2, "predecessor"].iloc[0] == 1
        assert result.loc[result["vertex"] == 3, "predecessor"].iloc[0] == 2
        assert result.loc[result["vertex"] == 4, "predecessor"].iloc[0] == 3

    def test_bfs_single_source_star(self, simple_star_graph):
        """Test BFS from center of star graph."""
        result = bfs(simple_star_graph, sources=0)

        # All non-center vertices should be at distance 1
        center_result = result[result["vertex"] == 0]
        assert len(center_result) == 1
        assert center_result["distance"].iloc[0] == 0

        leaf_results = result[result["vertex"].isin([1, 2, 3, 4])]
        assert len(leaf_results) == 4
        assert all(leaf_results["distance"] == 1)
        assert all(leaf_results["predecessor"] == 0)

    def test_bfs_multi_source(self, simple_chain_graph):
        """Test BFS with multiple sources."""
        result = bfs(simple_chain_graph, sources=[0, 4])

        # Sources should have distance 0
        source_results = result[result["vertex"].isin([0, 4])]
        assert all(source_results["distance"] == 0)
        assert all(pd.isna(source_results["predecessor"]))

        # Middle vertices should be reached from nearest source
        middle = result[result["vertex"] == 2].iloc[0]
        assert middle["distance"] == 2  # Either from 0 or 4

    def test_bfs_max_depth(self, simple_chain_graph):
        """Test BFS with depth limit."""
        result = bfs(simple_chain_graph, sources=0, max_depth=2)

        # Should only reach vertices 0, 1, 2 (distances 0, 1, 2)
        assert len(result) == 3
        assert list(result["vertex"]) == [0, 1, 2]
        assert list(result["distance"]) == [0, 1, 2]

    def test_bfs_disconnected_components(self, disconnected_graph):
        """Test BFS on disconnected graph."""
        result = bfs(disconnected_graph, sources=0)

        # Should only reach component containing vertex 0 (vertices 0,1)
        assert len(result) == 2
        reachable_vertices = set(result["vertex"])
        assert reachable_vertices == {0, 1}

        # Check distances
        assert result.loc[result["vertex"] == 0, "distance"].iloc[0] == 0
        assert result.loc[result["vertex"] == 1, "distance"].iloc[0] == 1

    def test_bfs_include_unreachable(self, disconnected_graph):
        """Test BFS with include_unreachable=True."""
        result = bfs(disconnected_graph, sources=0, include_unreachable=True)

        # Should include all vertices
        assert len(result) == 5

        # Reachable vertices have normal distances
        reachable = result[result["vertex"].isin([0, 1])]
        assert list(reachable["distance"]) == [0, 1]

        # Unreachable vertices have distance -1 (our sentinel value)
        unreachable = result[result["vertex"].isin([2, 3, 4])]
        assert all(unreachable["distance"] == -1)
        assert all(pd.isna(unreachable["predecessor"]))

    def test_bfs_undirected_graph(self, simple_chain_graph):
        """Test BFS on undirected version of chain graph."""
        # Create undirected metadata
        simple_chain_graph.metadata["directed"] = False

        result = bfs(simple_chain_graph, sources=2, directed=False)

        # From vertex 2, should reach all vertices in undirected chain
        assert len(result) == 5

        # Distances from vertex 2: 0->2, 1->1, 2->0, 3->1, 4->2
        expected_distances = {0: 2, 1: 1, 2: 0, 3: 1, 4: 2}
        for _, row in result.iterrows():
            vertex = row["vertex"]
            distance = row["distance"]
            assert distance == expected_distances[vertex]

    def test_bfs_empty_graph(self):
        """Test BFS on empty graph."""
        empty_vertices = pd.DataFrame({"vertex_id": []})
        empty_edges = pd.DataFrame({"src": [], "dst": []})
        empty_graph = GraphFrame(
            vertices=ParquetFrame(empty_vertices),
            edges=ParquetFrame(empty_edges),
            metadata={"directed": True},
        )

        with pytest.raises(ValueError, match="Cannot perform BFS on empty graph"):
            bfs(empty_graph)

    def test_bfs_invalid_source(self, simple_chain_graph):
        """Test BFS with invalid source vertex."""
        with pytest.raises(ValueError, match="Source vertex 10 out of range"):
            bfs(simple_chain_graph, sources=10)

        with pytest.raises(ValueError, match="Source vertex -1 out of range"):
            bfs(simple_chain_graph, sources=-1)

    def test_bfs_invalid_max_depth(self, simple_chain_graph):
        """Test BFS with invalid max_depth."""
        with pytest.raises(ValueError, match="max_depth must be non-negative"):
            bfs(simple_chain_graph, sources=0, max_depth=-1)

    def test_bfs_dask_not_implemented(self, simple_chain_graph):
        """Test that Dask backend raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Dask backend for BFS not yet implemented"
        ):
            bfs(simple_chain_graph, sources=0, backend="dask")

    def test_bfs_result_dtypes(self, simple_chain_graph):
        """Test that BFS result has correct column dtypes."""
        result = bfs(simple_chain_graph, sources=0)

        assert result["vertex"].dtype == "int64"
        assert result["distance"].dtype == "int64"
        assert result["predecessor"].dtype == "Int64"  # Nullable int
        assert result["layer"].dtype == "int64"

    def test_bfs_auto_source_selection(self, simple_chain_graph):
        """Test BFS with sources=None (auto-selection)."""
        result = bfs(simple_chain_graph, sources=None)

        # Should default to vertex 0
        source_row = result[result["vertex"] == 0].iloc[0]
        assert source_row["distance"] == 0
        assert pd.isna(source_row["predecessor"])
