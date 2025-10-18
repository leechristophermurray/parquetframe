"""
Permission management for the Todo/Kanban application using Zanzibar-style ReBAC.

This module implements a comprehensive permission system with:
- TupleStore for storing relation tuples
- All 4 Zanzibar APIs: check(), expand(), list_objects(), list_subjects()
- Permission inheritance (Board → List → Task)
- Role-based access control (owner, editor, viewer)
"""

from parquetframe.permissions import (
    RelationTuple,
    TupleStore,
    check,
    expand,
    list_objects,
    list_subjects,
)


class PermissionManager:
    """
    Permission manager for the Todo/Kanban application.

    Implements Zanzibar-style permission checking with:
    - Direct permissions
    - Permission inheritance (board → list → task)
    - Role-based access control

    Permission Model:
        Boards:
            - owner: Full control (create/edit/delete lists and tasks, manage permissions)
            - editor: Can create and edit lists and tasks, but cannot delete board
            - viewer: Read-only access to board, lists, and tasks

        Lists:
            - Inherit board permissions
            - Can have additional direct permissions

        Tasks:
            - Inherit list permissions
            - Assignees automatically get edit access
            - Can have additional direct permissions
    """

    def __init__(self, storage_path: str = "./kanban_data/permissions"):
        """
        Initialize the permission manager.

        Args:
            storage_path: Path to store permission tuples
        """
        self.store = TupleStore()
        self.storage_path = storage_path

    # =========================================================================
    # Core Permission Operations
    # =========================================================================

    def grant_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        relation: str,
    ) -> None:
        """
        Grant a permission to a user.

        Args:
            user_id: User ID to grant permission to
            resource_type: Type of resource (board, list, task)
            resource_id: ID of the resource
            relation: Relation/permission type (owner, editor, viewer)
        """
        tuple_obj = RelationTuple(
            namespace=resource_type,
            object_id=resource_id,
            relation=relation,
            subject_namespace="user",
            subject_id=user_id,
        )
        self.store.add_tuple(tuple_obj)

    def revoke_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        relation: str,
    ) -> None:
        """
        Revoke a permission from a user.

        Args:
            user_id: User ID to revoke permission from
            resource_type: Type of resource (board, list, task)
            resource_id: ID of the resource
            relation: Relation/permission type (owner, editor, viewer)
        """
        tuple_obj = RelationTuple(
            namespace=resource_type,
            object_id=resource_id,
            relation=relation,
            subject_namespace="user",
            subject_id=user_id,
        )
        self.store.remove_tuple(tuple_obj)

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

    def list_user_permissions(
        self,
        user_id: str,
        resource_type: str | None = None,
        relation: str | None = None,
    ) -> list[tuple[str, str]]:
        """
        List all resources a user has access to.

        Uses Zanzibar expand() API to find all accessible resources.

        Args:
            user_id: User ID to list permissions for
            resource_type: Optional filter by resource type
            relation: Optional filter by relation type

        Returns:
            List of (resource_type, resource_id) tuples
        """
        if relation is None:
            # Get permissions for all relation types
            all_perms = []
            for rel in ["owner", "editor", "viewer"]:
                perms = expand(
                    store=self.store,
                    subject_namespace="user",
                    subject_id=user_id,
                    relation=rel,
                    object_namespace=resource_type,
                    allow_indirect=True,
                )
                all_perms.extend(perms)
            return list(set(all_perms))  # Remove duplicates
        else:
            return expand(
                store=self.store,
                subject_namespace="user",
                subject_id=user_id,
                relation=relation,
                object_namespace=resource_type,
                allow_indirect=True,
            )

    def list_resource_permissions(
        self,
        resource_type: str,
        resource_id: str,
        relation: str | None = None,
    ) -> list[tuple[str, str]]:
        """
        List all users who have access to a resource.

        Uses Zanzibar list_subjects() API.

        Args:
            resource_type: Type of resource (board, list, task)
            resource_id: ID of the resource
            relation: Optional filter by relation type

        Returns:
            List of (subject_namespace, subject_id) tuples
        """
        if relation is None:
            # Get all users with any permission
            all_users = []
            for rel in ["owner", "editor", "viewer"]:
                users = list_subjects(
                    store=self.store,
                    relation=rel,
                    object_namespace=resource_type,
                    object_id=resource_id,
                    subject_namespace="user",
                )
                all_users.extend(users)
            return list(set(all_users))  # Remove duplicates
        else:
            return list_subjects(
                store=self.store,
                relation=relation,
                object_namespace=resource_type,
                object_id=resource_id,
                subject_namespace="user",
            )

    def expand_permissions(
        self,
        resource_type: str,
        relation: str,
    ) -> list[tuple[str, str]]:
        """
        Expand permissions to find all resources with a specific relation.

        Uses Zanzibar list_objects() API.

        Args:
            resource_type: Type of resource to filter by
            relation: Relation type to expand

        Returns:
            List of (resource_type, resource_id) tuples
        """
        return list_objects(
            store=self.store,
            relation=relation,
            object_namespace=resource_type,
        )

    # =========================================================================
    # Board-Level Operations
    # =========================================================================

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

    def revoke_board_access(
        self,
        user_id: str,
        board_id: str,
        role: str,
    ) -> None:
        """
        Revoke board-level access from a user.

        Args:
            user_id: User ID to revoke access from
            board_id: Board ID
            role: Role to revoke (owner, editor, viewer)
        """
        self.revoke_permission(user_id, "board", board_id, role)

    def check_board_access(
        self,
        user_id: str,
        board_id: str,
        required_role: str = "viewer",
    ) -> bool:
        """
        Check if user has required board access.

        Args:
            user_id: User ID to check
            board_id: Board ID
            required_role: Minimum required role (owner > editor > viewer)

        Returns:
            True if user has required access
        """
        # Check role hierarchy
        if required_role == "viewer":
            return (
                self.check_permission(user_id, "board", board_id, "owner")
                or self.check_permission(user_id, "board", board_id, "editor")
                or self.check_permission(user_id, "board", board_id, "viewer")
            )
        elif required_role == "editor":
            return self.check_permission(
                user_id, "board", board_id, "owner"
            ) or self.check_permission(user_id, "board", board_id, "editor")
        elif required_role == "owner":
            return self.check_permission(user_id, "board", board_id, "owner")
        else:
            return False

    # =========================================================================
    # List-Level Operations
    # =========================================================================

    def inherit_board_permissions(
        self,
        board_id: str,
        list_id: str,
    ) -> None:
        """
        Inherit board permissions for a list.

        Creates relation tuples so list permissions follow board permissions.

        Args:
            board_id: Board ID
            list_id: List ID
        """
        # Get all users with board permissions
        for role in ["owner", "editor", "viewer"]:
            users = self.list_resource_permissions("board", board_id, role)
            for _, user_id in users:
                self.grant_permission(user_id, "list", list_id, role)

    def check_list_access(
        self,
        user_id: str,
        list_id: str,
        board_id: str,
        required_role: str = "viewer",
    ) -> bool:
        """
        Check if user has required list access.

        Checks both direct list permissions and inherited board permissions.

        Args:
            user_id: User ID to check
            list_id: List ID
            board_id: Board ID (for permission inheritance)
            required_role: Minimum required role

        Returns:
            True if user has required access
        """
        # Check direct list permission
        if required_role == "viewer":
            has_direct = (
                self.check_permission(user_id, "list", list_id, "owner")
                or self.check_permission(user_id, "list", list_id, "editor")
                or self.check_permission(user_id, "list", list_id, "viewer")
            )
        elif required_role == "editor":
            has_direct = self.check_permission(
                user_id, "list", list_id, "owner"
            ) or self.check_permission(user_id, "list", list_id, "editor")
        elif required_role == "owner":
            has_direct = self.check_permission(user_id, "list", list_id, "owner")
        else:
            has_direct = False

        # Check inherited board permission
        has_inherited = self.check_board_access(user_id, board_id, required_role)

        return has_direct or has_inherited

    # =========================================================================
    # Task-Level Operations
    # =========================================================================

    def inherit_list_permissions(
        self,
        list_id: str,
        task_id: str,
    ) -> None:
        """
        Inherit list permissions for a task.

        Creates relation tuples so task permissions follow list permissions.

        Args:
            list_id: List ID
            task_id: Task ID
        """
        # Get all users with list permissions
        for role in ["owner", "editor", "viewer"]:
            users = self.list_resource_permissions("list", list_id, role)
            for _, user_id in users:
                self.grant_permission(user_id, "task", task_id, role)

    def grant_task_assignee_access(
        self,
        user_id: str,
        task_id: str,
    ) -> None:
        """
        Grant assignee access to a task.

        Assignees automatically get editor access to their assigned tasks.

        Args:
            user_id: User ID of assignee
            task_id: Task ID
        """
        self.grant_permission(user_id, "task", task_id, "editor")

    def check_task_access(
        self,
        user_id: str,
        task_id: str,
        list_id: str,
        board_id: str,
        required_role: str = "viewer",
    ) -> bool:
        """
        Check if user has required task access.

        Checks task, list, and board permissions (full hierarchy).

        Args:
            user_id: User ID to check
            task_id: Task ID
            list_id: List ID (for permission inheritance)
            board_id: Board ID (for permission inheritance)
            required_role: Minimum required role

        Returns:
            True if user has required access
        """
        # Check direct task permission
        if required_role == "viewer":
            has_direct = (
                self.check_permission(user_id, "task", task_id, "owner")
                or self.check_permission(user_id, "task", task_id, "editor")
                or self.check_permission(user_id, "task", task_id, "viewer")
            )
        elif required_role == "editor":
            has_direct = self.check_permission(
                user_id, "task", task_id, "owner"
            ) or self.check_permission(user_id, "task", task_id, "editor")
        elif required_role == "owner":
            has_direct = self.check_permission(user_id, "task", task_id, "owner")
        else:
            has_direct = False

        # Check inherited list permission
        has_list = self.check_list_access(user_id, list_id, board_id, required_role)

        return has_direct or has_list

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_stats(self) -> dict:
        """
        Get permission statistics.

        Returns:
            Dictionary with permission stats
        """
        return self.store.stats()

    def save(self, path: str | None = None) -> None:
        """
        Save permission tuples to disk.

        Args:
            path: Optional path to save to (defaults to storage_path)
        """
        save_path = path or self.storage_path
        self.store.save(save_path)

    def load(self, path: str | None = None) -> None:
        """
        Load permission tuples from disk.

        Args:
            path: Optional path to load from (defaults to storage_path)
        """
        load_path = path or self.storage_path
        self.store = TupleStore.load(load_path)

    def clear(self) -> None:
        """Clear all permission tuples."""
        self.store = TupleStore()


# Export classes and functions
__all__ = ["PermissionManager"]
