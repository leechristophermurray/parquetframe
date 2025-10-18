"""
Entity Framework Example - ParquetFrame Phase 2

Demonstrates declarative persistence using the @entity decorator for:
- CRUD operations (Create, Read, Update, Delete)
- Relationships between entities
- Parquet and Avro storage backends
- Query capabilities
- Data validation

This example shows:
- @entity decorator for dataclasses
- CRUD methods (save, find, find_all, delete)
- @rel decorator for relationships
- Storage backend configuration
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from parquetframe.entity import entity, rel

# =============================================================================
# EXAMPLE 1: Basic Entity with CRUD Operations
# =============================================================================


@entity(storage_path="./temp_entities/users", primary_key="user_id")
@dataclass
class User:
    """User entity with basic CRUD operations."""

    user_id: int
    username: str
    email: str
    age: int
    active: bool = True
    created_at: datetime | None = None


def example_basic_crud():
    """Demonstrate basic CRUD operations."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic CRUD Operations")
    print("=" * 80)

    # Clean up from previous runs
    storage_path = Path("./temp_entities")
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)

    print("\n1. CREATE: Save entities")
    # Create and save users
    user1 = User(
        user_id=1,
        username="alice",
        email="alice@example.com",
        age=25,
        created_at=datetime.now(),
    )
    user1.save()
    print(f"   ✓ Saved user: {user1.username}")

    user2 = User(user_id=2, username="bob", email="bob@example.com", age=30)
    user2.save()
    print(f"   ✓ Saved user: {user2.username}")

    print("\n2. READ: Find entities")
    # Find by primary key
    found_user = User.find(1)
    print(
        f"   ✓ Found user by ID: {found_user.username if found_user else 'Not found'}"
    )

    # Find all
    all_users = User.find_all()
    print(f"   ✓ Found {len(all_users)} users total")

    # Find by criteria
    active_users = User.find_by(active=True)
    print(f"   ✓ Found {len(active_users)} active users")

    print("\n3. UPDATE: Modify and save")
    if found_user:
        found_user.age = 26
        found_user.save()
        print(f"   ✓ Updated user age to {found_user.age}")

    print("\n4. DELETE: Remove entities")
    User.delete(2)
    print("   ✓ Deleted user with ID 2")

    remaining = User.find_all()
    print(f"   ✓ {len(remaining)} users remaining")

    # Cleanup
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)


# =============================================================================
# EXAMPLE 2: Relationships Between Entities
# =============================================================================


@entity(storage_path="./temp_entities/customers", primary_key="customer_id")
@dataclass
class Customer:
    """Customer entity."""

    customer_id: int
    name: str
    email: str


@entity(storage_path="./temp_entities/orders", primary_key="order_id")
@dataclass
class Order:
    """Order entity with relationship to Customer."""

    order_id: int
    customer_id: int  # Foreign key
    product: str
    amount: float
    order_date: datetime


# Relationships
Customer.orders = rel(Order, foreign_key="customer_id", rel_type="one-to-many")
Order.customer = rel(Customer, foreign_key="customer_id", rel_type="many-to-one")


def example_relationships():
    """Demonstrate entity relationships."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Entity Relationships")
    print("=" * 80)

    # Clean up
    storage_path = Path("./temp_entities")
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)

    print("\n1. Create related entities:")

    # Create customers
    customer1 = Customer(customer_id=1, name="Alice Johnson", email="alice@example.com")
    customer1.save()
    print(f"   ✓ Created customer: {customer1.name}")

    customer2 = Customer(customer_id=2, name="Bob Smith", email="bob@example.com")
    customer2.save()
    print(f"   ✓ Created customer: {customer2.name}")

    # Create orders
    order1 = Order(
        order_id=1,
        customer_id=1,
        product="Laptop",
        amount=1200.00,
        order_date=datetime.now(),
    )
    order1.save()
    print(f"   ✓ Created order: {order1.product} for customer {order1.customer_id}")

    order2 = Order(
        order_id=2,
        customer_id=1,
        product="Mouse",
        amount=25.00,
        order_date=datetime.now(),
    )
    order2.save()
    print(f"   ✓ Created order: {order2.product} for customer {order2.customer_id}")

    print("\n2. Navigate relationships:")
    print("   • Customer → Orders (one-to-many)")
    print("   • Order → Customer (many-to-one)")

    print("\n3. Query related data:")
    print("   customer = Customer.find(1)")
    print("   orders = customer.orders  # Get all orders for this customer")
    print("   ")
    print("   order = Order.find(1)")
    print("   customer = order.customer  # Get customer for this order")

    # Cleanup
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)


# =============================================================================
# EXAMPLE 3: Storage Backend Configuration
# =============================================================================


def example_storage_backends():
    """Demonstrate different storage backends."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Storage Backend Configuration")
    print("=" * 80)

    print("\n1. Parquet Storage (default):")
    print("   @entity(storage_path='./data/users', format='parquet')")
    print("   • Columnar format, great for analytics")
    print("   • Excellent compression")
    print("   • Fast filtering on columns")

    print("\n2. Avro Storage:")
    print("   @entity(storage_path='./data/users', format='avro')")
    print("   • Row-oriented format")
    print("   • Schema evolution support")
    print("   • Compact binary format")
    print("   • Good for data exchange")

    print("\n3. Additional options:")
    print("   @entity(")
    print("       storage_path='./data/users',")
    print("       primary_key='user_id',")
    print("       format='parquet',")
    print("       partition_by='created_date',  # Partition for performance")
    print("       compression='snappy'           # Compression codec")
    print("   )")


# =============================================================================
# EXAMPLE 4: Advanced Querying
# =============================================================================


def example_advanced_queries():
    """Demonstrate advanced query capabilities."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Advanced Querying")
    print("=" * 80)

    print("\n1. Simple queries:")
    print("   # Find by primary key")
    print("   user = User.find(1)")
    print("")
    print("   # Find all")
    print("   all_users = User.find_all()")
    print("")
    print("   # Find by single criterion")
    print("   active_users = User.find_by(active=True)")

    print("\n2. Multiple criteria:")
    print("   # Find by multiple fields")
    print("   young_active_users = User.find_by(")
    print("       active=True,")
    print("       age={'<': 30}")
    print("   )")

    print("\n3. Operators:")
    print("   # Comparison operators")
    print("   users = User.find_by(age={'>=': 18, '<': 65})")
    print("   users = User.find_by(username={'in': ['alice', 'bob']})")
    print("   users = User.find_by(email={'like': '%@example.com'})")

    print("\n4. Sorting and limiting:")
    print("   # Sort results")
    print("   users = User.find_all(order_by='age', ascending=False)")
    print("")
    print("   # Limit results")
    print("   recent_users = User.find_all(limit=10)")


# =============================================================================
# EXAMPLE 5: Data Validation
# =============================================================================


@entity(storage_path="./temp_entities/products", primary_key="product_id")
@dataclass
class Product:
    """Product entity with validation."""

    product_id: int
    name: str
    price: float
    stock: int
    category: str

    def __post_init__(self):
        """Validate entity data."""
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.stock < 0:
            raise ValueError("Stock cannot be negative")
        if len(self.name) == 0:
            raise ValueError("Name cannot be empty")


def example_validation():
    """Demonstrate data validation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Data Validation")
    print("=" * 80)

    storage_path = Path("./temp_entities")
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)

    print("\n1. Valid entity:")
    try:
        product = Product(
            product_id=1, name="Laptop", price=1200.00, stock=50, category="Electronics"
        )
        product.save()
        print("   ✓ Valid product saved successfully")
    except ValueError as e:
        print(f"   ✗ Validation error: {e}")

    print("\n2. Invalid entity (negative price):")
    try:
        invalid_product = Product(
            product_id=2,
            name="Invalid Product",
            price=-100.00,  # Invalid
            stock=10,
            category="Test",
        )
        invalid_product.save()
        print("   ✓ Saved (should not reach here)")
    except ValueError as e:
        print(f"   ✗ Validation error: {e}")

    print("\n3. Custom validation methods:")
    print("   def __post_init__(self):")
    print("       '''Validate entity data.'''")
    print("       if self.price < 0:")
    print("           raise ValueError('Price cannot be negative')")

    # Cleanup
    if storage_path.exists():
        import shutil

        shutil.rmtree(storage_path)


# =============================================================================
# EXAMPLE 6: Best Practices
# =============================================================================


def example_best_practices():
    """Display best practices for entity framework."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Best Practices")
    print("=" * 80)

    practices = {
        "Entity Design": [
            "Use dataclasses for clean, typed entity definitions",
            "Define primary_key explicitly",
            "Use Optional types for nullable fields",
            "Add __post_init__ for validation",
        ],
        "Relationships": [
            "Define foreign keys clearly",
            "Use @rel decorator for bidirectional relationships",
            "Consider lazy loading for large related datasets",
            "Document relationship cardinality",
        ],
        "Performance": [
            "Partition large datasets by date or category",
            "Use appropriate compression for your use case",
            "Index frequently queried fields",
            "Batch operations when possible",
        ],
        "Storage": [
            "Choose Parquet for analytics workloads",
            "Choose Avro for data exchange and evolution",
            "Organize entities in separate directories",
            "Use meaningful storage paths",
        ],
        "Transactions": [
            "Current version is file-based (no ACID transactions)",
            "Implement versioning for critical data",
            "Use try-except for error handling",
            "Consider backups for production data",
        ],
    }

    for category, tips in practices.items():
        print(f"\n{category}:")
        for tip in tips:
            print(f"   • {tip}")


def main():
    """Run all examples."""
    print("=" * 80)
    print("ParquetFrame Phase 2 - Entity Framework Examples")
    print("=" * 80)

    example_basic_crud()
    example_relationships()
    example_storage_backends()
    example_advanced_queries()
    example_validation()
    example_best_practices()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • @entity decorator provides declarative persistence")
    print("  • CRUD operations built-in (save, find, find_all, delete)")
    print("  • @rel decorator for entity relationships")
    print("  • Supports both Parquet and Avro storage")
    print("  • Data validation via __post_init__")
    print("\nNext steps:")
    print("  • Try engine_selection.py for automatic engine selection")
    print("  • Try avro_roundtrip.py for Avro format support")
    print("  • Try multi_engine_conversion.py for engine switching")
    print("\nNote:")
    print("  The entity framework examples demonstrate the API design.")
    print("  Full implementation may require additional setup.")


if __name__ == "__main__":
    main()
