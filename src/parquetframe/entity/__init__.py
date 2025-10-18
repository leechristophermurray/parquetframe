"""
Entity-Graph Framework for ParquetFrame Phase 2.3.

Provides ORM-like functionality with @entity and @rel decorators for
data modeling, persistence, and relationship management.
"""

from .decorators import entity, rel
from .entity_store import EntityStore
from .relationship import Relationship, RelationshipManager

__all__ = [
    "entity",
    "rel",
    "EntityStore",
    "Relationship",
    "RelationshipManager",
]
