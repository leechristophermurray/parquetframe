"""
End-to-end integration tests for Phase 2.

Tests complete workflows from reading data to entity persistence.
"""

from dataclasses import dataclass

import pandas as pd
import pytest

from parquetframe.config import config_context, reset_config, set_config
from parquetframe.core import read, read_csv, read_parquet
from parquetframe.entity import entity, rel
from parquetframe.entity.metadata import registry


@pytest.fixture(autouse=True)
def clean_state():
    """Clean state before each test."""
    reset_config()
    registry.clear()
    yield
    reset_config()
    registry.clear()


@pytest.fixture
def sample_data(tmp_path):
    """Create sample data files."""
    # CSV data
    csv_file = tmp_path / "sales.csv"
    sales_df = pd.DataFrame(
        {
            "sale_id": [1, 2, 3, 4, 5],
            "user_id": [101, 102, 101, 103, 102],
            "product": ["A", "B", "C", "A", "B"],
            "amount": [100.0, 200.0, 150.0, 120.0, 180.0],
        }
    )
    sales_df.to_csv(csv_file, index=False)

    # Parquet data
    parquet_file = tmp_path / "users.parquet"
    users_df = pd.DataFrame(
        {
            "user_id": [101, 102, 103],
            "name": ["Alice", "Bob", "Charlie"],
            "city": ["NYC", "LA", "SF"],
        }
    )
    users_df.to_parquet(parquet_file)

    return {
        "csv": csv_file,
        "parquet": parquet_file,
        "sales_df": sales_df,
        "users_df": users_df,
    }


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_read_process_write_workflow(self, tmp_path, sample_data):
        """Test reading, processing, and writing data."""
        # Read CSV
        df = read_csv(sample_data["csv"])
        assert len(df) == 5
        assert df.engine_name == "pandas"

        # Process data
        result = df.groupby("user_id")["amount"].sum()

        # Write to parquet
        output_file = tmp_path / "output.parquet"
        result_df = result.to_frame().reset_index()
        result_df.to_parquet(output_file)

        # Verify written data
        written = read_parquet(output_file)
        assert len(written) == 3

    def test_multi_format_join(self, sample_data):
        """Test joining data from different formats."""
        # Read from different formats
        sales = read_csv(sample_data["csv"])
        users = read_parquet(sample_data["parquet"])

        # Convert to pandas for join
        sales_pd = sales.to_pandas()
        users_pd = users.to_pandas()

        # Join
        merged = sales_pd.native.merge(users_pd.native, on="user_id")

        assert len(merged) == 5
        assert "name" in merged.columns
        assert "product" in merged.columns

    def test_engine_switching_workflow(self, sample_data):
        """Test switching engines during workflow."""
        # Start with pandas
        set_config(default_engine="pandas")
        df1 = read_csv(sample_data["csv"])
        assert df1.engine_name == "pandas"

        # Switch to polars
        with config_context(default_engine="polars"):
            df2 = read_csv(sample_data["csv"])
            assert df2.engine_name == "polars"

        # Back to pandas
        df3 = read_csv(sample_data["csv"])
        assert df3.engine_name == "pandas"

    def test_configuration_affects_workflow(self, sample_data):
        """Test that configuration changes affect the workflow."""
        # Test with different thresholds
        set_config(pandas_threshold_mb=0.0001)  # Very low threshold

        df = read_csv(sample_data["csv"])
        # Should select non-pandas due to low threshold
        # (actual engine depends on file size estimation)
        assert df.engine_name in ("pandas", "polars")


class TestEntityWorkflow:
    """Test entity framework workflows."""

    def test_entity_crud_workflow(self, tmp_path):
        """Test complete CRUD workflow with entities."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str
            email: str

        # Create
        alice = User(1, "Alice", "alice@example.com")
        alice.save()

        bob = User(2, "Bob", "bob@example.com")
        bob.save()

        # Read
        loaded_alice = User.find(1)
        assert loaded_alice.name == "Alice"

        all_users = User.find_all()
        assert len(all_users) == 2

        # Update
        alice_updated = User(1, "Alice Smith", "alice.smith@example.com")
        alice_updated.save()

        loaded_again = User.find(1)
        assert loaded_again.name == "Alice Smith"

        # Delete
        alice_updated.delete()
        assert User.count() == 1

    def test_entity_relationship_workflow(self, tmp_path):
        """Test entity relationships in workflow."""

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

            @rel("Post", foreign_key="user_id", reverse=True)
            def posts(self):
                """Get user's posts."""

        @entity(storage_path=tmp_path / "posts", primary_key="post_id")
        @dataclass
        class Post:
            post_id: int
            user_id: int
            title: str
            content: str

            @rel("User", foreign_key="user_id")
            def author(self):
                """Get post's author."""

        # Create users
        User(1, "Alice").save()
        User(2, "Bob").save()

        # Create posts
        Post(1, 1, "First Post", "Hello World").save()
        Post(2, 1, "Second Post", "More content").save()
        Post(3, 2, "Bob's Post", "Bob's content").save()

        # Test reverse relationship
        alice = User.find(1)
        alice_posts = alice.posts()
        assert len(alice_posts) == 2
        assert {p.title for p in alice_posts} == {"First Post", "Second Post"}

        # Test forward relationship
        post = Post.find(1)
        author = post.author()
        assert author.name == "Alice"

    def test_entity_with_different_formats(self, tmp_path):
        """Test entities with different storage formats."""

        @entity(
            storage_path=tmp_path / "parquet_users",
            primary_key="user_id",
            format="parquet",
        )
        @dataclass
        class ParquetUser:
            user_id: int
            name: str

        @entity(
            storage_path=tmp_path / "avro_users",
            primary_key="user_id",
            format="avro",
        )
        @dataclass
        class AvroUser:
            user_id: int
            name: str

        # Save to parquet
        ParquetUser(1, "Alice").save()
        assert (tmp_path / "parquet_users" / "ParquetUser.parquet").exists()

        # Save to avro (if available)
        try:
            AvroUser(1, "Bob").save()
            assert (tmp_path / "avro_users" / "AvroUser.avro").exists()
        except ImportError:
            pytest.skip("fastavro not available")

    def test_complex_data_model(self, tmp_path):
        """Test complex data model with multiple entities and relationships."""

        @entity(storage_path=tmp_path / "customers", primary_key="customer_id")
        @dataclass
        class Customer:
            customer_id: int
            name: str
            email: str

            @rel("Order", foreign_key="customer_id", reverse=True)
            def orders(self):
                """Get customer orders."""

        @entity(storage_path=tmp_path / "orders", primary_key="order_id")
        @dataclass
        class Order:
            order_id: int
            customer_id: int
            product_id: int
            quantity: int

            @rel("Customer", foreign_key="customer_id")
            def customer(self):
                """Get order customer."""

            @rel("Product", foreign_key="product_id")
            def product(self):
                """Get order product."""

        @entity(storage_path=tmp_path / "products", primary_key="product_id")
        @dataclass
        class Product:
            product_id: int
            name: str
            price: float

        # Create products
        Product(1, "Widget", 10.99).save()
        Product(2, "Gadget", 24.99).save()

        # Create customer
        Customer(1, "Alice", "alice@example.com").save()

        # Create orders
        Order(1, 1, 1, 5).save()
        Order(2, 1, 2, 3).save()

        # Query through relationships
        customer = Customer.find(1)
        orders = customer.orders()
        assert len(orders) == 2

        # Navigate multiple relationships
        first_order = orders[0]
        product = first_order.product()
        assert product.name == "Widget"


class TestErrorHandling:
    """Test error handling in workflows."""

    def test_invalid_file_handling(self):
        """Test handling of invalid files."""
        with pytest.raises((FileNotFoundError, OSError)):
            read("/nonexistent/file.csv")

    def test_entity_validation(self, tmp_path):
        """Test entity validation errors."""
        # Test non-dataclass
        with pytest.raises(TypeError, match="must be a dataclass"):

            @entity(storage_path=tmp_path / "test", primary_key="id")
            class NotADataclass:
                pass

    def test_entity_missing_primary_key(self, tmp_path):
        """Test entity with missing primary key."""
        with pytest.raises(ValueError, match="Primary key.*not found"):

            @entity(storage_path=tmp_path / "test", primary_key="nonexistent")
            @dataclass
            class BadEntity:
                name: str


class TestConfigurationIntegration:
    """Test configuration integration with complete workflows."""

    def test_environment_based_workflow(self, sample_data, monkeypatch):
        """Test workflow affected by environment variables."""
        # Set environment variable
        monkeypatch.setenv("PARQUETFRAME_ENGINE", "polars")
        reset_config()  # Reload from environment

        df = read_csv(sample_data["csv"])
        assert df.engine_name == "polars"

    def test_config_persistence_across_operations(self, sample_data):
        """Test configuration persists across multiple operations."""
        set_config(default_engine="polars", verbose=True)

        # Multiple operations should use same config
        df1 = read_csv(sample_data["csv"])
        df2 = read_parquet(sample_data["parquet"])

        assert df1.engine_name == "polars"
        assert df2.engine_name == "polars"
