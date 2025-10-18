"""Tests for connected components algorithms (union-find and label propagation)."""

import pandas as pd
import pytest

from parquetframe.core import ParquetFrame
from parquetframe.graph import GraphFrame
from parquetframe.graph.algo.components import (
    connected_components,
    label_propagation_components,
    union_find_components,
)


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

    # Edges - creates one connected component
    edge_data = pd.DataFrame({"src": [0, 1, 2, 3], "dst": [1, 2, 3, 4]})

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


@pytest.fixture
def undirected_triangle_graph():
    """Create an undirected triangle: 0-1, 1-2, 2-0."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2]})

    # Edges - triangle (bidirectional)
    edge_data = pd.DataFrame({"src": [0, 1, 1, 2, 2, 0], "dst": [1, 0, 2, 1, 0, 2]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": False},
    )


@pytest.fixture
def directed_weakly_connected_graph():
    """Create a directed graph that is weakly connected: 0->1, 2->1, 3->2."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3]})

    # Edges - weakly connected (all reachable if we ignore direction)
    edge_data = pd.DataFrame({"src": [0, 2, 3], "dst": [1, 1, 2]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def single_vertex_graph():
    """Create a graph with a single isolated vertex."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0]})

    # No edges
    edge_data = pd.DataFrame({"src": [], "dst": []})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.mark.graph
class TestConnectedComponents:
    """Test the main connected_components function."""

    def test_connected_components_single_component(self, simple_chain_graph):
        """Test connected components on a single connected component."""
        result = connected_components(simple_chain_graph)

        # Should have all vertices in one component
        assert len(result) == 5
        assert len(result["component_id"].unique()) == 1

        # All vertices should be in component 0
        assert all(result["component_id"] == 0)

        # Check data types
        assert result["vertex"].dtype == "int64"
        assert result["component_id"].dtype == "int64"

    def test_connected_components_multiple_components(self, disconnected_graph):
        """Test connected components on disconnected graph."""
        result = connected_components(disconnected_graph)

        # Should have all vertices
        assert len(result) == 5
        assert set(result["vertex"]) == {0, 1, 2, 3, 4}

        # Should have 3 components: {0,1}, {2,3}, {4}
        assert len(result["component_id"].unique()) == 3

        # Check component assignments
        component_map = dict(
            zip(result["vertex"], result["component_id"], strict=False)
        )

        # Vertices 0 and 1 should be in same component
        assert component_map[0] == component_map[1]

        # Vertices 2 and 3 should be in same component
        assert component_map[2] == component_map[3]

        # Vertex 4 should be in its own component
        assert component_map[4] not in [component_map[0], component_map[2]]

    def test_connected_components_undirected(self, undirected_triangle_graph):
        """Test connected components on undirected graph."""
        result = connected_components(undirected_triangle_graph, directed=False)

        # Should have all vertices in one component
        assert len(result) == 3
        assert len(result["component_id"].unique()) == 1

    def test_connected_components_weakly_connected(
        self, directed_weakly_connected_graph
    ):
        """Test weakly connected components on directed graph."""
        result = connected_components(directed_weakly_connected_graph, method="weak")

        # All vertices should be weakly connected
        assert len(result) == 4
        assert len(result["component_id"].unique()) == 1

    def test_connected_components_single_vertex(self, single_vertex_graph):
        """Test connected components on single vertex graph."""
        result = connected_components(single_vertex_graph)

        # Should have one vertex in one component
        assert len(result) == 1
        assert result.iloc[0]["vertex"] == 0
        assert result.iloc[0]["component_id"] == 0

    def test_connected_components_empty_graph(self):
        """Test connected components on empty graph."""
        empty_vertices = pd.DataFrame({"vertex_id": []})
        empty_edges = pd.DataFrame({"src": [], "dst": []})
        empty_graph = GraphFrame(
            vertices=ParquetFrame(empty_vertices),
            edges=ParquetFrame(empty_edges),
            metadata={"directed": True},
        )

        with pytest.raises(
            ValueError, match="Cannot find connected components on empty graph"
        ):
            connected_components(empty_graph)

    def test_connected_components_strong_not_implemented(self, simple_chain_graph):
        """Test that strong components raise not implemented error."""
        with pytest.raises(
            ValueError, match="Strongly connected components not implemented"
        ):
            connected_components(simple_chain_graph, method="strong")

    def test_connected_components_invalid_max_iter(self, simple_chain_graph):
        """Test that invalid max_iter raises error."""
        with pytest.raises(ValueError, match="max_iter must be positive"):
            connected_components(simple_chain_graph, max_iter=0)

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_connected_components_dask_backend(self, disconnected_graph):
        """Test connected components with Dask backend."""
        result = connected_components(disconnected_graph, backend="dask")

        # Should match pandas results
        pandas_result = connected_components(disconnected_graph, backend="pandas")

        # Both should have same number of components
        assert len(result["component_id"].unique()) == len(
            pandas_result["component_id"].unique()
        )
        assert len(result) == len(pandas_result)

    def test_connected_components_dask_not_available_error(self, simple_chain_graph):
        """Test error when Dask is not available."""
        # Mock DASK_AVAILABLE to False
        import parquetframe.graph.algo.components as components_module

        original_dask_available = components_module.DASK_AVAILABLE
        components_module.DASK_AVAILABLE = False

        try:
            with pytest.raises(
                ImportError,
                match="Dask is required for distributed connected components",
            ):
                connected_components(simple_chain_graph, backend="dask")
        finally:
            # Restore original value
            components_module.DASK_AVAILABLE = original_dask_available


@pytest.mark.graph
class TestUnionFindComponents:
    """Test union-find connected components algorithm."""

    def test_union_find_single_component(self, simple_chain_graph):
        """Test union-find on single connected component."""
        result = union_find_components(simple_chain_graph)

        # Should have all vertices in one component
        assert len(result) == 5
        assert len(result["component_id"].unique()) == 1

        # Check data types
        assert result["vertex"].dtype == "int64"
        assert result["component_id"].dtype == "int64"

    def test_union_find_multiple_components(self, disconnected_graph):
        """Test union-find on disconnected graph."""
        result = union_find_components(disconnected_graph)

        # Should have 3 components
        assert len(result) == 5
        assert len(result["component_id"].unique()) == 3

        # Verify component assignments
        component_map = dict(
            zip(result["vertex"], result["component_id"], strict=False)
        )

        # Connected vertices should have same component ID
        assert component_map[0] == component_map[1]
        assert component_map[2] == component_map[3]

        # Isolated vertex should have different component ID
        isolated_component = component_map[4]
        assert isolated_component != component_map[0]
        assert isolated_component != component_map[2]

    def test_union_find_undirected(self, undirected_triangle_graph):
        """Test union-find on undirected graph."""
        result = union_find_components(undirected_triangle_graph, directed=False)

        # All vertices should be in one component
        assert len(result) == 3
        assert len(result["component_id"].unique()) == 1

    def test_union_find_directed_weak_components(self, directed_weakly_connected_graph):
        """Test union-find for weakly connected components."""
        result = union_find_components(directed_weakly_connected_graph, directed=True)

        # Should find one weakly connected component
        assert len(result) == 4
        assert len(result["component_id"].unique()) == 1


@pytest.mark.graph
class TestLabelPropagationComponents:
    """Test label propagation connected components algorithm."""

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_label_propagation_single_component(self, simple_chain_graph):
        """Test label propagation on single connected component."""
        result = label_propagation_components(simple_chain_graph)

        # Should have all vertices in one component
        assert len(result) == 5
        assert len(result["component_id"].unique()) == 1

        # Check data types
        assert result["vertex"].dtype == "int64"
        assert result["component_id"].dtype == "int64"

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_label_propagation_multiple_components(self, disconnected_graph):
        """Test label propagation on disconnected graph."""
        result = label_propagation_components(disconnected_graph)

        # Should have 3 components
        assert len(result) == 5
        assert len(result["component_id"].unique()) == 3

        # Verify basic structure
        component_map = dict(
            zip(result["vertex"], result["component_id"], strict=False)
        )

        # Connected vertices should have same component
        assert component_map[0] == component_map[1]
        assert component_map[2] == component_map[3]

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_label_propagation_max_iter(self, simple_chain_graph):
        """Test label propagation with limited iterations."""
        result = label_propagation_components(simple_chain_graph, max_iter=5)

        # Should still find correct components even with few iterations
        assert len(result) == 5
        assert len(result["component_id"].unique()) == 1

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_label_propagation_lazy_computation(self, simple_chain_graph):
        """Test label propagation with lazy computation."""
        lazy_result = label_propagation_components(simple_chain_graph, compute=False)

        # Should be a Dask DataFrame
        import dask.dataframe as dd

        assert isinstance(lazy_result, dd.DataFrame)

        # Compute and verify
        computed_result = lazy_result.compute()
        assert len(computed_result) == 5
        assert len(computed_result["component_id"].unique()) == 1
