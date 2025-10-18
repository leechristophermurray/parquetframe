# Todo/Kanban Application - ParquetFrame Integration Example

A comprehensive multi-user Todo/Kanban application demonstrating ParquetFrame's advanced features including Entity Framework decorators (`@entity`, `@rel`), Zanzibar-style ReBAC permissions, and YAML workflow ETL pipelines.

## 📋 Overview

This example implements a complete Kanban board system with:
- **Multi-user collaboration** with role-based access control
- **Entity relationships** using declarative decorators
- **Zanzibar permissions** with all 4 core APIs (check, expand, list_objects, list_subjects)
- **Permission inheritance** from boards → lists → tasks
- **ETL workflows** for importing, exporting, and analyzing task data
- **Comprehensive testing** covering all features

## 🏗️ Architecture

### Entity Model

```
User
├── user_id (PK)
├── username
├── email
└── created_at

Board
├── board_id (PK)
├── name
├── description
├── owner_id (FK → User)
├── created_at
└── updated_at

TaskList
├── list_id (PK)
├── name
├── board_id (FK → Board)
├── position
├── created_at
└── updated_at

Task
├── task_id (PK)
├── title
├── description
├── status (enum: todo, in_progress, done, blocked)
├── priority (enum: low, medium, high, urgent)
├── list_id (FK → TaskList)
├── assigned_to (FK → User)
├── created_at
└── updated_at
```

### Relationships

- **User.boards** ← Board.owner (one-to-many)
- **Board.lists** ← TaskList.board (one-to-many)
- **TaskList.tasks** ← Task.list (one-to-many)
- **User.assigned_tasks** ← Task.assigned_user (one-to-many)

### Permission Model

The application implements **Zanzibar-style ReBAC** (Relationship-Based Access Control):

```
┌─────────────────┐
│     Board       │
│   Permissions   │
│                 │
│  owner: write   │  ← Full control
│  editor: edit   │  ← Can edit content
│  viewer: read   │  ← Read-only access
└────────┬────────┘
         │ (inherits)
         ↓
┌─────────────────┐
│    TaskList     │
│   Permissions   │
│                 │
│  parent: Board  │  ← Inherits board permissions
└────────┬────────┘
         │ (inherits)
         ↓
┌─────────────────┐
│      Task       │
│   Permissions   │
│                 │
│  parent: List   │  ← Inherits list permissions
│  assignee: edit │  ← Direct permission
└─────────────────┘
```

**Permission Inheritance Rules:**
1. Board `owner` → full access to all lists and tasks in board
2. Board `editor` → edit access to all lists and tasks in board
3. Board `viewer` → read access to all lists and tasks in board
4. Task `assignee` → edit access to assigned task (direct permission)

## ✨ Features Demonstrated

### Entity Framework
- ✅ `@entity` decorator with storage_path and primary_key
- ✅ `@rel` decorator for foreign key relationships
- ✅ Reverse relationships (e.g., `board.lists`, `user.boards`)
- ✅ Automatic relationship traversal
- ✅ Entity persistence to Parquet files

### Zanzibar Permissions
- ✅ **check(user, resource, relation)** - Verify permission
- ✅ **expand(resource, relation)** - Get permission tree
- ✅ **list_objects(user, resource_type, relation)** - List accessible resources
- ✅ **list_subjects(resource, relation)** - List users with access
- ✅ Permission inheritance with transitive relationships
- ✅ Permission revocation and propagation
- ✅ Multiple permission paths to same resource

### YAML Workflows
- ✅ ETL pipeline for importing tasks from CSV/JSON
- ✅ Report generation with filtering and aggregations
- ✅ Comprehensive analytics with groupby operations
- ✅ Variable interpolation (`${variable_name}`)
- ✅ Multi-format outputs (CSV, Parquet, JSON)

### Multi-User Collaboration
- ✅ Board sharing with different roles (owner, editor, viewer)
- ✅ Task assignment and reassignment
- ✅ Concurrent operations by multiple users
- ✅ Permission-based filtering of resources
- ✅ Role-based operation restrictions

## 🚀 Installation

### Prerequisites

```bash
# Ensure ParquetFrame is installed
pip install -e /path/to/parquetframe

# Or if from PyPI
pip install parquetframe
```

### Project Setup

```bash
cd examples/integration/todo_kanban

# The application will create storage directories automatically:
# - ./kanban_data/users/
# - ./kanban_data/boards/
# - ./kanban_data/lists/
# - ./kanban_data/tasks/
# - ./kanban_data/permissions/
```

## 📖 Quick Start

### Running the Demo

```bash
# Run the interactive demo
python demo.py
```

The demo will:
1. Create three users (Alice, Bob, Charlie)
2. Create a board with lists (Todo, In Progress, Done)
3. Create and assign tasks
4. Demonstrate permission inheritance
5. Show all 4 Zanzibar permission APIs in action
6. Demonstrate task state transitions
7. Show permission revocation effects

### Basic Usage Example

```python
from examples.integration.todo_kanban import TodoKanbanApp

# Initialize the application
app = TodoKanbanApp()

# Create users
alice = app.create_user("alice", "alice@example.com")
bob = app.create_user("bob", "bob@example.com")

# Alice creates a board
board = app.create_board(
    alice.user_id,
    "Project Alpha",
    "Main project board"
)

# Alice adds lists
todo_list = app.add_list(board.board_id, alice.user_id, "Todo", 0)
progress_list = app.add_list(board.board_id, alice.user_id, "In Progress", 1)
done_list = app.add_list(board.board_id, alice.user_id, "Done", 2)

# Alice creates a task
task = app.create_task(
    todo_list.list_id,
    alice.user_id,
    "Setup database",
    "Configure PostgreSQL",
    "high"
)

# Alice shares board with Bob as editor
app.share_board(board.board_id, alice.user_id, bob.user_id, "editor")

# Bob can now create tasks
bob_task = app.create_task(
    todo_list.list_id,
    bob.user_id,
    "Write tests",
    "Unit and integration tests",
    "medium"
)

# Alice moves task to In Progress
app.move_task(task.task_id, alice.user_id, progress_list.list_id, 0)

# Check permissions
can_edit = app.permissions.check_permission(
    bob.user_id,
    "task",
    task.task_id,
    "edit"
)
print(f"Bob can edit task: {can_edit}")  # True (via board editor role)
```

## 📚 API Reference

### TodoKanbanApp Class

#### User Management

**`create_user(username: str, email: str) -> User`**
- Creates a new user
- Returns User entity

```python
user = app.create_user("alice", "alice@example.com")
```

#### Board Management

**`create_board(owner_id: str, name: str, description: str = "") -> Board`**
- Creates a new board
- Automatically grants owner permissions to creator
- Returns Board entity

```python
board = app.create_board(user.user_id, "My Board", "Description")
```

**`share_board(board_id: str, owner_id: str, target_user_id: str, role: str)`**
- Shares board with another user
- Roles: `"owner"`, `"editor"`, `"viewer"`
- Requires owner permissions to share

```python
app.share_board(board.board_id, alice.user_id, bob.user_id, "editor")
```

**`get_user_boards(user_id: str) -> List[Board]`**
- Returns boards user has access to
- Filtered by permissions

```python
boards = app.get_user_boards(user.user_id)
```

#### List Management

**`add_list(board_id: str, user_id: str, name: str, position: int) -> TaskList`**
- Adds a list to a board
- Requires editor or owner permissions on board
- Returns TaskList entity

```python
task_list = app.add_list(board.board_id, user.user_id, "Todo", 0)
```

**`get_board_lists(board_id: str, user_id: str) -> List[TaskList]`**
- Returns lists in a board
- Requires read permissions on board

```python
lists = app.get_board_lists(board.board_id, user.user_id)
```

#### Task Management

**`create_task(list_id: str, user_id: str, title: str, description: str = "", priority: str = "medium") -> Task`**
- Creates a task in a list
- Priority: `"low"`, `"medium"`, `"high"`, `"urgent"`
- Requires editor or owner permissions on list
- Returns Task entity

```python
task = app.create_task(
    list_id,
    user.user_id,
    "Task title",
    "Task description",
    "high"
)
```

**`assign_task(task_id: str, user_id: str, assigned_to: str) -> Task`**
- Assigns task to a user
- Grants assignee edit permissions to task
- Requires editor or owner permissions on task

```python
app.assign_task(task.task_id, alice.user_id, bob.user_id)
```

**`move_task(task_id: str, user_id: str, new_list_id: str, new_position: int) -> Task`**
- Moves task to a different list
- Updates task position
- Requires edit permissions on both source and target lists

```python
app.move_task(task.task_id, user.user_id, progress_list.list_id, 0)
```

**`update_task_status(task_id: str, user_id: str, new_status: str) -> Task`**
- Updates task status
- Status: `"todo"`, `"in_progress"`, `"done"`, `"blocked"`
- Requires edit permissions on task

```python
app.update_task_status(task.task_id, user.user_id, "done")
```

**`get_list_tasks(list_id: str, user_id: str) -> List[Task]`**
- Returns tasks in a list
- Filtered by user permissions

```python
tasks = app.get_list_tasks(list_id, user.user_id)
```

### Permission Manager

**`check_permission(user_id: str, resource_type: str, resource_id: str, relation: str) -> bool`**
- Checks if user has permission on resource
- Returns True if permitted, False otherwise

```python
has_access = app.permissions.check_permission(
    user.user_id,
    "board",
    board.board_id,
    "edit"
)
```

**`list_user_permissions(user_id: str, resource_type: str = None) -> List[Tuple]`**
- Lists all resources user has access to
- Optionally filter by resource_type

```python
resources = app.permissions.list_user_permissions(user.user_id, "board")
```

**`list_resource_permissions(resource_type: str, resource_id: str) -> List[Tuple]`**
- Lists all users with access to resource

```python
users = app.permissions.list_resource_permissions("board", board.board_id)
```

**`expand_permissions(resource_type: str, resource_id: str) -> Dict`**
- Returns permission tree for resource

```python
tree = app.permissions.expand_permissions("board", board.board_id)
```

## 🔄 YAML Workflows

### Import Tasks Workflow

Import tasks from external CSV or JSON files with validation.

```bash
# Run with default variables
python -m parquetframe.workflows.engine workflows/import_tasks.yml

# Override variables
python -m parquetframe.workflows.engine workflows/import_tasks.yml \
  --var source_file=data/sample_tasks.csv \
  --var target_list_id=list_001 \
  --var user_id=user_001
```

**Features:**
- Reads CSV or JSON task data
- Validates required fields (task_id, title)
- Validates enum values (status, priority)
- Filters tasks by target list
- Generates import statistics
- Saves validated tasks to storage

### Export Report Workflow

Export filtered task reports with aggregations.

```bash
# Run with default variables
python -m parquetframe.workflows.engine workflows/export_report.yml

# Filter by status
python -m parquetframe.workflows.engine workflows/export_report.yml \
  --var filter_status=in_progress \
  --var output_csv=reports/active_tasks.csv
```

**Features:**
- Loads tasks, users, lists, and boards
- Filters by status, priority, date range
- Joins related entity data
- Calculates summary statistics by status, priority, user
- Saves to CSV and Parquet formats

### Task Analytics Workflow

Generate comprehensive task analytics and metrics.

```bash
# Run with default variables
python -m parquetframe.workflows.engine workflows/task_analytics.yml

# Filter by date range
python -m parquetframe.workflows.engine workflows/task_analytics.yml \
  --var start_date=2024-01-01 \
  --var end_date=2024-12-31 \
  --var output_dir=analytics
```

**Features:**
- Analytics by status, priority, user, list
- Cross-tabulation (status × priority matrix)
- Completion rate analysis (done vs active)
- High-priority task identification
- Blocked task analysis
- User workload metrics
- Multiple output formats (Parquet, CSV)

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/integration/test_todo_kanban.py -v

# Run specific test class
pytest tests/integration/test_todo_kanban.py::TestPermissions -v

# Run with coverage
pytest tests/integration/test_todo_kanban.py \
  --cov=examples.integration.todo_kanban \
  --cov-report=html \
  --cov-report=term
```

### Test Structure

- **TestEntityModels** - Entity CRUD and relationships (14 tests)
- **TestPermissions** - Zanzibar permission APIs (18 tests)
- **TestMultiUserWorkflows** - Multi-user scenarios (12 tests)
- **TestTaskStateTransitions** - Task lifecycle (13 tests)
- **TestWorkflowETL** - YAML workflow execution (18 tests)
- **TestIntegrationScenarios** - End-to-end scenarios (15 tests)

**Total: 90+ comprehensive tests**

## 💡 Common Use Cases

### Scenario 1: Project Team Collaboration

```python
# Manager creates project board
manager = app.create_user("manager", "manager@company.com")
project = app.create_board(manager.user_id, "Q4 Project", "Q4 objectives")

# Add sprint lists
backlog = app.add_list(project.board_id, manager.user_id, "Backlog", 0)
sprint = app.add_list(project.board_id, manager.user_id, "Current Sprint", 1)
done = app.add_list(project.board_id, manager.user_id, "Done", 2)

# Share with team members
app.share_board(project.board_id, manager.user_id, developer.user_id, "editor")
app.share_board(project.board_id, manager.user_id, designer.user_id, "editor")
app.share_board(project.board_id, manager.user_id, stakeholder.user_id, "viewer")

# Team members can now collaborate
task = app.create_task(backlog.list_id, developer.user_id, "Build API", "", "high")
app.assign_task(task.task_id, manager.user_id, developer.user_id)
```

### Scenario 2: Personal Task Management

```python
# Individual user creates personal board
user = app.create_user("john", "john@personal.com")
personal = app.create_board(user.user_id, "Personal Tasks", "My todo list")

# Organize by category
work = app.add_list(personal.board_id, user.user_id, "Work", 0)
home = app.add_list(personal.board_id, user.user_id, "Home", 1)
shopping = app.add_list(personal.board_id, user.user_id, "Shopping", 2)

# Create tasks
app.create_task(work.list_id, user.user_id, "Finish report", "", "high")
app.create_task(home.list_id, user.user_id, "Fix leaky faucet", "", "medium")
app.create_task(shopping.list_id, user.user_id, "Buy groceries", "", "low")
```

### Scenario 3: Permission Auditing

```python
# List all boards a user can access
boards = app.get_user_boards(user.user_id)
print(f"User has access to {len(boards)} boards")

# Check specific permission
can_edit = app.permissions.check_permission(
    user.user_id, "board", board.board_id, "edit"
)

# Get full permission tree for a board
tree = app.permissions.expand_permissions("board", board.board_id)
print(f"Permission tree: {tree}")

# List all users with access to a board
users_with_access = app.permissions.list_resource_permissions(
    "board", board.board_id
)
print(f"{len(users_with_access)} users have access")
```

## 🔍 Data Storage

All data is stored in Parquet format under `./kanban_data/`:

```
kanban_data/
├── users/           # User entities
├── boards/          # Board entities
├── lists/           # TaskList entities
├── tasks/           # Task entities
└── permissions/     # Permission tuples
```

Each entity type is stored in its own directory with Parquet files providing:
- Efficient storage and fast queries
- Schema evolution support
- Compression (Snappy by default)
- Columnar format for analytics

## 🚦 Limitations & Future Enhancements

### Current Limitations

- Workflows use placeholders for JOIN operations (requires custom transforms)
- Permission filtering in workflows needs custom transform functions
- Time series analysis requires date component extraction
- No built-in task history/audit trail

### Planned Enhancements

- [ ] Add JOIN step type to workflow engine
- [ ] Implement audit trail for task changes
- [ ] Add webhook/notification system
- [ ] Support for task dependencies
- [ ] Task templates and recurring tasks
- [ ] Board templates
- [ ] Advanced analytics dashboard
- [ ] Real-time collaboration support

## 📝 License

This example is part of the ParquetFrame project and follows the same license.

## 🤝 Contributing

Contributions are welcome! This example demonstrates:
- Best practices for entity modeling with ParquetFrame
- Zanzibar-style permission patterns
- YAML workflow design patterns
- Comprehensive testing strategies

Use this as a reference for building your own ParquetFrame applications.

## 📞 Support

For questions or issues:
- Open an issue in the ParquetFrame repository
- Check the ParquetFrame documentation
- Review the test suite for usage examples

---

**Built with ParquetFrame** - A powerful Python framework for entity management, permissions, and data workflows backed by Parquet storage.
