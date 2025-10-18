"""
Entity models for the Todo/Kanban application.

This module defines the core data models using ParquetFrame's Entity Framework:
- User: Application users
- Board: Top-level kanban boards
- TaskList: Lists within boards (columns)
- Task: Individual tasks

All entities use the @entity decorator for persistence and @rel decorator for relationships.
"""

from dataclasses import dataclass
from datetime import datetime

from parquetframe.entity import entity, rel


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


@entity(storage_path="./kanban_data/boards", primary_key="board_id")
@dataclass
class Board:
    """
    Board entity representing a kanban board.

    Fields:
        board_id: Unique board identifier
        name: Board name
        description: Board description
        owner_id: ID of the user who owns this board
        created_at: Timestamp when board was created
        updated_at: Timestamp when board was last updated

    Relationships:
        owner: Forward relationship to User (board owner)
        lists: Reverse relationship to TaskLists in this board
    """

    board_id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize timestamps if not provided."""
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


@entity(storage_path="./kanban_data/lists", primary_key="list_id")
@dataclass
class TaskList:
    """
    TaskList entity representing a list/column in a board.

    Fields:
        list_id: Unique list identifier
        name: List name (e.g., "Todo", "In Progress", "Done")
        board_id: ID of the board this list belongs to
        position: Display position of the list (0-indexed)
        created_at: Timestamp when list was created
        updated_at: Timestamp when list was last updated

    Relationships:
        board: Forward relationship to Board (parent board)
        tasks: Reverse relationship to Tasks in this list
    """

    list_id: str
    name: str
    board_id: str
    position: int = 0
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @rel("Board", foreign_key="board_id")
    def board(self):
        """Get the board this list belongs to."""
        pass

    @rel("Task", foreign_key="list_id", reverse=True)
    def tasks(self):
        """Get all tasks in this list."""
        pass


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

    def __post_init__(self):
        """Initialize timestamps if not provided."""
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


# Export all models
__all__ = ["User", "Board", "TaskList", "Task"]
