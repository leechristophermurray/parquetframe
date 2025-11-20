# Quick Start Guide

Get up and running with ParquetFrame Phase 2 in minutes!

> **Note:** This guide covers Phase 2 API with the Entity Framework. For legacy Phase 1 documentation, see [Legacy Basic Usage](../legacy-migration/phase1-usage.md).

## Installation

```bash
pip install parquetframe
```

## Phase 2 Core Concepts

Phase 2 introduces:

- **Multi-Engine Core** - Seamlessly switch between pandas, Polars, and Dask
- **Entity Framework** - Define data models with decorators
- **Relationships** - Navigate object graphs with ease
- **Zanzibar Permissions** - Fine-grained access control
- **Workflow System** - YAML-based ETL pipelines

## Basic Usage

### 1. Initialize Core

```python
import parquetframe.core as pf2

# Initialize with default engine (pandas)
df = pf2.read()

# Or specify engine explicitly
df = pf2.read(engine="polars")  # pandas, polars, or dask
```

### 2. Define Entities

Use the `@entity` decorator to define data models:

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=141

@entity(storage_path="./kanban_data/tasks", primary_key="task_id")
@dataclass
class Task:
    """
    Task entity representing an individual task.

    Fields:
        task_id: Unique task identifier
        title: Task title
        description: Detailed task description
        status: Current status (todo, in_progress, done)
        priority: Task priority (low, medium, high)
        list_id: ID of the list this task belongs to
        assigned_to: Optional ID of the user assigned to this task
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last updated

    Relationships:
        list: Forward relationship to TaskList (parent list)
        assigned_user: Forward relationship to User (assignee)
    """

    task_id: str
    title: str
    description: str
    status: str = "todo"  # todo, in_progress, done
    priority: str = "medium"  # low, medium, high
    list_id: str = ""
    assigned_to: str | None = None
    position: int = 0  # Position within the list
    created_at: datetime = None
    updated_at: datetime = None
```

### 3. Create and Save Entities

```python
from datetime import datetime

# Create a task instance
task = Task(
    task_id="task_001",
    title="Implement user authentication",
    description="Add OAuth2 support with JWT tokens",
    status="todo",
    priority="high",
    list_id="list_001",
    assigned_to="user_123"
)

# Save to storage
core.save(task)

# Load back
loaded_task = core.load(Task, task_id="task_001")
print(f"Task: {loaded_task.title} - {loaded_task.status}")
```

### 4. Define Relationships

Use the `@rel` decorator to define relationships between entities:

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/models.py start=190

    @rel("TaskList", foreign_key="list_id")
    def list(self):
        """Get the list this task belongs to."""
        pass

    @rel("User", foreign_key="assigned_to")
    def assigned_user(self):
        """Get the user assigned to this task."""
        pass
```

Navigate relationships easily:

```python
# Navigate from task to list to board
task = core.load(Task, task_id="task_001")
task_list = task.list()  # Get parent list
board = task_list.board()  # Get parent board

print(f"Task '{task.title}' is in list '{task_list.name}' on board '{board.name}'")

# Navigate reverse relationships
board = core.load(Board, board_id="board_001")
all_lists = board.lists()  # Get all lists in board
for lst in all_lists:
    tasks = lst.tasks()  # Get all tasks in list
    print(f"List '{lst.name}' has {len(tasks)} tasks")
```

### 5. Implement Permissions

Use Zanzibar-style permissions for fine-grained access control:

```python
# path=/Users/temp/Documents/Projects/parquetframe/examples/integration/todo_kanban/permissions.py start=110

    def check_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        relation: str,
        allow_indirect: bool = True,
    ) -> bool:
        """
        Check if a user has a specific permission.

        Uses Zanzibar check() API for both direct and indirect permissions.

        Args:
            user_id: User ID to check
            resource_type: Type of resource (board, list, task)
            resource_id: ID of the resource
            relation: Relation/permission type to check
            allow_indirect: Whether to check indirect permissions via graph traversal

        Returns:
            True if user has the permission, False otherwise
        """
        return check(
            store=self.store,
            subject_namespace="user",
            subject_id=user_id,
            relation=relation,
            object_namespace=resource_type,
            object_id=resource_id,
            allow_indirect=allow_indirect,
        )
```

Usage example:

```python
from parquetframe.permissions import PermissionManager

# Initialize permission manager
perm_mgr = PermissionManager()

# Grant board access to a user
perm_mgr.grant_board_access(user_id="user_123", board_id="board_001", role="editor")

# Check if user can edit a task
can_edit = perm_mgr.check_task_access(
    user_id="user_123",
    task_id="task_001",
    list_id="list_001",
    board_id="board_001",
    required_role="editor"
)

if can_edit:
    # Update the task
    task.status = "in_progress"
    core.save(task)
```

### 6. Define Workflows

Create YAML workflows for ETL pipelines:

```yaml
# import_tasks.yml
name: Import Tasks from CSV
description: Load tasks from external CSV file

steps:
  - name: Read CSV
    action: read
    params:
      path: "external_tasks.csv"
      format: "csv"

  - name: Transform Data
    action: transform
    params:
      operations:
        - type: filter
          condition: "status in ['todo', 'in_progress']"
        - type: map
          field: priority
          mapping:
            1: "low"
            2: "medium"
            3: "high"

  - name: Save to ParquetFrame
    action: save_entities
    params:
      entity_type: Task
      storage_path: "./kanban_data/tasks"
```

Run workflows:

```python
from parquetframe.workflow import WorkflowEngine

# Initialize workflow engine
engine = WorkflowEngine(core)

# Run workflow
result = engine.run_workflow("import_tasks.yml")
print(f"Imported {result['records_processed']} tasks")
```

## Multi-Engine Support

Switch between compute engines based on your needs. See [Engine Selection](../core-features/engine-selection.md) for details.

```python
# Start with pandas for small datasets
df = pf2.read(engine="pandas")

# Switch to Polars for faster operations
core.switch_engine("polars")

# Or use Dask for distributed computing
core.switch_engine("dask")

# All entity operations work seamlessly across engines
tasks = core.query(Task).filter(status="in_progress").all()
```

## Complete Example

Here's a full example bringing it all together:

```python
import parquetframe.core as pf2
from parquetframe.permissions import PermissionManager
from datetime import datetime

# Initialize
df = pf2.read(engine="pandas")
perm_mgr = PermissionManager()

# Create entities
user = User(user_id="user_001", username="alice", email="alice@example.com")
board = Board(
    board_id="board_001",
    name="Q1 Roadmap",
    description="Product features for Q1 2024",
    owner_id="user_001"
)
task_list = TaskList(
    list_id="list_001",
    name="In Progress",
    board_id="board_001",
    position=1
)
task = Task(
    task_id="task_001",
    title="Design new login flow",
    description="Modernize authentication UX",
    status="in_progress",
    priority="high",
    list_id="list_001",
    assigned_to="user_001"
)

# Save all entities
core.save(user)
core.save(board)
core.save(task_list)
core.save(task)

# Set up permissions
perm_mgr.grant_board_access("user_001", "board_001", "owner")
perm_mgr.inherit_board_permissions("board_001", "list_001")
perm_mgr.inherit_list_permissions("list_001", "task_001")

# Navigate relationships
loaded_task = core.load(Task, task_id="task_001")
print(f"Task: {loaded_task.title}")
print(f"List: {loaded_task.list().name}")
print(f"Board: {loaded_task.list().board().name}")
print(f"Owner: {loaded_task.list().board().owner().username}")

# Check permissions
can_edit = perm_mgr.check_task_access(
    user_id="user_001",
    task_id="task_001",
    list_id="list_001",
    board_id="board_001",
    required_role="editor"
)

if can_edit:
    loaded_task.status = "done"
    core.save(loaded_task)
    print("Task marked as done!")
```

## Next Steps

**Explore the Todo/Kanban Tutorial:**

- **[Full Todo/Kanban Walkthrough](todo-kanban-example.md)** - Complete application example with all Phase 2 features

**Learn More:**

1. **[Entity Framework Guide](../phase2/entities.md)** - Deep dive into entities and decorators
2. **[Relationships Guide](../phase2/relationships.md)** - Master object navigation
3. **[Permissions System](../user-guide/permissions.md)** - Comprehensive Zanzibar permission examples
4. **[Workflows](../user-guide/workflows.md)** - YAML-based ETLFor existing users of ParquetFrame v1.x, please see the [Migration Guide](../legacy-migration/migration-guide.md).

## Core Concepts

ParquetFrame is built around a few key concepts:

*   **[DataFrameProxy](../documentation-examples/api-core.md)**: The main entry point for data operations.
*   **[Entities](../documentation-examples/api-entities.md)**: Define schema and relationships for your data.
*   **[Permissions](../documentation-examples/api-permissions.md)**: Manage access control with Zanzibar-style tuples.

**API Documentation:**

- **[Core API Reference](../documentation-examples/api-core.md)** - Complete core API documentation
- **[Entity API Reference](../documentation-examples/api-entities.md)** - Entity framework APIs
- **[Permissions API Reference](../documentation-examples/api-permissions.md)** - Zanzibar permission APIs

## Need Help?

- Browse **[examples](../documentation-examples/examples-gallery.md)** for common use cases
- Check the **[Migration Guide](../legacy-migration/migration-guide.md)** if coming from Phase 1
- Report issues on **[GitHub](https://github.com/leechristophermurray/parquetframe/issues)**

Happy building! 🚀
```
