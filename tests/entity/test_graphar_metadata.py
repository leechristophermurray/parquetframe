"""
Tests for EntityStore GraphAr metadata generation.

These tests verify that EntityStore generates GraphAr-compliant metadata
files alongside entity storage files.
"""

import shutil
from dataclasses import dataclass

import yaml

from src.parquetframe.entity import entity
from src.parquetframe.entity.metadata import EntityRegistry


class TestEntityGraphArMetadata:
    """Test GraphAr metadata generation for entities."""

    def test_save_generates_metadata_file(self, tmp_path):
        """Test that saving an entity generates _metadata.yaml."""

        @entity(storage_path=str(tmp_path / "users"), primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            username: str
            email: str

        # Save entity
        user = User(user_id=1, username="alice", email="alice@example.com")
        user.save()

        # Verify metadata file exists
        metadata_file = tmp_path / "users" / "_metadata.yaml"
        assert metadata_file.exists()

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "users").exists():
            shutil.rmtree(tmp_path / "users")

    def test_metadata_has_correct_structure(self, tmp_path):
        """Test _metadata.yaml has correct GraphAr structure."""

        @entity(storage_path=str(tmp_path / "products"), primary_key="product_id")
        @dataclass
        class Product:
            product_id: int
            name: str
            price: float

        # Save entity
        product = Product(product_id=1, name="Laptop", price=1200.0)
        product.save()

        # Load metadata
        metadata_file = tmp_path / "products" / "_metadata.yaml"
        with open(metadata_file) as f:
            metadata = yaml.safe_load(f)

        # Verify structure
        assert "name" in metadata
        assert metadata["name"] == "Product"
        assert "version" in metadata
        assert "format" in metadata
        assert metadata["format"] == "graphar"
        assert "vertices" in metadata
        assert "edges" in metadata

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "products").exists():
            shutil.rmtree(tmp_path / "products")

    def test_save_generates_schema_file(self, tmp_path):
        """Test that saving an entity generates _schema.yaml."""

        @entity(storage_path=str(tmp_path / "tasks"), primary_key="task_id")
        @dataclass
        class Task:
            task_id: int
            title: str
            completed: bool

        # Save entity
        task = Task(task_id=1, title="Test task", completed=False)
        task.save()

        # Verify schema file exists
        schema_file = tmp_path / "tasks" / "_schema.yaml"
        assert schema_file.exists()

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "tasks").exists():
            shutil.rmtree(tmp_path / "tasks")

    def test_schema_has_correct_structure(self, tmp_path):
        """Test _schema.yaml has correct GraphAr structure."""

        @entity(storage_path=str(tmp_path / "orders"), primary_key="order_id")
        @dataclass
        class Order:
            order_id: int
            customer_id: int
            amount: float
            status: str

        # Save entity
        order = Order(order_id=1, customer_id=100, amount=250.0, status="pending")
        order.save()

        # Load schema
        schema_file = tmp_path / "orders" / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        # Verify structure
        assert "vertices" in schema
        assert "edges" in schema

        # Verify vertex schema
        vertices = schema["vertices"]
        assert len(vertices) == 1  # Single entity type
        vertex = vertices[0]
        assert "label" in vertex
        assert vertex["label"] == "Order"
        assert "properties" in vertex
        assert "primary_key" in vertex
        assert vertex["primary_key"] == "order_id"

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "orders").exists():
            shutil.rmtree(tmp_path / "orders")

    def test_schema_includes_all_properties(self, tmp_path):
        """Test schema includes all entity properties with correct types."""

        @entity(storage_path=str(tmp_path / "employees"), primary_key="emp_id")
        @dataclass
        class Employee:
            emp_id: int
            name: str
            salary: float
            active: bool

        # Save entity
        emp = Employee(emp_id=1, name="John Doe", salary=75000.0, active=True)
        emp.save()

        # Load schema
        schema_file = tmp_path / "employees" / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        # Get properties
        properties = schema["vertices"][0]["properties"]
        prop_names = {p["name"] for p in properties}

        # Verify all fields present
        assert "emp_id" in prop_names
        assert "name" in prop_names
        assert "salary" in prop_names
        assert "active" in prop_names

        # Verify types
        prop_types = {p["name"]: p["type"] for p in properties}
        assert prop_types["emp_id"] == "int64"
        assert prop_types["name"] == "string"
        assert prop_types["salary"] == "double"
        assert prop_types["active"] == "bool"

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "employees").exists():
            shutil.rmtree(tmp_path / "employees")

    def test_metadata_updates_on_new_save(self, tmp_path):
        """Test metadata updates when new entities are saved."""

        @entity(storage_path=str(tmp_path / "items"), primary_key="item_id")
        @dataclass
        class Item:
            item_id: int
            name: str

        # Save first entity
        item1 = Item(item_id=1, name="Item 1")
        item1.save()

        # Load initial metadata
        metadata_file = tmp_path / "items" / "_metadata.yaml"
        with open(metadata_file) as f:
            metadata1 = yaml.safe_load(f)
        count1 = metadata1["vertices"][0]["count"]
        assert count1 == 1

        # Save second entity
        item2 = Item(item_id=2, name="Item 2")
        item2.save()

        # Load updated metadata
        with open(metadata_file) as f:
            metadata2 = yaml.safe_load(f)
        count2 = metadata2["vertices"][0]["count"]
        assert count2 == 2

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "items").exists():
            shutil.rmtree(tmp_path / "items")


class TestEntityGraphArIntegration:
    """Test integration with GraphAr ecosystem."""

    def test_entity_storage_graphar_compatible(self, tmp_path):
        """Test entity storage is GraphAr-compatible."""

        @entity(storage_path=str(tmp_path / "documents"), primary_key="doc_id")
        @dataclass
        class Document:
            doc_id: int
            title: str
            content: str

        # Save entity
        doc = Document(doc_id=1, title="Test Doc", content="Content here")
        doc.save()

        # Verify GraphAr structure
        storage_path = tmp_path / "documents"
        assert (storage_path / "_metadata.yaml").exists()
        assert (storage_path / "_schema.yaml").exists()

        # Verify entity data file exists
        assert (storage_path / "Document.parquet").exists()

        # Cleanup
        EntityRegistry().clear()
        if storage_path.exists():
            shutil.rmtree(storage_path)

    def test_multiple_entities_separate_metadata(self, tmp_path):
        """Test multiple entity types have separate metadata."""

        @entity(storage_path=str(tmp_path / "users"), primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            username: str

        @entity(storage_path=str(tmp_path / "posts"), primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            title: str

        # Save both entity types
        user = User(user_id=1, username="alice")
        user.save()

        post = Post(post_id=1, title="First Post")
        post.save()

        # Verify separate metadata files
        assert (tmp_path / "users" / "_metadata.yaml").exists()
        assert (tmp_path / "posts" / "_metadata.yaml").exists()

        # Verify metadata names are different
        with open(tmp_path / "users" / "_metadata.yaml") as f:
            user_meta = yaml.safe_load(f)
        with open(tmp_path / "posts" / "_metadata.yaml") as f:
            post_meta = yaml.safe_load(f)

        assert user_meta["name"] == "User"
        assert post_meta["name"] == "Post"

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "users").exists():
            shutil.rmtree(tmp_path / "users")
        if (tmp_path / "posts").exists():
            shutil.rmtree(tmp_path / "posts")


class TestEntityGraphArSchemaMapping:
    """Test schema type mapping for entities."""

    def test_integer_types_mapped_correctly(self, tmp_path):
        """Test integer types map to GraphAr types."""

        @entity(storage_path=str(tmp_path / "numbers"), primary_key="id")
        @dataclass
        class Numbers:
            id: int
            count: int

        num = Numbers(id=1, count=100)
        num.save()

        schema_file = tmp_path / "numbers" / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        prop_types = {p["name"]: p["type"] for p in schema["vertices"][0]["properties"]}
        assert "int" in prop_types["id"] or prop_types["id"] == "int64"

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "numbers").exists():
            shutil.rmtree(tmp_path / "numbers")

    def test_string_types_mapped_correctly(self, tmp_path):
        """Test string types map to GraphAr types."""

        @entity(storage_path=str(tmp_path / "texts"), primary_key="id")
        @dataclass
        class Texts:
            id: int
            text: str

        txt = Texts(id=1, text="Hello World")
        txt.save()

        schema_file = tmp_path / "texts" / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        prop_types = {p["name"]: p["type"] for p in schema["vertices"][0]["properties"]}
        assert prop_types["text"] == "string"

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "texts").exists():
            shutil.rmtree(tmp_path / "texts")

    def test_float_types_mapped_correctly(self, tmp_path):
        """Test float types map to GraphAr types."""

        @entity(storage_path=str(tmp_path / "floats"), primary_key="id")
        @dataclass
        class Floats:
            id: int
            value: float

        flt = Floats(id=1, value=3.14159)
        flt.save()

        schema_file = tmp_path / "floats" / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        prop_types = {p["name"]: p["type"] for p in schema["vertices"][0]["properties"]}
        assert prop_types["value"] in ["float", "double"]

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "floats").exists():
            shutil.rmtree(tmp_path / "floats")

    def test_boolean_types_mapped_correctly(self, tmp_path):
        """Test boolean types map to GraphAr types."""

        @entity(storage_path=str(tmp_path / "flags"), primary_key="id")
        @dataclass
        class Flags:
            id: int
            active: bool

        flag = Flags(id=1, active=True)
        flag.save()

        schema_file = tmp_path / "flags" / "_schema.yaml"
        with open(schema_file) as f:
            schema = yaml.safe_load(f)

        prop_types = {p["name"]: p["type"] for p in schema["vertices"][0]["properties"]}
        assert prop_types["active"] == "bool"

        # Cleanup
        EntityRegistry().clear()
        if (tmp_path / "flags").exists():
            shutil.rmtree(tmp_path / "flags")
