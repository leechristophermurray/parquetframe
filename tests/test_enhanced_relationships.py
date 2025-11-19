"""
Test enhanced relationship queries with filtering, ordering, and limiting.

Verifies the RelationshipQuery functionality integrated with @rel decorator.
"""

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from parquetframe.entity import entity, rel


def test_relationship_query_filtering():
    """Test filtering relationships with kwargs."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Post", foreign_key="user_id", reverse=True)
            def posts(self):
                pass

        @entity(storage_path=temp_dir / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: str
            user_id: str
            title: str
            status: str

        # Create test data
        user = User("u1", "Alice")
        user.save()

        Post("p1", "u1", "Draft Post", "draft").save()
        Post("p2", "u1", "Published Post", "published").save()
        Post("p3", "u1", "Another Published", "published").save()

        # Test filtering with kwargs
        published = user.posts(status="published")
        assert len(published) == 2
        assert all(p.status == "published" for p in published)

        # Test chained filtering
        query_result = user.posts().filter(status="draft").all()
        assert len(query_result) == 1
        assert query_result[0].status == "draft"

    finally:
        shutil.rmtree(temp_dir)


def test_relationship_query_ordering():
    """Test ordering relationship results."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Comment", foreign_key="user_id", reverse=True)
            def comments(self):
                pass

        @entity(storage_path=temp_dir / "comments", primary_key="comment_id")
        @dataclass
        class Comment:
            comment_id: str
            user_id: str
            text: str
            score: int

        user = User("u1", "Bob")
        user.save()

        Comment("c1", "u1", "First", 5).save()
        Comment("c2", "u1", "Second", 10).save()
        Comment("c3", "u1", "Third", 3).save()

        # Test ascending order
        asc = user.comments().order_by("score").all()
        assert [c.score for c in asc] == [3, 5, 10]

        # Test descending order
        desc = user.comments().order_by("score", desc=True).all()
        assert [c.score for c in desc] == [10, 5, 3]

    finally:
        shutil.rmtree(temp_dir)


def test_relationship_query_limiting():
    """Test limiting relationship results."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Task", foreign_key="user_id", reverse=True)
            def tasks(self):
                pass

        @entity(storage_path=temp_dir / "tasks", primary_key="task_id")
        @dataclass
        class Task:
            task_id: str
            user_id: str
            title: str

        user = User("u1", "Charlie")
        user.save()

        for i in range(10):
            Task(f"t{i}", "u1", f"Task {i}").save()

        # Test limit
        limited = user.tasks().limit(3).all()
        assert len(limited) == 3

        # Test limit with order
        top_tasks = user.tasks().order_by("task_id").limit(5).all()
        assert len(top_tasks) == 5

    finally:
        shutil.rmtree(temp_dir)


def test_relationship_query_chaining():
    """Test chaining multiple query operations."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Article", foreign_key="author_id", reverse=True)
            def articles(self):
                pass

        @entity(storage_path=temp_dir / "articles", primary_key="article_id")
        @dataclass
        class Article:
            article_id: str
            author_id: str
            title: str
            category: str
            views: int

        user = User("u1", "Dave")
        user.save()

        Article("a1", "u1", "Python Tips", "tech", 100).save()
        Article("a2", "u1", "Python Advanced", "tech", 500).save()
        Article("a3", "u1", "Cooking 101", "lifestyle", 200).save()
        Article("a4", "u1", "Python Basics", "tech", 50).save()

        # Chain filter + order + limit
        top_tech = (
            user.articles()
            .filter(category="tech")
            .order_by("views", desc=True)
            .limit(2)
            .all()
        )

        assert len(top_tech) == 2
        assert top_tech[0].title == "Python Advanced"
        assert top_tech[1].title == "Python Tips"

    finally:
        shutil.rmtree(temp_dir)


def test_relationship_query_count():
    """Test counting relationship results."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Order", foreign_key="customer_id", reverse=True)
            def orders(self):
                pass

        @entity(storage_path=temp_dir / "orders", primary_key="order_id")
        @dataclass
        class Order:
            order_id: str
            customer_id: str
            status: str

        user = User("u1", "Eve")
        user.save()

        Order("o1", "u1", "completed").save()
        Order("o2", "u1", "pending").save()
        Order("o3", "u1", "completed").save()

        # Test count
        total = user.orders().count()
        assert total == 3

        # Test count with filter
        completed_count = user.orders().filter(status="completed").count()
        assert completed_count == 2

    finally:
        shutil.rmtree(temp_dir)


def test_relationship_query_first():
    """Test getting first result from query."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Message", foreign_key="sender_id", reverse=True)
            def messages(self):
                pass

        @entity(storage_path=temp_dir / "messages", primary_key="message_id")
        @dataclass
        class Message:
            message_id: str
            sender_id: str
            text: str
            priority: int

        user = User("u1", "Frank")
        user.save()

        Message("m1", "u1", "Low priority", 1).save()
        Message("m2", "u1", "High priority", 10).save()
        Message("m3", "u1", "Medium priority", 5).save()

        # Test first
        first_msg = user.messages().order_by("priority", desc=True).first()
        assert first_msg is not None
        assert first_msg.priority == 10

        # Test first with no results
        no_msg = user.messages().filter(priority=999).first()
        assert no_msg is None

    finally:
        shutil.rmtree(temp_dir)


def test_relationship_query_exists():
    """Test checking if results exist."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Notification", foreign_key="user_id", reverse=True)
            def notifications(self):
                pass

        @entity(storage_path=temp_dir / "notifications", primary_key="notif_id")
        @dataclass
        class Notification:
            notif_id: str
            user_id: str
            read: bool

        user = User("u1", "Grace")
        user.save()

        Notification("n1", "u1", True).save()
        Notification("n2", "u1", False).save()

        # Test exists
        has_unread = user.notifications().filter(read=False).exists()
        assert has_unread is True

        # Test not exists
        has_archived = user.notifications().filter(read=999).exists()
        assert has_archived is False

    finally:
        shutil.rmtree(temp_dir)


def test_backward_compatibility():
    """Test that old relationship usage still works."""
    temp_dir = Path(tempfile.mkdtemp())

    try:

        @entity(storage_path=temp_dir / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: str
            name: str

            @rel("Item", foreign_key="owner_id", reverse=True)
            def items(self):
                pass

        @entity(storage_path=temp_dir / "items", primary_key="item_id")
        @dataclass
        class Item:
            item_id: str
            owner_id: str
            name: str

        user = User("u1", "Henry")
        user.save()

        Item("i1", "u1", "Laptop").save()
        Item("i2", "u1", "Phone").save()

        # Old style - should return RelationshipQuery that can be iterated
        items_query = user.items()
        assert hasattr(items_query, "all")

        # Should be able to call .all()
        items_list = items_query.all()
        assert len(items_list) == 2

        # Can also iterate directly
        count = 0
        for item in user.items():
            count += 1
        assert count == 2

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("Testing Enhanced Relationship Queries...")

    test_relationship_query_filtering()
    print("✓ Filtering works")

    test_relationship_query_ordering()
    print("✓ Ordering works")

    test_relationship_query_limiting()
    print("✓ Limiting works")

    test_relationship_query_chaining()
    print("✓ Chaining works")

    test_relationship_query_count()
    print("✓ Count works")

    test_relationship_query_first()
    print("✓ First works")

    test_relationship_query_exists()
    print("✓ Exists works")

    test_backward_compatibility()
    print("✓ Backward compatibility maintained")

    print("\n✅ All enhanced relationship query tests passed!")
