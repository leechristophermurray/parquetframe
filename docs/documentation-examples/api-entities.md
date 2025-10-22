# Entity Framework API Reference

Complete API documentation for ParquetFrame's Entity Framework (Phase 2).

## Decorators

### @entity

```python
@entity(
    storage_path: str,
    primary_key: str,
    format: str = "parquet",
    engine: str = "pandas"
)
```

Decorator that transforms a dataclass into a persistent entity with automatic CRUD operations.

**Parameters:**

- `storage_path` (str): Directory path where entity data will be stored
- `primary_key` (str): Name of the field to use as primary key
- `format` (str, optional): Storage format - "parquet", "avro", or "csv". Default: "parquet"
- `engine` (str, optional): Processing engine - "pandas", "polars", or "dask". Default: "pandas"

**Returns:**

Decorated class with added methods:
- `save()`: Persist entity to storage
- `delete()`: Remove entity from storage
- `find(pk_value)`: Load entity by primary key
- `find_all()`: Load all entities
- `find_by(**filters)`: Query entities with filters
- `count()`: Count total entities

**Example:**

```python path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=19
@entity(storage_path="./kanban_data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str
    email: str
    created_at: datetime = None
```

### @rel

```python
@rel(
    target_entity: str,
    foreign_key: str,
    reverse: bool = False
)
```

Decorator that defines a relationship between entities.

**Parameters:**

- `target_entity` (str): Name of the related entity class
- `foreign_key` (str): Name of the foreign key field
- `reverse` (bool, optional): Whether this is a reverse relationship (one-to-many). Default: False

**Returns:**

Method decorator that enables relationship navigation.

**Forward Relationship Example:**

```python path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=190
@rel("TaskList", foreign_key="list_id")
def list(self):
    """Get the list this task belongs to."""
    pass
```

**Reverse Relationship Example:**

```python path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=90
@rel("TaskList", foreign_key="board_id", reverse=True)
def lists(self):
    """Get all task lists in this board."""
    pass
```

## Entity Methods

### save()

```python
entity_instance.save() -> None
```

Persists the entity to storage. Creates new record if entity doesn't exist, updates if it does.

**Example:**

```python path=null start=null
user = User(user_id="u001", username="alice", email="alice@example.com")
user.save()
```

### delete()

```python
entity_instance.delete() -> None
```

Removes the entity from storage.

**Example:**

```python path=null start=null
user = User.find("u001")
user.delete()
```

## Class Methods

### find()

```python
EntityClass.find(pk_value: Any) -> EntityClass | None
```

Loads an entity by its primary key value.

**Parameters:**

- `pk_value`: Value of the primary key to search for

**Returns:**

Entity instance if found, None otherwise.

**Example:**

```python path=null start=null
user = User.find("u001")
if user:
    print(f"Found: {user.username}")
```

### find_all()

```python
EntityClass.find_all() -> list[EntityClass]
```

Loads all entities from storage.

**Returns:**

List of all entity instances.

**Example:**

```python path=null start=null
all_users = User.find_all()
for user in all_users:
    print(user.username)
```

### find_by()

```python
EntityClass.find_by(**filters) -> list[EntityClass]
```

Queries entities with field filters.

**Parameters:**

- `**filters`: Keyword arguments where keys are field names and values are filter values

**Returns:**

List of matching entity instances.

**Example:**

```python path=null start=null
alice_users = User.find_by(username="alice")
active_tasks = Task.find_by(status="in_progress", priority="high")
```

### count()

```python
EntityClass.count() -> int
```

Returns the total number of entities in storage.

**Returns:**

Integer count of entities.

**Example:**

```python path=null start=null
total_users = User.count()
print(f"Total users: {total_users}")
```

### delete_all()

```python
EntityClass.delete_all() -> None
```

Removes all entities from storage. Use with caution!

**Example:**

```python path=null start=null
# Clear all test data
TestUser.delete_all()
```

## Relationship Navigation

### Forward Relationships (Many-to-One)

Navigate from child to parent entity.

**Example:**

```python path=null start=null
task = Task.find("task_001")
task_list = task.list()  # Get parent TaskList
board = task_list.board()  # Get parent Board
owner = board.owner()  # Get User who owns the board
```

### Reverse Relationships (One-to-Many)

Navigate from parent to child entities.

**Example:**

```python path=null start=null
board = Board.find("board_001")
lists = board.lists()  # Get all TaskLists in board

for lst in lists:
    tasks = lst.tasks()  # Get all Tasks in each list
    print(f"{lst.name}: {len(tasks)} tasks")
```

## Storage Formats

### Parquet (Default)

```python path=null start=null
@entity(storage_path="./data/users", primary_key="user_id", format="parquet")
@dataclass
class User:
    user_id: str
    name: str
```

**Advantages:**
- Columnar format, efficient for analytics
- Fast read/write performance
- Excellent compression
- Wide ecosystem support

### Avro

```python path=null start=null
@entity(storage_path="./data/users", primary_key="user_id", format="avro")
@dataclass
class User:
    user_id: str
    name: str
```

**Advantages:**
- Schema evolution support
- Compact binary format
- Fast serialization
- Cross-language compatibility

### CSV

```python path=null start=null
@entity(storage_path="./data/users", primary_key="user_id", format="csv")
@dataclass
class User:
    user_id: str
    name: str
```

**Advantages:**
- Human-readable
- Universal compatibility
- Easy debugging
- Simple to inspect

## Engine Selection

### Pandas (Default)

```python path=null start=null
@entity(storage_path="./data/users", primary_key="user_id", engine="pandas")
```

**Best for:**
- Small to medium datasets (< 1GB)
- Interactive analysis
- Compatibility with existing pandas code

### Polars

```python path=null start=null
@entity(storage_path="./data/users", primary_key="user_id", engine="polars")
```

**Best for:**
- Medium to large datasets (1GB - 100GB)
- Lazy evaluation
- Faster query performance

### Dask

```python path=null start=null
@entity(storage_path="./data/users", primary_key="user_id", engine="dask")
```

**Best for:**
- Very large datasets (> 100GB)
- Distributed processing
- Out-of-core computation

## Best Practices

### 1. Use Descriptive Storage Paths

```python path=null start=null
# Good: organized by entity type
@entity(storage_path="./data/entities/users", primary_key="user_id")

# Avoid: generic paths
@entity(storage_path="./data", primary_key="user_id")
```

### 2. Choose Appropriate Primary Keys

```python path=null start=null
# Good: UUID or unique identifier
@entity(storage_path="./data/users", primary_key="user_id")
class User:
    user_id: str  # UUID

# Avoid: non-unique fields
@entity(storage_path="./data/users", primary_key="username")  # usernames can change
```

### 3. Add Timestamps

```python path=null start=null
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
```

### 4. Validate Data in __post_init__

```python path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=174
def __post_init__(self):
    now = datetime.now()
    if self.created_at is None:
        self.created_at = now
    if self.updated_at is None:
        self.updated_at = now

    # Validate status
    if self.status not in ["todo", "in_progress", "done"]:
        raise ValueError(f"Invalid status: {self.status}")

    # Validate priority
    if self.priority not in ["low", "medium", "high"]:
        raise ValueError(f"Invalid priority: {self.priority}")
```

## See Also

- **[Entity Framework Guide](../phase2/USER_GUIDE.md#entity-framework)** - Complete entity framework tutorial
- **[Todo/Kanban Walkthrough](../documentation-examples/tutorials.md)** - Real-world entity framework example
- **[Relationships Guide](../phase2/USER_GUIDE.md#relationships)** - Deep dive into entity relationships
