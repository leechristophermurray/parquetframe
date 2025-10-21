# GraphAr Permissions Schema Specification

**Version**: 1.0
**Date**: 2025-10-21
**Status**: Draft
**Purpose**: Define GraphAr-compliant storage format for Zanzibar-style permissions

---

## Overview

This specification defines how Zanzibar-style permission relation tuples are stored as a GraphAr-compliant graph structure. The permissions graph represents access control relationships as edges between subject and object vertices.

### Key Concepts

- **Subjects**: Entities that can have permissions (users, groups, service accounts)
- **Objects**: Resources that can be accessed (boards, lists, tasks, documents)
- **Relations**: Permission types (owner, editor, viewer, etc.)
- **Tuples**: Edges representing "subject has relation to object"

---

## Directory Structure

```text
permissions_graph/
├── _metadata.yaml           # Graph-level metadata
├── _schema.yaml             # Vertex and edge schemas
├── vertices/                # Subject and object vertices
│   ├── user/               # User subjects
│   │   └── part0.parquet
│   ├── group/              # Group subjects (optional)
│   │   └── part0.parquet
│   ├── board/              # Board objects
│   │   └── part0.parquet
│   ├── list/               # List objects
│   │   └── part0.parquet
│   └── task/               # Task objects
│       └── part0.parquet
└── edges/                   # Permission relationships
    ├── owner/              # Owner relations
    │   └── part0.parquet
    ├── editor/             # Editor relations
    │   └── part0.parquet
    └── viewer/             # Viewer relations
        └── part0.parquet
```

---

## Metadata File Specification

### `_metadata.yaml`

```yaml
name: "permissions"
version: "1.0"
directed: true
description: "Zanzibar-style permission graph with relation-based access control"
creator: "ParquetFrame Permissions System"
created_at: "2025-10-21T00:00:00Z"
```

**Fields**:

- `name` (required): Graph identifier, always "permissions"
- `version` (required): Schema version (semver)
- `directed` (required): Always `true` for permissions
- `description` (optional): Human-readable description
- `creator` (optional): System that created the graph
- `created_at` (optional): ISO 8601 timestamp

---

## Schema File Specification

### `_schema.yaml`

```yaml
version: "1.0"

vertices:
  # Subject vertex types
  user:
    properties:
      id:
        type: "string"
        primary: true
        description: "Unique user identifier"
      created_at:
        type: "timestamp"
        nullable: true

  group:
    properties:
      id:
        type: "string"
        primary: true
        description: "Unique group identifier"
      created_at:
        type: "timestamp"
        nullable: true

  # Object vertex types
  board:
    properties:
      id:
        type: "string"
        primary: true
        description: "Unique board identifier"

  list:
    properties:
      id:
        type: "string"
        primary: true
        description: "Unique list identifier"

  task:
    properties:
      id:
        type: "string"
        primary: true
        description: "Unique task identifier"

edges:
  # Permission relation types
  owner:
    properties:
      src:
        type: "string"
        source: true
        description: "Subject ID (user or group)"
      dst:
        type: "string"
        target: true
        description: "Object ID (board, list, or task)"
      subject_namespace:
        type: "string"
        description: "Type of subject (user, group)"
      object_namespace:
        type: "string"
        description: "Type of object (board, list, task)"
      created_at:
        type: "timestamp"
        nullable: true
        description: "When permission was granted"
      granted_by:
        type: "string"
        nullable: true
        description: "User ID who granted the permission"

  editor:
    properties:
      src:
        type: "string"
        source: true
        description: "Subject ID (user or group)"
      dst:
        type: "string"
        target: true
        description: "Object ID (board, list, or task)"
      subject_namespace:
        type: "string"
        description: "Type of subject (user, group)"
      object_namespace:
        type: "string"
        description: "Type of object (board, list, task)"
      created_at:
        type: "timestamp"
        nullable: true
      granted_by:
        type: "string"
        nullable: true

  viewer:
    properties:
      src:
        type: "string"
        source: true
        description: "Subject ID (user or group)"
      dst:
        type: "string"
        target: true
        description: "Object ID (board, list, or task)"
      subject_namespace:
        type: "string"
        description: "Type of subject (user, group)"
      object_namespace:
        type: "string"
        description: "Type of object (board, list, task)"
      created_at:
        type: "timestamp"
        nullable: true
      granted_by:
        type: "string"
        nullable: true
```

---

## Data Type Mapping

### Parquet Schema

| YAML Type | Parquet Type | Notes |
|-----------|--------------|-------|
| `string` | `STRING` | UTF-8 encoded |
| `int32` | `INT32` | Signed 32-bit integer |
| `int64` | `INT64` | Signed 64-bit integer |
| `float64` | `DOUBLE` | IEEE 754 double precision |
| `boolean` | `BOOLEAN` | True/false |
| `timestamp` | `TIMESTAMP_MILLIS` | Milliseconds since epoch |

---

## Permission Tuple Representation

### Zanzibar Tuple Format

```text
RelationTuple(
    namespace="board",
    object_id="board_123",
    relation="owner",
    subject_namespace="user",
    subject_id="alice"
)
```

### GraphAr Representation

**As an edge** in `edges/owner/part0.parquet`:

| src | dst | subject_namespace | object_namespace | created_at | granted_by |
|-----|-----|-------------------|------------------|------------|------------|
| alice | board_123 | user | board | 2025-10-21T10:00:00Z | admin |

**Vertex entries**:

- `vertices/user/part0.parquet`: `{id: "alice", created_at: ...}`
- `vertices/board/part0.parquet`: `{id: "board_123"}`

---

## Relation Types

### Standard Relations

| Relation | Description | Inherits From |
|----------|-------------|---------------|
| `owner` | Full control, can delete | `editor`, `viewer` |
| `editor` | Can modify content | `viewer` |
| `viewer` | Read-only access | - |

### Custom Relations (Extensible)

Applications can define custom relations by adding edge types:

```yaml
edges:
  admin:
    properties: { ... }
  contributor:
    properties: { ... }
  guest:
    properties: { ... }
```

---

## Two-Graph Architecture

### Application Data Graph (`app_graph/`)

```text
app_graph/
├── _metadata.yaml
├── _schema.yaml
├── vertices/
│   ├── User/
│   ├── Board/
│   ├── TaskList/
│   └── Task/
└── edges/
    ├── owns/          # Ownership relationships
    ├── contains/      # Containment relationships
    └── assigned_to/   # Assignment relationships
```

**Purpose**: Business domain data and entity relationships

### Permissions Graph (`permissions_graph/`)

```text
permissions_graph/
├── _metadata.yaml
├── _schema.yaml
├── vertices/          # Subjects and objects
│   ├── user/
│   ├── board/
│   ├── list/
│   └── task/
└── edges/             # Permission tuples
    ├── owner/
    ├── editor/
    └── viewer/
```

**Purpose**: Access control and authorization

### Separation Rationale

1. **Concern Separation**: Business logic vs authorization
2. **Independent Evolution**: Schema changes don't affect each other
3. **Performance**: Optimize queries for different access patterns
4. **Security**: Different backup/replication strategies
5. **Compliance**: Easier to audit and regulate permissions

---

## Usage Examples

### Creating Permission Tuples

```python
from parquetframe.permissions import TupleStore, RelationTuple

# Create tuple store
store = TupleStore()

# Add permission tuples
store.add_tuple(RelationTuple(
    namespace="board",
    object_id="board_123",
    relation="owner",
    subject_namespace="user",
    subject_id="alice"
))

# Save as GraphAr structure
store.save("./permissions_graph")
```

**Result**:

- Creates `permissions_graph/_metadata.yaml`
- Creates `permissions_graph/_schema.yaml`
- Saves vertices to `permissions_graph/vertices/`
- Saves edges to `permissions_graph/edges/owner/part0.parquet`

### Loading Permission Graph

```python
import parquetframe as pf

# Load with GraphAr reader
perm_graph = pf.read_graph("./permissions_graph")

# Query permissions using graph algorithms
# Find all users who can access a board
board_viewers = perm_graph.edges.query("dst == 'board_123'")
```

### Checking Permissions

```python
from parquetframe.permissions import check

# Check if user has permission
has_access = check(
    store=store,
    subject_namespace="user",
    subject_id="alice",
    relation="owner",
    object_namespace="board",
    object_id="board_123"
)
```

---

## Migration from Legacy Format

### Legacy Format (Single File)

```text
permissions.parquet
- namespace | object_id | relation | subject_namespace | subject_id
```

### Migration Script

```python
from pathlib import Path
import pandas as pd
from parquetframe.permissions import TupleStore, RelationTuple

# Read legacy format
legacy_df = pd.read_parquet("permissions.parquet")

# Create new tuple store
store = TupleStore()

# Convert to relation tuples
for _, row in legacy_df.iterrows():
    store.add_tuple(RelationTuple(
        namespace=row["namespace"],
        object_id=row["object_id"],
        relation=row["relation"],
        subject_namespace=row["subject_namespace"],
        subject_id=row["subject_id"]
    ))

# Save as GraphAr structure
store.save("./permissions_graph")
```

---

## Validation Rules

### Structure Validation

1. **Required Files**:
   - `_metadata.yaml` must exist
   - `_schema.yaml` must exist
   - `vertices/` directory must exist
   - `edges/` directory must exist

2. **Vertex Requirements**:
   - Each vertex type must have an `id` property marked as `primary: true`
   - Vertex IDs must be unique within their namespace

3. **Edge Requirements**:
   - Edges must have `src` and `dst` properties
   - `src` and `dst` must reference valid vertex IDs
   - `subject_namespace` and `object_namespace` must match vertex types

### Data Validation

```python
from parquetframe.permissions.validation import validate_permissions_graph

# Validate GraphAr structure
is_valid = validate_permissions_graph("./permissions_graph")
```

**Checks**:

- All subject vertices exist
- All object vertices exist
- No dangling edges
- Schema compliance
- Data type correctness

---

## Performance Considerations

### Partitioning Strategy

For large permission datasets, partition by relation type:

```text
edges/
├── owner/
│   ├── part0.parquet  # First 1M edges
│   ├── part1.parquet  # Next 1M edges
│   └── ...
├── editor/
│   ├── part0.parquet
│   └── ...
└── viewer/
    ├── part0.parquet
    └── ...
```

### Indexing

Use Parquet row groups for efficient filtering:

```python
# Write with optimized row groups
store.save("./permissions_graph", row_group_size=100_000)
```

### Compression

Recommended compression: SNAPPY or ZSTD

```python
store.save("./permissions_graph", compression="snappy")
```

---

## Compatibility

### Apache GraphAr Compliance

This specification is fully compatible with [Apache GraphAr v1.0](https://graphar.apache.org/).

**Compliance checklist**:

- ✅ Directory structure follows GraphAr spec
- ✅ Metadata YAML format compliant
- ✅ Schema YAML format compliant
- ✅ Parquet file format compliant
- ✅ Vertex/edge separation compliant

### Tool Support

Compatible with:

- ParquetFrame graph reader (`pf.read_graph()`)
- Apache Arrow tools
- DuckDB for SQL queries
- NetworkX for graph analysis (via conversion)
- Graph visualization tools

---

## References

- [Apache GraphAr Specification](https://graphar.apache.org/)
- [Zanzibar: Google's Consistent, Global Authorization System](https://research.google/pubs/pub48190/)
- [Apache Parquet Documentation](https://parquet.apache.org/docs/)

---

## Changelog

### Version 1.0 (2025-10-21)

- Initial specification
- Define core vertex and edge schemas
- Document two-graph architecture
- Provide migration guide from legacy format

---

**Status**: Ready for implementation
**Next Steps**: Implement `TupleStore.save()` and `TupleStore.load()` with GraphAr format
