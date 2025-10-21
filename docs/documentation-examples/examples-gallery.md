# Examples

Comprehensive examples showcasing ParquetFrame Phase 2 features through real-world applications.

> **Note:** This page focuses on Phase 2 examples. For legacy Phase 1 examples, see [Legacy Documentation](legacy/legacy-basic-usage.md).

## Featured Example: Todo/Kanban Application

A complete task management application showcasing all Phase 2 features:

- **Entity Framework** - Type-safe data models with `@entity` decorator
- **Relationships** - Object navigation with `@rel` decorator
- **Zanzibar Permissions** - Fine-grained access control with all 4 APIs
- **Multi-User Collaboration** - Permission inheritance and role-based access
- **YAML Workflows** - ETL pipelines for import/export

### Quick Preview

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=19
@entity(storage_path="./kanban_data/users", primary_key="user_id")
@dataclass
class User:
    """
    User entity representing an application user.

    Fields:
        user_id: Unique user identifier
        username: User's display name
        email: User's email address
        created_at: Timestamp when user was created

    Relationships:
        boards: Reverse relationship to boards owned by this user
    """

    user_id: str
    username: str
    email: str
    created_at: datetime = None

    def __post_init__(self):
        """Initialize created_at if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()

    @rel("Board", foreign_key="owner_id", reverse=True)
    def boards(self):
        """Get all boards owned by this user."""
        pass
```

### Key Features Demonstrated

**Entity Framework:**
- Four related entities: User, Board, TaskList, Task
- Type validation and auto-timestamps
- Bidirectional relationships

**Permission System:**
- Role-based access (owner, editor, viewer)
- Permission inheritance (Board → List → Task)
- All 4 Zanzibar APIs:
  - `check()` - Verify permissions
  - `expand()` - List accessible resources
  - `list_objects()` - Find all resources with permission
  - `list_subjects()` - Find all users with access

**Workflows:**
- CSV import pipeline
- Report export pipeline
- ETL transformations

### 📚 Full Tutorial

**[Complete Todo/Kanban Walkthrough →](tutorials/todo-kanban-walkthrough.md)**

The complete 850+ line tutorial covers:
- Architecture and setup
- Entity definitions and relationships
- Permission system implementation
- Multi-user collaboration scenarios
- YAML workflow examples
- Running the application

---

## Phase 2 Examples

### Entity Framework

#### Defining Entities with Decorators

```python
# path=null start=null
from dataclasses import dataclass
from datetime import datetime
from parquetframe.entity import entity, rel
import parquetframe.core as pf2

# Initialize core
df = pf2.read(engine="pandas")

@entity(storage_path="./data/products", primary_key="product_id")
@dataclass
class Product:
    """Product entity with automatic persistence."""
    product_id: str
    name: str
    category: str
    price: float
    stock_quantity: int
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

# Create and save products
product = Product(
    product_id="prod_001",
    name="Wireless Mouse",
    category="Electronics",
    price=29.99,
    stock_quantity=150
)

core.save(product)

# Load products
loaded = core.load(Product, product_id="prod_001")
print(f"Loaded: {loaded.name} - ${loaded.price}")
```

#### Entity Relationships

Define relationships between entities:

```python
# path=null start=null
@entity(storage_path="./data/orders", primary_key="order_id")
@dataclass
class Order:
    """Order entity with customer relationship."""
    order_id: str
    customer_id: str
    total_amount: float
    status: str
    created_at: datetime = None

    @rel("Customer", foreign_key="customer_id")
    def customer(self):
        """Get the customer for this order."""
        pass

@entity(storage_path="./data/customers", primary_key="customer_id")
@dataclass
class Customer:
    """Customer entity with reverse order relationship."""
    customer_id: str
    name: str
    email: str

    @rel("Order", foreign_key="customer_id", reverse=True)
    def orders(self):
        """Get all orders for this customer."""
        pass

# Navigate relationships
order = core.load(Order, order_id="ord_001")
customer = order.customer()  # Follow forward relationship
print(f"Order {order.order_id} belongs to {customer.name}")

# Navigate reverse relationship
all_orders = customer.orders()  # Get all orders
print(f"{customer.name} has {len(all_orders)} orders")
```

### Permission System

#### Zanzibar Permission Checking

```python
# path=null start=null
from parquetframe.permissions import PermissionManager

# Initialize permission manager
perm_mgr = PermissionManager()

# Grant permissions
perm_mgr.grant_permission(
    user_id="user_001",
    resource_type="document",
    resource_id="doc_123",
    relation="editor"
)

# Check permissions - uses Zanzibar check() API
can_edit = perm_mgr.check_permission(
    user_id="user_001",
    resource_type="document",
    resource_id="doc_123",
    relation="editor"
)

print(f"User can edit: {can_edit}")
```

#### List User Permissions

```python
# path=null start=null
# Find all documents user can access - uses expand() API
accessible_docs = perm_mgr.list_user_permissions(
    user_id="user_001",
    resource_type="document",
    relation="viewer"
)

print(f"User has access to {len(accessible_docs)} documents")

# Find all users with access to a document - uses list_subjects() API
authorized_users = perm_mgr.list_resource_permissions(
    resource_type="document",
    resource_id="doc_123",
    relation="editor"
)

print(f"{len(authorized_users)} users can edit this document")
```

#### Permission Inheritance

From the Todo/Kanban example:

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/permissions.py start=254
    def grant_board_access(
        self,
        user_id: str,
        board_id: str,
        role: str,
    ) -> None:
        """
        Grant board-level access to a user.

        This automatically propagates permissions to all lists and tasks in the board.

        Args:
            user_id: User ID to grant access to
            board_id: Board ID
            role: Role (owner, editor, viewer)

        Raises:
            ValueError: If role is invalid
        """
        if role not in ["owner", "editor", "viewer"]:
            raise ValueError(f"Invalid role: {role}. Must be owner, editor, or viewer")

        self.grant_permission(user_id, "board", board_id, role)
```

### YAML Workflows

#### ETL Pipeline Example

```yaml
# path=null start=null
# data_pipeline.yml
name: Customer Data ETL
description: Import customer data from CSV and process

steps:
  - name: Read Customer CSV
    action: read
    params:
      path: "customers.csv"
      format: "csv"

  - name: Clean Data
    action: transform
    params:
      operations:
        - type: filter
          condition: "status == 'active'"
        - type: dropna
          subset: ["email", "customer_id"]

  - name: Enrich with Orders
    action: join
    params:
      right_source: "orders.parquet"
      on: "customer_id"
      how: "left"

  - name: Save Entities
    action: save_entities
    params:
      entity_type: Customer
      storage_path: "./data/customers"
```

Run the workflow:

```python
# path=null start=null
from parquetframe.workflow import WorkflowEngine
import parquetframe.core as pf2

# Initialize
df = pf2.read()
engine = WorkflowEngine(core)

# Run workflow
result = engine.run_workflow("data_pipeline.yml")
print(f"Processed {result['records_processed']} customers")
```

### Multi-Engine Support

#### Switch Between Compute Engines

```python
# path=null start=null
import parquetframe.core as pf2

# Start with pandas for small data
df = pf2.read(engine="pandas")

# Create some entities
product = Product(product_id="p1", name="Widget", price=19.99)
core.save(product)

# Switch to Polars for faster operations
core.switch_engine("polars")
products = core.query(Product).filter(price__gt=10).all()

# Switch to Dask for distributed computing
core.switch_engine("dask")
large_query_result = core.query(Product).filter(category="Electronics").all()

print(f"Found {len(large_query_result)} electronics products")
```

#### Engine-Specific Optimizations

```python
# path=null start=null
# Polars - fastest for single-machine workloads
df = pf2.read(engine="polars")
products = core.query(Product).all()
print(f"Loaded {len(products)} products with Polars")

# Dask - best for distributed/large-scale data
df = pf2.read(engine="dask", dask_scheduler="distributed")
tasks = core.query(Task).filter(status="in_progress").all()
print(f"Processing {len(tasks)} tasks across cluster")

# pandas - compatible with existing ecosystem
df = pf2.read(engine="pandas")
import matplotlib.pyplot as plt

# Direct pandas access for plotting
orders_df = core.query(Order).to_dataframe()
orders_df.groupby('status').size().plot(kind='bar')
plt.show()
```

---

## Integration Examples

### With FastAPI

```python
# path=null start=null
from fastapi import FastAPI, HTTPException
import parquetframe.core as pf2
from parquetframe.permissions import PermissionManager

app = FastAPI()
df = pf2.read()
perm_mgr = PermissionManager()

@app.post("/tasks/")
def create_task(task_data: dict, user_id: str):
    """Create a new task with permission check."""
    # Check if user can create tasks in this list
    can_create = perm_mgr.check_list_access(
        user_id=user_id,
        list_id=task_data["list_id"],
        board_id=task_data["board_id"],
        required_role="editor"
    )

    if not can_create:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Create and save task
    task = Task(**task_data)
    core.save(task)

    return {"task_id": task.task_id, "status": "created"}

@app.get("/tasks/{task_id}")
def get_task(task_id: str, user_id: str):
    """Get task with permission check."""
    task = core.load(Task, task_id=task_id)

    # Check read permission
    can_view = perm_mgr.check_task_access(
        user_id=user_id,
        task_id=task_id,
        list_id=task.list_id,
        board_id=task.list().board_id,
        required_role="viewer"
    )

    if not can_view:
        raise HTTPException(status_code=403, detail="Permission denied")

    return task
```

### With Data Science Tools

```python
# path=null start=null
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import parquetframe.core as pf2

# Initialize
df = pf2.read(engine="pandas")

# Load entities as DataFrame for analysis
tasks = core.query(Task).to_dataframe()
users = core.query(User).to_dataframe()

# Merge for analysis
analysis_df = tasks.merge(users, left_on="assigned_to", right_on="user_id")

# Visualizations
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Task status distribution
analysis_df['status'].value_counts().plot(kind='pie', ax=axes[0, 0], autopct='%1.1f%%')
axes[0, 0].set_title('Task Status Distribution')

# Tasks by priority
sns.countplot(data=analysis_df, x='priority', hue='status', ax=axes[0, 1])
axes[0, 1].set_title('Tasks by Priority and Status')

# Tasks per user
analysis_df.groupby('username').size().plot(kind='barh', ax=axes[1, 0])
axes[1, 0].set_title('Tasks per User')

# Task completion timeline
analysis_df['created_at'] = pd.to_datetime(analysis_df['created_at'])
analysis_df.set_index('created_at').resample('D').size().plot(ax=axes[1, 1])
axes[1, 1].set_title('Tasks Created Over Time')

plt.tight_layout()
plt.savefig('task_analysis.png')
print("Analysis complete! Saved to task_analysis.png")
```

---

## Legacy Examples (Phase 1)

For examples using the legacy Phase 1 API with pandas/Dask backend switching:

- **[Legacy Basic Usage](legacy/legacy-basic-usage.md)** - Phase 1 file operations
- **[Legacy Backend Switching](legacy/legacy-backends.md)** - pandas/Dask switching examples

### Migration Path

If you're using Phase 1 code, see the **[Migration Guide](getting-started/migration.md)** for:
- Side-by-side code comparisons
- Step-by-step migration instructions
- Breaking changes and workarounds

---

## More Examples

- **[📚 Todo/Kanban Tutorial](tutorials/todo-kanban-walkthrough.md)** - Complete 850+ line walkthrough
- **[Entity Framework Guide](phase2/entities.md)** - Deep dive into entities
- **[Permissions Guide](user-guide/permissions.md)** - Complete permission examples
- **[Workflows Guide](user-guide/workflows.md)** - YAML workflow patterns

All examples use Phase 2 API unless explicitly marked as legacy.
```
