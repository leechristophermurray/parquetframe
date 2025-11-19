# Advanced Relationship Queries

ParquetFrame's Entity Framework supports advanced querying on relationships with filtering, ordering, and limiting capabilities. This enables efficient data navigation without loading all entities into memory.

## Overview

Enhanced relationship queries allow you to:
- **Filter** relationships by field values
- **Order** results by any field
- **Limit** the number of results returned
- **Chain** operations for complex queries
- **Count** or check existence without loading data

All operations are lazy and only execute when needed.

---

## Basic Usage

### Simple Relationship Navigation

```python
# Get all posts for a user
posts = user.posts().all()

# Equivalent to (backward compatible)
posts = [p for p in user.posts()]
```

### Filtering

```python
# Filter with kwargs - executes immediately
published = user.posts(status="published")

# Chain filtering - lazy evaluation
query = user.posts().filter(status="published", category="tech")
results = query.all()
```

### Ordering

```python
# Order ascending
recent = user.posts().order_by("created_at").all()

# Order descending
popular = user.posts().order_by("views", desc=True).all()
```

### Limiting

```python
# Get first 10 posts
top_10 = user.posts().limit(10).all()

# Combined with ordering
latest_5 = user.posts().order_by("created_at", desc=True).limit(5).all()
```

---

## Query Methods

### `.filter(**kwargs)`

Add filter conditions to the query.

```python
# Single filter
active = user.tasks().filter(status="active")

# Multiple filters
urgent = user.tasks().filter(status="active", priority="high")

# Chain multiple filters
result = user.tasks().filter(status="active").filter(priority="high")
```

**Returns:** `RelationshipQuery` for chaining

### `.order_by(field, desc=False)`

Set ordering for results.

```python
# Ascending order (default)
sorted_asc = user.posts().order_by("created_at")

# Descending order
sorted_desc = user.posts().order_by("created_at", desc=True)
```

**Returns:** `RelationshipQuery` for chaining

### `.limit(n)`

Limit the number of results.

```python
# Get first 5 results
first_5 = user.posts().limit(5).all()

# Works with ordering
top_3 = user.posts().order_by("views", desc=True).limit(3).all()
```

**Returns:** `RelationshipQuery` for chaining

### `.count()`

Count matching results without loading them.

```python
# Count all
total = user.posts().count()

# Count filtered
published_count = user.posts().filter(status="published").count()
```

**Returns:** `int`

### `.all()`

Execute query and return all matching results.

```python
# Get all results
results = user.posts().all()

# Works with any query
filtered = user.posts().filter(status="draft").order_by("title").all()
```

**Returns:** `list[Entity]`

### `.first()`

Get the first matching result or None.

```python
# Get latest post
latest = user.posts().order_by("created_at", desc=True).first()

# Returns None if no matches
no_match = user.posts().filter(status="deleted").first()
if no_match is None:
    print("No deleted posts")
```

**Returns:** `Entity | None`

### `.exists()`

Check if any matching results exist.

```python
# Check existence
has_drafts = user.posts().filter(status="draft").exists()

if has_drafts:
    print("User has draft posts")
```

**Returns:** `bool`

---

## Complex Examples

### Pagination

```python
page_size = 10
page_number = 2

posts = (user.posts()
         .order_by("created_at", desc=True)
         .limit(page_size)
         .all())

# For page 2, you'd need to implement offset
# (not yet supported, but can work around with filtering)
```

### Top N by Criteria

```python
# Get top 5 most viewed tech posts
top_tech = (user.posts()
            .filter(category="tech")
            .order_by("views", desc=True)
            .limit(5)
            .all())

for post in top_tech:
    print(f"{post.title}: {post.views} views")
```

### Conditional Queries

```python
def get_user_posts(user, status=None, limit=None):
    """Get user posts with optional filtering."""
    query = user.posts()

    if status:
        query = query.filter(status=status)

    if limit:
        query = query.limit(limit)

    return query.all()

# Usage
all_posts = get_user_posts(user)
recent_published = get_user_posts(user, status="published", limit=10)
```

### Dashboard Queries

```python
# Dashboard aggregations
stats = {
    "total_posts": user.posts().count(),
    "published": user.posts().filter(status="published").count(),
    "drafts": user.posts().filter(status="draft").count(),
    "latest": user.posts().order_by("created_at", desc=True).first(),
}

print(f"Total: {stats['total_posts']}")
print(f"Published: {stats['published']}")
print(f"Latest: {stats['latest'].title}")
```

---

## Performance Considerations

### Lazy Evaluation

Queries are lazy - they don't execute until you call a terminal method:

```python
# No database access yet
query = user.posts().filter(status="published").order_by("views")

# Database access happens here
results = query.all()  # Executes the query
```

### Terminal Methods

These methods execute the query:
- `.all()` - Returns full result list
- `.first()` - Returns first item or None
- `.count()` - Returns count
- `.exists()` - Returns boolean
- Iteration: `for item in query:`

### Efficient Counting

Use `.count()` instead of `len(.all())` when you only need the count:

```python
# Efficient
count = user.posts().filter(status="published").count()

# Less efficient (loads all data)
count = len(user.posts().filter(status="published").all())
```

---

## Backward Compatibility

Old relationship code continues to work:

```python
# Old style - still works
posts = user.posts()  # Returns RelationshipQuery
for post in posts:  # Can iterate directly
    print(post.title)

# Or convert to list
posts_list = list(user.posts())
```

The key difference: relationships now return `RelationshipQuery` instead of `list`, but `RelationshipQuery` is iterable and provides `.all()`.

---

## API Summary

| Method | Returns | Executes? | Description |
|--------|---------|-----------|-------------|
| `.filter(**kwargs)` | RelationshipQuery | No | Add filters |
| `.order_by(field, desc)` | RelationshipQuery | No | Set ordering |
| `.limit(n)` | RelationshipQuery | No | Set limit |
| `.all()` | list[Entity] | Yes | Get all results |
| `.first()` | Entity \| None | Yes | Get first result |
| `.count()` | int | Yes | Count results |
| `.exists()` | bool | Yes | Check existence |
| `.__iter__()` | Iterator | Yes | Iterate results |

---

## Full Example: Blog System

```python
from dataclasses import dataclass
from parquetframe.entity import entity, rel

@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str

    @rel("Post", foreign_key="author_id", reverse=True)
    def posts(self):
        pass

@entity(storage_path="./data/posts", primary_key="post_id")
@dataclass
class Post:
    post_id: str
    author_id: str
    title: str
    status: str
    category: str
    views: int
    created_at: str

# Create user and posts
user = User("u1", "alice")
user.save()

Post("p1", "u1", "Python Tips", "published", "tech", 1000, "2024-01-01").save()
Post("p2", "u1", "Cooking 101", "published", "lifestyle", 500, "2024-01-02").save()
Post("p3", "u1", "Draft Post", "draft", "tech", 0, "2024-01-03").save()

# Query examples
print("All posts:", user.posts().count())
print("Published:", user.posts(status="published").count())

top_post = user.posts().order_by("views", desc=True).first()
print(f"Top post: {top_post.title}")

tech_posts = user.posts().filter(category="tech", status="published").all()
for post in tech_posts:
    print(f"- {post.title}")
```

---

## See Also

- [Entity Framework](index.md) - Entity system overview
- [Relationship Schema](relationship-schema.md) - Storage patterns
- [API Reference](../documentation-examples/api-entities.md) - Complete API docs
