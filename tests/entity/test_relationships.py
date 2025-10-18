"""
Tests for entity relationship functionality.

Tests @rel decorator and relationship resolution.
"""

from dataclasses import dataclass

import pytest

from parquetframe.entity import entity, rel
from parquetframe.entity.metadata import registry


@pytest.fixture(autouse=True)
def clean_registry():
    """Clean registry before each test."""
    registry.clear()
    yield
    registry.clear()


class TestRelationshipDecorator:
    """Test @rel decorator."""

    def test_one_to_many_relationship(self, tmp_path):
        """Test defining a one-to-many relationship."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str

            @rel("User", foreign_key="user_id")
            def author(self):
                """Get the author of this post."""
                pass

        # Verify relationship is registered
        post_meta = registry.get("Post")
        assert "author" in post_meta.relationships
        assert post_meta.relationships["author"]["target"] == "User"
        assert post_meta.relationships["author"]["foreign_key"] == "user_id"

    def test_many_to_one_relationship(self, tmp_path):
        """Test defining a many-to-one relationship."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

            @rel("Post", foreign_key="user_id", reverse=True)
            def posts(self):
                """Get all posts by this user."""
                pass

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str

        # Verify relationship is registered
        user_meta = registry.get("User")
        assert "posts" in user_meta.relationships
        assert user_meta.relationships["posts"]["target"] == "Post"
        assert user_meta.relationships["posts"]["reverse"] is True


class TestRelationshipResolution:
    """Test relationship resolution."""

    def test_resolve_one_to_many(self, tmp_path):
        """Test resolving a one-to-many relationship."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str

            @rel("User", foreign_key="user_id")
            def author(self):
                """Get the author of this post."""
                pass

        # Create and save entities
        user = User(1, "Alice")
        user.save()

        post = Post(1, 1, "First Post")
        post.save()

        # Resolve relationship
        author = post.author()

        assert author is not None
        assert author.user_id == 1
        assert author.name == "Alice"

    def test_resolve_many_to_one(self, tmp_path):
        """Test resolving a many-to-one relationship."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

            @rel("Post", foreign_key="user_id", reverse=True)
            def posts(self):
                """Get all posts by this user."""
                pass

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str

        # Create and save entities
        user = User(1, "Alice")
        user.save()

        Post(1, 1, "First Post").save()
        Post(2, 1, "Second Post").save()
        Post(3, 2, "Other Post").save()  # Different user

        # Resolve relationship
        user_posts = user.posts()

        assert len(user_posts) == 2
        assert {p.title for p in user_posts} == {"First Post", "Second Post"}

    def test_relationship_with_nonexistent_target(self, tmp_path):
        """Test relationship returns None for nonexistent target."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str

            @rel("User", foreign_key="user_id")
            def author(self):
                """Get the author of this post."""
                pass

        # Create post without author
        post = Post(1, 999, "Orphaned Post")
        post.save()

        # Resolve relationship - should return None
        author = post.author()
        assert author is None

    def test_reverse_relationship_with_no_matches(self, tmp_path):
        """Test reverse relationship returns empty list when no matches."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

            @rel("Post", foreign_key="user_id", reverse=True)
            def posts(self):
                """Get all posts by this user."""
                pass

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str

        # Create user with no posts
        user = User(1, "Alice")
        user.save()

        # Resolve relationship - should return empty list
        user_posts = user.posts()
        assert user_posts == []


class TestComplexRelationships:
    """Test complex relationship scenarios."""

    def test_multiple_relationships_on_entity(self, tmp_path):
        """Test entity with multiple relationships."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        @entity(storage_path=tmp_path / "categories", primary_key="category_id")
        @dataclass
        class Category:
            category_id: int
            name: str

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            category_id: int
            title: str

            @rel("User", foreign_key="user_id")
            def author(self):
                """Get the author."""
                pass

            @rel("Category", foreign_key="category_id")
            def category(self):
                """Get the category."""
                pass

        # Create and save entities
        User(1, "Alice").save()
        Category(1, "Tech").save()
        Post(1, 1, 1, "Tech Post").save()

        # Load and resolve both relationships
        post = Post.find(1)
        author = post.author()
        category = post.category()

        assert author.name == "Alice"
        assert category.name == "Tech"

    def test_bidirectional_relationships(self, tmp_path):
        """Test bidirectional relationships."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

            @rel("Post", foreign_key="user_id", reverse=True)
            def posts(self):
                """Get all posts by this user."""
                pass

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str

            @rel("User", foreign_key="user_id")
            def author(self):
                """Get the author of this post."""
                pass

        # Create and save entities
        User(1, "Alice").save()
        Post(1, 1, "First Post").save()
        Post(2, 1, "Second Post").save()

        # Test forward relationship (post -> user)
        post = Post.find(1)
        author = post.author()
        assert author.name == "Alice"

        # Test reverse relationship (user -> posts)
        user = User.find(1)
        user_posts = user.posts()
        assert len(user_posts) == 2
        assert {p.title for p in user_posts} == {"First Post", "Second Post"}
