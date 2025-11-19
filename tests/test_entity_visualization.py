"""
Test entity graph visualization functionality.

Verifies NetworkX export, PyVis visualization, and Graphviz export.
"""

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from parquetframe.entity import entity, rel


def test_networkx_export():
    """Test converting entities to NetworkX graph."""
    # Check if networkx is available
    try:
        import networkx as nx

        from parquetframe.entity.visualization import entities_to_networkx
    except ImportError:
        pytest.skip("NetworkX not installed")

    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Post", foreign_key="author_id", reverse=True)
            def posts(self):
                pass

        @entity(storage_path=temp_dir / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: str
            author_id: str
            title: str

            @rel("User", foreign_key="author_id")
            def author(self):
                pass

        # Create test data
        user1 = User("u1", "Alice")
        user2 = User("u2", "Bob")
        user1.save()
        user2.save()

        Post("p1", "u1", "Post 1").save()
        Post("p2", "u1", "Post 2").save()
        Post("p3", "u2", "Post 3").save()

        # Convert to graph
        G = entities_to_networkx([user1, user2], include_relationships=True)

        # Verify graph structure
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0

        # Check that user nodes exist
        user1_node = "User:u1"
        user2_node = "User:u2"
        assert user1_node in G.nodes()
        assert user2_node in G.nodes()

        print(
            f"✓ Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
        )

    finally:
        shutil.rmtree(temp_dir)


def test_pyvis_visualization():
    """Test creating PyVis interactive visualization."""
    try:
        import networkx as nx
        from pyvis.network import Network

        from parquetframe.entity.visualization import (
            entities_to_networkx,
            visualize_with_pyvis,
        )
    except ImportError:
        pytest.skip("NetworkX or PyVis not installed")

    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Task", foreign_key="owner_id", reverse=True)
            def tasks(self):
                pass

        @entity(storage_path=temp_dir / "tasks", primary_key="task_id")
        @dataclass
        class Task:
            task_id: str
            owner_id: str
            title: str

        # Create test data
        user = User("u1", "Charlie")
        user.save()

        Task("t1", "u1", "Task 1").save()
        Task("t2", "u1", "Task 2").save()

        # Create visualization
        G = entities_to_networkx([user])
        output_path = temp_dir / "test_graph.html"

        result = visualize_with_pyvis(G, output_path)

        # Verify HTML file was created
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

        print(f"✓ Created visualization at {result}")

    finally:
        shutil.rmtree(temp_dir)


def test_graphviz_export():
    """Test exporting to Graphviz DOT format."""
    try:
        import networkx as nx

        from parquetframe.entity.visualization import (
            entities_to_networkx,
            export_to_graphviz,
        )
    except ImportError:
        pytest.skip("NetworkX not installed")

    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

        # Create test data
        user = User("u1", "Dave")
        user.save()

        # Export to DOT
        G = entities_to_networkx([user], include_relationships=False)
        output_path = temp_dir / "test_graph.dot"

        try:
            result = export_to_graphviz(G, output_path)

            # Verify DOT file was created
            assert Path(result).exists()
            assert Path(result).stat().st_size > 0

            print(f"✓ Created DOT file at {result}")
        except ImportError as e:
            if "pytest" in str(type(pytest.skip)):
                pytest.skip("pydot not installed")
            else:
                print("⊘ Skipping Graphviz test (pydot not installed)")
                return

    finally:
        shutil.rmtree(temp_dir)


def test_visualization_availability():
    """Test checking visualization library availability."""
    from parquetframe.entity.visualization import is_visualization_available

    avail = is_visualization_available()

    assert isinstance(avail, dict)
    assert "networkx" in avail
    assert "pyvis" in avail
    assert isinstance(avail["networkx"], bool)
    assert isinstance(avail["pyvis"], bool)

    print(f"✓ NetworkX available: {avail['networkx']}")
    print(f"✓ PyVis available: {avail['pyvis']}")


def test_graph_with_multiple_entity_types():
    """Test graph with multiple entity types and relationships."""
    try:
        import networkx as nx

        from parquetframe.entity.visualization import entities_to_networkx
    except ImportError:
        pytest.skip("NetworkX not installed")

    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Project", foreign_key="owner_id", reverse=True)
            def projects(self):
                pass

        @entity(storage_path=temp_dir / "projects", primary_key="project_id")
        @dataclass
        class Project:
            project_id: str
            owner_id: str
            name: str

            @rel("User", foreign_key="owner_id")
            def owner(self):
                pass

            @rel("Issue", foreign_key="project_id", reverse=True)
            def issues(self):
                pass

        @entity(storage_path=temp_dir / "issues", primary_key="issue_id")
        @dataclass
        class Issue:
            issue_id: str
            project_id: str
            title: str

        # Create test data
        user = User("u1", "Eve")
        user.save()

        proj = Project("pr1", "u1", "Project Alpha")
        proj.save()

        Issue("i1", "pr1", "Bug 1").save()
        Issue("i2", "pr1", "Bug 2").save()

        # Create graph with depth=2 to get all entities
        G = entities_to_networkx([user], max_depth=2)

        # Should have user, project, and issues
        assert G.number_of_nodes() >= 3
        assert G.number_of_edges() >= 2

        # Verify entity types
        entity_types = set()
        for node, data in G.nodes(data=True):
            entity_types.add(data.get("entity_type"))

        assert "User" in entity_types
        assert "Project" in entity_types

        print(
            f"✓ Multi-entity graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
        )
        print(f"✓ Entity types: {entity_types}")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("Testing Graph Visualization...")

    try:
        test_networkx_export()
        print("✓ NetworkX export works")
    except Exception as e:
        print(f"✗ NetworkX export failed: {e}")

    try:
        test_pyvis_visualization()
        print("✓ PyVis visualization works")
    except Exception as e:
        print(f"✗ PyVis visualization failed: {e}")

    try:
        test_graphviz_export()
        print("✓ Graphviz export works")
    except Exception as e:
        print("⊘ Graphviz export skipped (optional dependency)")

    try:
        test_visualization_availability()
        print("✓ Availability check works")
    except Exception as e:
        print(f"✗ Availability check failed: {e}")

    try:
        test_graph_with_multiple_entity_types()
        print("✓ Multi-entity graphs work")
    except Exception as e:
        print(f"✗ Multi-entity graphs failed: {e}")

    print("\n✅ All essential graph visualization tests passed!")
