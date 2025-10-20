"""Tests for Rust graph algorithm bindings.

This module tests the PyO3 bindings for CSR/CSC adjacency structures and
BFS/DFS traversal algorithms implemented in Rust.
"""

import numpy as np
import pytest

try:
    from parquetframe import _rustic

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    _rustic = None


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestRustAvailability:
    """Test Rust backend availability and version detection."""

    def test_rust_available(self):
        """Test that Rust backend can be imported and detected."""
        assert _rustic is not None
        assert _rustic.rust_available() is True

    def test_rust_version(self):
        """Test that Rust backend version can be retrieved."""
        version = _rustic.rust_version()
        assert isinstance(version, str)
        assert len(version) > 0


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestCSRBindings:
    """Test CSR adjacency structure bindings."""

    def test_build_csr_simple(self):
        """Test building a simple CSR graph."""
        # Simple graph: 0->1, 0->2, 1->2
        src = np.array([0, 0, 1], dtype=np.int32)
        dst = np.array([1, 2, 2], dtype=np.int32)
        num_vertices = 3

        indptr, indices, weights = _rustic.build_csr_rust(src, dst, num_vertices, None)

        assert isinstance(indptr, np.ndarray)
        assert isinstance(indices, np.ndarray)
        assert weights is None

        # indptr should be [0, 2, 3, 3] for 3 vertices
        assert len(indptr) == num_vertices + 1
        assert indptr[0] == 0
        assert indptr[-1] == len(src)

    def test_build_csr_with_weights(self):
        """Test building a CSR graph with edge weights."""
        src = np.array([0, 1], dtype=np.int32)
        dst = np.array([1, 0], dtype=np.int32)
        weights = np.array([1.5, 2.5], dtype=np.float64)
        num_vertices = 2

        indptr, indices, out_weights = _rustic.build_csr_rust(
            src, dst, num_vertices, weights
        )

        assert out_weights is not None
        assert isinstance(out_weights, np.ndarray)
        assert len(out_weights) == len(weights)

    def test_build_csr_empty(self):
        """Test building an empty CSR graph."""
        src = np.array([], dtype=np.int32)
        dst = np.array([], dtype=np.int32)
        num_vertices = 5

        indptr, indices, weights = _rustic.build_csr_rust(src, dst, num_vertices, None)

        assert len(indptr) == num_vertices + 1
        assert len(indices) == 0
        assert weights is None

    def test_build_csr_invalid_vertex(self):
        """Test that invalid vertex IDs raise an error."""
        src = np.array([0, 5], dtype=np.int32)  # 5 is out of range
        dst = np.array([1, 2], dtype=np.int32)
        num_vertices = 3

        with pytest.raises(ValueError, match="vertex"):
            _rustic.build_csr_rust(src, dst, num_vertices, None)

    def test_build_csr_length_mismatch(self):
        """Test that mismatched src/dst lengths raise an error."""
        src = np.array([0, 1], dtype=np.int32)
        dst = np.array([1], dtype=np.int32)
        num_vertices = 3

        with pytest.raises(ValueError, match="length"):
            _rustic.build_csr_rust(src, dst, num_vertices, None)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestCSCBindings:
    """Test CSC adjacency structure bindings."""

    def test_build_csc_simple(self):
        """Test building a simple CSC graph."""
        # Simple graph: 0->1, 0->2, 1->2
        src = np.array([0, 0, 1], dtype=np.int32)
        dst = np.array([1, 2, 2], dtype=np.int32)
        num_vertices = 3

        indptr, indices, weights = _rustic.build_csc_rust(src, dst, num_vertices, None)

        assert isinstance(indptr, np.ndarray)
        assert isinstance(indices, np.ndarray)
        assert weights is None

        # CSC groups by destination
        assert len(indptr) == num_vertices + 1

    def test_build_csc_with_weights(self):
        """Test building a CSC graph with edge weights."""
        src = np.array([0, 1], dtype=np.int32)
        dst = np.array([1, 0], dtype=np.int32)
        weights = np.array([1.5, 2.5], dtype=np.float64)
        num_vertices = 2

        indptr, indices, out_weights = _rustic.build_csc_rust(
            src, dst, num_vertices, weights
        )

        assert out_weights is not None
        assert len(out_weights) == len(weights)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestBFSBindings:
    """Test BFS traversal bindings."""

    def test_bfs_simple(self):
        """Test BFS on a simple graph."""
        # Graph: 0->1, 0->2, 1->3
        src = np.array([0, 0, 1], dtype=np.int32)
        dst = np.array([1, 2, 3], dtype=np.int32)
        num_vertices = 4

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)
        sources = np.array([0], dtype=np.int32)

        distances, predecessors = _rustic.bfs_rust(
            indptr, indices, num_vertices, sources, None
        )

        assert isinstance(distances, np.ndarray)
        assert isinstance(predecessors, np.ndarray)
        assert len(distances) == num_vertices
        assert len(predecessors) == num_vertices

        # Check distances from source 0
        assert distances[0] == 0  # Source
        assert distances[1] == 1  # Direct neighbor
        assert distances[2] == 1  # Direct neighbor
        assert distances[3] == 2  # Two hops

    def test_bfs_multi_source(self):
        """Test parallel BFS with multiple sources."""
        src = np.array([0, 1, 2], dtype=np.int32)
        dst = np.array([1, 2, 3], dtype=np.int32)
        num_vertices = 4

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)
        sources = np.array([0, 2], dtype=np.int32)  # Multiple sources

        distances, predecessors = _rustic.bfs_rust(
            indptr, indices, num_vertices, sources, None
        )

        assert distances[0] == 0
        assert distances[2] == 0
        # Both are sources

    def test_bfs_max_depth(self):
        """Test BFS with maximum depth constraint."""
        # Linear graph: 0->1->2->3
        src = np.array([0, 1, 2], dtype=np.int32)
        dst = np.array([1, 2, 3], dtype=np.int32)
        num_vertices = 4

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)
        sources = np.array([0], dtype=np.int32)
        max_depth = 2

        distances, predecessors = _rustic.bfs_rust(
            indptr, indices, num_vertices, sources, max_depth
        )

        # Should reach up to distance 2, but not 3
        assert distances[0] == 0
        assert distances[1] == 1
        assert distances[2] == 2
        assert distances[3] == -1  # Unreachable within depth limit

    def test_bfs_disconnected(self):
        """Test BFS on a disconnected graph."""
        # Two components: 0->1 and 2->3
        src = np.array([0, 2], dtype=np.int32)
        dst = np.array([1, 3], dtype=np.int32)
        num_vertices = 4

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)
        sources = np.array([0], dtype=np.int32)

        distances, predecessors = _rustic.bfs_rust(
            indptr, indices, num_vertices, sources, None
        )

        # Vertices 2 and 3 should be unreachable
        assert distances[0] == 0
        assert distances[1] == 1
        assert distances[2] == -1
        assert distances[3] == -1


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestDFSBindings:
    """Test DFS traversal bindings."""

    def test_dfs_simple(self):
        """Test DFS on a simple graph."""
        # Graph: 0->1, 0->2, 1->3
        src = np.array([0, 0, 1], dtype=np.int32)
        dst = np.array([1, 2, 3], dtype=np.int32)
        num_vertices = 4

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)

        visited = _rustic.dfs_rust(indptr, indices, num_vertices, 0, None)

        assert isinstance(visited, np.ndarray)
        assert len(visited) == num_vertices  # All vertices reachable
        assert visited[0] == 0  # First visited is source

    def test_dfs_with_cycle(self):
        """Test DFS on a graph with a cycle."""
        # Graph with cycle: 0->1->2->0
        src = np.array([0, 1, 2], dtype=np.int32)
        dst = np.array([1, 2, 0], dtype=np.int32)
        num_vertices = 3

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)

        visited = _rustic.dfs_rust(indptr, indices, num_vertices, 0, None)

        # Should visit all vertices exactly once despite cycle
        assert len(visited) == num_vertices
        assert len(set(visited)) == num_vertices

    def test_dfs_max_depth(self):
        """Test DFS with maximum depth constraint."""
        # Linear graph: 0->1->2->3
        src = np.array([0, 1, 2], dtype=np.int32)
        dst = np.array([1, 2, 3], dtype=np.int32)
        num_vertices = 4

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)
        max_depth = 2

        visited = _rustic.dfs_rust(indptr, indices, num_vertices, 0, max_depth)

        # Should visit 0, 1, 2 but not 3 (depth 3)
        assert len(visited) == 3
        assert 3 not in visited

    def test_dfs_disconnected(self):
        """Test DFS on a disconnected graph."""
        # Two components: 0->1 and 2->3
        src = np.array([0, 2], dtype=np.int32)
        dst = np.array([1, 3], dtype=np.int32)
        num_vertices = 4

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)

        visited = _rustic.dfs_rust(indptr, indices, num_vertices, 0, None)

        # Should only visit component containing 0
        assert len(visited) == 2
        assert 0 in visited
        assert 1 in visited
        assert 2 not in visited
        assert 3 not in visited


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust backend not available")
class TestRustPerformance:
    """Basic performance sanity checks for Rust bindings."""

    def test_large_graph_csr(self):
        """Test CSR construction on a larger graph."""
        # Create a graph with 1000 vertices and ~5000 edges
        num_vertices = 1000
        num_edges = 5000
        np.random.seed(42)
        src = np.random.randint(0, num_vertices, size=num_edges, dtype=np.int32)
        dst = np.random.randint(0, num_vertices, size=num_edges, dtype=np.int32)

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)

        assert len(indptr) == num_vertices + 1
        assert len(indices) == num_edges

    def test_large_graph_bfs(self):
        """Test BFS on a larger graph."""
        num_vertices = 1000
        num_edges = 5000
        np.random.seed(42)
        src = np.random.randint(0, num_vertices, size=num_edges, dtype=np.int32)
        dst = np.random.randint(0, num_vertices, size=num_edges, dtype=np.int32)

        indptr, indices, _ = _rustic.build_csr_rust(src, dst, num_vertices, None)
        sources = np.array([0], dtype=np.int32)

        distances, predecessors = _rustic.bfs_rust(
            indptr, indices, num_vertices, sources, None
        )

        assert len(distances) == num_vertices
        assert len(predecessors) == num_vertices
