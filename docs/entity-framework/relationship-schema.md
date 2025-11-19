# Relationship Log Schema

ParquetFrame's Entity Framework uses a **foreign key pattern** combined with relationship metadata to model connections between entities. This document explains how relationships are stored and queried.

## Overview

Unlike traditional graph databases that maintain a separate edge list, ParquetFrame stores relationships through:

1. **Foreign Key Columns**: Stored directly in entity Parquet files
2. **Relationship Metadata**: Registered in-memory via `@rel` decorator
3. **On-Demand Resolution**: Relationships are traversed at query time using foreign key lookups

This approach provides the benefits of relational modeling while enabling GraphAr-compliant graph exports when needed.

---

## Relationship Storage Pattern

### Forward Relationships (Many-to-One)

A child entity stores a foreign key reference to its parent.

**Example: Post → User**

```python
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str
    email: str

@entity(storage_path="./data/posts", primary_key="post_id")
@dataclass
class Post:
    post_id: str
    title: str
    author_id: str  # Foreign key column

    @rel("User", foreign_key="author_id")
    def author(self):
        """Navigate to parent User"""
        pass
```

**Storage Schema:**

`./data/posts/*.parquet`:
| post_id | title | author_id |
|---------|-------|-----------|
| p1 | "Hello" | u1 |
| p2 | "World" | u1 |
| p3 | "Test" | u2 |

`./data/users/*.parquet`:
| user_id | username | email |
|---------|----------|-------|
| u1 | "alice" | "alice@example.com" |
| u2 | "bob" | "bob@example.com" |

### Reverse Relationships (One-to-Many)

A parent entity can navigate to all children that reference it.

```python
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str

    @rel("Post", foreign_key="author_id", reverse=True)
    def posts(self):
        """Navigate to child Posts"""
        pass
```

**Query Pattern:**
- Reverse relationships scan the child entity's parquet files
- Filter for rows where `author_id == user.user_id`
- Return list of matching Post instances

---

## Relationship Metadata Schema

When entities are decorated with `@rel`, ParquetFrame registers metadata:

```python
# Internal metadata structure
metadata.relationships = {
    "author": {
        "target": "User",          # Target entity class name
        "foreign_key": "author_id", # FK column in source entity
        "reverse": False            # Forward relationship
    },
    "posts": {
        "target": "Post",
        "foreign_key": "author_id",
        "reverse": True             # Reverse relationship
    }
}
```

This metadata is stored in-memory and used for:
- **Validation**: Ensuring foreign keys reference valid entities
- **Resolution**: Loading related entities on demand
- **GraphAr Export**: Converting to edge lists for graph analysis

---

## Many-to-Many Relationships

ParquetFrame uses an **intermediate entity** (association table) pattern for many-to-many.

**Example: Users ↔ Groups**

```python
@entity(storage_path="./data/users", primary_key="id")
@dataclass
class User:
    id: str
    name: str

@entity(storage_path="./data/groups", primary_key="id")
@dataclass
class Group:
    id: str
    name: str

@entity(storage_path="./data/memberships", primary_key="id")
@dataclass
class Membership:
    id: str
    user_id: str = rel("User", "id")
    group_id: str = rel("Group", "id")
    role: str = "member"  # Association metadata
```

**Storage:**

`./data/memberships/*.parquet`:
| id | user_id | group_id | role |
|----|---------|----------|------|
| m1 | u1 | g1 | admin |
| m2 | u1 | g2 | member |
| m3 | u2 | g1 | member |

**Query Pattern:**
```python
# Get user's groups
user = User.find("u1")
memberships = Membership.find_by(user_id=user.id)
groups = [Group.find(m.group_id) for m in memberships]
```

---

## Schema Specification

### Foreign Key Column Schema

Foreign key columns are stored as regular **string** fields in entity Parquet files:

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `{fk_name}` | `string` (UTF8) | Foreign key value | Must reference valid primary key in target entity |

**Example:**
- `author_id: string` in Post entity
- References `user_id: string` in User entity

### Validation Rules

1. **Type Consistency**: FK column type must match target entity's PK type
2. **Referential Integrity** (optional): FK values should exist in target entity
3. **Nullability**: FKs are nullable by default unless explicitly required

---

## GraphAr Export (Edge List Format)

When exporting to GraphAr format, relationships are materialized as edge lists:

**Edge List Schema:**

`./graph/edges/{edge_type}/*.parquet`:
| src | dst | edge_type | properties |
|-----|-----|-----------|----------|
| u1 | p1 | authored | {} |
| u1 | p2 | authored | {} |
| u2 | p3 | authored | {} |

**Conversion Rules:**
- **src**: Source vertex ID (parent entity PK)
- **dst**: Destination vertex ID (child entity PK or FK value)
- **edge_type**: Relationship name from `@rel` decorator
- **properties**: Additional edge attributes (e.g., timestamp, weight)

---

## Performance Considerations

### Index Strategy

```python
# Entities are stored as Parquet files with columnar layout
# Query performance depends on file organization:

# Good: Few large files with column pruning
./data/posts/
  └── posts.parquet  # 10M rows, author_id column indexed

# Less optimal: Many small files
./data/posts/
  ├── post_000001.parquet  # 100 rows
  ├── post_000002.parquet  # 100 rows
  └── ...  # 100,000 files
```

**Recommendations:**
1. **Batch Saves**: Save entities in groups to create larger Parquet files
2. **Column Projection**: Only load FK columns when traversing relationships
3. **Filter Pushdown**: Use Parquet predicate pushdown for FK filtering
4. **Partitioning**: Partition large entity tables by FK value for locality

### Query Optimization

```python
# Efficient: Single scan with column projection
posts = Post.find_by(author_id="u1")  # Filter in Parquet

# Less efficient: Load all, filter in Python
all_posts = Post.find_all()
.user_posts = [p for p in all_posts if p.author_id == "u1"]
```

---

## Advanced Patterns

### Composite Foreign Keys

For entities with composite primary keys:

```python
@entity(storage_path="./data/order_items", primary_key="item_id")
@dataclass
class OrderItem:
    item_id: str
    order_id: str
    product_id: str
    warehouse_id: str
    quantity: int

    # Composite FK to Product (product_id + warehouse_id)
    @rel("Product", foreign_key=["product_id", "warehouse_id"])
    def product(self):
        pass
```

### Self-Referential Relationships

Entities can reference themselves:

```python
@entity(storage_path="./data/employees", primary_key="employee_id")
@dataclass
class Employee:
    employee_id: str
    name: str
    manager_id: str | None

    @rel("Employee", foreign_key="manager_id")
    def manager(self):
        """Navigate to manager"""
        pass

    @rel("Employee", foreign_key="manager_id", reverse=True)
    def direct_reports(self):
        """Navigate to subordinates"""
        pass
```

---

## Comparison with Traditional Graph Databases

| Aspect | ParquetFrame (FK Pattern) | Graph DB (Edge List) |
|--------|---------------------------|----------------------|
| **Storage** | FKs in entity files | Separate edge table |
| **Writes** | Single entity write | Entity + edge writes |
| **Reads** | Scan + filter on FK | Index lookup on edge |
| **Traversals** | Multiple scans | Native graph traversal |
| **Analytics** | Excellent (columnar) | Good (specialized) |
| **Use Case** | OLAP, batch analytics | OLTP, graph queries |

**When to Use Each:**
- **ParquetFrame**: Analytics-heavy workflows, batch processing, reporting
- **Graph DB**: Real-time traversals, recommendation engines, fraud detection

---

## Migration to GraphAr

For graph-specific workloads, convert to GraphAr:

```python
from parquetframe.graph import export_to_graphar

# Export entities and relationships to GraphAr format
export_to_graphar(
    entities=[User, Post],
    output_path="./graph_export",
    include_relationships=True
)
```

This creates:
- `vertices/users/*.parquet`
- `vertices/posts/*.parquet`
- `edges/authored/*.parquet`

---

## References

- Implementation: [`src/parquetframe/entity/decorators.py`](file:///Users/temp/Documents/Projects/parquetframe/src/parquetframe/entity/decorators.py)
- Entity Store: [`src/parquetframe/entity/entity_store.py`](file:///Users/temp/Documents/Projects/parquetframe/src/parquetframe/entity/entity_store.py)
- Relationship Management: [`src/parquetframe/entity/relationship.py`](file:///Users/temp/Documents/Projects/parquetframe/src/parquetframe/entity/relationship.py)
- Entity Framework Guide: [docs/entity-framework/index.md](file:///Users/temp/Documents/Projects/parquetframe/docs/entity-framework/index.md)
- Many-to-Many Patterns: [docs/entity-framework/advanced-examples.md](file:///Users/temp/Documents/Projects/parquetframe/docs/entity-framework/advanced-examples.md)
