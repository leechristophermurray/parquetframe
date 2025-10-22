# Permissions API Reference

Complete API documentation for ParquetFrame's Zanzibar-style permissions system (Phase 2).

## Core Classes

### RelationTuple

```python
class RelationTuple:
    namespace: str
    object_id: str
    relation: str
    subject_namespace: str
    subject_id: str
```

Represents a relation tuple in the Zanzibar permission model.

**Fields:**

- `namespace` (str): Type of resource (e.g., "board", "task", "document")
- `object_id` (str): Specific resource identifier
- `relation` (str): Type of access (e.g., "owner", "editor", "viewer")
- `subject_namespace` (str): Type of actor (e.g., "user", "group")
- `subject_id` (str): Specific actor identifier

**Example:**

```python path=null start=null
from parquetframe.permissions import RelationTuple

# User alice has viewer access to document doc1
tuple = RelationTuple(
    namespace="document",
    object_id="doc1",
    relation="viewer",
    subject_namespace="user",
    subject_id="alice"
)
```

### TupleStore

```python
class TupleStore:
    def __init__(self, storage_path: str = None)
    def add_tuple(self, tuple: RelationTuple) -> None
    def remove_tuple(self, tuple: RelationTuple) -> None
    def get_tuples(self, **filters) -> list[RelationTuple]
    def save(self, path: str) -> None
    @classmethod
    def load(cls, path: str) -> "TupleStore"
    def stats(self) -> dict
```

Storage and management for relation tuples.

**Example:**

```python path=null start=null
from parquetframe.permissions import TupleStore, RelationTuple

# Create store
store = TupleStore()

# Add permissions
store.add_tuple(RelationTuple("doc", "doc1", "owner", "user", "alice"))
store.add_tuple(RelationTuple("doc", "doc1", "viewer", "user", "bob"))

# Save to disk
store.save("permissions.parquet")

# Load from disk
store = TupleStore.load("permissions.parquet")

# Get statistics
stats = store.stats()
print(f"Total tuples: {stats['total_tuples']}")
```

## Zanzibar APIs

### check()

```python
def check(
    store: TupleStore,
    subject_namespace: str,
    subject_id: str,
    relation: str,
    object_namespace: str,
    object_id: str,
    allow_indirect: bool = True
) -> bool
```

Checks if a subject has a specific relation to an object.

**Parameters:**

- `store` (TupleStore): Permission store to query
- `subject_namespace` (str): Type of subject (e.g., "user")
- `subject_id` (str): Subject identifier
- `relation` (str): Relation to check (e.g., "viewer")
- `object_namespace` (str): Type of object (e.g., "document")
- `object_id` (str): Object identifier
- `allow_indirect` (bool): Whether to check indirect permissions via graph traversal

**Returns:**

`True` if subject has the relation to object, `False` otherwise.

**Example:**

```python path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/permissions.py start=110
def check_permission(
    self,
    user_id: str,
    resource_type: str,
    resource_id: str,
    relation: str,
    allow_indirect: bool = True,
) -> bool:
    """
    Check if a user has a specific permission.

    Uses Zanzibar check() API for both direct and indirect permissions.
    """
    return check(
        store=self.store,
        subject_namespace="user",
        subject_id=user_id,
        relation=relation,
        object_namespace=resource_type,
        object_id=resource_id,
        allow_indirect=allow_indirect,
    )
```

### expand()

```python
def expand(
    store: TupleStore,
    subject_namespace: str,
    subject_id: str,
    relation: str,
    object_namespace: str = None,
    allow_indirect: bool = True
) -> list[tuple[str, str]]
```

Finds all objects a subject has a specific relation to.

**Parameters:**

- `store` (TupleStore): Permission store to query
- `subject_namespace` (str): Type of subject
- `subject_id` (str): Subject identifier
- `relation` (str): Relation to expand
- `object_namespace` (str, optional): Filter by object type
- `allow_indirect` (bool): Whether to check indirect permissions

**Returns:**

List of `(object_namespace, object_id)` tuples.

**Example:**

```python path=null start=null
from parquetframe.permissions import expand

# Find all documents alice can view
viewable_docs = expand(
    store=store,
    subject_namespace="user",
    subject_id="alice",
    relation="viewer",
    object_namespace="document"
)

for namespace, doc_id in viewable_docs:
    print(f"Alice can view {namespace}:{doc_id}")
```

### list_objects()

```python
def list_objects(
    store: TupleStore,
    relation: str,
    object_namespace: str
) -> list[tuple[str, str]]
```

Finds all objects with a specific relation in a namespace.

**Parameters:**

- `store` (TupleStore): Permission store to query
- `relation` (str): Relation to filter by
- `object_namespace` (str): Type of objects to find

**Returns:**

List of `(object_namespace, object_id)` tuples.

**Example:**

```python path=null start=null
from parquetframe.permissions import list_objects

# Find all documents with any editors
documents_with_editors = list_objects(
    store=store,
    relation="editor",
    object_namespace="document"
)

print(f"Found {len(documents_with_editors)} documents with editors")
```

### list_subjects()

```python
def list_subjects(
    store: TupleStore,
    relation: str,
    object_namespace: str,
    object_id: str,
    subject_namespace: str
) -> list[tuple[str, str]]
```

Finds all subjects with a specific relation to an object.

**Parameters:**

- `store` (TupleStore): Permission store to query
- `relation` (str): Relation to check
- `object_namespace` (str): Type of object
- `object_id` (str): Object identifier
- `subject_namespace` (str): Type of subjects to find

**Returns:**

List of `(subject_namespace, subject_id)` tuples.

**Example:**

```python path=null start=null
from parquetframe.permissions import list_subjects

# Find all users who can edit a document
editors = list_subjects(
    store=store,
    relation="editor",
    object_namespace="document",
    object_id="doc1",
    subject_namespace="user"
)

for namespace, user_id in editors:
    print(f"User {user_id} can edit the document")
```

## PermissionManager

Higher-level permission management for applications.

### __init__()

```python path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/permissions.py start=46
def __init__(self, storage_path: str = "./kanban_data/permissions"):
    """
    Initialize the permission manager.

    Args:
        storage_path: Path to store permission tuples
    """
    self.store = TupleStore()
    self.storage_path = storage_path
```

### grant_permission()

```python
def grant_permission(
    user_id: str,
    resource_type: str,
    resource_id: str,
    relation: str
) -> None
```

Grants a permission to a user.

**Example:**

```python path=null start=null
perm_mgr = PermissionManager()

# Grant editor access
perm_mgr.grant_permission(
    user_id="alice",
    resource_type="document",
    resource_id="doc1",
    relation="editor"
)
```

### revoke_permission()

```python
def revoke_permission(
    user_id: str,
    resource_type: str,
    resource_id: str,
    relation: str
) -> None
```

Revokes a permission from a user.

**Example:**

```python path=null start=null
# Revoke editor access
perm_mgr.revoke_permission(
    user_id="alice",
    resource_type="document",
    resource_id="doc1",
    relation="editor"
)
```

### check_permission()

```python
def check_permission(
    user_id: str,
    resource_type: str,
    resource_id: str,
    relation: str,
    allow_indirect: bool = True
) -> bool
```

Checks if a user has a permission.

**Example:**

```python path=null start=null
can_edit = perm_mgr.check_permission(
    user_id="alice",
    resource_type="document",
    resource_id="doc1",
    relation="editor"
)

if can_edit:
    # Allow editing
    pass
```

## Permission Patterns

### Permission Inheritance

Grant access that cascades down a hierarchy.

**Example from Todo/Kanban:**

```python path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/permissions.py start=254
def grant_board_access(
    self,
    user_id: str,
    board_id: str,
    role: str,
) -> None:
    """
    Grant board-level access to a user.

    This automatically propagates permissions to all lists and tasks in the board.
    """
    if role not in ["owner", "editor", "viewer"]:
        raise ValueError(f"Invalid role: {role}. Must be owner, editor, or viewer")

    self.grant_permission(user_id, "board", board_id, role)
```

### Role Hierarchy

Implement role-based access with inheritance (owner > editor > viewer).

**Example:**

```python path=null start=null
def check_board_access(self, user_id: str, board_id: str, required_role: str = "viewer") -> bool:
    # Check role hierarchy
    if required_role == "viewer":
        return (
            self.check_permission(user_id, "board", board_id, "owner")
            or self.check_permission(user_id, "board", board_id, "editor")
            or self.check_permission(user_id, "board", board_id, "viewer")
        )
    elif required_role == "editor":
        return (
            self.check_permission(user_id, "board", board_id, "owner")
            or self.check_permission(user_id, "board", board_id, "editor")
        )
    elif required_role == "owner":
        return self.check_permission(user_id, "board", board_id, "owner")
```

### Group Permissions

Grant permissions through group membership.

**Example:**

```python path=null start=null
# Add user to group
store.add_tuple(RelationTuple("group", "engineering", "member", "user", "alice"))

# Grant group access to resource
store.add_tuple(RelationTuple("document", "doc1", "viewer", "group", "engineering"))

# Check if alice has access (through group membership)
can_view = check(store, "user", "alice", "viewer", "document", "doc1")
# Returns True via graph traversal
```

## Best Practices

### 1. Use Permission Manager

Prefer the higher-level `PermissionManager` over direct tuple manipulation.

```python path=null start=null
# Good: Using PermissionManager
perm_mgr = PermissionManager()
perm_mgr.grant_board_access("alice", "board1", "editor")

# Avoid: Direct tuple manipulation
store.add_tuple(RelationTuple("board", "board1", "editor", "user", "alice"))
```

### 2. Implement Permission Inheritance

Design hierarchical permissions for better organization.

```python path=null start=null
# Grant board access (inherits to lists and tasks)
perm_mgr.grant_board_access("alice", "board1", "owner")
perm_mgr.inherit_board_permissions("board1", "list1")
perm_mgr.inherit_list_permissions("list1", "task1")
```

### 3. Use Role Hierarchies

Implement roles with built-in hierarchy (owner > editor > viewer).

```python path=null start=null
# Check with minimum required role
can_edit = perm_mgr.check_board_access(
    user_id="alice",
    board_id="board1",
    required_role="editor"  # Passes if owner or editor
)
```

### 4. Persist Permissions

Save and load permission state for production use.

```python path=null start=null
# Save permissions
perm_mgr.save("permissions.parquet")

# Load permissions
perm_mgr.load("permissions.parquet")
```

## See Also

- **[Permissions Overview](../permissions/index.md)** - Complete permissions system guide
- **[Todo/Kanban Walkthrough](../documentation-examples/tutorials.md)** - Real-world permissions example
- **[CLI Reference](../permissions/cli-reference.md)** - Command-line permission management
