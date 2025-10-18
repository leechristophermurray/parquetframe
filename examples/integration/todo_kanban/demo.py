"""
Interactive demonstration of the Todo/Kanban application.

This demo showcases:
- Entity Framework (@entity, @rel decorators)
- Zanzibar permissions (all 4 APIs)
- Multi-user collaboration
- Permission inheritance
- Task state transitions
- Permission revocation

Run with: python demo.py
"""

import shutil
from pathlib import Path

from .app import PermissionError, TodoKanbanApp


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f" {text}")
    print("=" * 80)


def print_step(step_num: int, text: str) -> None:
    """Print a formatted step."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 80)


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"  ✓ {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"  ✗ {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"  • {text}")


def cleanup_demo_data():
    """Clean up demo data directory."""
    data_path = Path("./kanban_data")
    if data_path.exists():
        shutil.rmtree(data_path)
        print("  ✓ Cleaned up demo data")


def main():
    """Run the comprehensive demo."""
    print_header("Todo/Kanban Application Demo")
    print("This demo showcases ParquetFrame features:")
    print_info("Entity Framework with @entity and @rel decorators")
    print_info("Zanzibar permissions with all 4 APIs")
    print_info("Multi-user collaboration")
    print_info("Permission inheritance (board → list → task)")
    print_info("Task state transitions")
    print_info("Permission revocation")

    # Initialize app
    print("\n" + "-" * 80)
    print("Initializing Todo/Kanban application...")
    app = TodoKanbanApp(storage_base="./kanban_data")
    print_success("Application initialized")

    # =========================================================================
    # Step 1: Create Users
    # =========================================================================
    print_step(1, "Create three users: alice, bob, charlie")

    alice = app.create_user("alice", "alice@example.com")
    print_success(f"Created user: {alice.username} ({alice.user_id})")

    bob = app.create_user("bob", "bob@example.com")
    print_success(f"Created user: {bob.username} ({bob.user_id})")

    charlie = app.create_user("charlie", "charlie@example.com")
    print_success(f"Created user: {charlie.username} ({charlie.user_id})")

    # =========================================================================
    # Step 2: Alice creates a board
    # =========================================================================
    print_step(2, "Alice creates 'Project Alpha' board")

    board = app.create_board(
        alice.user_id, "Project Alpha", "Sprint board for Project Alpha development"
    )
    print_success(f"Board created: {board.name} ({board.board_id})")
    print_info(f"Owner: {alice.username}")
    print_info("Permission granted: alice → board:owner")

    # =========================================================================
    # Step 3: Alice adds task lists
    # =========================================================================
    print_step(3, "Alice adds three lists: Todo, In Progress, Done")

    todo_list = app.add_list(board.board_id, alice.user_id, "Todo", 0)
    print_success(f"List created: {todo_list.name} ({todo_list.list_id})")

    progress_list = app.add_list(board.board_id, alice.user_id, "In Progress", 1)
    print_success(f"List created: {progress_list.name} ({progress_list.list_id})")

    done_list = app.add_list(board.board_id, alice.user_id, "Done", 2)
    print_success(f"List created: {done_list.name} ({done_list.list_id})")

    # =========================================================================
    # Step 4: Alice creates tasks
    # =========================================================================
    print_step(4, "Alice creates tasks in 'Todo' list")

    task1 = app.create_task(
        list_id=todo_list.list_id,
        user_id=alice.user_id,
        title="Setup database",
        description="Configure PostgreSQL with proper schema",
        priority="high",
        assigned_to=alice.user_id,
    )
    print_success(f"Task created: {task1.title} ({task1.task_id})")
    print_info(f"Assigned to: {alice.username}")

    task2 = app.create_task(
        list_id=todo_list.list_id,
        user_id=alice.user_id,
        title="Design API endpoints",
        description="RESTful API design for the service",
        priority="high",
    )
    print_success(f"Task created: {task2.title} ({task2.task_id})")
    print_info("Unassigned")

    task3 = app.create_task(
        list_id=todo_list.list_id,
        user_id=alice.user_id,
        title="Write unit tests",
        description="Unit and integration tests",
        priority="medium",
    )
    print_success(f"Task created: {task3.title} ({task3.task_id})")

    # =========================================================================
    # Step 5: Share board with Bob and Charlie
    # =========================================================================
    print_step(5, "Alice shares board with Bob (editor) and Charlie (viewer)")

    app.share_board(board.board_id, alice.user_id, bob.user_id, "editor")
    print_success(f"Shared with {bob.username} as editor")
    print_info("Bob can: create/edit lists and tasks, view everything")
    print_info("Bob cannot: delete board, manage permissions")

    app.share_board(board.board_id, alice.user_id, charlie.user_id, "viewer")
    print_success(f"Shared with {charlie.username} as viewer")
    print_info("Charlie can: view board, lists, and tasks")
    print_info("Charlie cannot: create/edit/delete anything")

    # =========================================================================
    # Step 6: Permission inheritance demonstration
    # =========================================================================
    print_step(6, "Demonstrate permission inheritance")

    print_info("Checking board permissions:")
    alice_owner = app.permissions.check_board_access(
        alice.user_id, board.board_id, "owner"
    )
    print(f"  - Alice owner access: {alice_owner} ✓")

    bob_editor = app.permissions.check_board_access(
        bob.user_id, board.board_id, "editor"
    )
    print(f"  - Bob editor access: {bob_editor} ✓")

    charlie_viewer = app.permissions.check_board_access(
        charlie.user_id, board.board_id, "viewer"
    )
    print(f"  - Charlie viewer access: {charlie_viewer} ✓")

    print_info("Permission inheritance (board → list → task):")
    # Check inherited list permissions
    bob_list_access = app.permissions.check_list_access(
        bob.user_id, todo_list.list_id, board.board_id, "editor"
    )
    print(f"  - Bob can edit Todo list: {bob_list_access} ✓")

    # Check inherited task permissions
    charlie_task_access = app.permissions.check_task_access(
        charlie.user_id, task1.task_id, todo_list.list_id, board.board_id, "viewer"
    )
    print(f"  - Charlie can view tasks: {charlie_task_access} ✓")

    # =========================================================================
    # Step 7: Bob creates and assigns tasks
    # =========================================================================
    print_step(7, "Bob creates tasks and assigns to Alice")

    task4 = app.create_task(
        list_id=todo_list.list_id,
        user_id=bob.user_id,
        title="Code review process",
        description="Setup code review workflow",
        priority="medium",
        assigned_to=alice.user_id,
    )
    print_success(f"Bob created: {task4.title}")
    print_info(f"Assigned to: {alice.username}")

    # =========================================================================
    # Step 8: Alice moves tasks
    # =========================================================================
    print_step(8, "Alice moves tasks between lists (state transitions)")

    # Move task to In Progress
    task1 = app.move_task(task1.task_id, alice.user_id, progress_list.list_id)
    print_success(f"Moved '{task1.title}' to In Progress")
    print_info(f"Status: {task1.status}")

    # Move task to Done
    task1 = app.move_task(task1.task_id, alice.user_id, done_list.list_id)
    print_success(f"Moved '{task1.title}' to Done")
    print_info(f"Status: {task1.status}")

    # =========================================================================
    # Step 9: Charlie attempts to edit (should fail)
    # =========================================================================
    print_step(9, "Charlie attempts to edit (should be denied)")

    try:
        app.create_task(
            list_id=todo_list.list_id,
            user_id=charlie.user_id,
            title="Unauthorized task",
            description="This should fail",
        )
        print_error("Charlie was able to create task (unexpected!)")
    except PermissionError as e:
        print_success("Charlie denied: Cannot create tasks (viewer role)")
        print_info(f"Error: {str(e)}")

    try:
        app.assign_task(task2.task_id, charlie.user_id, charlie.user_id)
        print_error("Charlie was able to assign task (unexpected!)")
    except PermissionError as e:
        print_success("Charlie denied: Cannot assign tasks (viewer role)")
        print_info(f"Error: {str(e)}")

    # =========================================================================
    # Step 10: Bob reassigns tasks
    # =========================================================================
    print_step(10, "Bob reassigns tasks")

    task2 = app.assign_task(task2.task_id, bob.user_id, bob.user_id)
    print_success(f"Bob assigned '{task2.title}' to himself")
    print_info(f"Assigned to: {bob.username}")

    task3 = app.assign_task(task3.task_id, bob.user_id, alice.user_id)
    print_success(f"Bob assigned '{task3.title}' to {alice.username}")

    # =========================================================================
    # Step 11: Demonstrate Zanzibar APIs
    # =========================================================================
    print_step(11, "Demonstrate Zanzibar permission APIs")

    # API 1: check()
    print_info("API 1: check() - Verify specific permissions")
    alice_can_edit = app.permissions.check_permission(
        alice.user_id, "board", board.board_id, "owner"
    )
    print(f"  - check(alice, board, owner): {alice_can_edit} ✓")

    # API 2: expand()
    print_info("API 2: expand() - List accessible resources")
    alice_boards = app.permissions.list_user_permissions(
        alice.user_id, resource_type="board"
    )
    print(f"  - Alice has access to {len(alice_boards)} board(s) ✓")

    bob_boards = app.permissions.list_user_permissions(
        bob.user_id, resource_type="board"
    )
    print(f"  - Bob has access to {len(bob_boards)} board(s) ✓")

    # API 3: list_objects()
    print_info("API 3: list_objects() - Find all resources with relation")
    all_viewable = app.permissions.expand_permissions("board", "viewer")
    print(f"  - {len(all_viewable)} board(s) with viewer permission ✓")

    # API 4: list_subjects()
    print_info("API 4: list_subjects() - Find all users with access")
    board_viewers = app.permissions.list_resource_permissions(
        "board", board.board_id, "viewer"
    )
    print(f"  - {len(board_viewers)} user(s) with viewer access to board ✓")
    for _, user_id in board_viewers:
        user = app.get_user(user_id)
        if user:
            print(f"    - {user.username}")

    # =========================================================================
    # Step 12: Display board summary
    # =========================================================================
    print_step(12, "Display board summary")

    # Get all lists for alice
    alice_lists = app.get_board_lists(board.board_id, alice.user_id)
    print_info(f"Board: {board.name}")
    for task_list in alice_lists:
        tasks = app.get_list_tasks(task_list.list_id, alice.user_id)
        print(f"  {task_list.name} ({len(tasks)} tasks):")
        for task in tasks:
            assigned = task.assigned_to
            assigned_name = "Unassigned"
            if assigned:
                assigned_user = app.get_user(assigned)
                if assigned_user:
                    assigned_name = assigned_user.username
            print(f"    - [{task.priority}] {task.title} (assigned: {assigned_name})")

    # =========================================================================
    # Step 13: Permission statistics
    # =========================================================================
    print_step(13, "Permission system statistics")

    stats = app.permissions.get_stats()
    print_info(f"Total permission tuples: {stats['total_tuples']}")
    print_info(f"Unique resources: {stats['unique_objects']}")
    print_info(f"Unique users: {stats['unique_subjects']}")
    print_info(f"Unique relations: {stats['unique_relations']}")

    # =========================================================================
    # Step 14: Revoke permissions
    # =========================================================================
    print_step(14, "Revoke Charlie's access")

    app.permissions.revoke_board_access(charlie.user_id, board.board_id, "viewer")
    print_success(f"Revoked {charlie.username}'s viewer access")

    # Verify revocation
    charlie_access = app.permissions.check_board_access(
        charlie.user_id, board.board_id, "viewer"
    )
    print_info(f"Charlie can access board: {charlie_access} ✗")

    # Charlie should not see the board anymore
    charlie_boards = app.get_user_boards(charlie.user_id)
    print_info(f"Charlie can see {len(charlie_boards)} boards (expected: 0)")

    # =========================================================================
    # Step 15: Cleanup
    # =========================================================================
    print_step(15, "Cleanup demo data")

    cleanup_demo_data()

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Demo Summary")
    print("\n✅ Features Demonstrated:")
    print_info("Entity Framework - @entity and @rel decorators working")
    print_info("Permission Management - Zanzibar ReBAC implementation")
    print_info("All 4 Zanzibar APIs - check, expand, list_objects, list_subjects")
    print_info("Permission Inheritance - board → list → task hierarchy")
    print_info(
        "Multi-user Collaboration - alice (owner), bob (editor), charlie (viewer)"
    )
    print_info("Task State Transitions - todo → in_progress → done")
    print_info("Permission Revocation - revoking access works correctly")
    print_info("Access Control - viewers blocked from editing")

    print("\n✅ Entity Relationships:")
    print_info("User → Board (one-to-many, ownership)")
    print_info("Board → TaskList (one-to-many, contains)")
    print_info("TaskList → Task (one-to-many, contains)")
    print_info("Task → User (many-to-one, assignment)")

    print("\n✅ Permission Model:")
    print_info("Board owner: full control including permission management")
    print_info("Board editor: create/edit lists and tasks")
    print_info("Board viewer: read-only access")
    print_info("Permissions inherited: board → list → task")

    print("\n🎉 Demo completed successfully!")
    print("\nNext steps:")
    print_info("Run tests: pytest tests/integration/test_todo_kanban.py")
    print_info("Try workflows: see workflows/ directory")
    print_info("Read docs: see README.md")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
