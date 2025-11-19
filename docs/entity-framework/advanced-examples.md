# Entity Framework Advanced Examples

This guide covers advanced patterns for the Entity Framework, including many-to-many relationships, inheritance strategies, and complex querying.

## Many-to-Many Relationships

Modeling relationships like **Tags** on **Posts** or **Users** in **Groups** requires a many-to-many pattern. In ParquetFrame, this is handled by an intermediate entity or direct list relationships if the cardinality is low.

### Pattern 1: Intermediate Entity (Recommended)

Best for relationships with metadata (e.g., "joined at" timestamp).

```python
from parquetframe.entity import entity, rel
from dataclasses import dataclass
from typing import List

@entity(storage_path="data/users", primary_key="id")
@dataclass
class User:
    id: str
    name: str

@entity(storage_path="data/groups", primary_key="id")
@dataclass
class Group:
    id: str
    name: str

@entity(storage_path="data/memberships", primary_key="id")
@dataclass
class Membership:
    id: str
    user_id: str = rel("User", "id")
    group_id: str = rel("Group", "id")
    role: str = "member"

# Usage
u = User("u1", "Alice")
g = Group("g1", "Devs")
m = Membership("m1", user_id="u1", group_id="g1", role="admin")

u.save(); g.save(); m.save()

# Query
all_memberships = Membership.find_all()
user_memberships = [m for m in all_memberships if m.user_id == "u1"]
my_groups = [m.group_id for m in user_memberships]  # Returns ['g1']
```

## Inheritance Strategies

ParquetFrame entities are Python dataclasses, so they support standard inheritance.

### Pattern: Abstract Base Entity

Share common fields like IDs and timestamps.

```python
from datetime import datetime

@dataclass
class BaseEntity:
    id: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

@entity(storage_path="data/products", primary_key="id")
@dataclass
class Product(BaseEntity):
    name: str
    price: float

@entity(storage_path="data/orders", primary_key="id")
@dataclass
class Order(BaseEntity):
    customer_id: str
    total: float
```

## Advanced Querying

### Complex Filtering

Combine conditions using standard Python logic in lambdas.

```python
# Find high-value orders from 2024
all_orders = Order.find_all()
high_value_2024 = [
    o for o in all_orders
    if o.total > 1000 and o.created_at.year == 2024
]
```

### Aggregations via DataFrame

For heavy lifting, drop down to the underlying DataFrame.

```python
# Get underlying DataFrame
df = Order.dataframe()

# Use SQL or pandas/Dask API
stats = df.sql("""
    SELECT
        customer_id,
        COUNT(*) as order_count,
        SUM(total) as lifetime_value
    FROM df
    GROUP BY customer_id
    HAVING lifetime_value > 5000
""")
print(stats)
```

## GraphAr Integration

Entities can be exported to GraphAr format for graph processing.

```python
from parquetframe.graph import GraphFrame

# Assuming entities are stored
# Convert entity relationships to graph edges
# (This feature is part of the GraphAr integration layer)

# Example: Visualize User-Membership-Group as a graph
# ...
```

## Best Practices

1.  **Keys**: Always use string IDs for primary keys to ensure compatibility across systems.
2.  **Indexing**: ParquetFrame partitions by primary key chunks; for other lookups, consider secondary index entities.
3.  **Batching**: When saving many entities, use `Entity.save_batch([e1, e2, ...])` (if available) or parallelize writes.
