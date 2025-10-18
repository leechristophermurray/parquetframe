"""
Tests for core permissions functionality: RelationTuple and TupleStore.
"""

import pandas as pd
import pytest

from src.parquetframe.core import ParquetFrame
from src.parquetframe.permissions.core import RelationTuple, TupleStore


class TestRelationTuple:
    """Test RelationTuple data structure."""

    def test_create_valid_tuple(self):
        """Test creating a valid relation tuple."""
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")

        assert tuple_obj.namespace == "doc"
        assert tuple_obj.object_id == "doc1"
        assert tuple_obj.relation == "viewer"
        assert tuple_obj.subject_namespace == "user"
        assert tuple_obj.subject_id == "alice"

    def test_tuple_properties(self):
        """Test tuple computed properties."""
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")

        assert tuple_obj.object_ref == "doc:doc1"
        assert tuple_obj.subject_ref == "user:alice"
        assert tuple_obj.tuple_key == "doc:doc1#viewer@user:alice"

    def test_tuple_string_representations(self):
        """Test string representations."""
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")

        assert str(tuple_obj) == "user:alice viewer doc:doc1"
        assert "RelationTuple" in repr(tuple_obj)
        assert "doc1" in repr(tuple_obj)
        assert "alice" in repr(tuple_obj)

    def test_tuple_validation_empty_fields(self):
        """Test validation rejects empty fields."""
        with pytest.raises(
            ValueError, match="All relation tuple fields must be non-empty"
        ):
            RelationTuple("", "doc1", "viewer", "user", "alice")

        with pytest.raises(
            ValueError, match="All relation tuple fields must be non-empty"
        ):
            RelationTuple("doc", "", "viewer", "user", "alice")

        with pytest.raises(
            ValueError, match="All relation tuple fields must be non-empty"
        ):
            RelationTuple("doc", "doc1", "", "user", "alice")

    def test_tuple_validation_whitespace(self):
        """Test validation rejects leading/trailing whitespace."""
        with pytest.raises(ValueError, match="cannot have leading/trailing whitespace"):
            RelationTuple(" doc", "doc1", "viewer", "user", "alice")

        with pytest.raises(ValueError, match="cannot have leading/trailing whitespace"):
            RelationTuple("doc", "doc1 ", "viewer", "user", "alice")

    def test_tuple_validation_type_check(self):
        """Test validation requires string types."""
        with pytest.raises(TypeError, match="namespace must be a string"):
            RelationTuple(123, "doc1", "viewer", "user", "alice")

        with pytest.raises(TypeError, match="object_id must be a string"):
            RelationTuple("doc", 456, "viewer", "user", "alice")

    def test_tuple_to_dict(self):
        """Test converting tuple to dictionary."""
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")
        data = tuple_obj.to_dict()

        expected_keys = {
            "namespace",
            "object_id",
            "relation",
            "subject_namespace",
            "subject_id",
            "object_ref",
            "subject_ref",
            "tuple_key",
        }
        assert set(data.keys()) == expected_keys
        assert data["tuple_key"] == "doc:doc1#viewer@user:alice"

    def test_tuple_from_dict(self):
        """Test creating tuple from dictionary."""
        data = {
            "namespace": "doc",
            "object_id": "doc1",
            "relation": "viewer",
            "subject_namespace": "user",
            "subject_id": "alice",
        }

        tuple_obj = RelationTuple.from_dict(data)
        assert tuple_obj.namespace == "doc"
        assert tuple_obj.subject_id == "alice"

    def test_tuple_equality(self):
        """Test tuple equality and hashing."""
        tuple1 = RelationTuple("doc", "doc1", "viewer", "user", "alice")
        tuple2 = RelationTuple("doc", "doc1", "viewer", "user", "alice")
        tuple3 = RelationTuple("doc", "doc1", "editor", "user", "alice")

        assert tuple1 == tuple2
        assert tuple1 != tuple3

        # Test as dict keys (hashing)
        tuple_dict = {tuple1: "value1", tuple3: "value3"}
        assert tuple_dict[tuple2] == "value1"


class TestTupleStore:
    """Test TupleStore functionality."""

    def test_create_empty_store(self):
        """Test creating empty tuple store."""
        store = TupleStore()

        assert store.is_empty()
        assert len(store) == 0
        assert not store  # __bool__ should be False
        assert store.size == 0

    def test_add_single_tuple(self):
        """Test adding a single tuple."""
        store = TupleStore()
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")

        result = store.add_tuple(tuple_obj)

        assert result is store  # Should return self for chaining
        assert not store.is_empty()
        assert len(store) == 1
        assert store.has_tuple(tuple_obj)

    def test_add_multiple_tuples(self):
        """Test adding multiple tuples."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
            RelationTuple("folder", "folder1", "owner", "user", "charlie"),
        ]

        store.add_tuples(tuples)

        assert len(store) == 3
        for tuple_obj in tuples:
            assert store.has_tuple(tuple_obj)

    def test_add_duplicate_tuples(self):
        """Test that duplicate tuples are deduplicated."""
        store = TupleStore()
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")

        store.add_tuple(tuple_obj)
        store.add_tuple(tuple_obj)  # Add same tuple again

        assert len(store) == 1  # Should still be 1

    def test_remove_tuple(self):
        """Test removing a tuple."""
        store = TupleStore()
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")

        store.add_tuple(tuple_obj)
        assert store.has_tuple(tuple_obj)

        store.remove_tuple(tuple_obj)
        assert not store.has_tuple(tuple_obj)
        assert len(store) == 0

    def test_query_tuples_all_fields(self):
        """Test querying tuples by all field combinations."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "viewer", "user", "alice"),
            RelationTuple("doc", "doc1", "editor", "user", "bob"),
            RelationTuple("folder", "folder1", "viewer", "user", "alice"),
        ]
        store.add_tuples(tuples)

        # Query by namespace
        results = store.query_tuples(namespace="doc")
        assert len(results) == 3

        # Query by subject
        results = store.query_tuples(subject_namespace="user", subject_id="alice")
        assert len(results) == 3

        # Query by relation
        results = store.query_tuples(relation="viewer")
        assert len(results) == 3

        # Query by multiple fields
        results = store.query_tuples(
            namespace="doc", relation="viewer", subject_id="alice"
        )
        assert len(results) == 2

        # Query with no matches
        results = store.query_tuples(namespace="nonexistent")
        assert len(results) == 0

    def test_get_objects_for_subject(self):
        """Test getting objects accessible by a subject."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "alice"),
            RelationTuple("folder", "folder1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc3", "viewer", "user", "bob"),
        ]
        store.add_tuples(tuples)

        # Get all objects for alice
        objects = store.get_objects_for_subject("user", "alice")
        expected = {("doc", "doc1"), ("doc", "doc2"), ("folder", "folder1")}
        assert set(objects) == expected

        # Get docs only for alice with viewer relation
        objects = store.get_objects_for_subject(
            "user", "alice", relation="viewer", namespace="doc"
        )
        assert objects == [("doc", "doc1")]

    def test_get_subjects_for_object(self):
        """Test getting subjects that can access an object."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc1", "viewer", "user", "bob"),
            RelationTuple("doc", "doc1", "editor", "user", "charlie"),
            RelationTuple("doc", "doc2", "viewer", "user", "alice"),
        ]
        store.add_tuples(tuples)

        # Get all subjects for doc1
        subjects = store.get_subjects_for_object("doc", "doc1")
        expected = {("user", "alice"), ("user", "bob"), ("user", "charlie")}
        assert set(subjects) == expected

        # Get viewers only for doc1
        subjects = store.get_subjects_for_object("doc", "doc1", relation="viewer")
        expected = {("user", "alice"), ("user", "bob")}
        assert set(subjects) == expected

    def test_get_metadata(self):
        """Test getting store metadata."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "alice"),
            RelationTuple("folder", "folder1", "viewer", "group", "team1"),
        ]
        store.add_tuples(tuples)

        relations = store.get_relations()
        assert relations == {"viewer", "editor"}

        namespaces = store.get_namespaces()
        assert namespaces == {"doc", "folder"}

        subject_namespaces = store.get_subject_namespaces()
        assert subject_namespaces == {"user", "group"}

    def test_store_iteration(self):
        """Test iterating over store contents."""
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        # Test iteration
        iterated_tuples = list(store)
        assert len(iterated_tuples) == 2

        # Check that we get the same tuples back
        for tuple_obj in tuples:
            found = any(t.tuple_key == tuple_obj.tuple_key for t in iterated_tuples)
            assert found

    def test_store_stats(self):
        """Test store statistics."""
        store = TupleStore()

        # Empty store stats
        stats = store.stats()
        assert stats["total_tuples"] == 0
        assert stats["unique_objects"] == 0

        # Add some tuples and check stats
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc1", "editor", "user", "bob"),  # Same object
            RelationTuple("doc", "doc2", "viewer", "user", "alice"),  # Same subject
        ]
        store.add_tuples(tuples)

        stats = store.stats()
        assert stats["total_tuples"] == 3
        assert stats["unique_objects"] == 2  # doc:doc1 and doc:doc2
        assert stats["unique_subjects"] == 2  # user:alice and user:bob
        assert stats["unique_relations"] == 2  # viewer and editor

    def test_store_from_dataframe(self):
        """Test creating store from DataFrame."""
        # Create a DataFrame with tuple data
        data = pd.DataFrame(
            [
                {
                    "namespace": "doc",
                    "object_id": "doc1",
                    "relation": "viewer",
                    "subject_namespace": "user",
                    "subject_id": "alice",
                    "object_ref": "doc:doc1",
                    "subject_ref": "user:alice",
                    "tuple_key": "doc:doc1#viewer@user:alice",
                }
            ]
        )

        store = TupleStore(data)
        assert len(store) == 1

        # Verify the tuple can be retrieved
        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")
        assert store.has_tuple(tuple_obj)

    def test_store_from_parquetframe(self):
        """Test creating store from ParquetFrame."""
        data = pd.DataFrame(
            [
                {
                    "namespace": "doc",
                    "object_id": "doc1",
                    "relation": "viewer",
                    "subject_namespace": "user",
                    "subject_id": "alice",
                    "object_ref": "doc:doc1",
                    "subject_ref": "user:alice",
                    "tuple_key": "doc:doc1#viewer@user:alice",
                }
            ]
        )
        pf = ParquetFrame(data)

        store = TupleStore(pf)
        assert len(store) == 1

        tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")
        assert store.has_tuple(tuple_obj)


class TestTupleStorePersistence:
    """Test TupleStore save/load functionality."""

    def test_save_and_load_store(self, tmp_path):
        """Test saving and loading a tuple store."""
        # Create store with some data
        store = TupleStore()
        tuples = [
            RelationTuple("doc", "doc1", "viewer", "user", "alice"),
            RelationTuple("doc", "doc2", "editor", "user", "bob"),
        ]
        store.add_tuples(tuples)

        # Save to temporary file
        file_path = tmp_path / "test_store.parquet"
        store.save(str(file_path))

        # Load from file
        loaded_store = TupleStore.load(str(file_path))

        # Verify the loaded store has the same data
        assert len(loaded_store) == len(store)
        for tuple_obj in tuples:
            assert loaded_store.has_tuple(tuple_obj)

    def test_save_empty_store(self, tmp_path):
        """Test saving and loading an empty store."""
        store = TupleStore()

        file_path = tmp_path / "empty_store.parquet"
        store.save(str(file_path))

        loaded_store = TupleStore.load(str(file_path))
        assert loaded_store.is_empty()
        assert len(loaded_store) == 0
