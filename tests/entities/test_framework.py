"""
Unit tests for Entity Framework.
"""

from dataclasses import dataclass

import pytest

# Updated imports to point to the correct package
from parquetframe.entity import entity, rel
from parquetframe.entity.metadata import registry
from parquetframe.entity.schema import GraphArSchema

# Note: We define User and Product inside a fixture to avoid conflicts with
# test_entity_basic.py's autouse clean_registry fixture that clears the global registry


class TestEntityFramework:
    """Test Entity Framework components."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary storage for tests."""

        # @entity(storage_path=tmp_path / "FrameworkUser", primary_key="id")
        @dataclass
        class FrameworkUser:
            id: int
            name: str
            age: int

            @rel("FrameworkUser", foreign_key="id", reverse=True)
            def knows(self):
                """Friendship relationship."""
                pass

        # Manual decorator application to force execution
        FrameworkUser = entity(
            storage_path=tmp_path / "FrameworkUser", primary_key="id"
        )(FrameworkUser)
        self.FrameworkUser = FrameworkUser

        # @entity(storage_path=tmp_path / "FrameworkProduct", primary_key="id")
        @dataclass
        class FrameworkProduct:
            id: int
            name: str
            price: float

        # Manual decorator application to force execution
        FrameworkProduct = entity(
            storage_path=tmp_path / "FrameworkProduct", primary_key="id"
        )(FrameworkProduct)
        self.FrameworkProduct = FrameworkProduct

        yield

        # Cleanup - clear our entities from registry
        registry._entities.pop("FrameworkUser", None)
        registry._entities.pop("FrameworkProduct", None)

    def test_entity_decorator(self):
        """Test that @entity adds methods."""
        User = self.FrameworkUser
        u = User(1, "Alice", 30)
        assert hasattr(u, "save")
        assert hasattr(u, "delete")
        assert hasattr(User, "find")

    def test_save_and_find(self):
        """Test saving and finding entities."""
        User = self.FrameworkUser
        u = User(1, "Alice", 30)
        u.save()

        # Get updated registry entry
        user_meta = registry.get("User")
        if user_meta is None:
            # If not in registry, check if User class has the decorator's store
            if hasattr(User, "_entity_store"):
                user_meta = User._entity_store.metadata

        assert user_meta is not None, (
            "FrameworkUser entity not registered - ensure @entity decorator was applied"
        )
        file_path = user_meta.storage_path / "FrameworkUser.parquet"
        # Note: The existing store uses delta logs, so base file might not exist immediately
        # unless compacted. But find() should work.

        # Find entity
        found = User.find(1)
        assert found is not None
        assert found.id == 1
        assert found.name == "Alice"
        assert found.age == 30

    def test_find_nonexistent(self):
        """Test finding nonexistent entity."""
        User = self.FrameworkUser
        found = User.find(999)
        assert found is None

    def test_relationship(self):
        """Test adding relationships."""
        User = self.FrameworkUser
        u1 = User(1, "Alice", 30)
        u2 = User(2, "Bob", 35)
        u1.save()
        u2.save()

        # Add relationship - verify user is registered first
        user_meta = registry.get("User")
        if user_meta is None and hasattr(User, "_entity_store"):
            user_meta = User._entity_store.metadata

        assert user_meta is not None, "User entity not registered"

        # Add relationship using the new .add() method on the query object
        u1.knows().add(u2, since=2023)

        # Verify edge file exists
        # Parent of storage path is root
        root = user_meta.storage_path.parent
        rel_path = root / "FrameworkUser_knows_FrameworkUser" / "adj_list.parquet"

        assert rel_path.exists()

        # Check content
        import pandas as pd

        df = pd.read_parquet(rel_path)
        assert len(df) == 1
        assert df.iloc[0]["src_id"] == 1
        assert df.iloc[0]["dst_id"] == 2
        assert df.iloc[0]["since"] == 2023

    def test_schema_generation(self):
        """Test GraphAr schema generation."""
        User = self.FrameworkUser
        schema_yaml = GraphArSchema.generate_entity_schema(User, primary_key="id")
        assert "name: FrameworkUser" in schema_yaml
        assert "type: VERTEX" in schema_yaml
        assert "name: id" in schema_yaml
        assert "data_type: INT64" in schema_yaml

        assert "name: name" in schema_yaml
        assert "data_type: STRING" in schema_yaml
