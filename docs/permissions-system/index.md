# Permissions System

Google Zanzibar-style Relationship-Based Access Control (ReBAC) with check, expand, list_objects, and list_subjects APIs.

## Overview

- **🔐 Zanzibar ReBAC** - Industry-standard relationship-based access control
- **🌳 Permission Inheritance** - Automatic propagation through hierarchies
- **📊 Graph Storage** - Efficient GraphAr-based permission tuples
- **⚡ High Performance** - Million-permission scale

## Quick Start

```python
from parquetframe.permissions import PermissionManager

permissions = PermissionManager("./permissions_graph")

# Grant permission
permissions.grant("user:alice", "document:readme", "viewer")

# Check permission
can_view = permissions.check("user:alice", "document:readme", "viewer")

# List accessible resources
docs = permissions.list_objects("user:alice", "document", "viewer")

# List users with access
viewers = permissions.list_subjects("document:readme", "viewer")
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
