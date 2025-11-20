# Relationship Management

ParquetFrame's Entity Framework uses a **relationship log** (edge list) to track connections between entities. This document describes the schema, operations, and best practices.

## Relationship Log Schema

All relationships are stored in a Parquet-based edge list with the following schema:

### Core Schema

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `source_id` | string | ID of the source entity | ✓ |
| `target_id` | string | ID of the target entity | ✓ |
| `relation_type` | string | Type of relationship (e.g., "OWNS", "MEMBER_OF") | ✓ |
| `timestamp` | datetime64[ns] | When the relationship was created | ✓ |
| `metadata` | string (JSON) | Additional relationship properties | ✗ |

### Example Data

```python
import pandas as pd

relationships = pd.DataFrame({
    "source_id": ["user_123", "user_123", "user_456"],
    "target_id": ["order_789", "group_abc", "order_101"],
    "relation_type": ["PURCHASED", "MEMBER_OF", "PURCHASED"],
    "timestamp": pd.to_datetime([
        "2024-01-15 10:30:00",
        "2024-01-16 14:20:00",
        "2024-01-17 09:15:00"
    ]),
    "metadata": [
        '{"amount": 99.99, "currency": "USD"}',
        '{"role": "admin"}',
        '{"amount": 149.50, "currency": "USD"}'
    ]
})
```

## Creating Relationships

### Basic Relationship

```python
from parquetframe.entity import Entity, add_relationship

# Define entities
@Entity(name="User")
class User:
    id: str
    name: str

@Entity(name="Order")
class Order:
    id: str
    total: float

# Create relationship
user = User(id="user_123", name="Alice")
order = Order(id="order_789", total=99.99)

add_relationship(
    source=user,
    target=order,
    relation_type="PURCHASED",
    metadata={"payment_method": "credit_card"}
)
```

### Bulk Relationship Creation

```python
from parquetframe.entity import bulk_add_relationships

relationships = [
    {"source_id": "user_123", "target_id": "order_789", "relation_type": "PURCHASED"},
    {"source_id": "user_123", "target_id": "order_790", "relation_type": "PURCHASED"},
    {"source_id": "user_456", "target_id": "order_791", "relation_type": "PURCHASED"},
]

bulk_add_relationships(relationships)
```

## Querying Relationships

### Find All Relationships

```python
from parquetframe.entity import get_relationships

# Get all relationships from a source entity
purchases = get_relationships(
    source_id="user_123",
    relation_type="PURCHASED"
)

# Get all relationships to a target entity
buyers = get_relationships(
    target_id="order_789",
    relation_type="PURCHASED"
)
```

### Filter by Time Range

```python
from datetime import datetime, timedelta

# Get recent purchases
recent_date = datetime.now() - timedelta(days=30)

recent_purchases = get_relationships(
    source_id="user_123",
    relation_type="PURCHASED",
    since=recent_date
)
```

### Complex Queries with DataFrames

```python
import parquetframe as pf

# Load relationship log as DataFrame
relationships_df = pf.read("relationships.parquet")

# Complex query: Users who purchased in the last week
from datetime import datetime, timedelta

last_week = datetime.now() - timedelta(days=7)

recent_buyers = (
    relationships_df
    .query("relation_type == 'PURCHASED' and timestamp > @last_week")
    .groupby("source_id")
    .agg({"target_id": "count", "timestamp": "max"})
    .rename(columns={"target_id": "purchase_count", "timestamp": "last_purchase"})
)
```

## Relationship Types

### Standard Relationship Types

ParquetFrame follows a naming convention for relationship types:

| Pattern | Example | Description |
|---------|---------|-------------|
| `VERB` | `OWNS`, `MANAGES` | Action-based relationships |
| `NOUN_OF` | `MEMBER_OF`, `PART_OF` | Membership/composition |
| `HAS_NOUN` | `HAS_ADDRESS`, `HAS_ROLE` | Possession |
| `IS_NOUN` | `IS_ADMIN`, `IS_ACTIVE` | State/classification |

### Custom Relationship Types

```python
# Define custom relationship types
CUSTOM_RELATIONS = {
    "REVIEWED": {"inverse": "REVIEWED_BY"},
    "FOLLOWS": {"inverse": "FOLLOWED_BY"},
    "TAGGED_WITH": {"inverse": "TAG_OF"},
}

# Use custom relationship
add_relationship(
    source=user,
    target=product,
    relation_type="REVIEWED",
    metadata={"rating": 5, "comment": "Great product!"}
)
```

## Bidirectional Relationships

Some relationships have natural inverses:

```python
from parquetframe.entity import add_bidirectional_relationship

# Automatically creates both directions
add_bidirectional_relationship(
    entity_a=user,
    entity_b=group,
    relation_type_a_to_b="MEMBER_OF",
    relation_type_b_to_a="HAS_MEMBER"
)

# This creates two entries:
# user_123 --MEMBER_OF--> group_abc
# group_abc --HAS_MEMBER--> user_123
```

## Metadata Schema

The `metadata` column stores JSON-encoded relationship properties:

### Common Metadata Patterns

```python
# Weighted relationships (e.g., friendship strength)
metadata = {"weight": 0.85}

# Timestamped attributes
metadata = {
    "created_by": "user_admin",
    "approved_at": "2024-01-15T10:30:00Z"
}

# Contextual information
metadata = {
    "context": "web_app",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
}

# Business logic
metadata = {
    "status": "active",
    "expires_at": "2024-12-31T23:59:59Z",
    "auto_renew": True
}
```

### Querying Metadata

```python
import json

# Parse metadata column
relationships_df["parsed_metadata"] = relationships_df["metadata"].apply(
    lambda x: json.loads(x) if pd.notna(x) else {}
)

# Extract specific fields
relationships_df["amount"] = relationships_df["parsed_metadata"].apply(
    lambda x: x.get("amount")
)

# Filter by metadata
high_value_purchases = relationships_df[
    relationships_df["amount"] > 100
]
```

## Storage Layout

### Default Location

```
project_root/
└── .parquetframe/
    └── relationships/
        ├── relationships.parquet    # Main edge list
        ├── _metadata               # Parquet metadata
        └── _common_metadata        # Global metadata
```

### Partitioned Storage

For large-scale applications, partition by relation type:

```python
from parquetframe.entity import configure_relationship_storage

configure_relationship_storage(
    partition_cols=["relation_type"],
    partition_strategy="hive"
)

# Results in:
# relationships/
# ├── relation_type=PURCHASED/
# │   └── data.parquet
# ├── relation_type=MEMBER_OF/
# │   └── data.parquet
# └── relation_type=FOLLOWS/
#     └── data.parquet
```

## Performance Optimization

### Indexing

```python
# Create indices for common queries
from parquetframe.entity import create_relationship_index

create_relationship_index(
    columns=["source_id", "relation_type"],
    name="source_relation_idx"
)

create_relationship_index(
    columns=["target_id", "relation_type"],
    name="target_relation_idx"
)
```

### Caching

```python
from parquetframe.entity import enable_relationship_cache

# Enable in-memory caching for frequently accessed relationships
enable_relationship_cache(
    max_size_mb=100,
    ttl_seconds=300  # 5 minutes
)
```

## Graph Traversal

### Finding Paths

```python
from parquetframe.entity import find_path

# Find shortest path between entities
path = find_path(
    start_id="user_123",
    end_id="product_789",
    max_depth=3
)

# Example result:
# [
#   ("user_123", "MEMBER_OF", "group_abc"),
#   ("group_abc", "HAS_ACCESS_TO", "catalog_xyz"),
#   ("catalog_xyz", "CONTAINS", "product_789")
# ]
```

### Neighborhood Queries

```python
from parquetframe.entity import get_neighbors

# Get all entities within N hops
neighbors = get_neighbors(
    entity_id="user_123",
    relation_types=["FOLLOWS", "FRIEND_OF"],
    max_hops=2
)
```

## Integration with Permissions

The relationship log integrates with ParquetFrame's Zanzibar-style permissions:

```python
from parquetframe.permissions import check_permission

# Check if user can access resource via relationship
has_access = check_permission(
    user="user_123",
    permission="view",
    resource="document_456"
)

# Under the hood, this checks relationships like:
# user_123 --MEMBER_OF--> group_abc --CAN_VIEW--> document_456
```

See [Permissions System](../permissions-system/overview.md) for details.

## Best Practices

### 1. Use Consistent Naming

```python
# Good: Clear, verb-based
"PURCHASED", "OWNS", "MANAGES"

# Avoid: Vague or ambiguous
"RELATED_TO", "CONNECTED", "LINK"
```

### 2. Include Timestamps

Always include timestamps for audit trails and temporal queries:

```python
add_relationship(
    source=user,
    target=order,
    relation_type="PURCHASED",
    timestamp=datetime.now()  # Explicit timestamp
)
```

### 3. Use Metadata Judiciously

Keep metadata lightweight; avoid storing large objects:

```python
# Good: Small, relevant metadata
metadata = {"amount": 99.99, "currency": "USD"}

# Bad: Large, nested objects
metadata = {"entire_order_details": {...}}  # Store in separate entity instead
```

### 4. Partition Large Graphs

For graphs with >10M relationships, use partitioning:

```python
# Partition by time for temporal queries
configure_relationship_storage(
    partition_cols=["timestamp"]
)

# Or by relation type for filtered queries
configure_relationship_storage(
    partition_cols=["relation_type"]
)
```

### 5. Clean Up Old Relationships

Implement TTL or archival for stale relationships:

```python
from datetime import datetime, timedelta

# Archive relationships older than 1 year
cutoff = datetime.now() - timedelta(days=365)

old_relationships = relationships_df[
    relationships_df["timestamp"] < cutoff
]

old_relationships.to_parquet("relationships_archive_2023.parquet")
```

## Examples

### E-commerce Purchase Graph

```python
from parquetframe.entity import Entity, add_relationship
import pandas as pd

# Entities
@Entity(name="User")
class User:
    id: str
    email: str

@Entity(name="Product")
class Product:
    id: str
    name: str
    price: float

@Entity(name="Order")
class Order:
    id: str
    total: float
    status: str

# Build relationship graph
user = User(id="user_123", email="alice@example.com")
product = Product(id="prod_456", name="Widget", price=29.99)
order = Order(id="order_789", total=29.99, status="completed")

# User placed order
add_relationship(user, order, "PLACED")

# Order contains product
add_relationship(order, product, "CONTAINS")

# Query: What did this user buy?
user_purchases = (
    get_relationships("user_123", "PLACED")
    .merge(
        get_relationships(relation_type="CONTAINS"),
        left_on="target_id",
        right_on="source_id"
    )
)
```

### Social Network

```python
# Follow relationships
add_relationship(
    source=user_alice,
    target=user_bob,
    relation_type="FOLLOWS",
    metadata={"since": "2024-01-01"}
)

# Mutual follows
if check_relationship(user_bob, user_alice, "FOLLOWS"):
    print("Alice and Bob are mutual followers")

# Find followers
followers = get_relationships(
    target_id="user_alice",
    relation_type="FOLLOWS"
)
```

## Related Documentation

- [Entity Framework Overview](./overview.md)
- [Permissions System](../permissions-system/overview.md)
- [Graph Processing](../graph-processing/overview.md)
- [Advanced Queries](./advanced-queries.md)
