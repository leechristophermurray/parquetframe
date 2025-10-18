"""Tests for GraphAr reader functionality."""

import pytest

from parquetframe.graph import read_graph
from parquetframe.graph.io.graphar import GraphArError

from ..fixtures.graphar_samples import (
    build_empty_graphar,
    build_invalid_graphar,
    build_large_graphar,
    build_minimal_graphar,
)


@pytest.mark.graph
def test_loads_minimal_graph_successfully(tmp_path):
    """Test that GraphArReader can load a minimal well-formed graph."""
    sample = build_minimal_graphar(tmp_path)

    # Load the graph
    graph = read_graph(sample["graph_path"])

    # Verify basic properties
    assert graph.num_vertices == sample["expected_vertices"]
    assert graph.num_edges == sample["expected_edges"]
    assert graph.is_directed == sample["metadata"]["directed"]
    assert graph.metadata["name"] == sample["metadata"]["name"]

    # Verify data integrity
    assert len(graph.vertices) == 4
    assert len(graph.edges) == 5

    # Check vertex properties
    vertex_cols = set(graph.vertices.columns)
    expected_vertex_cols = {"id", "name", "age"}
    assert expected_vertex_cols.issubset(vertex_cols)

    # Check edge properties
    edge_cols = set(graph.edges.columns)
    expected_edge_cols = {"src", "dst", "weight"}
    assert expected_edge_cols.issubset(edge_cols)


@pytest.mark.graph
def test_loads_empty_graph_successfully(tmp_path):
    """Test that GraphArReader can handle empty graphs."""
    sample = build_empty_graphar(tmp_path)

    # Load empty graph
    graph = read_graph(sample["graph_path"])

    # Verify empty graph properties
    assert graph.num_vertices == 0
    assert graph.num_edges == 0
    assert graph.metadata["name"] == sample["metadata"]["name"]

    # Should have empty but valid dataframes
    assert len(graph.vertices) == 0
    assert len(graph.edges) == 0
    assert "vertex_id" in graph.vertices.columns or "id" in graph.vertices.columns
    assert "src" in graph.edges.columns
    assert "dst" in graph.edges.columns


@pytest.mark.graph
def test_validation_fails_on_missing_metadata(tmp_path):
    """Test validation fails when metadata file is missing."""
    invalid_path = build_invalid_graphar(tmp_path, "missing_metadata")

    with pytest.raises(GraphArError, match="Required metadata file not found"):
        read_graph(invalid_path)


@pytest.mark.graph
def test_validation_fails_on_invalid_yaml(tmp_path):
    """Test validation fails when YAML is malformed."""
    invalid_path = build_invalid_graphar(tmp_path, "invalid_yaml")

    with pytest.raises(GraphArError, match="Invalid YAML in metadata file"):
        read_graph(invalid_path)


@pytest.mark.graph
def test_validation_fails_on_missing_required_fields(tmp_path):
    """Test validation fails when required metadata fields are missing."""
    invalid_path = build_invalid_graphar(tmp_path, "missing_required_fields")

    with pytest.raises(GraphArError, match="Missing required metadata fields"):
        read_graph(invalid_path)


@pytest.mark.graph
def test_validation_fails_on_wrong_field_types(tmp_path):
    """Test validation fails when metadata fields have wrong types."""
    invalid_path = build_invalid_graphar(tmp_path, "wrong_field_types")

    with pytest.raises(GraphArError, match="must be a"):
        read_graph(invalid_path)


@pytest.mark.graph
def test_dtypes_and_index_columns_are_correct(tmp_path):
    """Test that loaded data has correct data types and expected columns."""
    sample = build_minimal_graphar(tmp_path)
    graph = read_graph(sample["graph_path"])

    # Get actual dataframes (not lazy)
    vertices_df = (
        graph.vertices._df
        if not graph.vertices.islazy
        else graph.vertices._df.compute()
    )
    edges_df = graph.edges._df if not graph.edges.islazy else graph.edges._df.compute()

    # Check vertex data types
    assert vertices_df["id"].dtype.name in ["int64", "Int64"]
    assert vertices_df["name"].dtype.name in ["object", "string"]
    assert vertices_df["age"].dtype.name in ["int32", "int64", "Int32", "Int64"]

    # Check edge data types
    assert edges_df["src"].dtype.name in ["int64", "Int64"]
    assert edges_df["dst"].dtype.name in ["int64", "Int64"]
    assert edges_df["weight"].dtype.name in ["float64", "Float64"]

    # Verify data content matches expectations
    vertex_names = set(vertices_df["name"].tolist())
    expected_names = set(sample["vertex_data"]["name"].tolist())
    assert vertex_names == expected_names


@pytest.mark.graph
def test_schema_validation_can_be_disabled(tmp_path):
    """Test that schema validation can be disabled for performance."""
    sample = build_minimal_graphar(tmp_path)

    # Should work with validation disabled
    graph = read_graph(sample["graph_path"], validate_schema=False)

    assert graph.num_vertices == sample["expected_vertices"]
    assert graph.num_edges == sample["expected_edges"]


@pytest.mark.graph
def test_backend_auto_switch_respected_on_size_threshold(tmp_path, monkeypatch):
    """Test that backend selection respects size thresholds."""
    # Create small graph - should use pandas
    small_sample = build_minimal_graphar(tmp_path)
    small_graph = read_graph(
        small_sample["graph_path"], threshold_mb=1000
    )  # High threshold
    assert not small_graph.vertices.islazy, "Small graph should use pandas backend"

    # Force Dask backend
    dask_graph = read_graph(small_sample["graph_path"], islazy=True)
    assert dask_graph.vertices.islazy, "Should use Dask when explicitly requested"

    # Force pandas backend
    pandas_graph = read_graph(small_sample["graph_path"], islazy=False)
    assert (
        not pandas_graph.vertices.islazy
    ), "Should use pandas when explicitly requested"


@pytest.mark.graph
@pytest.mark.dask
def test_large_graph_auto_selects_dask(tmp_path):
    """Test that large graphs automatically select Dask backend."""
    # Create larger graph that should trigger Dask selection
    large_sample = build_large_graphar(tmp_path, num_vertices=100)

    # Use very low threshold to force Dask selection
    graph = read_graph(
        large_sample["graph_path"], threshold_mb=0.0000001
    )  # Extremely low threshold to force Dask

    # Should use Dask for large data
    assert graph.vertices.islazy, "Large graph should automatically use Dask backend"

    # Verify data integrity with Dask
    assert graph.num_vertices == large_sample["expected_vertices"]
    assert graph.num_edges == large_sample["expected_edges"]


@pytest.mark.graph
def test_graph_properties_accessible(tmp_path):
    """Test that graph properties are accessible through GraphFrame interface."""
    sample = build_minimal_graphar(tmp_path)
    graph = read_graph(sample["graph_path"])

    # Test property accessors
    assert len(graph.vertex_properties) > 0, "Should have vertex properties"
    assert len(graph.edge_properties) > 0, "Should have edge properties"

    # Verify specific properties exist
    vertex_props = graph.vertex_properties
    edge_props = graph.edge_properties

    assert "name" in vertex_props
    assert "age" in vertex_props
    assert "weight" in edge_props

    # Test boolean properties
    assert isinstance(graph.is_directed, bool)
    assert graph.is_directed == sample["metadata"]["directed"]


@pytest.mark.graph
def test_nonexistent_directory_raises_error(tmp_path):
    """Test that attempting to read nonexistent directory raises appropriate error."""
    nonexistent_path = tmp_path / "does_not_exist"

    with pytest.raises(FileNotFoundError, match="GraphAr directory not found"):
        read_graph(nonexistent_path)


@pytest.mark.graph
def test_file_instead_of_directory_raises_error(tmp_path):
    """Test that attempting to read a file instead of directory raises error."""
    # Create a file instead of directory
    test_file = tmp_path / "not_a_directory.txt"
    test_file.write_text("This is not a directory")

    with pytest.raises(GraphArError, match="Path is not a directory"):
        read_graph(test_file)


@pytest.mark.graph
def test_adjacency_loading_flag(tmp_path):
    """Test that load_adjacency flag affects loading behavior."""
    sample = build_minimal_graphar(tmp_path)

    # Load without adjacency preloading
    graph_no_adj = read_graph(sample["graph_path"], load_adjacency=False)

    # Load with adjacency preloading
    graph_with_adj = read_graph(sample["graph_path"], load_adjacency=True)

    # Both should work and have same basic properties
    assert graph_no_adj.num_vertices == graph_with_adj.num_vertices
    assert graph_no_adj.num_edges == graph_with_adj.num_edges

    # Adjacency should be lazy-loaded in both cases (for now)
    # This tests the current implementation where adjacency is always lazy
    assert hasattr(graph_no_adj, "csr_adjacency")
    assert hasattr(graph_with_adj, "csr_adjacency")
