# ParquetFrame Phase 2 User Guide

## Overview

Phase 2 introduces a powerful multi-engine architecture with automatic engine selection, entity-graph framework, and comprehensive configuration system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Multi-Engine Core](#multi-engine-core)
3. [Entity Framework](#entity-framework)
4. [Configuration](#configuration)
5. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Installation

```bash
pip install parquetframe
# Optional dependencies
pip install polars  # For Polars engine
pip install dask[complete]  # For Dask engine
pip install fastavro  # For Avro format support
```

### Basic Reading

```python
import parquetframe.core as pf2

# Read with automatic engine selection
df = pf2.read("data.parquet")
print(f"Using {df.engine_name} engine")

# Read specific formats
csv_df = pf2.read_csv("data.csv")
parquet_df = pf2.read_parquet("data.parquet")
avro_df = pf2.read_avro("data.avro")
```

---

## Multi-Engine Core

Phase 2 automatically selects the best DataFrame engine based on data size and system resources.

### Available Engines

- **Pandas**: Best for small datasets (<100MB), eager execution
- **Polars**: Best for medium datasets (100MB-10GB), lazy evaluation
- **Dask**: Best for large datasets (>10GB), distributed processing

### Automatic Engine Selection

```python
import parquetframe.core as pf2

# Automatic selection based on file size
small_df = pf2.read("small.csv")      # Uses pandas
medium_df = pf2.read("medium.csv")    # Uses polars
large_df = pf2.read("large.csv")      # May use dask
```

### Manual Engine Selection

```python
# Force specific engine
df = pf2.read("data.csv", engine="polars")

# Convert between engines
pandas_df = df.to_pandas()
polars_df = df.to_polars()
dask_df = df.to_dask()
```

### DataFrameProxy

All readers return a `DataFrameProxy` that provides a unified interface:

```python
df = pf2.read("data.csv")

# Access properties
print(df.shape)          # (rows, cols)
print(df.columns)        # Column names
print(df.engine_name)    # "pandas", "polars", or "dask"

# Access native DataFrame
native_df = df.native

# Perform operations (automatically delegated)
filtered = df[df["age"] > 30]
grouped = df.groupby("category")["value"].sum()
```

---

## Entity Framework

The entity framework provides declarative persistence with Parquet/Avro backends.

### Basic Entity

```python
from dataclasses import dataclass
from parquetframe.entity import entity

@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str
    email: str

# Create and save
user = User(1, "Alice", "alice@example.com")
user.save()

# Find by primary key
loaded = User.find(1)

# Find all
all_users = User.find_all()

# Query with filters
alice_users = User.find_by(name="Alice")

# Count
total = User.count()

# Delete
user.delete()
User.delete_all()
```

### Storage Formats

```python
# Parquet (default)
@entity(storage_path="./data/users", primary_key="user_id", format="parquet")
@dataclass
class User:
    user_id: int
    name: str

# Avro
@entity(storage_path="./data/users", primary_key="user_id", format="avro")
@dataclass
class UserAvro:
    user_id: int
    name: str
```

### Relationships

#### One-to-Many (Forward)

```python
@entity(storage_path="./data/posts", primary_key="post_id")
@dataclass
class Post:
    post_id: int
    user_id: int
    title: str

    @rel("User", foreign_key="user_id")
    def author(self):
        """Get the post's author."""

# Usage
post = Post.find(1)
author = post.author()  # Returns User instance
```

#### Many-to-One (Reverse)

```python
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str

    @rel("Post", foreign_key="user_id", reverse=True)
    def posts(self):
        """Get all user's posts."""

# Usage
user = User.find(1)
posts = user.posts()  # Returns list of Post instances
```

#### Bidirectional Relationships

```python
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str

    @rel("Post", foreign_key="user_id", reverse=True)
    def posts(self):
        pass

@entity(storage_path="./data/posts", primary_key="post_id")
@dataclass
class Post:
    post_id: int
    user_id: int
    title: str

    @rel("User", foreign_key="user_id")
    def author(self):
        pass

# Usage works both ways
user = User.find(1)
user_posts = user.posts()

post = Post.find(1)
post_author = post.author()
```

---

## Configuration

### Programmatic Configuration

```python
from parquetframe import set_config, get_config

# Set configuration
set_config(
    default_engine="polars",
    pandas_threshold_mb=50.0,
    verbose=True
)

# Get current configuration
config = get_config()
print(config.to_dict())
```

### Environment Variables

```bash
export PARQUETFRAME_ENGINE=polars
export PARQUETFRAME_PANDAS_THRESHOLD_MB=50
export PARQUETFRAME_POLARS_THRESHOLD_MB=5000
export PARQUETFRAME_VERBOSE=1
```

### Context Manager

```python
from parquetframe import config_context
import parquetframe.core as pf2

# Temporary configuration change
with config_context(default_engine="dask"):
    df = pf2.read("large_file.parquet")  # Uses Dask
# Reverts to previous configuration
```

### Available Settings

- **Engine Selection**
  - `default_engine`: Override automatic selection ("pandas", "polars", "dask")
  - `pandas_threshold_mb`: Pandas size threshold (default: 100.0)
  - `polars_threshold_mb`: Polars size threshold (default: 10000.0)

- **Entity Framework**
  - `default_entity_format`: Default format ("parquet", "avro", "csv")
  - `default_entity_base_path`: Base path for entity storage

- **UX Settings**
  - `verbose`: Enable verbose logging (default: False)
  - `show_warnings`: Show warnings (default: True)
  - `progress_bar`: Enable progress bars (default: False)

- **Performance**
  - `parallel_read`: Enable parallel reading (default: True)
  - `max_workers`: Maximum worker threads

---

## Advanced Usage

### Multi-Format Workflows

```python
import parquetframe.core as pf2
from parquetframe import set_config

# Read from multiple formats
sales = pf2.read_csv("sales.csv")
customers = pf2.read_parquet("customers.parquet")
events = pf2.read_avro("events.avro")

# Convert to common engine for joining
sales_pd = sales.to_pandas()
customers_pd = customers.to_pandas()

# Perform operations
merged = sales_pd.native.merge(customers_pd.native, on="customer_id")
```

### Engine Switching

```python
import parquetframe.core as pf2

# Start with pandas
df = pf2.read("data.csv", engine="pandas")

# Convert to polars for better performance
polars_df = df.to_polars()

# Perform lazy operations
result = polars_df.filter(pl.col("age") > 30).select(["name", "age"])
```

### Complete Example: Todo/Kanban Application

Here's a real-world example showing a complete Kanban board system with multiple related entities:

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=19
@entity(storage_path="./kanban_data/users", primary_key="user_id")
@dataclass
class User:
    """User entity representing an application user."""
    user_id: str
    username: str
    email: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @rel("Board", foreign_key="owner_id", reverse=True)
    def boards(self):
        """Get all boards owned by this user."""
        pass
```

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=51
@entity(storage_path="./kanban_data/boards", primary_key="board_id")
@dataclass
class Board:
    """Board entity representing a kanban board."""
    board_id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @rel("User", foreign_key="owner_id")
    def owner(self):
        """Get the user who owns this board."""
        pass

    @rel("TaskList", foreign_key="board_id", reverse=True)
    def lists(self):
        """Get all task lists in this board."""
        pass
```

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=141
@entity(storage_path="./kanban_data/tasks", primary_key="task_id")
@dataclass
class Task:
    """Task entity representing an individual task."""
    task_id: str
    title: str
    description: str
    status: str = "todo"
    priority: str = "medium"
    list_id: str = ""
    assigned_to: str | None = None
    position: int = 0
    created_at: datetime = None
    updated_at: datetime = None

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

    @rel("TaskList", foreign_key="list_id")
    def list(self):
        """Get the list this task belongs to."""
        pass

    @rel("User", foreign_key="assigned_to")
    def assigned_user(self):
        """Get the user assigned to this task."""
        pass
```

**Using the Todo/Kanban Entities:**

```python
from datetime import datetime

# Create user
user = User(
    user_id="user_001",
    username="alice",
    email="alice@example.com"
)
user.save()

# Create board
board = Board(
    board_id="board_001",
    name="Q1 Roadmap",
    description="Product features for Q1 2024",
    owner_id="user_001"
)
board.save()

# Create task list
task_list = TaskList(
    list_id="list_001",
    name="In Progress",
    board_id="board_001",
    position=1
)
task_list.save()

# Create task
task = Task(
    task_id="task_001",
    title="Implement user authentication",
    description="Add OAuth2 support",
    status="in_progress",
    priority="high",
    list_id="list_001",
    assigned_to="user_001"
)
task.save()

# Navigate relationships
loaded_task = Task.find("task_001")
print(f"Task: {loaded_task.title}")
print(f"List: {loaded_task.list().name}")
print(f"Board: {loaded_task.list().board().name}")
print(f"Owner: {loaded_task.list().board().owner().username}")
print(f"Assigned to: {loaded_task.assigned_user().username}")

# Reverse navigation
user_boards = user.boards()  # Get all boards owned by alice
board_lists = board.lists()  # Get all lists in the board
for lst in board_lists:
    tasks = lst.tasks()  # Get all tasks in each list
    print(f"List '{lst.name}' has {len(tasks)} tasks")
```

**Key Features Demonstrated:**

- ✅ **Nested Relationships**: User → Board → TaskList → Task
- ✅ **Bidirectional Navigation**: Forward and reverse relationships
- ✅ **Field Validation**: Status and priority validation in `__post_init__`
- ✅ **Auto-Timestamps**: Created and updated timestamps
- ✅ **Optional Fields**: `assigned_to` can be None

👉 **[See Full Tutorial](../documentation-examples/tutorials.md)** for complete application including permissions and workflows.

### Complex Entity Models

```python
from dataclasses import dataclass
from parquetframe.entity import entity, rel

@entity(storage_path="./data/customers", primary_key="customer_id")
@dataclass
class Customer:
    customer_id: int
    name: str
    email: str

    @rel("Order", foreign_key="customer_id", reverse=True)
    def orders(self):
        pass

@entity(storage_path="./data/orders", primary_key="order_id")
@dataclass
class Order:
    order_id: int
    customer_id: int
    product_id: int
    quantity: int

    @rel("Customer", foreign_key="customer_id")
    def customer(self):
        pass

    @rel("Product", foreign_key="product_id")
    def product(self):
        pass

@entity(storage_path="./data/products", primary_key="product_id")
@dataclass
class Product:
    product_id: int
    name: str
    price: float

# Create data
Product(1, "Widget", 10.99).save()
Customer(1, "Alice", "alice@example.com").save()
Order(1, 1, 1, 5).save()

# Navigate relationships
order = Order.find(1)
customer = order.customer()
product = order.product()

print(f"{customer.name} ordered {order.quantity}x {product.name}")
```

### Performance Optimization

```python
from parquetframe import set_config
import parquetframe.core as pf2

# Optimize for large datasets
set_config(
    default_engine="dask",
    parallel_read=True,
    max_workers=8
)

# Read large files efficiently
df = pf2.read("large_dataset.parquet")
```

---

## Best Practices

1. **Engine Selection**
   - Let automatic selection work for you
   - Use `config_context` for temporary engine overrides
   - Convert engines only when necessary

2. **Entity Design**
   - Keep entities simple with clear primary keys
   - Use relationships for normalized data models
   - Choose appropriate storage format (Parquet for most cases)

3. **Configuration**
   - Set configuration once at application startup
   - Use environment variables for deployment settings
   - Use context managers for temporary changes

4. **Performance**
   - Use lazy evaluation (Polars/Dask) for large datasets
   - Avoid unnecessary engine conversions
   - Enable parallel reading for large files

---

## Troubleshooting

### Engine Not Available

```python
# Check available engines
import parquetframe.core as pf2
# Available engines will be auto-detected at import
```

### Entity Primary Key Errors

```python
# Ensure primary key exists in dataclass
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int  # Must exist!
    name: str
```

### Configuration Not Applied

```python
from parquetframe import reset_config

# Reset to reload from environment
reset_config()
```

---

## Next Steps

- See [API Reference](documentation-examples/api-reference.md) for complete API documentation
- See [Migration Guide](legacy-migration/migration-guide.md) for upgrading from Phase 1
- See [Examples](documentation-examples/examples-gallery.md) for more code examples
