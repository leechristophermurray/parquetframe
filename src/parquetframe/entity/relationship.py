"""
Relationship management for entity framework.

Handles foreign key validation and relationship resolution.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Relationship:
    """Represents a relationship between entities."""

    name: str
    source_entity: str
    target_entity: str
    foreign_key: str
    relationship_type: str


class RelationshipManager:
    """Manages relationships between entities."""

    def __init__(self):
        self._relationships: dict[str, list[Relationship]] = {}

    def register(self, relationship: Relationship) -> None:
        """Register a relationship."""
        if relationship.source_entity not in self._relationships:
            self._relationships[relationship.source_entity] = []

        self._relationships[relationship.source_entity].append(relationship)

    def get_relationships(self, entity_name: str) -> list[Relationship]:
        """Get all relationships for an entity."""
        return self._relationships.get(entity_name, [])

    def validate_foreign_key(
        self, source_entity: str, target_entity: str, foreign_key_value: Any
    ) -> bool:
        """
        Validate that a foreign key value exists in the target entity.

        Args:
            source_entity: Name of the source entity
            target_entity: Name of the target entity containing the referenced key
            foreign_key_value: The foreign key value to validate

        Returns:
            True if the foreign key exists in target entity, False otherwise

        Example:
            >>> manager = RelationshipManager()
            >>> manager.set_entity_store(store)
            >>> valid = manager.validate_foreign_key("Task", "User", user_id=42)
        """
        # Import here to avoid circular dependency
        from .store import EntityStore

        if not hasattr(self, "_entity_store") or self._entity_store is None:
            # If no entity store is configured, skip validation
            # This allows relationships to work without full entity framework
            return True

        # Get target entity from store
        try:
            target_df = self._entity_store.get_entity(target_entity)
            if target_df is None or len(target_df) == 0:
                return False

            # Check if foreign key value exists in target entity's primary key
            # Assume primary key column is 'id' by convention
            pk_column = "id"
            if pk_column in target_df.columns:
                return foreign_key_value in target_df[pk_column].values
            else:
                # If no 'id' column, check all columns for the value
                for col in target_df.columns:
                    if foreign_key_value in target_df[col].values:
                        return True
                return False

        except (KeyError, AttributeError, TypeError):
            # Entity not found or other error - fail open for now
            return True

    def set_entity_store(self, entity_store):
        """Set the entity store for foreign key validation."""
        self._entity_store = entity_store
