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
        # The decorators are applied at module level, so metadata should be registered
        # Just ensure storage paths are updated to use tmp_path

        # Verify entities are registered
        user_meta = registry.get("User")
        assert (
            user_meta is not None
        ), "User entity should be registered by @entity decorator"

        prod_meta = registry.get("Product")
        assert (
            prod_meta is not None
        ), "Product entity should be registered by @entity decorator"

        # Update storage paths for this test run
        user_meta.storage_path = tmp_path / "User"
        user_meta.storage_path.mkdir(parents=True, exist_ok=True)

        prod_meta.storage_path = tmp_path / "Product"
        prod_meta.storage_path.mkdir(parents=True, exist_ok=True)

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

        assert (
            user_meta is not None
        ), "FrameworkUser entity not registered - ensure @entity decorator was applied"
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
        rel_path = root / "User_knows_User" / "adj_list.parquet"

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
