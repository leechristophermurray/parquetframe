"""
Todo/Kanban Integration Example for ParquetFrame.

This package demonstrates:
- Entity Framework with @entity and @rel decorators
- Zanzibar-style permissions with all 4 APIs
- Multi-user collaboration
- Permission inheritance
- YAML workflow ETL pipelines

Example:
    >>> from examples.integration.todo_kanban import TodoKanbanApp
    >>> app = TodoKanbanApp()
    >>> user = app.create_user("alice", "alice@example.com")
    >>> board = app.create_board(user.user_id, "My Board", "Description")
"""

from .app import PermissionError, TodoKanbanApp, ValidationError
from .models import Board, Task, TaskList, User
from .permissions import PermissionManager

__all__ = [
    "TodoKanbanApp",
    "PermissionManager",
    "User",
    "Board",
    "TaskList",
    "Task",
    "PermissionError",
    "ValidationError",
]

__version__ = "1.0.0"
