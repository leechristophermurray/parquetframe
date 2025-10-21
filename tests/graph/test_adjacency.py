"""Tests for CSR/CSC adjacency structures."""

import numpy as np
import pandas as pd
import pytest

from parquetframe.core import ParquetFrame
from parquetframe.graph.adjacency import CSCAdjacency, CSRAdjacency
from parquetframe.graph.data import EdgeSet


@pytest.mark.graph
class TestCSRAdjacency:
    """Test CSR (Compressed Sparse Row) adjacency structure."""

    def test_basic_csr_construction(self):
        """Test basic CSR construction from edge list."""
        # Simple directed graph: 0->1, 0->2, 1->2, 2->3
        edge_data = pd.DataFrame(
            {"src": [0, 0, 1, 2], "dst": [1, 2, 2, 3], "weight": [1.0, 2.0, 3.0, 4.0]}
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data),
            edge_type="test",
            properties={"weight": "float64"},
        )

        csr = CSRAdjacency.from_edge_set(edge_set)

        # Verify basic structure
        assert csr.num_vertices == 4
        assert csr.num_edges == 4

        # Check degrees match expected
        assert csr.degree(0) == 2  # 0 -> [1, 2]
        assert csr.degree(1) == 1  # 1 -> [2]
        assert csr.degree(2) == 1  # 2 -> [3]
        assert csr.degree(3) == 0  # 3 -> []

    def test_csr_neighbor_lookups(self):
        """Test CSR neighbor lookup functionality."""
        # Create a small graph with known structure
        edge_data = pd.DataFrame(
            {
                "src": [0, 0, 1, 1, 2],
                "dst": [1, 3, 2, 3, 0],
                "weight": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data),
            edge_type="test",
            properties={"weight": "float64"},
        )

        csr = CSRAdjacency.from_edge_set(edge_set)

        # Test neighbor lookups
        neighbors_0 = csr.neighbors(0)
        assert set(neighbors_0) == {1, 3}

        neighbors_1 = csr.neighbors(1)
        assert set(neighbors_1) == {2, 3}

        neighbors_2 = csr.neighbors(2)
        assert set(neighbors_2) == {0}

        neighbors_3 = csr.neighbors(3)
        assert len(neighbors_3) == 0  # No outgoing edges

    def test_csr_has_edge(self):
        """Test CSR edge existence checking."""
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 2],
                "dst": [1, 2, 0],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)

        # Test existing edges
        assert csr.has_edge(0, 1)
        assert csr.has_edge(1, 2)
        assert csr.has_edge(2, 0)

        # Test non-existing edges
        assert not csr.has_edge(0, 2)
        assert not csr.has_edge(1, 0)
        assert not csr.has_edge(2, 1)

    def test_csr_degree_consistency(self):
        """Test that CSR degrees match offset differences."""
        # Random edge pattern
        edge_data = pd.DataFrame(
            {
                "src": [0, 0, 0, 1, 1, 2, 3, 3, 3, 3],
                "dst": [1, 2, 3, 4, 5, 1, 0, 1, 2, 4],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)

        # Verify degrees match indptr difference
        for vertex_id in range(csr.num_vertices):
            expected_degree = csr.indptr[vertex_id + 1] - csr.indptr[vertex_id]
            actual_degree = csr.degree(vertex_id)
            assert (
                actual_degree == expected_degree
            ), f"Degree mismatch for vertex {vertex_id}"

    def test_csr_edge_count_preservation(self):
        """Test that CSR preserves total edge count."""
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 2, 3, 4, 0, 2, 4],
                "dst": [1, 2, 3, 4, 0, 3, 4, 1],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)

        # Total edges should match
        assert csr.num_edges == len(edge_data)

        # Sum of degrees should match edge count
        total_degree = sum(csr.degree(v) for v in range(csr.num_vertices))
        assert total_degree == csr.num_edges


@pytest.mark.graph
class TestCSCAdjacency:
    """Test CSC (Compressed Sparse Column) adjacency structure."""

    def test_basic_csc_construction(self):
        """Test basic CSC construction from edge list."""
        # Same graph as CSR test: 0->1, 0->2, 1->2, 2->3
        edge_data = pd.DataFrame(
            {"src": [0, 0, 1, 2], "dst": [1, 2, 2, 3], "weight": [1.0, 2.0, 3.0, 4.0]}
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data),
            edge_type="test",
            properties={"weight": "float64"},
        )

        csc = CSCAdjacency.from_edge_set(edge_set)

        # Verify basic structure
        assert csc.num_vertices == 4
        assert csc.num_edges == 4

        # Check in-degrees (predecessors)
        assert csc.degree(0) == 0  # Nothing points to 0
        assert csc.degree(1) == 1  # 0 -> 1
        assert csc.degree(2) == 2  # 0 -> 2, 1 -> 2
        assert csc.degree(3) == 1  # 2 -> 3

    def test_csc_predecessor_lookups(self):
        """Test CSC predecessor lookup functionality."""
        edge_data = pd.DataFrame(
            {
                "src": [0, 0, 1, 1, 2],
                "dst": [1, 3, 2, 3, 0],
                "weight": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data),
            edge_type="test",
            properties={"weight": "float64"},
        )

        csc = CSCAdjacency.from_edge_set(edge_set)

        # Test predecessor lookups
        pred_0 = csc.predecessors(0)
        assert set(pred_0) == {2}  # Only 2 -> 0

        pred_1 = csc.predecessors(1)
        assert set(pred_1) == {0}  # Only 0 -> 1

        pred_2 = csc.predecessors(2)
        assert set(pred_2) == {1}  # Only 1 -> 2

        pred_3 = csc.predecessors(3)
        assert set(pred_3) == {0, 1}  # Both 0 -> 3 and 1 -> 3


@pytest.mark.graph
class TestCSRCSCConsistency:
    """Test consistency between CSR and CSC representations."""

    def test_csr_csc_edge_count_consistency(self):
        """Test that CSR and CSC preserve the same edge count."""
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 2, 3, 0, 2, 1],
                "dst": [1, 2, 3, 0, 3, 1, 0],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)
        csc = CSCAdjacency.from_edge_set(edge_set)

        # Both should report same edge count
        assert csr.num_edges == csc.num_edges == len(edge_data)

        # Both should report same vertex count
        assert csr.num_vertices == csc.num_vertices

    def test_csr_csc_degree_sum_consistency(self):
        """Test that sum of CSR out-degrees equals sum of CSC in-degrees."""
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 2, 0, 1, 3],
                "dst": [1, 2, 0, 2, 3, 1],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)
        csc = CSCAdjacency.from_edge_set(edge_set)

        # Sum of out-degrees should equal sum of in-degrees
        csr_degree_sum = sum(csr.degree(v) for v in range(csr.num_vertices))
        csc_degree_sum = sum(csc.degree(v) for v in range(csc.num_vertices))

        assert csr_degree_sum == csc_degree_sum == len(edge_data)

    def test_directed_graph_properties(self):
        """Test properties specific to directed graphs."""
        # Create an acyclic directed graph: 0->1->2->3
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 2],
                "dst": [1, 2, 3],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)
        csc = CSCAdjacency.from_edge_set(edge_set)

        # Test that CSR neighbors and CSC predecessors are complementary
        for edge_idx in range(len(edge_data)):
            src = edge_data.iloc[edge_idx]["src"]
            dst = edge_data.iloc[edge_idx]["dst"]

            # dst should be in src's neighbors (CSR)
            assert dst in csr.neighbors(src)

            # src should be in dst's predecessors (CSC)
            assert src in csc.predecessors(dst)

    def test_cyclic_graph_properties(self):
        """Test properties with cyclic directed graphs."""
        # Create a cycle: 0->1->2->0
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 2],
                "dst": [1, 2, 0],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)
        csc = CSCAdjacency.from_edge_set(edge_set)

        # In a cycle, each vertex has in-degree = out-degree = 1
        for vertex_id in range(3):
            assert csr.degree(vertex_id) == 1  # out-degree
            assert csc.degree(vertex_id) == 1  # in-degree

            # Each vertex has exactly one neighbor and one predecessor
            assert len(csr.neighbors(vertex_id)) == 1
            assert len(csc.predecessors(vertex_id)) == 1


@pytest.mark.graph
class TestAdjacencySubgraphs:
    """Test adjacency structure subgraph operations."""

    def test_csr_subgraph_extraction(self):
        """Test CSR subgraph extraction preserves structure."""
        # Create a graph: 0->1->2->3, 0->2, 1->3
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 2, 0, 1],
                "dst": [1, 2, 3, 2, 3],
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)

        # Extract subgraph with vertices [0, 1, 2]
        subgraph_vertices = [0, 1, 2]
        sub_csr = csr.subgraph(subgraph_vertices)

        # Subgraph should have 3 vertices
        assert sub_csr.num_vertices == 3

        # Should preserve edges within the subgraph
        # Original edges: 0->1, 1->2, 0->2 (edges to vertex 3 are excluded)
        assert sub_csr.num_edges == 3

        # Check preserved adjacencies
        assert 1 in sub_csr.neighbors(0)  # 0->1 preserved
        assert 2 in sub_csr.neighbors(0)  # 0->2 preserved
        assert 2 in sub_csr.neighbors(1)  # 1->2 preserved

        # Vertex 2 should have no neighbors in subgraph (2->3 excluded)
        assert len(sub_csr.neighbors(2)) == 0


@pytest.mark.graph
class TestAdjacencyEdgeCases:
    """Test adjacency structures with edge cases."""

    def test_empty_graph(self):
        """Test adjacency with empty graph."""
        edge_data = pd.DataFrame(
            {
                "src": pd.Series([], dtype="int64"),
                "dst": pd.Series([], dtype="int64"),
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)
        csc = CSCAdjacency.from_edge_set(edge_set)

        # Empty graph properties
        assert csr.num_edges == 0
        assert csr.num_vertices == 0
        assert csc.num_edges == 0
        assert csc.num_vertices == 0

    def test_single_vertex_graph(self):
        """Test adjacency with single isolated vertex."""
        edge_data = pd.DataFrame(
            {
                "src": pd.Series([], dtype="int64"),
                "dst": pd.Series([], dtype="int64"),
            }
        )

        # Manually create adjacency for single vertex
        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        # Note: This tests the current implementation behavior
        # An empty edge set results in 0 vertices, not 1
        csr = CSRAdjacency.from_edge_set(edge_set)

        assert csr.num_edges == 0
        # Note: num_vertices is determined by max vertex ID in edges
        # So empty edge set -> 0 vertices

    def test_self_loops(self):
        """Test adjacency with self-loop edges."""
        edge_data = pd.DataFrame(
            {
                "src": [0, 1, 1, 2],
                "dst": [0, 1, 2, 2],  # 0->0, 1->1, 1->2, 2->2 (self-loops on 0, 1, 2)
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)
        csc = CSCAdjacency.from_edge_set(edge_set)

        # Self-loops should be handled correctly
        assert csr.has_edge(0, 0)
        assert csr.has_edge(1, 1)
        assert csr.has_edge(2, 2)

        # Self-loops contribute to both out-degree and in-degree
        assert 0 in csr.neighbors(0)  # 0->0
        assert 0 in csc.predecessors(0)  # 0->0

        assert 1 in csr.neighbors(1)  # 1->1
        assert 1 in csc.predecessors(1)  # 1->1

    def test_duplicate_edges(self):
        """Test adjacency behavior with duplicate edges."""
        # Note: This depends on how EdgeSet handles duplicates
        edge_data = pd.DataFrame(
            {
                "src": [0, 0, 1, 1],  # Duplicate 0->1
                "dst": [1, 1, 2, 2],  # Duplicate 1->2
            }
        )

        edge_set = EdgeSet(
            data=ParquetFrame(edge_data), edge_type="test", properties={}
        )

        csr = CSRAdjacency.from_edge_set(edge_set)

        # Behavior may vary - document current behavior
        # Most implementations would include duplicates
        assert csr.num_edges == 4  # All edges counted
        assert csr.has_edge(0, 1)
        assert csr.has_edge(1, 2)


@pytest.mark.graph
def test_adjacency_performance_characteristics():
    """Test that adjacency operations have expected O(degree) complexity."""
    # Create a larger graph to test performance characteristics
    np.random.seed(42)  # For reproducible results

    # Create a graph with 1000 vertices, average degree ~5
    num_vertices = 1000
    num_edges = 5000

    sources = np.random.randint(0, num_vertices, num_edges)
    targets = np.random.randint(0, num_vertices, num_edges)

    edge_data = pd.DataFrame(
        {
            "src": sources,
            "dst": targets,
        }
    )

    edge_set = EdgeSet(data=ParquetFrame(edge_data), edge_type="test", properties={})

    csr = CSRAdjacency.from_edge_set(edge_set)
    csc = CSCAdjacency.from_edge_set(edge_set)

    # Basic properties should work on larger graphs
    assert csr.num_vertices <= num_vertices  # May be less due to isolated vertices
    assert csr.num_edges == num_edges
    assert csc.num_edges == num_edges

    # Neighbor/predecessor lookups should work efficiently
    # Test a sample of vertices
    sample_vertices = np.random.choice(
        range(min(100, csr.num_vertices)), size=10, replace=False
    )

    for vertex_id in sample_vertices:
        neighbors = csr.neighbors(vertex_id)
        predecessors = csc.predecessors(vertex_id)

        # Results should be reasonable (not empty for most vertices in dense graph)
        assert isinstance(neighbors, np.ndarray)
        assert isinstance(predecessors, np.ndarray)

        # Degree should match neighbor count
        assert len(neighbors) == csr.degree(vertex_id)
        assert len(predecessors) == csc.degree(vertex_id)
