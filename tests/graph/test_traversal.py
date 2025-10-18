"""Tests for graph traversal algorithms (BFS and DFS)."""

import pandas as pd
import pytest

from parquetframe.core import ParquetFrame
from parquetframe.graph import GraphFrame
from parquetframe.graph.algo.traversal import bfs, dfs
from parquetframe.graph.data import EdgeSet, VertexSet


def _dask_available():
    """Check if Dask is available for testing."""
    try:
        import dask.dataframe  # noqa: F401

        return True
    except ImportError:
        return False


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

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_bfs_dask_backend_chain(self, simple_chain_graph):
        """Test Dask BFS on chain graph."""
        # Force Dask backend
        result = bfs(simple_chain_graph, sources=0, backend="dask")

        # Should match pandas results
        pandas_result = bfs(simple_chain_graph, sources=0, backend="pandas")

        # Compare results (sort for consistent comparison)
        result_sorted = result.sort_values("vertex").reset_index(drop=True)
        pandas_sorted = pandas_result.sort_values("vertex").reset_index(drop=True)

        assert len(result_sorted) == len(pandas_sorted)
        assert list(result_sorted["vertex"]) == list(pandas_sorted["vertex"])
        assert list(result_sorted["distance"]) == list(pandas_sorted["distance"])
        assert list(result_sorted["layer"]) == list(pandas_sorted["layer"])

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_bfs_dask_backend_star(self, simple_star_graph):
        """Test Dask BFS on star graph."""
        result = bfs(simple_star_graph, sources=0, backend="dask", npartitions=2)

        # All non-center vertices should be at distance 1
        center_result = result[result["vertex"] == 0]
        assert len(center_result) == 1
        assert center_result["distance"].iloc[0] == 0

        leaf_results = result[result["vertex"].isin([1, 2, 3, 4])]
        assert len(leaf_results) == 4
        assert all(leaf_results["distance"] == 1)

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_bfs_dask_lazy_computation(self, simple_chain_graph):
        """Test Dask BFS with lazy computation."""
        # Get lazy result
        lazy_result = bfs(simple_chain_graph, sources=0, backend="dask", compute=False)

        # Should be a Dask DataFrame
        import dask.dataframe as dd

        assert isinstance(lazy_result, dd.DataFrame)

        # Compute and verify
        computed_result = lazy_result.compute()
        assert len(computed_result) == 5
        assert list(computed_result.sort_values("vertex")["distance"]) == [
            0,
            1,
            2,
            3,
            4,
        ]

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_bfs_dask_multi_source(self, simple_chain_graph):
        """Test Dask BFS with multiple sources."""
        result = bfs(simple_chain_graph, sources=[0, 4], backend="dask")

        # Sources should have distance 0
        source_results = result[result["vertex"].isin([0, 4])]
        assert all(source_results["distance"] == 0)

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_bfs_dask_max_depth(self, simple_chain_graph):
        """Test Dask BFS with depth limit."""
        result = bfs(simple_chain_graph, sources=0, max_depth=2, backend="dask")

        # Should only reach vertices 0, 1, 2
        assert len(result) == 3
        assert set(result["vertex"]) == {0, 1, 2}
        assert max(result["distance"]) == 2

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_bfs_dask_undirected(self, simple_chain_graph):
        """Test Dask BFS on undirected graph."""
        result = bfs(simple_chain_graph, sources=2, directed=False, backend="dask")

        # Should reach all vertices in undirected chain
        assert len(result) == 5

        # Distances from vertex 2: 0->2, 1->1, 2->0, 3->1, 4->2
        expected_distances = {0: 2, 1: 1, 2: 0, 3: 1, 4: 2}
        for _, row in result.iterrows():
            vertex = row["vertex"]
            distance = row["distance"]
            assert distance == expected_distances[vertex]

    def test_bfs_dask_not_available_error(self, simple_chain_graph):
        """Test error when Dask is not available."""
        # Mock DASK_AVAILABLE to False
        import parquetframe.graph.algo.traversal as traversal_module

        original_dask_available = traversal_module.DASK_AVAILABLE
        traversal_module.DASK_AVAILABLE = False

        try:
            with pytest.raises(
                ImportError, match="Dask is required for distributed BFS"
            ):
                bfs(simple_chain_graph, sources=0, backend="dask")
        finally:
            # Restore original value
            traversal_module.DASK_AVAILABLE = original_dask_available

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


@pytest.mark.graph
class TestDFS:
    """Test DFS (Depth-First Search) implementation."""

    def test_dfs_single_source_chain(self, simple_chain_graph):
        """Test DFS from single source on chain graph."""
        result = dfs(simple_chain_graph, sources=0)

        # All vertices should be reachable
        assert len(result) == 5
        assert set(result["vertex"]) == {0, 1, 2, 3, 4}

        # Source should have no predecessor
        source_row = result[result["vertex"] == 0].iloc[0]
        assert pd.isna(source_row["predecessor"])
        assert source_row["component_id"] == 0

        # Discovery times should be in DFS order (0, 1, 2, 3, 4 for chain)
        result_sorted = result.sort_values("discovery_time")
        expected_order = [0, 1, 2, 3, 4]  # DFS goes deep first
        assert list(result_sorted["vertex"]) == expected_order

        # Finish times should be in reverse DFS order (4, 3, 2, 1, 0)
        result_sorted_finish = result.sort_values("finish_time")
        expected_finish_order = [4, 3, 2, 1, 0]  # Deepest finishes first
        assert list(result_sorted_finish["vertex"]) == expected_finish_order

    def test_dfs_single_source_star(self, simple_star_graph):
        """Test DFS from center of star graph."""
        result = dfs(simple_star_graph, sources=0)

        # All vertices should be reachable
        assert len(result) == 5
        assert set(result["vertex"]) == {0, 1, 2, 3, 4}

        # Center should have discovery time 0
        center_row = result[result["vertex"] == 0].iloc[0]
        assert center_row["discovery_time"] == 0
        assert pd.isna(center_row["predecessor"])

        # All leaf vertices should have center as predecessor
        leaf_results = result[result["vertex"].isin([1, 2, 3, 4])]
        assert all(leaf_results["predecessor"] == 0)

        # Center should finish last (highest finish time)
        assert center_row["finish_time"] == result["finish_time"].max()

    def test_dfs_forest_mode(self, disconnected_graph):
        """Test DFS forest traversal on disconnected graph."""
        result = dfs(disconnected_graph, forest=True)

        # Should visit all vertices
        assert len(result) == 5
        assert set(result["vertex"]) == {0, 1, 2, 3, 4}

        # Should have multiple components
        components = set(result["component_id"])
        assert len(components) >= 2  # At least 2 components

        # Vertices 0,1 should be in one component
        comp_0_1 = result[result["vertex"].isin([0, 1])]["component_id"]
        assert len(set(comp_0_1)) == 1  # Same component

        # Vertices 2,3 should be in another component
        comp_2_3 = result[result["vertex"].isin([2, 3])]["component_id"]
        assert len(set(comp_2_3)) == 1  # Same component

        # Vertex 4 should be in its own component (isolated)
        comp_4 = result[result["vertex"] == 4]["component_id"].iloc[0]
        assert comp_4 not in set(comp_0_1) and comp_4 not in set(comp_2_3)

    def test_dfs_max_depth_limiting(self, simple_chain_graph):
        """Test DFS with depth limit."""
        result = dfs(simple_chain_graph, sources=0, max_depth=2)

        # Should only reach vertices at depth <= 2 from source 0
        # Chain: 0->1->2 (depths 0,1,2), so vertices 3,4 unreachable
        assert len(result) == 3
        assert set(result["vertex"]) == {0, 1, 2}

        # Discovery times should still be in DFS order
        result_sorted = result.sort_values("discovery_time")
        assert list(result_sorted["vertex"]) == [0, 1, 2]

    def test_dfs_multi_source(self, disconnected_graph):
        """Test DFS with multiple sources on disconnected graph."""
        result = dfs(disconnected_graph, sources=[0, 2])

        # Should visit vertices from both components
        assert len(result) == 4  # 0,1 from first source, 2,3 from second source
        assert set(result["vertex"]) == {0, 1, 2, 3}

        # Should have two components (one from each source)
        components = set(result["component_id"])
        assert len(components) == 2

        # Sources should have no predecessor
        source_results = result[result["vertex"].isin([0, 2])]
        assert all(pd.isna(source_results["predecessor"]))

        # Components should be separate
        comp_0_vertices = result[result["component_id"] == 0]["vertex"]
        comp_1_vertices = result[result["component_id"] == 1]["vertex"]
        assert set(comp_0_vertices).isdisjoint(set(comp_1_vertices))

    def test_dfs_undirected_graph(self, simple_chain_graph):
        """Test DFS on undirected version of chain graph."""
        # Make graph undirected
        simple_chain_graph.metadata["directed"] = False

        result = dfs(simple_chain_graph, sources=2, directed=False)

        # From vertex 2, should reach all vertices in undirected chain
        assert len(result) == 5
        assert set(result["vertex"]) == {0, 1, 2, 3, 4}

        # Source vertex 2 should have discovery time 0
        source_row = result[result["vertex"] == 2].iloc[0]
        assert source_row["discovery_time"] == 0
        assert pd.isna(source_row["predecessor"])

    def test_dfs_discovery_finish_times(self, simple_chain_graph):
        """Test that DFS discovery and finish times are consistent."""
        result = dfs(simple_chain_graph, sources=0)

        # For each vertex, discovery time should be < finish time
        for _, row in result.iterrows():
            assert row["discovery_time"] < row["finish_time"]

        # Discovery times should be unique and start from 0
        discovery_times = sorted(result["discovery_time"])
        assert discovery_times == list(range(len(discovery_times)))

        # Finish times should be unique and continue from discovery times
        finish_times = sorted(result["finish_time"])
        num_vertices = len(result)
        expected_finish_times = list(range(num_vertices, 2 * num_vertices))
        assert finish_times == expected_finish_times

        # All times should be unique across discovery and finish
        all_times = result["discovery_time"].tolist() + result["finish_time"].tolist()
        assert len(set(all_times)) == len(all_times)  # No duplicates

    def test_dfs_empty_graph(self):
        """Test DFS on empty graph."""
        empty_vertices = pd.DataFrame({"vertex_id": []})
        empty_edges = pd.DataFrame({"src": [], "dst": []})
        empty_graph = GraphFrame(
            vertices=ParquetFrame(empty_vertices),
            edges=ParquetFrame(empty_edges),
            metadata={"directed": True},
        )

        with pytest.raises(ValueError, match="Cannot perform DFS on empty graph"):
            dfs(empty_graph)

    def test_dfs_invalid_source(self, simple_chain_graph):
        """Test DFS with invalid source vertex."""
        with pytest.raises(ValueError, match="Source vertex 10 out of range"):
            dfs(simple_chain_graph, sources=10)

        with pytest.raises(ValueError, match="Source vertex -1 out of range"):
            dfs(simple_chain_graph, sources=-1)

    def test_dfs_invalid_max_depth(self, simple_chain_graph):
        """Test DFS with invalid max_depth."""
        with pytest.raises(ValueError, match="max_depth must be non-negative"):
            dfs(simple_chain_graph, sources=0, max_depth=-1)

    def test_dfs_dask_not_implemented(self, simple_chain_graph):
        """Test that Dask backend raises informative NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Dask backend for DFS not implemented"
        ):
            dfs(simple_chain_graph, sources=0, backend="dask")

    def test_dfs_result_dtypes(self, simple_chain_graph):
        """Test that DFS result has correct column dtypes."""
        result = dfs(simple_chain_graph, sources=0)

        assert result["vertex"].dtype == "int64"
        assert result["predecessor"].dtype == "Int64"  # Nullable int
        assert result["discovery_time"].dtype == "int64"
        assert result["finish_time"].dtype == "int64"
        assert result["component_id"].dtype == "int64"

    def test_dfs_component_consistency(self, simple_chain_graph):
        """Test that vertices in same DFS tree have same component ID."""
        result = dfs(simple_chain_graph, sources=0)

        # All vertices should be in the same component (connected chain)
        components = set(result["component_id"])
        assert len(components) == 1
        assert list(components)[0] == 0  # First component

    def test_dfs_auto_source_selection(self, simple_chain_graph):
        """Test DFS with sources=None (auto-selection)."""
        result = dfs(simple_chain_graph, sources=None)

        # Should default to vertex 0
        source_row = result[result["vertex"] == 0].iloc[0]
        assert source_row["discovery_time"] == 0
        assert pd.isna(source_row["predecessor"])
