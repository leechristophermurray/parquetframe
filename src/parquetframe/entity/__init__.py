"""
Entity-Graph Framework for ParquetFrame Phase 2.3.

Provides ORM-like functionality with @entity and @rel decorators for
data modeling, persistence, and relationship management.
"""

from .decorators import entity, rel
from .entity_store import EntityStore
from .relationship import Relationship, RelationshipManager

# Optional visualization support
try:
    from .visualization import (
        entities_to_networkx,
        export_to_graphviz,
        is_visualization_available,
        visualize_with_pyvis,
    )

    _VISUALIZATION_IMPORTS = [
        "entities_to_networkx",
        "visualize_with_pyvis",
        "export_to_graphviz",
        "is_visualization_available",
    ]
except ImportError:
    _VISUALIZATION_IMPORTS = []

__all__ = [
    "entity",
    "rel",
    "EntityStore",
    "Relationship",
    "RelationshipManager",
] + _VISUALIZATION_IMPORTS
