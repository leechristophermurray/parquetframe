"""
Basic tests for entity framework.

Tests core @entity decorator functionality and CRUD operations.
"""

from dataclasses import dataclass

import pytest

from parquetframe.entity import entity
from parquetframe.entity.metadata import registry


@pytest.fixture(autouse=True)
def clean_registry():
    """Clean registry before each test."""
    registry.clear()
    yield
    registry.clear()


class TestEntityDecorator:
    """Test @entity decorator."""

    def test_entity_decorator_basic(self, tmp_path):
        """Test basic entity decoration."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str
            email: str

        # Verify class has persistence methods
        assert hasattr(User, "save")
        assert hasattr(User, "delete")
        assert hasattr(User, "find")
        assert hasattr(User, "find_all")
        assert hasattr(User, "count")

    def test_entity_must_be_dataclass(self, tmp_path):
        """Test that @entity requires dataclass."""
        with pytest.raises(TypeError, match="must be a dataclass"):

            @entity(storage_path=tmp_path / "users", primary_key="user_id")
            class NotADataclass:
                pass

    def test_entity_validates_primary_key(self, tmp_path):
        """Test that primary key must exist in fields."""
        with pytest.raises(ValueError, match="Primary key.*not found"):

            @entity(storage_path=tmp_path / "users", primary_key="nonexistent_id")
            @dataclass
            class BadEntity:
                name: str


class TestEntityPersistence:
    """Test entity persistence operations."""

    def test_save_and_find(self, tmp_path):
        """Test saving and finding an entity."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str
            email: str

        # Create and save
        user = User(1, "Alice", "alice@example.com")
        user.save()

        # Find by primary key
        loaded = User.find(1)

        assert loaded is not None
        assert loaded.user_id == 1
        assert loaded.name == "Alice"
        assert loaded.email == "alice@example.com"

    def test_find_nonexistent_returns_none(self, tmp_path):
        """Test finding nonexistent entity returns None."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        result = User.find(999)
        assert result is None

    def test_find_all(self, tmp_path):
        """Test finding all entities."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        # Save multiple entities
        User(1, "Alice").save()
        User(2, "Bob").save()
        User(3, "Charlie").save()

        # Find all
        all_users = User.find_all()

        assert len(all_users) == 3
        assert {u.user_id for u in all_users} == {1, 2, 3}
        assert {u.name for u in all_users} == {"Alice", "Bob", "Charlie"}

    def test_find_by(self, tmp_path):
        """Test finding entities by filter."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str
            city: str

        # Save entities
        User(1, "Alice", "NYC").save()
        User(2, "Bob", "LA").save()
        User(3, "Charlie", "NYC").save()

        # Find by city
        nyc_users = User.find_by(city="NYC")

        assert len(nyc_users) == 2
        assert {u.name for u in nyc_users} == {"Alice", "Charlie"}

    def test_update_entity(self, tmp_path):
        """Test updating an existing entity."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str
            email: str

        # Create and save
        user = User(1, "Alice", "alice@old.com")
        user.save()

        # Update and save again
        updated_user = User(1, "Alice Smith", "alice@new.com")
        updated_user.save()

        # Verify update
        loaded = User.find(1)
        assert loaded.name == "Alice Smith"
        assert loaded.email == "alice@new.com"

        # Should only be one record
        assert User.count() == 1

    def test_delete_entity(self, tmp_path):
        """Test deleting an entity."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        # Create and save
        user = User(1, "Alice")
        user.save()

        assert User.count() == 1

        # Delete
        user.delete()

        assert User.count() == 0
        assert User.find(1) is None

    def test_count(self, tmp_path):
        """Test counting entities."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        assert User.count() == 0

        User(1, "Alice").save()
        assert User.count() == 1

        User(2, "Bob").save()
        assert User.count() == 2

    def test_delete_all(self, tmp_path):
        """Test deleting all entities."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        # Save multiple entities
        User(1, "Alice").save()
        User(2, "Bob").save()
        User(3, "Charlie").save()

        assert User.count() == 3

        # Delete all
        User.delete_all()

        assert User.count() == 0
        assert User.find_all() == []


class TestEntityFormats:
    """Test different storage formats."""

    def test_parquet_format(self, tmp_path):
        """Test entity with Parquet format."""

        @entity(
            storage_path=tmp_path / "users", primary_key="user_id", format="parquet"
        )
        @dataclass
        class User:
            user_id: int
            name: str

        user = User(1, "Alice")
        user.save()

        # Verify file exists
        storage_file = tmp_path / "users" / "User.parquet"
        assert storage_file.exists()

        # Verify can load
        loaded = User.find(1)
        assert loaded.name == "Alice"

    @pytest.mark.skipif(
        not pytest.importorskip("fastavro", reason="fastavro not available"),
        reason="fastavro not available",
    )
    def test_avro_format(self, tmp_path):
        """Test entity with Avro format."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id", format="avro")
        @dataclass
        class User:
            user_id: int
            name: str

        user = User(1, "Alice")
        user.save()

        # Verify file exists
        storage_file = tmp_path / "users" / "User.avro"
        assert storage_file.exists()

        # Verify can load
        loaded = User.find(1)
        assert loaded.name == "Alice"
