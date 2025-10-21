# GraphAr Permissions Schema Specification

**Version**: 1.0
**Date**: 2025-10-21
**Status**: Implemented
**Compliance**: Apache GraphAr v0.11.0

---

## Overview

This document specifies the GraphAr-compliant schema for storing Zanzibar-style permission tuples as a property graph. The schema enables permissions to be stored, queried, and analyzed using graph algorithms while maintaining full compatibility with the Apache GraphAr specification.

---

## Architecture

### Storage Model

Permissions are stored as a **directed property graph** with:

- **Vertices**: Subjects (users, groups) and Objects (resources)
- **Edges**: Relations (owner, editor, viewer, etc.)
- **Properties**: Metadata attached to vertices and edges

### Directory Structure

```
permissions_graph/
├── _metadata.yaml          # Graph-level metadata
├── _schema.yaml            # Vertex and edge schemas
├── vertices/               # Vertex data by type
│   ├── user/
│   │   └── part0.parquet
│   ├── group/
│   │   └── part0.parquet
│   ├── board/
│   │   └── part0.parquet
│   ├── list/
│   │   └── part0.parquet
│   └── task/
│       └── part0.parquet
└── edges/                  # Edge data by relation type
    ├── owner/
    │   └── part0.parquet
    ├── editor/
    │   └── part0.parquet
    └── viewer/
        └── part0.parquet
```

---

## Metadata File (`_metadata.yaml`)

### Required Fields

```yaml
name: string              # Graph name (e.g., "permissions")
version: string           # Schema version (e.g., "1.0")
directed: boolean         # Always true for permissions
description: string       # Human-readable description
creator: string           # System that created the graph
created_at: string        # ISO 8601 timestamp
```

### Example

```yaml
name: permissions
version: '1.0'
directed: true
description: Zanzibar-style permission graph with relation-based access control
creator: ParquetFrame Permissions System
created_at: '2025-10-21T16:58:59.899433Z'
```

---

## Schema File (`_schema.yaml`)

### Structure

```yaml
version: string
vertices:
  <vertex_type>:
    properties:
      <property_name>:
        type: string
        primary: boolean
        description: string
edges:
  <edge_type>:
    properties:
      <property_name>:
        type: string
        source: boolean
        target: boolean
        description: string
```

### Vertex Schemas

#### Subject Vertices (User, Group)

```yaml
user:
  properties:
    id:
      type: string
      primary: true
      description: Unique user identifier

group:
  properties:
    id:
      type: string
      primary: true
      description: Unique group identifier
```

#### Object Vertices (Resources)

```yaml
board:
  properties:
    id:
      type: string
      primary: true
      description: Unique board identifier

list:
  properties:
    id:
      type: string
      primary: true
      description: Unique list identifier

task:
  properties:
    id:
      type: string
      primary: true
      description: Unique task identifier
```

**Note**: Object vertex types are determined by the application domain. Additional resource types can be added as needed.

### Edge Schemas

#### Relation Edges

```yaml
owner:
  properties:
    src:
      type: string
      source: true
      description: Subject ID (user or group)
    dst:
      type: string
      target: true
      description: Object ID (resource)
    subject_namespace:
      type: string
      description: Type of subject (user, group)
    object_namespace:
      type: string
      description: Type of object (board, list, task)

editor:
  properties:
    src:
      type: string
      source: true
      description: Subject ID
    dst:
      type: string
      target: true
      description: Object ID
    subject_namespace:
      type: string
      description: Type of subject
    object_namespace:
      type: string
      description: Type of object

viewer:
  properties:
    src:
      type: string
      source: true
      description: Subject ID
    dst:
      type: string
      target: true
      description: Object ID
    subject_namespace:
      type: string
      description: Type of subject
    object_namespace:
      type: string
      description: Type of object
```

**Note**: Additional relation types can be added by creating new edge schemas.

---

## Data Format

### Vertex Parquet Files

**Location**: `vertices/<vertex_type>/part0.parquet`

**Schema**:
```
id: string (primary key)
```

**Example** (`vertices/user/part0.parquet`):
```
| id                    |
|-----------------------|
| user_alice_12345      |
| user_bob_67890        |
| user_charlie_11223    |
```

### Edge Parquet Files

**Location**: `edges/<relation_type>/part0.parquet`

**Schema**:
```
src: string (source vertex ID)
dst: string (target vertex ID)
subject_namespace: string
object_namespace: string
```

**Example** (`edges/owner/part0.parquet`):
```
| src               | dst             | subject_namespace | object_namespace |
|-------------------|-----------------|-------------------|------------------|
| user_alice_12345  | board_9876      | user              | board            |
| user_bob_67890    | board_5432      | user              | board            |
```

---

## Zanzibar Relation Tuple Mapping

### Original Tuple Format

```
namespace:object_id#relation@subject_namespace:subject_id
```

Example: `board:board_9876#owner@user:user_alice_12345`

### GraphAr Mapping

| Tuple Component      | GraphAr Representation |
|---------------------|------------------------|
| `subject_namespace` | Vertex type (subject)  |
| `subject_id`        | Vertex ID (src)        |
| `relation`          | Edge type              |
| `namespace`         | Vertex type (object)   |
| `object_id`         | Vertex ID (dst)        |

**Tuple**: `board:board_9876#owner@user:user_alice_12345`

**Graph Representation**:
- Subject vertex: `user/user_alice_12345`
- Object vertex: `board/board_9876`
- Edge: `owner` (src=user_alice_12345, dst=board_9876)

---

## Type System

### Supported Data Types

| GraphAr Type | Parquet Type | Description |
|--------------|--------------|-------------|
| `string`     | UTF8         | Variable-length text |
| `int32`      | INT32        | 32-bit integer |
| `int64`      | INT64        | 64-bit integer |
| `float`      | FLOAT        | 32-bit float |
| `double`     | DOUBLE       | 64-bit float |
| `bool`       | BOOLEAN      | Boolean value |
| `timestamp`  | TIMESTAMP_MILLIS | ISO 8601 timestamp |

**Primary Type**: `string` is used for all vertex IDs and edge endpoints to support flexible naming schemes.

---

## Constraints and Validation

### Vertex Constraints

1. **Unique IDs**: Each vertex ID must be unique within its type
2. **Non-empty IDs**: Vertex IDs cannot be empty strings
3. **No whitespace**: IDs cannot have leading/trailing whitespace

### Edge Constraints

1. **Valid References**: `src` and `dst` must reference existing vertices
2. **Non-empty Fields**: All edge fields must be non-empty
3. **Namespace Consistency**: `subject_namespace` must match `src` vertex type
4. **Object Consistency**: `object_namespace` must match `dst` vertex type

### File Constraints

1. **Parquet Format**: All data files must be valid Parquet files
2. **Schema Compliance**: Column names and types must match schema
3. **Directory Structure**: Must follow GraphAr conventions

---

## Query Patterns

### 1. Check Permission

**Question**: Does user X have relation Y on object Z?

**Graph Query**:
```
Find edge of type Y from vertex user/X to vertex object_type/Z
```

**Example**: Does `user_alice` have `owner` on `board_9876`?
```
Find edge: owner(src=user_alice, dst=board_9876)
```

### 2. List User Permissions

**Question**: What objects can user X access with relation Y?

**Graph Query**:
```
Find all edges of type Y from vertex user/X
Return all dst vertices
```

**Example**: What boards can `user_alice` own?
```
Find edges: owner(src=user_alice, dst=*)
```

### 3. List Resource Permissions

**Question**: Who has relation Y on object Z?

**Graph Query**:
```
Find all edges of type Y to vertex object_type/Z
Return all src vertices
```

**Example**: Who can edit `board_9876`?
```
Find edges: editor(src=*, dst=board_9876)
```

### 4. Transitive Permissions

**Question**: What permissions does user X have via group membership?

**Graph Query**:
```
1. Find all groups user X belongs to (member_of edges)
2. For each group, find all permissions (relation edges)
3. Union with direct user permissions
```

---

## Performance Characteristics

### Storage Efficiency

- **Columnar Format**: Parquet provides 2-10x compression vs row formats
- **Grouped Edges**: Edges grouped by relation type enable efficient filtering
- **Partitioning**: Can partition large graphs by date or resource type

### Query Performance

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Check permission | O(1) | Direct edge lookup |
| List user permissions | O(E_u) | Edges from user |
| List resource permissions | O(E_r) | Edges to resource |
| Transitive closure | O(V + E) | BFS/DFS traversal |

Where:
- E_u = edges from a specific user
- E_r = edges to a specific resource
- V = total vertices
- E = total edges

### Scalability

| Scale | Vertices | Edges | Performance |
|-------|----------|-------|-------------|
| Small | <10K | <100K | Sub-millisecond queries |
| Medium | 10K-1M | 100K-10M | Millisecond queries |
| Large | 1M-100M | 10M-1B | Second-range queries |
| X-Large | >100M | >1B | Requires partitioning |

---

## Extensions

### Custom Relations

Add new relation types by:

1. Adding edge schema to `_schema.yaml`
2. Creating edge directory: `edges/<relation_type>/`
3. Saving edges to `edges/<relation_type>/part0.parquet`

### Custom Attributes

Add properties to vertices or edges:

```yaml
user:
  properties:
    id:
      type: string
      primary: true
    email:
      type: string
      description: User email address
    created_at:
      type: timestamp
      description: Account creation time
```

### Hierarchical Resources

Model resource hierarchies with additional edges:

```yaml
contains:
  properties:
    src:
      type: string
      source: true
      description: Parent resource
    dst:
      type: string
      target: true
      description: Child resource
```

---

## Migration from Legacy Format

### Old Format (Single File)

```
permissions.parquet:
  - namespace: string
  - object_id: string
  - relation: string
  - subject_namespace: string
  - subject_id: string
```

### Migration Steps

1. **Load**: Read legacy Parquet file
2. **Extract Vertices**:
   - Unique subjects → `vertices/<subject_type>/`
   - Unique objects → `vertices/<object_type>/`
3. **Group Edges**: Group by relation → `edges/<relation>/`
4. **Generate Metadata**: Create `_metadata.yaml` and `_schema.yaml`
5. **Save**: Write GraphAr structure

**Migration Script**: See `scripts/migrate_permissions_to_graphar.py`

---

## Compliance Checklist

### Apache GraphAr v0.11.0

- [x] `_metadata.yaml` with required fields
- [x] `_schema.yaml` with vertex and edge schemas
- [x] `vertices/` directory with typed subdirectories
- [x] `edges/` directory with typed subdirectories
- [x] Parquet files with correct schemas
- [x] Property graphs with typed vertices and edges
- [x] Directed graph support
- [x] UTF-8 string IDs
- [x] Columnar storage format

---

## References

1. **Apache GraphAr Specification**: https://graphar.apache.org/
2. **Zanzibar Paper**: "Zanzibar: Google's Consistent, Global Authorization System" (USENIX ATC 2019)
3. **ParquetFrame Documentation**: `docs/graph/index.md`
4. **Implementation**: `src/parquetframe/permissions/core.py`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-21 | Initial specification |

---

**Maintainer**: ParquetFrame Development Team
**License**: Apache License 2.0
**Status**: Production Ready
