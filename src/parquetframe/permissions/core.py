"""
Core data structures for Zanzibar-style permissions.

This module defines the fundamental data structures used in the permission system:
- RelationTuple: Individual permission relationships
- TupleStore: Efficient storage and querying of relation tuples
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ..core import ParquetFrame


@dataclass(frozen=True)
class RelationTuple:
    """
    A relation tuple representing a permission relationship.

    Follows the Zanzibar model where permissions are expressed as:
    "subject has relation to object in namespace"

    Examples:
        RelationTuple("doc", "doc1", "viewer", "user", "alice")
        -> user:alice has viewer relation to doc:doc1

        RelationTuple("folder", "folder1", "editor", "group", "eng-team")
        -> group:eng-team has editor relation to folder:folder1

        RelationTuple("doc", "doc1", "viewer", "folder", "folder1#viewer")
        -> folder:folder1#viewer has viewer relation to doc:doc1
        (inherited permission via folder membership)

    Attributes:
        namespace: The namespace/type of the object (e.g., "doc", "folder")
        object_id: The ID of the object (e.g., "doc1", "folder1")
        relation: The relation type (e.g., "viewer", "editor", "owner")
        subject_namespace: The namespace of the subject (e.g., "user", "group")
        subject_id: The ID of the subject (e.g., "alice", "eng-team")
    """

    namespace: str
    object_id: str
    relation: str
    subject_namespace: str
    subject_id: str

    def __post_init__(self):
        """Validate the relation tuple after initialization."""
        if not all(
            [
                self.namespace,
                self.object_id,
                self.relation,
                self.subject_namespace,
                self.subject_id,
            ]
        ):
            raise ValueError("All relation tuple fields must be non-empty")

        # Basic format validation
        for field_name, value in [
            ("namespace", self.namespace),
            ("object_id", self.object_id),
            ("relation", self.relation),
            ("subject_namespace", self.subject_namespace),
            ("subject_id", self.subject_id),
        ]:
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            if len(value.strip()) != len(value):
                raise ValueError(
                    f"{field_name} cannot have leading/trailing whitespace"
                )

    @property
    def object_ref(self) -> str:
        """Get the full object reference (namespace:object_id)."""
        return f"{self.namespace}:{self.object_id}"

    @property
    def subject_ref(self) -> str:
        """Get the full subject reference (subject_namespace:subject_id)."""
        return f"{self.subject_namespace}:{self.subject_id}"

    @property
    def tuple_key(self) -> str:
        """Get a unique key for this tuple (for deduplication and indexing)."""
        return f"{self.object_ref}#{self.relation}@{self.subject_ref}"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.subject_ref} {self.relation} {self.object_ref}"

    def __repr__(self) -> str:
        """Machine-readable string representation."""
        return (
            f"RelationTuple(namespace='{self.namespace}', object_id='{self.object_id}', "
            f"relation='{self.relation}', subject_namespace='{self.subject_namespace}', "
            f"subject_id='{self.subject_id}')"
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for DataFrame storage."""
        return {
            "namespace": self.namespace,
            "object_id": self.object_id,
            "relation": self.relation,
            "subject_namespace": self.subject_namespace,
            "subject_id": self.subject_id,
            "object_ref": self.object_ref,
            "subject_ref": self.subject_ref,
            "tuple_key": self.tuple_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> RelationTuple:
        """Create RelationTuple from dictionary."""
        return cls(
            namespace=data["namespace"],
            object_id=data["object_id"],
            relation=data["relation"],
            subject_namespace=data["subject_namespace"],
            subject_id=data["subject_id"],
        )


class TupleStore:
    """
    Efficient storage and querying of relation tuples using ParquetFrame.

    The TupleStore provides the foundational storage layer for the permission system,
    optimized for the common query patterns:
    - Check if a specific tuple exists
    - Find all objects a subject can access with a given relation
    - Find all subjects that have a relation to an object
    - Bulk operations for UI generation

    Uses ParquetFrame for storage with optimized schema and indexing.
    """

    def __init__(self, data: ParquetFrame | pd.DataFrame | None = None):
        """
        Initialize TupleStore.

        Args:
            data: Optional initial data as ParquetFrame or DataFrame
        """
        if data is None:
            # Create empty DataFrame with optimized schema
            data = pd.DataFrame(
                columns=[
                    "namespace",
                    "object_id",
                    "relation",
                    "subject_namespace",
                    "subject_id",
                    "object_ref",
                    "subject_ref",
                    "tuple_key",
                ]
            )

        if isinstance(data, pd.DataFrame):
            self._data = ParquetFrame(data, islazy=False)
        else:
            self._data = data

    @property
    def data(self) -> ParquetFrame:
        """Get the underlying ParquetFrame data."""
        return self._data

    @property
    def size(self) -> int:
        """Get the number of tuples in the store."""
        return len(self._data)

    def is_empty(self) -> bool:
        """Check if the tuple store is empty."""
        return self.size == 0

    def add_tuple(self, tuple_obj: RelationTuple) -> TupleStore:
        """
        Add a single relation tuple to the store.

        Args:
            tuple_obj: The RelationTuple to add

        Returns:
            Self for method chaining
        """
        new_row = pd.DataFrame([tuple_obj.to_dict()])

        if self.is_empty():
            self._data = ParquetFrame(new_row, islazy=False)
        else:
            combined = pd.concat([self._data._df, new_row], ignore_index=True)
            # Remove duplicates based on tuple_key
            combined = combined.drop_duplicates(subset=["tuple_key"], keep="last")
            self._data = ParquetFrame(combined, islazy=False)

        return self

    def add_tuples(self, tuples: list[RelationTuple]) -> TupleStore:
        """
        Add multiple relation tuples to the store.

        Args:
            tuples: List of RelationTuple objects to add

        Returns:
            Self for method chaining
        """
        if not tuples:
            return self

        new_rows = pd.DataFrame([t.to_dict() for t in tuples])

        if self.is_empty():
            self._data = ParquetFrame(new_rows, islazy=False)
        else:
            combined = pd.concat([self._data._df, new_rows], ignore_index=True)
            # Remove duplicates based on tuple_key
            combined = combined.drop_duplicates(subset=["tuple_key"], keep="last")
            self._data = ParquetFrame(combined, islazy=False)

        return self

    def remove_tuple(self, tuple_obj: RelationTuple) -> TupleStore:
        """
        Remove a relation tuple from the store.

        Args:
            tuple_obj: The RelationTuple to remove

        Returns:
            Self for method chaining
        """
        if self.is_empty():
            return self

        mask = self._data._df["tuple_key"] != tuple_obj.tuple_key
        filtered = self._data._df[mask]
        self._data = ParquetFrame(filtered.reset_index(drop=True), islazy=False)

        return self

    def has_tuple(self, tuple_obj: RelationTuple) -> bool:
        """
        Check if a specific tuple exists in the store.

        Args:
            tuple_obj: The RelationTuple to check for

        Returns:
            True if the tuple exists, False otherwise
        """
        if self.is_empty():
            return False

        return tuple_obj.tuple_key in self._data._df["tuple_key"].values

    def query_tuples(
        self,
        namespace: str | None = None,
        object_id: str | None = None,
        relation: str | None = None,
        subject_namespace: str | None = None,
        subject_id: str | None = None,
    ) -> list[RelationTuple]:
        """
        Query tuples by any combination of fields.

        Args:
            namespace: Filter by object namespace
            object_id: Filter by object ID
            relation: Filter by relation type
            subject_namespace: Filter by subject namespace
            subject_id: Filter by subject ID

        Returns:
            List of matching RelationTuple objects
        """
        if self.is_empty():
            return []

        df = self._data._df

        # Build filter conditions
        conditions = []
        if namespace is not None:
            conditions.append(df["namespace"] == namespace)
        if object_id is not None:
            conditions.append(df["object_id"] == object_id)
        if relation is not None:
            conditions.append(df["relation"] == relation)
        if subject_namespace is not None:
            conditions.append(df["subject_namespace"] == subject_namespace)
        if subject_id is not None:
            conditions.append(df["subject_id"] == subject_id)

        # Apply all conditions
        if conditions:
            mask = conditions[0]
            for condition in conditions[1:]:
                mask &= condition
            filtered = df[mask]
        else:
            filtered = df

        # Convert back to RelationTuple objects
        return [RelationTuple.from_dict(row) for _, row in filtered.iterrows()]

    def get_objects_for_subject(
        self,
        subject_namespace: str,
        subject_id: str,
        relation: str | None = None,
        namespace: str | None = None,
    ) -> list[tuple[str, str]]:
        """
        Get all objects that a subject has relations to.

        Args:
            subject_namespace: The subject's namespace
            subject_id: The subject's ID
            relation: Optional filter by relation type
            namespace: Optional filter by object namespace

        Returns:
            List of (namespace, object_id) tuples
        """
        tuples = self.query_tuples(
            subject_namespace=subject_namespace,
            subject_id=subject_id,
            relation=relation,
            namespace=namespace,
        )

        return [(t.namespace, t.object_id) for t in tuples]

    def get_subjects_for_object(
        self,
        namespace: str,
        object_id: str,
        relation: str | None = None,
        subject_namespace: str | None = None,
    ) -> list[tuple[str, str]]:
        """
        Get all subjects that have relations to an object.

        Args:
            namespace: The object's namespace
            object_id: The object's ID
            relation: Optional filter by relation type
            subject_namespace: Optional filter by subject namespace

        Returns:
            List of (subject_namespace, subject_id) tuples
        """
        tuples = self.query_tuples(
            namespace=namespace,
            object_id=object_id,
            relation=relation,
            subject_namespace=subject_namespace,
        )

        return [(t.subject_namespace, t.subject_id) for t in tuples]

    def get_relations(self) -> set[str]:
        """Get all unique relation types in the store."""
        if self.is_empty():
            return set()
        return set(self._data._df["relation"].unique())

    def get_namespaces(self) -> set[str]:
        """Get all unique object namespaces in the store."""
        if self.is_empty():
            return set()
        return set(self._data._df["namespace"].unique())

    def get_subject_namespaces(self) -> set[str]:
        """Get all unique subject namespaces in the store."""
        if self.is_empty():
            return set()
        return set(self._data._df["subject_namespace"].unique())

    def __iter__(self) -> Iterator[RelationTuple]:
        """Iterate over all tuples in the store."""
        if self.is_empty():
            return iter([])

        for _, row in self._data._df.iterrows():
            yield RelationTuple.from_dict(row)

    def __len__(self) -> int:
        """Get the number of tuples in the store."""
        return self.size

    def __bool__(self) -> bool:
        """Check if the store has any tuples."""
        return not self.is_empty()

    def save(self, path: str) -> None:
        """Save the tuple store to a parquet file."""
        self._data.save(path)

    @classmethod
    def load(cls, path: str) -> TupleStore:
        """Load a tuple store from a parquet file."""
        data = ParquetFrame.read(path)
        return cls(data)

    def stats(self) -> dict[str, Any]:
        """Get statistics about the tuple store."""
        if self.is_empty():
            return {
                "total_tuples": 0,
                "unique_objects": 0,
                "unique_subjects": 0,
                "unique_relations": 0,
                "unique_namespaces": 0,
            }

        df = self._data._df
        return {
            "total_tuples": len(df),
            "unique_objects": df["object_ref"].nunique(),
            "unique_subjects": df["subject_ref"].nunique(),
            "unique_relations": df["relation"].nunique(),
            "unique_namespaces": df["namespace"].nunique()
            + df["subject_namespace"].nunique(),
        }
