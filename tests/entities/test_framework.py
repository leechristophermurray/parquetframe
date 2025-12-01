"""
Unit tests for Entity Framework.
"""

from dataclasses import dataclass

import pytest

# Updated imports to point to the correct package
from parquetframe.entity import entity, rel
from parquetframe.entity.metadata import registry
from parquetframe.entity.schema import GraphArSchema


@entity(storage_path="User", primary_key="id")
@dataclass
class User:
    id: int
    name: str
    age: int

    @rel("User", foreign_key="id")
    def knows(self):
        pass


@entity(storage_path="Product", primary_key="id")
@dataclass
class Product:
    id: int
    title: str


class TestEntityFramework:
    """Test Entity Framework components."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary storage for tests."""
        # The existing framework uses absolute paths or relative to cwd if not careful.
        # We need to make sure the decorators use the tmp_path.
        # However, the decorators are applied at module level.
        # We might need to patch the storage path in the registry metadata for the tests.

        # Patch metadata storage paths
        user_meta = registry.get("User")
        if user_meta:
            user_meta.storage_path = tmp_path / "User"
            user_meta.storage_path.mkdir(parents=True, exist_ok=True)
            # Also update the entity store's metadata reference
            if hasattr(User, "_entity_store"):
                User._entity_store.metadata.storage_path = user_meta.storage_path

        prod_meta = registry.get("Product")
        if prod_meta:
            prod_meta.storage_path = tmp_path / "Product"
            prod_meta.storage_path.mkdir(parents=True, exist_ok=True)
            if hasattr(Product, "_entity_store"):
                Product._entity_store.metadata.storage_path = prod_meta.storage_path

        yield
        # Cleanup handled by tmp_path fixture

    def test_entity_decorator(self):
        """Test that @entity adds methods."""
        u = User(1, "Alice", 30)
        assert hasattr(u, "save")
        assert hasattr(u, "delete")
        assert hasattr(User, "find")

    def test_save_and_find(self):
        """Test saving and finding entities."""
        u = User(1, "Alice", 30)
        u.save()

        # Verify file exists
        user_meta = registry.get("User")
        assert (
            user_meta is not None
        ), "User entity not registered - ensure @entity decorator was applied"
        file_path = user_meta.storage_path / "User.parquet"
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
        found = User.find(999)
        assert found is None

    def test_relationship(self):
        """Test adding relationships."""
        u1 = User(1, "Alice", 30)
        u2 = User(2, "Bob", 35)
        u1.save()
        u2.save()

        # Add relationship using the new .add() method on the query object
        u1.knows().add(u2, since=2023)

        # Verify edge file exists
        user_meta = registry.get("User")
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
        schema_yaml = GraphArSchema.generate_entity_schema(User, primary_key="id")
        assert "name: User" in schema_yaml
        assert "type: VERTEX" in schema_yaml
        assert "name: id" in schema_yaml
        assert "data_type: INT64" in schema_yaml

        assert "name: name" in schema_yaml
        assert "data_type: STRING" in schema_yaml
