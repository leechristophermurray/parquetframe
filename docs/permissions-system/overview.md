# Permissions System

ParquetFrame includes a comprehensive Zanzibar-style permissions system for implementing relation-based access control (ReBAC) in your applications. This system provides fine-grained, scalable permission management using graph-based algorithms for efficient querying and expansion.

## Overview

The permissions system is built on the **relation tuple model** where permissions are expressed as:

```
subject_namespace:subject_id has relation to object_namespace:object_id
```

For example:
- `user:alice` has `viewer` relation to `doc:doc1`
- `group:engineering` has `editor` relation to `folder:shared`
- `user:bob` has `owner` relation to `project:webapp`

## Key Features

✅ **Zanzibar Compatibility**: Implements Google's Zanzibar relation tuple model
✅ **Graph-Based Traversal**: Uses ParquetFrame's graph algorithms for transitive permissions
✅ **Efficient Storage**: ParquetFrame backend for columnar storage and fast queries
✅ **Standard Models**: Pre-built permission models (Google Drive, GitHub, Cloud IAM)
✅ **CLI Tools**: Rich terminal commands for permission management
✅ **Batch Operations**: Efficient bulk permission checking and expansion

## Quick Start

### Basic Permission Checking

```python
import parquetframe as pf
from parquetframe.permissions import RelationTuple, TupleStore, check

# Create a tuple store
store = TupleStore()

# Add some permissions
store.add_tuple(RelationTuple("doc", "doc1", "viewer", "user", "alice"))
store.add_tuple(RelationTuple("doc", "doc1", "owner", "user", "bob"))

# Check permissions
can_alice_view = check(store, "user", "alice", "viewer", "doc", "doc1")  # True
can_alice_edit = check(store, "user", "alice", "editor", "doc", "doc1")  # False (no editor permission)
```

### Using Standard Permission Models

```python
from parquetframe.permissions import StandardModels, ModelTupleStore

# Use Google Drive-style permissions with inheritance
model = StandardModels.google_drive()
store = ModelTupleStore(model, expand_inheritance=True)

# Add an owner permission (automatically grants editor, commenter, viewer)
store.add_tuple(RelationTuple("doc", "doc1", "owner", "user", "alice"))

# Alice now has all inherited permissions
can_view = check(store, "user", "alice", "viewer", "doc", "doc1")  # True (inherited)
can_edit = check(store, "user", "alice", "editor", "doc", "doc1")  # True (inherited)
```

### CLI Usage

```bash
# Check permissions
pframe permissions check user:alice viewer doc:doc1 --store permissions.parquet

# Find all documents a user can access
pframe permissions expand user:alice viewer --namespace doc --store permissions.parquet

# Add permissions with inheritance
pframe permissions add user:bob owner doc:doc2 --store permissions.parquet --model google_drive

# List all objects with a specific relation
pframe permissions list-objects editor --namespace doc --store permissions.parquet
```

## Core Concepts

### Relation Tuples

The fundamental unit of permissions is a **relation tuple** with five components:

- **Object Namespace**: Type of resource (e.g., `doc`, `folder`, `project`)
- **Object ID**: Specific resource identifier (e.g., `doc1`, `shared`, `webapp`)
- **Relation**: Type of access (e.g., `viewer`, `editor`, `owner`)
- **Subject Namespace**: Type of actor (e.g., `user`, `group`, `service`)
- **Subject ID**: Specific actor identifier (e.g., `alice`, `engineering`, `api-service`)

### Permission Inheritance

Standard permission models support **inheritance hierarchies** where higher-level permissions automatically grant lower-level ones:

```
owner → editor → commenter → viewer
admin → maintain → write → triage → read
```

### Transitive Permissions

The system supports **indirect permissions** through graph traversal:

```python
# Group membership gives indirect access
store.add_tuple(RelationTuple("group", "engineering", "member", "user", "alice"))
store.add_tuple(RelationTuple("doc", "doc1", "editor", "group", "engineering"))

# Alice gets editor access through group membership
can_edit = check(store, "user", "alice", "editor", "doc", "doc1")  # True (via graph traversal)
```

## Documentation Sections

### 📖 [Getting Started Guide](getting-started.md)
Step-by-step tutorial for setting up permissions in your application

### 🏗️ [Permission Models](models.md)
Overview of standard models and creating custom permission hierarchies

### 🔧 [API Reference](api-reference.md)
Complete API documentation for all classes and functions

### 💻 [CLI Reference](cli-reference.md)
Detailed guide to command-line permission management tools

### 🚀 [Performance Guide](../analytics-statistics/benchmarking.md)
Best practices for scaling permissions to large datasets

### 🎯 [Use Cases & Examples](../documentation-examples/examples.md)
Real-world examples and implementation patterns

## Architecture

The permissions system is built on ParquetFrame's graph processing engine:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Commands  │    │  Permission APIs │    │  Standard Models│
│                 │    │                  │    │                 │
│ • check         │    │ • check()        │    │ • Google Drive  │
│ • expand        │───▶│ • expand()       │───▶│ • GitHub Org    │
│ • list-objects  │    │ • list_objects() │    │ • Cloud IAM     │
│ • add           │    │ • list_subjects()│    │ • Simple RBAC   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   TupleStore     │    │   Graph Engine  │
                       │                  │    │                 │
                       │ • ParquetFrame   │───▶│ • BFS Traversal │
                       │   Backend        │    │ • Shortest Path │
                       │ • CRUD Ops       │    │ • CSR/CSC Index │
                       │ • Persistence    │    │ • Transitive    │
                       └──────────────────┘    └─────────────────┘
```

## Performance Characteristics

- **Permission Checks**: Sub-millisecond for typical datasets
- **Storage**: Columnar Parquet format for efficient storage and queries
- **Traversal**: O(V+E) graph algorithms for transitive permissions
- **Batch Operations**: Optimized for bulk permission expansion and UI generation
- **Scalability**: Tested with millions of relation tuples

## Integration Examples

### Web Application Middleware

```python
from parquetframe.permissions import TupleStore, check

# Load permissions at startup
permissions = TupleStore.load("app_permissions.parquet")

def check_permission(user_id, action, resource):
    """Middleware function for request authorization"""
    return check(
        store=permissions,
        subject_namespace="user",
        subject_id=user_id,
        relation=action,
        object_namespace="resource",
        object_id=resource,
        allow_indirect=True
    )

# Usage in Flask/FastAPI
@app.route("/api/documents/<doc_id>")
def get_document(doc_id):
    if not check_permission(current_user.id, "viewer", doc_id):
        abort(403)
    return get_document_data(doc_id)
```

### Microservices Authorization

```python
from parquetframe.permissions import expand

def get_user_accessible_documents(user_id):
    """Get all documents a user can access for UI generation"""
    accessible = expand(
        store=permissions,
        subject_namespace="user",
        subject_id=user_id,
        relation="viewer",
        object_namespace="doc"
    )
    return [doc_id for _, doc_id in accessible]
```

## Next Steps

1. **[Getting Started](getting-started.md)**: Set up your first permission system
2. **[Models Guide](models.md)**: Choose or create the right permission model
3. **[CLI Tutorial](cli-reference.md)**: Learn the command-line tools
4. **[API Deep Dive](api-reference.md)**: Master the programmatic interface

---

**Need Help?** Check out the [examples](../documentation-examples/examples.md) for common patterns or the [performance guide](../analytics-statistics/benchmarking.md) for optimization tips.
