"""
Main application class for the Todo/Kanban system.

This module provides the TodoKanbanApp class which orchestrates:
- Entity management (User, Board, TaskList, Task)
- Permission management using Zanzibar ReBAC
- CRUD operations with permission validation
- Multi-user collaboration
"""

import time
import uuid
from datetime import datetime

from .models import Board, Task, TaskList, User
from .permissions import PermissionManager


class PermissionError(Exception):
    """Raised when a user lacks required permissions."""

    pass


class ValidationError(Exception):
    """Raised when entity validation fails."""

    pass


class TodoKanbanApp:
    """
    Main application class for the Todo/Kanban system.

    Provides a high-level API for managing boards, lists, and tasks with
    built-in permission checking using Zanzibar-style ReBAC.

    Features:
        - User management
        - Board creation and sharing
        - Task list management
        - Task CRUD with assignment
        - Permission-based access control
        - Task state transitions

    Example:
        >>> app = TodoKanbanApp()
        >>> alice = app.create_user("alice", "alice@example.com")
        >>> board = app.create_board(alice.user_id, "My Board", "Description")
        >>> app.share_board(board.board_id, alice.user_id, bob.user_id, "editor")
    """

    def __init__(self, storage_base: str = "./kanban_data"):
        """
        Initialize the Todo/Kanban application.

        Args:
            storage_base: Base path for entity and permission storage
        """
        self.storage_base = storage_base
        self.permissions = PermissionManager(f"{storage_base}/permissions")

    # =========================================================================
    # User Management
    # =========================================================================

    def create_user(self, username: str, email: str) -> User:
        """
        Create a new user.

        Args:
            username: Username
            email: Email address

        Returns:
            Created User entity

        Example:
            >>> user = app.create_user("alice", "alice@example.com")
        """
        # Generate unique ID with timestamp and random component
        user_id = f"user_{username}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        user = User(user_id=user_id, username=username, email=email)
        user.save()
        return user

    def get_user(self, user_id: str) -> User | None:
        """Get a user by ID."""
        return User.find(user_id)

    # =========================================================================
    # Board Management
    # =========================================================================

    def create_board(self, owner_id: str, name: str, description: str = "") -> Board:
        """
        Create a new board.

        Automatically grants owner permissions to the creator.

        Args:
            owner_id: User ID of the board owner
            name: Board name
            description: Board description

        Returns:
            Created Board entity

        Example:
            >>> board = app.create_board(user.user_id, "Project Alpha", "Sprint board")
        """
        # Generate unique ID with timestamp and random component
        board_id = f"board_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        board = Board(
            board_id=board_id,
            name=name,
            description=description,
            owner_id=owner_id,
        )
        board.save()

        # Grant owner permissions
        self.permissions.grant_board_access(owner_id, board_id, "owner")

        return board

    def get_board(self, board_id: str) -> Board | None:
        """Get a board by ID."""
        return Board.find(board_id)

    def get_user_boards(self, user_id: str) -> list[Board]:
        """
        Get all boards accessible by a user.

        Uses permission system to filter boards.

        Args:
            user_id: User ID

        Returns:
            List of accessible Board entities

        Example:
            >>> boards = app.get_user_boards(user.user_id)
        """
        # Get all boards user has access to
        accessible = self.permissions.list_user_permissions(
            user_id, resource_type="board"
        )

        boards = []
        for _, board_id in accessible:
            board = Board.find(board_id)
            if board:
                boards.append(board)

        return boards

    def share_board(
        self, board_id: str, owner_id: str, target_user_id: str, role: str
    ) -> None:
        """
        Share a board with another user.

        Only board owners can share boards.

        Args:
            board_id: Board ID
            owner_id: ID of user performing the share (must be owner)
            target_user_id: ID of user to grant access to
            role: Role to grant (owner, editor, viewer)

        Raises:
            PermissionError: If owner_id is not the board owner

        Example:
            >>> app.share_board(board.board_id, alice.user_id, bob.user_id, "editor")
        """
        # Check if user is owner
        if not self.permissions.check_board_access(owner_id, board_id, "owner"):
            raise PermissionError(
                f"User {owner_id} does not have owner access to board {board_id}"
            )

        # Grant access to target user
        self.permissions.grant_board_access(target_user_id, board_id, role)

    def delete_board(self, board_id: str, user_id: str) -> None:
        """
        Delete a board.

        Only board owners can delete boards.

        Args:
            board_id: Board ID
            user_id: User ID performing the deletion

        Raises:
            PermissionError: If user is not the board owner
        """
        if not self.permissions.check_board_access(user_id, board_id, "owner"):
            raise PermissionError(
                f"User {user_id} does not have permission to delete board {board_id}"
            )

        # Delete board
        Board.delete(board_id)

        # Revoke all permissions
        for role in ["owner", "editor", "viewer"]:
            users = self.permissions.list_resource_permissions("board", board_id, role)
            for _, uid in users:
                self.permissions.revoke_board_access(uid, board_id, role)

    # =========================================================================
    # List Management
    # =========================================================================

    def add_list(
        self, board_id: str, user_id: str, name: str, position: int = 0
    ) -> TaskList:
        """
        Add a list to a board.

        Requires editor or owner permissions on the board.

        Args:
            board_id: Board ID
            user_id: User ID performing the operation
            name: List name (e.g., "Todo", "In Progress", "Done")
            position: Display position

        Returns:
            Created TaskList entity

        Raises:
            PermissionError: If user lacks editor permissions

        Example:
            >>> todo_list = app.add_list(board.board_id, user.user_id, "Todo", 0)
        """
        # Check permissions
        if not self.permissions.check_board_access(user_id, board_id, "editor"):
            raise PermissionError(
                f"User {user_id} does not have editor access to board {board_id}"
            )

        # Generate unique ID with timestamp and random component
        list_id = f"list_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        task_list = TaskList(
            list_id=list_id, name=name, board_id=board_id, position=position
        )
        task_list.save()

        # Inherit board permissions
        self.permissions.inherit_board_permissions(board_id, list_id)

        return task_list

    def get_list(self, list_id: str) -> TaskList | None:
        """Get a list by ID."""
        return TaskList.find(list_id)

    def get_board_lists(self, board_id: str, user_id: str) -> list[TaskList]:
        """
        Get all lists in a board accessible by a user.

        Args:
            board_id: Board ID
            user_id: User ID

        Returns:
            List of accessible TaskList entities

        Example:
            >>> lists = app.get_board_lists(board.board_id, user.user_id)
        """
        # Check board access
        if not self.permissions.check_board_access(user_id, board_id, "viewer"):
            return []

        # Get all lists for the board
        all_lists = TaskList.find_by(board_id=board_id)

        # Filter by permissions
        accessible_lists = []
        for task_list in all_lists:
            if self.permissions.check_list_access(
                user_id, task_list.list_id, board_id, "viewer"
            ):
                accessible_lists.append(task_list)

        # Sort by position
        accessible_lists.sort(key=lambda x: x.position)
        return accessible_lists

    def delete_list(self, list_id: str, user_id: str, board_id: str) -> None:
        """
        Delete a list.

        Requires editor permissions on the board.

        Args:
            list_id: List ID
            user_id: User ID performing the deletion
            board_id: Board ID

        Raises:
            PermissionError: If user lacks editor permissions
        """
        if not self.permissions.check_board_access(user_id, board_id, "editor"):
            raise PermissionError(
                f"User {user_id} does not have permission to delete list {list_id}"
            )

        TaskList.delete(list_id)

    # =========================================================================
    # Task Management
    # =========================================================================

    def create_task(
        self,
        list_id: str,
        user_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        assigned_to: str | None = None,
    ) -> Task:
        """
        Create a new task.

        Requires editor permissions on the parent list/board.

        Args:
            list_id: List ID
            user_id: User ID performing the operation
            title: Task title
            description: Task description
            priority: Task priority (low, medium, high)
            assigned_to: Optional user ID to assign task to

        Returns:
            Created Task entity

        Raises:
            PermissionError: If user lacks editor permissions

        Example:
            >>> task = app.create_task(
            ...     list_id=todo_list.list_id,
            ...     user_id=user.user_id,
            ...     title="Setup database",
            ...     priority="high",
            ...     assigned_to=user.user_id
            ... )
        """
        # Get list to find board_id
        task_list = TaskList.find(list_id)
        if not task_list:
            raise ValidationError(f"List {list_id} not found")

        # Check permissions
        if not self.permissions.check_list_access(
            user_id, list_id, task_list.board_id, "editor"
        ):
            raise PermissionError(
                f"User {user_id} does not have editor access to list {list_id}"
            )

        # Generate unique ID with timestamp and random component
        task_id = f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            status="todo",
            priority=priority,
            list_id=list_id,
            assigned_to=assigned_to,
        )
        task.save()

        # Inherit list permissions
        self.permissions.inherit_list_permissions(list_id, task_id)

        # Grant assignee editor access
        if assigned_to:
            self.permissions.grant_task_assignee_access(assigned_to, task_id)

        return task

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return Task.find(task_id)

    def get_list_tasks(self, list_id: str, user_id: str) -> list[Task]:
        """
        Get all tasks in a list accessible by a user.

        Args:
            list_id: List ID
            user_id: User ID

        Returns:
            List of accessible Task entities

        Example:
            >>> tasks = app.get_list_tasks(todo_list.list_id, user.user_id)
        """
        # Get list to find board_id
        task_list = TaskList.find(list_id)
        if not task_list:
            return []

        # Check list access
        if not self.permissions.check_list_access(
            user_id, list_id, task_list.board_id, "viewer"
        ):
            return []

        # Get all tasks for the list
        all_tasks = Task.find_by(list_id=list_id)

        # Filter by permissions
        accessible_tasks = []
        for task in all_tasks:
            if self.permissions.check_task_access(
                user_id, task.task_id, list_id, task_list.board_id, "viewer"
            ):
                accessible_tasks.append(task)

        return accessible_tasks

    def assign_task(self, task_id: str, user_id: str, assigned_to: str) -> Task:
        """
        Assign a task to a user.

        Requires editor permissions on the task.

        Args:
            task_id: Task ID
            user_id: User ID performing the operation
            assigned_to: User ID to assign task to

        Returns:
            Updated Task entity

        Raises:
            PermissionError: If user lacks editor permissions

        Example:
            >>> task = app.assign_task(task.task_id, alice.user_id, bob.user_id)
        """
        # Get task to find list and board
        task = Task.find(task_id)
        if not task:
            raise ValidationError(f"Task {task_id} not found")

        task_list = TaskList.find(task.list_id)
        if not task_list:
            raise ValidationError(f"List {task.list_id} not found")

        # Check permissions
        if not self.permissions.check_task_access(
            user_id, task_id, task.list_id, task_list.board_id, "editor"
        ):
            raise PermissionError(
                f"User {user_id} does not have editor access to task {task_id}"
            )

        # Update assignment
        task.assigned_to = assigned_to
        task.updated_at = datetime.now()
        task.save()

        # Grant assignee editor access
        self.permissions.grant_task_assignee_access(assigned_to, task_id)

        return task

    def move_task(
        self, task_id: str, user_id: str, new_list_id: str, new_position: int = 0
    ) -> Task:
        """
        Move a task to a different list.

        Requires editor permissions on both source and destination lists.

        Args:
            task_id: Task ID
            user_id: User ID performing the operation
            new_list_id: Destination list ID
            new_position: New position in destination list

        Returns:
            Updated Task entity

        Raises:
            PermissionError: If user lacks editor permissions

        Example:
            >>> task = app.move_task(task.task_id, user.user_id, done_list.list_id)
        """
        # Get task and lists
        task = Task.find(task_id)
        if not task:
            raise ValidationError(f"Task {task_id} not found")

        old_list = TaskList.find(task.list_id)
        new_list = TaskList.find(new_list_id)

        if not old_list or not new_list:
            raise ValidationError("Source or destination list not found")

        # Check permissions on old list
        if not self.permissions.check_list_access(
            user_id, task.list_id, old_list.board_id, "editor"
        ):
            raise PermissionError(
                f"User {user_id} does not have editor access to source list"
            )

        # Check permissions on new list
        if not self.permissions.check_list_access(
            user_id, new_list_id, new_list.board_id, "editor"
        ):
            raise PermissionError(
                f"User {user_id} does not have editor access to destination list"
            )

        # Update task
        task.list_id = new_list_id
        task.updated_at = datetime.now()
        task.save()

        # Update status based on list name if applicable
        if "done" in new_list.name.lower():
            task.status = "done"
        elif "progress" in new_list.name.lower():
            task.status = "in_progress"
        else:
            task.status = "todo"
        task.save()

        return task

    def update_task_status(self, task_id: str, user_id: str, new_status: str) -> Task:
        """
        Update a task's status.

        Requires editor permissions on the task.

        Args:
            task_id: Task ID
            user_id: User ID performing the operation
            new_status: New status (todo, in_progress, done)

        Returns:
            Updated Task entity

        Raises:
            PermissionError: If user lacks editor permissions
            ValidationError: If status is invalid

        Example:
            >>> task = app.update_task_status(task.task_id, user.user_id, "done")
        """
        # Get task
        task = Task.find(task_id)
        if not task:
            raise ValidationError(f"Task {task_id} not found")

        task_list = TaskList.find(task.list_id)
        if not task_list:
            raise ValidationError(f"List {task.list_id} not found")

        # Check permissions
        if not self.permissions.check_task_access(
            user_id, task_id, task.list_id, task_list.board_id, "editor"
        ):
            raise PermissionError(
                f"User {user_id} does not have editor access to task {task_id}"
            )

        # Validate status
        if new_status not in ["todo", "in_progress", "done"]:
            raise ValidationError(f"Invalid status: {new_status}")

        # Update status
        task.status = new_status
        task.updated_at = datetime.now()
        task.save()

        return task

    def delete_task(self, task_id: str, user_id: str) -> None:
        """
        Delete a task.

        Requires editor permissions on the task.

        Args:
            task_id: Task ID
            user_id: User ID performing the deletion

        Raises:
            PermissionError: If user lacks editor permissions
        """
        # Get task
        task = Task.find(task_id)
        if not task:
            raise ValidationError(f"Task {task_id} not found")

        task_list = TaskList.find(task.list_id)
        if not task_list:
            raise ValidationError(f"List {task.list_id} not found")

        # Check permissions
        if not self.permissions.check_task_access(
            user_id, task_id, task.list_id, task_list.board_id, "editor"
        ):
            raise PermissionError(
                f"User {user_id} does not have permission to delete task {task_id}"
            )

        Task.delete(task_id)

    # =========================================================================
    # Convenience Permission Check Methods
    # =========================================================================

    def check_list_access(
        self, user_id: str, list_id: str, required_role: str = "viewer"
    ) -> bool:
        """
        Check if user has required list access (convenience wrapper).

        Automatically looks up board_id from list_id.

        Args:
            user_id: User ID to check
            list_id: List ID
            required_role: Minimum required role

        Returns:
            True if user has required access
        """
        task_list = TaskList.find(list_id)
        if not task_list:
            return False

        return self.permissions.check_list_access(
            user_id, list_id, task_list.board_id, required_role
        )

    def check_task_access(
        self, user_id: str, task_id: str, required_role: str = "viewer"
    ) -> bool:
        """
        Check if user has required task access (convenience wrapper).

        Automatically looks up list_id and board_id from task_id.

        Args:
            user_id: User ID to check
            task_id: Task ID
            required_role: Minimum required role

        Returns:
            True if user has required access
        """
        task = Task.find(task_id)
        if not task:
            return False

        task_list = TaskList.find(task.list_id)
        if not task_list:
            return False

        return self.permissions.check_task_access(
            user_id, task_id, task.list_id, task_list.board_id, required_role
        )


# Export main class
__all__ = ["TodoKanbanApp", "PermissionError", "ValidationError"]
