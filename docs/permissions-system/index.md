# Permissions System

Google Zanzibar-style Relationship-Based Access Control (ReBAC) with check, expand, list_objects, and list_subjects APIs.

## Overview

- **🔐 Zanzibar ReBAC** - Industry-standard relationship-based access control
- **🌳 Permission Inheritance** - Automatic propagation through hierarchies
- **📊 Graph Storage** - Efficient GraphAr-based permission tuples
- **⚡ High Performance** - Million-permission scale

## Quick Start

> [!TIP]
> Check out the **[Step-by-Step Tutorial](tutorial.md)** for a complete walkthrough.

```python
```python
from parquetframe.permissions import TupleStore, RelationTuple, check, list_objects, list_subjects

store = TupleStore()

# Grant permission
store.add_tuple(RelationTuple("document", "readme", "viewer", "user", "alice"))

# Check permission
can_view = check(store, "user", "alice", "viewer", "document", "readme")

# List accessible resources (for a subject)
# Note: list_objects finds objects with a specific relation,
# to find what 'alice' can view requires expand() or logic
docs = list_objects(store, "viewer", "document")

# List users with access
viewers = list_subjects(store, "viewer", "document", "readme")
```

## Zanzibar Four APIs

1. **check** - Verify permission
2. **expand** - Get permission tree
3. **list_objects** - Find accessible resources
4. **list_subjects** - Find users with access

## Real-World Example

See [Todo/Kanban Example](../documentation-examples/todo-kanban.md) for complete multi-user permission system.

## Related Categories

- **[Entity Framework](../entity-framework/index.md)** - Entity-level access control
- **[Graph Processing](../graph-processing/index.md)** - Permission graph analysis
