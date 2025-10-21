"""
Tests for GraphAr-compliant permissions storage.

These tests verify that the TupleStore saves and loads permissions
in GraphAr format with proper directory structure, metadata, and schema.
"""

import pandas as pd
import pytest
import yaml

from src.parquetframe.permissions.core import RelationTuple, TupleStore


class TestGraphArStructure:
    """Test GraphAr directory structure and metadata generation."""

    def test_save_creates_graphar_structure(self, tmp_path):
        """Test that save() creates proper GraphAr directory structure."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Verify directory structure
        assert storage_path.exists()
        assert (storage_path / "_metadata.yaml").exists()
        assert (storage_path / "_schema.yaml").exists()
        assert (storage_path / "vertices").exists()
        assert (storage_path / "edges").exists()

    def test_save_empty_store_skips_creation(self, tmp_path):
        """Test that empty stores don't create directory structure."""
        store = TupleStore()
        storage_path = tmp_path / "empty_permissions"

        store.save(str(storage_path))

        # Empty store should skip creation
        assert not storage_path.exists()

    def test_metadata_yaml_structure(self, tmp_path):
        """Test _metadata.yaml has correct structure."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("folder", "f1", "owner", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Load and verify metadata
        metadata_file = storage_path / "_metadata.yaml"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)

        assert metadata["name"] == "permissions"
        assert metadata["format"] == "graphar"
        assert "version" in metadata
        assert "vertices" in metadata
        assert "edges" in metadata

        # Verify vertices section
        vertices = metadata["vertices"]
        assert len(vertices) == 2  # subjects and objects
        vertex_labels = {v["label"] for v in vertices}
        assert "subjects" in vertex_labels
        assert "objects" in vertex_labels

        # Verify edges section
        edges = metadata["edges"]
        assert len(edges) > 0
        edge_labels = {e["label"] for e in edges}
        assert "viewer" in edge_labels or "owner" in edge_labels

    def test_schema_yaml_structure(self, tmp_path):
        """Test _schema.yaml has correct structure."""
        store = TupleStore()
        tuples = [RelationTuple("doc", "doc1", "viewer", "user", "alice")]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Load and verify schema
        schema_file = storage_path / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        assert "vertices" in schema
        assert "edges" in schema

        # Verify vertex schemas
        vertices = schema["vertices"]
        assert len(vertices) == 2
        for vertex in vertices:
            assert "label" in vertex
            assert "properties" in vertex
            assert len(vertex["properties"]) > 0

        # Verify edge schemas
        edges = schema["edges"]
        assert len(edges) > 0
        for edge in edges:
            assert "label" in edge
            assert "source" in edge
            assert "target" in edge
            assert "properties" in edge


class TestGraphArVertices:
    """Test vertex storage in GraphAr format."""

    def test_vertices_directory_structure(self, tmp_path):
        """Test vertices are stored in correct directory structure."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Verify vertex directories
        vertices_dir = storage_path / "vertices"
        assert (vertices_dir / "subjects").exists()
        assert (vertices_dir / "objects").exists()

    def test_subjects_parquet_content(self, tmp_path):
        """Test subjects vertex file has correct content."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Read subjects parquet
        subjects_file = storage_path / "vertices" / "subjects" / "part0.parquet"
        df = pd.read_parquet(subjects_file)

        # Verify content
        assert "namespace" in df.columns
        assert "id" in df.columns
        assert len(df) == 2
        assert set(df["id"]) == {"alice", "bob"}
        assert all(df["namespace"] == "user")

    def test_objects_parquet_content(self, tmp_path):
        """Test objects vertex file has correct content."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Read objects parquet
        objects_file = storage_path / "vertices" / "objects" / "part0.parquet"
        df = pd.read_parquet(objects_file)

        # Verify content
        assert "namespace" in df.columns
        assert "id" in df.columns
        assert len(df) == 2
        assert set(df["id"]) == {"doc1", "doc2"}
        assert all(df["namespace"] == "doc")

    def test_deduplication_of_vertices(self, tmp_path):
        """Test that duplicate subjects/objects are deduplicated."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "viewer", "user", "alice"),  # alice again
            RelationTuple("doc", "doc1", "editor", "user", "bob"),  # doc1 again
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Verify subjects deduplicated
        subjects_file = storage_path / "vertices" / "subjects" / "part0.parquet"
        subjects_df = pd.read_parquet(subjects_file)
        assert len(subjects_df) == 2  # alice, bob

        # Verify objects deduplicated
        objects_file = storage_path / "vertices" / "objects" / "part0.parquet"
        objects_df = pd.read_parquet(objects_file)
        assert len(objects_df) == 2  # doc1, doc2


class TestGraphArEdges:
    """Test edge storage in GraphAr format."""

    def test_edges_directory_structure(self, tmp_path):
        """Test edges are stored grouped by relation type."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Verify edge directories
        edges_dir = storage_path / "edges"
        assert (edges_dir / "viewer").exists()
        assert (edges_dir / "editor").exists()

    def test_edge_parquet_content(self, tmp_path):
        """Test edge files have correct content."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "viewer", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Read viewer edges
        viewer_file = storage_path / "edges" / "viewer" / "part0.parquet"
        df = pd.read_parquet(viewer_file)

        # Verify content
        assert "subject_namespace" in df.columns
        assert "subject_id" in df.columns
        assert "object_namespace" in df.columns
        assert "object_id" in df.columns
        assert len(df) == 2

    def test_multiple_relations_create_separate_files(self, tmp_path):
        """Test that different relations create separate edge directories."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
            RelationTuple("doc", "doc3", "owner", "user", "charlie"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Verify all relation directories exist
        edges_dir = storage_path / "edges"
        assert (edges_dir / "viewer").exists()
        assert (edges_dir / "editor").exists()
        assert (edges_dir / "owner").exists()


class TestGraphArLoadValidation:
    """Test loading and validation of GraphAr structure."""

    def test_load_validates_structure(self, tmp_path):
        """Test load() validates GraphAr structure."""
        store = TupleStore()
        tuples = [RelationTuple("doc", "doc1", "viewer", "user", "alice")]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Load should succeed with valid structure
        loaded_store = TupleStore.load(str(storage_path))
        assert len(loaded_store) == 1

    def test_load_fails_without_metadata(self, tmp_path):
        """Test load() fails if _metadata.yaml is missing."""
        storage_path = tmp_path / "invalid_permissions"
        storage_path.mkdir()

        with pytest.raises(FileNotFoundError, match="_metadata.yaml"):
            TupleStore.load(str(storage_path))

    def test_load_fails_without_schema(self, tmp_path):
        """Test load() fails if _schema.yaml is missing."""
        storage_path = tmp_path / "invalid_permissions"
        storage_path.mkdir()

        # Create metadata but no schema
        metadata = {"name": "test", "format": "graphar"}
        with open(storage_path / "_metadata.yaml", "w") as f:
            yaml.dump(metadata, f)

        with pytest.raises(FileNotFoundError, match="_schema.yaml"):
            TupleStore.load(str(storage_path))

    def test_load_fails_without_vertices_dir(self, tmp_path):
        """Test load() fails if vertices/ directory is missing."""
        storage_path = tmp_path / "invalid_permissions"
        storage_path.mkdir()

        # Create metadata and schema
        metadata = {"name": "test", "format": "graphar"}
        schema = {"vertices": [], "edges": []}
        with open(storage_path / "_metadata.yaml", "w") as f:
            yaml.dump(metadata, f)
        with open(storage_path / "_schema.yaml", "w") as f:
            yaml.dump(schema, f)

        with pytest.raises(FileNotFoundError, match="vertices"):
            TupleStore.load(str(storage_path))


class TestGraphArRoundtrip:
    """Test save/load roundtrip preserves all data."""

    def test_roundtrip_simple_tuples(self, tmp_path):
        """Test roundtrip with simple tuples."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        loaded_store = TupleStore.load(str(storage_path))

        # Verify all tuples preserved
        assert len(loaded_store) == len(store)
        for tuple_obj in tuples:
            assert loaded_store.has_tuple(tuple_obj)

    def test_roundtrip_complex_tuples(self, tmp_path):
        """Test roundtrip with complex tuple set."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "alice"),
            RelationTuple("folder", "f1", "owner", "user", "bob"),
            RelationTuple("folder", "f2", "viewer", "group", "team1"),
            RelationTuple("doc", "doc3", "editor", "group", "team2"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        loaded_store = TupleStore.load(str(storage_path))

        # Verify all tuples preserved
        assert len(loaded_store) == len(store)
        for tuple_obj in tuples:
            assert loaded_store.has_tuple(tuple_obj)

        # Verify stats match
        original_stats = store.stats()
        loaded_stats = loaded_store.stats()
        assert loaded_stats["total_tuples"] == original_stats["total_tuples"]
        assert loaded_stats["unique_objects"] == original_stats["unique_objects"]
        assert loaded_stats["unique_subjects"] == original_stats["unique_subjects"]


class TestGraphArCompatibility:
    """Test GraphAr spec compatibility."""

    def test_metadata_follows_graphar_spec(self, tmp_path):
        """Test metadata follows Apache GraphAr specification."""
        store = TupleStore()
        tuples = [RelationTuple("doc", "doc1", "viewer", "user", "alice")]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        metadata_file = storage_path / "_metadata.yaml"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)

        # Required GraphAr metadata fields
        assert "name" in metadata
        assert "version" in metadata
        assert "vertices" in metadata
        assert "edges" in metadata

        # Vertex info should have required fields
        for vertex in metadata["vertices"]:
            assert "label" in vertex
            assert "prefix" in vertex
            assert "count" in vertex

        # Edge info should have required fields
        for edge in metadata["edges"]:
            assert "label" in edge
            assert "prefix" in edge
            assert "source" in edge
            assert "target" in edge

    def test_schema_follows_graphar_spec(self, tmp_path):
        """Test schema follows Apache GraphAr specification."""
        store = TupleStore()
        tuples = [RelationTuple("doc", "doc1", "viewer", "user", "alice")]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        schema_file = storage_path / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        # Required GraphAr schema fields
        assert "vertices" in schema
        assert "edges" in schema

        # Vertex schema should have properties
        for vertex in schema["vertices"]:
            assert "label" in vertex
            assert "properties" in vertex
            for prop in vertex["properties"]:
                assert "name" in prop
                assert "type" in prop

        # Edge schema should have properties
        for edge in schema["edges"]:
            assert "label" in edge
            assert "source" in edge
            assert "target" in edge
            assert "properties" in edge


class TestGraphArIntegration:
    """Test integration with ParquetFrame graph reading."""

    def test_permissions_loadable_as_graph(self, tmp_path):
        """Test that saved permissions can be loaded with pf.read_graph()."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        storage_path = tmp_path / "permissions"
        store.save(str(storage_path))

        # Verify structure is compatible with graph reader
        # (actual read_graph test would require full ParquetFrame integration)
        assert (storage_path / "_metadata.yaml").exists()
        assert (storage_path / "_schema.yaml").exists()
        assert (storage_path / "vertices").is_dir()
        assert (storage_path / "edges").is_dir()
