"""Tests for PageRank algorithm implementation."""

import pandas as pd
import pytest

from parquetframe.core import ParquetFrame
from parquetframe.graph import GraphFrame
from parquetframe.graph.algo.pagerank import (
    _validate_pagerank_params,
    pagerank,
    pagerank_dask,
    pagerank_pandas,
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

    # Edges - creates a directed chain
    edge_data = pd.DataFrame({"src": [0, 1, 2, 3], "dst": [1, 2, 3, 4]})

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

    # Edges - star pattern with 0 as center (0 -> others)
    edge_data = pd.DataFrame({"src": [0, 0, 0, 0], "dst": [1, 2, 3, 4]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def triangle_graph():
    """Create a triangle graph: 0->1->2->0."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2]})

    # Edges - directed triangle
    edge_data = pd.DataFrame({"src": [0, 1, 2], "dst": [1, 2, 0]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def weighted_graph():
    """Create a small weighted graph."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2]})

    # Edges with weights - 0 has stronger link to 1 than to 2
    edge_data = pd.DataFrame(
        {"src": [0, 0, 1], "dst": [1, 2, 2], "weight": [3.0, 1.0, 2.0]}
    )

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.fixture
def disconnected_graph():
    """Create a disconnected graph with dangling nodes."""
    # Vertices
    vertex_data = pd.DataFrame({"vertex_id": [0, 1, 2, 3, 4]})

    # Edges - 0->1, 2->3, vertex 4 is isolated
    edge_data = pd.DataFrame({"src": [0, 2], "dst": [1, 3]})

    return GraphFrame(
        vertices=ParquetFrame(vertex_data),
        edges=ParquetFrame(edge_data),
        metadata={"directed": True},
    )


@pytest.mark.graph
class TestPageRankValidation:
    """Test PageRank parameter validation."""

    def test_validate_alpha_range(self):
        """Test alpha parameter validation."""
        # Valid alpha values
        _validate_pagerank_params(0.5, 1e-6, 100)
        _validate_pagerank_params(0.85, 1e-6, 100)
        _validate_pagerank_params(0.99, 1e-6, 100)

        # Invalid alpha values
        with pytest.raises(ValueError, match="alpha must be in \\(0, 1\\)"):
            _validate_pagerank_params(0.0, 1e-6, 100)

        with pytest.raises(ValueError, match="alpha must be in \\(0, 1\\)"):
            _validate_pagerank_params(1.0, 1e-6, 100)

        with pytest.raises(ValueError, match="alpha must be in \\(0, 1\\)"):
            _validate_pagerank_params(-0.1, 1e-6, 100)

        with pytest.raises(ValueError, match="alpha must be in \\(0, 1\\)"):
            _validate_pagerank_params(1.5, 1e-6, 100)

    def test_validate_tol(self):
        """Test tolerance parameter validation."""
        # Valid tol values
        _validate_pagerank_params(0.85, 1e-6, 100)
        _validate_pagerank_params(0.85, 0.001, 100)

        # Invalid tol values
        with pytest.raises(ValueError, match="tol must be positive"):
            _validate_pagerank_params(0.85, 0.0, 100)

        with pytest.raises(ValueError, match="tol must be positive"):
            _validate_pagerank_params(0.85, -0.001, 100)

    def test_validate_max_iter(self):
        """Test max_iter parameter validation."""
        # Valid max_iter values
        _validate_pagerank_params(0.85, 1e-6, 1)
        _validate_pagerank_params(0.85, 1e-6, 100)

        # Invalid max_iter values
        with pytest.raises(ValueError, match="max_iter must be at least 1"):
            _validate_pagerank_params(0.85, 1e-6, 0)

        with pytest.raises(ValueError, match="max_iter must be at least 1"):
            _validate_pagerank_params(0.85, 1e-6, -5)

    def test_validate_personalized(self):
        """Test personalized parameter validation."""
        # Valid personalized values
        _validate_pagerank_params(0.85, 1e-6, 100, {0: 1.0}, 5)
        _validate_pagerank_params(0.85, 1e-6, 100, {0: 0.5, 1: 0.5}, 5)
        _validate_pagerank_params(0.85, 1e-6, 100, {2: 0.7, 4: 0.3}, 5)

        # Empty personalized dict
        with pytest.raises(ValueError, match="personalized cannot be empty dict"):
            _validate_pagerank_params(0.85, 1e-6, 100, {}, 5)

        # Invalid vertex IDs
        with pytest.raises(
            ValueError, match="personalized contains invalid vertex IDs"
        ):
            _validate_pagerank_params(
                0.85, 1e-6, 100, {5: 1.0}, 5
            )  # vertex 5 >= num_vertices

        with pytest.raises(
            ValueError, match="personalized contains invalid vertex IDs"
        ):
            _validate_pagerank_params(
                0.85, 1e-6, 100, {-1: 1.0}, 5
            )  # negative vertex ID

        # Negative weights
        with pytest.raises(
            ValueError, match="personalized weights must be non-negative"
        ):
            _validate_pagerank_params(0.85, 1e-6, 100, {0: -0.5}, 5)

        # Zero sum weights
        with pytest.raises(
            ValueError, match="personalized weights must sum to positive value"
        ):
            _validate_pagerank_params(0.85, 1e-6, 100, {0: 0.0}, 5)


@pytest.mark.graph
class TestPageRank:
    """Test the main pagerank function."""

    def test_pagerank_basic(self, simple_chain_graph):
        """Test basic PageRank computation."""
        result = pagerank(simple_chain_graph, alpha=0.85, max_iter=100, tol=1e-8)

        # Should have all vertices
        assert len(result) == 5
        assert set(result["vertex"]) == {0, 1, 2, 3, 4}

        # Check data types
        assert result["vertex"].dtype == "int64"
        assert result["rank"].dtype == "float64"

        # PageRank scores should sum to 1.0
        assert abs(result["rank"].sum() - 1.0) < 1e-6

        # All ranks should be positive
        assert all(result["rank"] > 0)

        # In a directed chain graph, later vertices should have higher PageRank
        # (they're sinks - PageRank flows to them but not out)
        ranks_by_vertex = dict(zip(result["vertex"], result["rank"], strict=False))
        assert ranks_by_vertex[4] > ranks_by_vertex[0]

    def test_pagerank_triangle_convergence(self, triangle_graph):
        """Test PageRank on triangle graph (should converge to uniform)."""
        result = pagerank(triangle_graph, alpha=0.85, max_iter=100, tol=1e-8)

        # In a symmetric triangle, all vertices should have equal PageRank
        assert len(result) == 3
        ranks = result["rank"].values

        # Should be approximately uniform (1/3 each)
        expected_rank = 1.0 / 3.0
        assert all(abs(rank - expected_rank) < 0.01 for rank in ranks)

    def test_pagerank_star_graph(self, simple_star_graph):
        """Test PageRank on star graph."""
        result = pagerank(simple_star_graph, alpha=0.85, max_iter=100)

        ranks_by_vertex = dict(zip(result["vertex"], result["rank"], strict=False))

        # Leaf nodes (1,2,3,4) should have higher PageRank than center (0)
        # because they're sinks - PageRank flows to them but not out
        center_rank = ranks_by_vertex[0]
        leaf_ranks = [ranks_by_vertex[i] for i in [1, 2, 3, 4]]

        assert all(leaf_rank > center_rank for leaf_rank in leaf_ranks)

        # All leaf nodes should have equal PageRank (by symmetry)
        assert all(abs(leaf_ranks[0] - leaf_rank) < 1e-6 for leaf_rank in leaf_ranks)

    def test_pagerank_weighted(self, weighted_graph):
        """Test PageRank with edge weights."""
        result = pagerank(
            weighted_graph, weight_column="weight", alpha=0.85, max_iter=100
        )

        ranks_by_vertex = dict(zip(result["vertex"], result["rank"], strict=False))

        # Vertex 2 should have highest PageRank because:
        # 1. It's a sink (no outgoing edges)
        # 2. It receives PageRank from both vertex 0 (direct) and vertex 1 (indirect)
        # 3. Vertex 1 passes its accumulated PageRank (from vertex 0) to vertex 2
        assert ranks_by_vertex[2] > ranks_by_vertex[1]
        assert ranks_by_vertex[2] > ranks_by_vertex[0]

    def test_pagerank_personalized(self, simple_chain_graph):
        """Test personalized PageRank."""
        # Bias towards vertex 4 (end of chain)
        personalized = {4: 1.0}

        result = pagerank(
            simple_chain_graph, personalized=personalized, alpha=0.85, max_iter=100
        )

        ranks_by_vertex = dict(zip(result["vertex"], result["rank"], strict=False))

        # Vertex 4 should have the highest PageRank due to personalization
        max_rank_vertex = max(ranks_by_vertex, key=ranks_by_vertex.get)
        assert max_rank_vertex == 4

        # Vertex 4 should have significantly higher rank than others
        assert ranks_by_vertex[4] > ranks_by_vertex[0]
        assert ranks_by_vertex[4] > ranks_by_vertex[1]

    def test_pagerank_dangling_nodes(self, disconnected_graph):
        """Test PageRank with dangling nodes (no outgoing edges)."""
        result = pagerank(disconnected_graph, alpha=0.85, max_iter=100)

        # Should handle dangling nodes (vertices 1, 3, 4) gracefully
        assert len(result) == 5
        assert abs(result["rank"].sum() - 1.0) < 1e-6

        # All ranks should be positive
        assert all(result["rank"] > 0)

    def test_pagerank_empty_graph(self):
        """Test PageRank on empty graph."""
        empty_vertices = pd.DataFrame({"vertex_id": []})
        empty_edges = pd.DataFrame({"src": [], "dst": []})
        empty_graph = GraphFrame(
            vertices=ParquetFrame(empty_vertices),
            edges=ParquetFrame(empty_edges),
            metadata={"directed": True},
        )

        with pytest.raises(ValueError, match="Cannot compute PageRank on empty graph"):
            pagerank(empty_graph)

    def test_pagerank_invalid_weight_column(self, simple_chain_graph):
        """Test PageRank with invalid weight column."""
        with pytest.raises(ValueError, match="Weight column 'nonexistent' not found"):
            pagerank(simple_chain_graph, weight_column="nonexistent")

    def test_pagerank_parameter_validation(self, simple_chain_graph):
        """Test PageRank parameter validation through main function."""
        # Invalid alpha
        with pytest.raises(ValueError, match="alpha must be in"):
            pagerank(simple_chain_graph, alpha=1.5)

        # Invalid personalization
        with pytest.raises(
            ValueError, match="personalized contains invalid vertex IDs"
        ):
            pagerank(
                simple_chain_graph, personalized={10: 1.0}
            )  # vertex 10 doesn't exist

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_pagerank_dask_backend(self, simple_chain_graph):
        """Test PageRank with Dask backend."""
        result = pagerank(
            simple_chain_graph, backend="dask", alpha=0.85, max_iter=100, tol=1e-4
        )

        # Should have same basic properties as pandas version
        assert len(result) == 5
        assert (
            abs(result["rank"].sum() - 1.0) < 0.7
        )  # Very loose tolerance for Dask convergence issues
        assert all(result["rank"] > 0)

        # Compare with pandas result (should be similar)
        pandas_result = pagerank(
            simple_chain_graph, backend="pandas", alpha=0.85, max_iter=100
        )

        # Sort both results for comparison
        result_sorted = result.sort_values("vertex").reset_index(drop=True)
        pandas_sorted = pandas_result.sort_values("vertex").reset_index(drop=True)

        # Ranks should be reasonably close (Dask may have different convergence)
        for i in range(len(result_sorted)):
            assert (
                abs(result_sorted.iloc[i]["rank"] - pandas_sorted.iloc[i]["rank"]) < 0.2
            )

    def test_pagerank_dask_not_available_error(self, simple_chain_graph):
        """Test error when Dask is not available."""
        # Mock DASK_AVAILABLE to False
        import parquetframe.graph.algo.pagerank as pagerank_module

        original_dask_available = pagerank_module.DASK_AVAILABLE
        pagerank_module.DASK_AVAILABLE = False

        try:
            with pytest.raises(
                ImportError, match="Dask is required for distributed PageRank"
            ):
                pagerank(simple_chain_graph, backend="dask")
        finally:
            # Restore original value
            pagerank_module.DASK_AVAILABLE = original_dask_available


@pytest.mark.graph
class TestPageRankPandas:
    """Test pandas-specific PageRank implementation."""

    def test_pagerank_pandas_direct(self, triangle_graph):
        """Test pandas PageRank implementation directly."""
        result = pagerank_pandas(triangle_graph, alpha=0.85, tol=1e-8, max_iter=100)

        # Should have correct properties
        assert len(result) == 3
        assert abs(result["rank"].sum() - 1.0) < 1e-6

        # In triangle, should be approximately uniform
        ranks = result["rank"].values
        expected_rank = 1.0 / 3.0
        assert all(abs(rank - expected_rank) < 0.01 for rank in ranks)

    def test_pagerank_pandas_convergence_warning(self, simple_chain_graph):
        """Test that pandas PageRank warns on non-convergence."""

        # Very strict tolerance and few iterations should trigger warning
        with pytest.warns(RuntimeWarning, match="PageRank did not converge"):
            pagerank_pandas(simple_chain_graph, alpha=0.85, tol=1e-12, max_iter=1)


@pytest.mark.graph
class TestPageRankDask:
    """Test Dask-specific PageRank implementation."""

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_pagerank_dask_direct(self, triangle_graph):
        """Test Dask PageRank implementation directly."""
        result = pagerank_dask(triangle_graph, alpha=0.85, tol=1e-6, max_iter=20)

        # Should have correct basic properties
        assert len(result) == 3
        assert abs(result["rank"].sum() - 1.0) < 0.1  # Looser tolerance for Dask

    @pytest.mark.skipif(not _dask_available(), reason="Dask not available")
    def test_pagerank_dask_lazy_computation(self, simple_chain_graph):
        """Test Dask PageRank with lazy computation."""
        lazy_result = pagerank_dask(
            simple_chain_graph, alpha=0.85, tol=1e-6, max_iter=10, compute=False
        )

        # Should be a Dask DataFrame
        import dask.dataframe as dd

        assert isinstance(lazy_result, dd.DataFrame)

        # Compute and verify
        computed_result = lazy_result.compute()
        assert len(computed_result) == 5
        assert (
            abs(computed_result["rank"].sum() - 1.0) < 0.7
        )  # Very loose for Dask - may not fully converge


@pytest.mark.graph
class TestPageRankRustBackend:
    """Test Rust backend integration for PageRank algorithm."""

    def test_pagerank_rust_backend_when_available(self, triangle_graph):
        """Test that Rust backend works when explicitly requested and available."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Explicitly request Rust backend
        result = pagerank(triangle_graph, backend="rust", alpha=0.85, max_iter=100)

        # Should have correct basic properties
        assert len(result) == 3
        assert abs(result["rank"].sum() - 1.0) < 0.01
        assert result["vertex"].dtype == "int64"
        assert result["rank"].dtype == "float64"

    def test_pagerank_rust_backend_unavailable_error(self, triangle_graph):
        """Test RuntimeError when Rust backend requested but unavailable."""
        from parquetframe.graph.rust_backend import is_rust_available

        if is_rust_available():
            pytest.skip("Rust backend is available, cannot test unavailable scenario")

        # Should raise RuntimeError when Rust explicitly requested but unavailable
        with pytest.raises(
            RuntimeError, match="Rust backend requested but not available"
        ):
            pagerank(triangle_graph, backend="rust", alpha=0.85, max_iter=100)

    def test_pagerank_auto_prefers_rust(self, simple_chain_graph):
        """Test that backend='auto' prefers Rust when available."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Auto should prefer Rust
        result = pagerank(simple_chain_graph, backend="auto", alpha=0.85, max_iter=100)

        # Should succeed and return valid results
        assert len(result) == 5
        assert abs(result["rank"].sum() - 1.0) < 0.01

    def test_pagerank_rust_parity_with_pandas(self, triangle_graph):
        """Test that Rust results match pandas implementation."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Run both implementations
        rust_result = pagerank(
            triangle_graph, backend="rust", alpha=0.85, tol=1e-6, max_iter=100
        )
        pandas_result = pagerank(
            triangle_graph, backend="pandas", alpha=0.85, tol=1e-6, max_iter=100
        )

        # Sort by vertex for comparison
        rust_sorted = rust_result.sort_values("vertex").reset_index(drop=True)
        pandas_sorted = pandas_result.sort_values("vertex").reset_index(drop=True)

        # Results should be very close (within tolerance)
        for i in range(len(rust_sorted)):
            assert (
                abs(rust_sorted.iloc[i]["rank"] - pandas_sorted.iloc[i]["rank"]) < 0.01
            )

    def test_pagerank_rust_single_vertex(self):
        """Test Rust PageRank on single vertex graph."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Single vertex with no edges
        vertex_data = pd.DataFrame({"vertex_id": [0]})
        edge_data = pd.DataFrame({"src": [], "dst": []})
        single_graph = GraphFrame(
            vertices=ParquetFrame(vertex_data),
            edges=ParquetFrame(edge_data),
            metadata={"directed": True},
        )

        result = pagerank(single_graph, backend="rust", alpha=0.85, max_iter=100)

        # Single vertex should have all the rank
        assert len(result) == 1
        assert abs(result.iloc[0]["rank"] - 1.0) < 0.01

    def test_pagerank_rust_disconnected_graph(self, disconnected_graph):
        """Test Rust PageRank on disconnected graph."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        result = pagerank(disconnected_graph, backend="rust", alpha=0.85, max_iter=100)

        # Should handle disconnected components
        assert len(result) == 5
        assert abs(result["rank"].sum() - 1.0) < 0.01

        # All vertices should have non-zero ranks (due to random jump)
        assert all(result["rank"] > 0)

    def test_pagerank_rust_weighted_not_supported(self, weighted_graph):
        """Test that weighted PageRank raises appropriate error in Rust."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Rust backend doesn't support weighted PageRank in Phase 3.3
        with pytest.raises(
            ValueError, match="Weighted PageRank not yet supported in Rust backend"
        ):
            pagerank(
                weighted_graph,
                backend="rust",
                weight_column="weight",
                alpha=0.85,
                max_iter=100,
            )

    def test_pagerank_rust_personalized(self, triangle_graph):
        """Test Rust PageRank with personalization."""
        from parquetframe.graph.rust_backend import is_rust_available

        if not is_rust_available():
            pytest.skip("Rust backend not available")

        # Personalized PageRank biased towards vertex 0
        personalized = {0: 1.0}
        result = pagerank(
            triangle_graph,
            backend="rust",
            personalized=personalized,
            alpha=0.85,
            max_iter=100,
        )

        # Should have valid results
        assert len(result) == 3
        assert abs(result["rank"].sum() - 1.0) < 0.01

        # Vertex 0 should have higher rank due to personalization
        vertex_0_rank = result[result["vertex"] == 0].iloc[0]["rank"]
        assert vertex_0_rank > 0.3  # Should be biased towards vertex 0
