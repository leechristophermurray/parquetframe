"""
Basic SQL Queries Example

Demonstrates simple SQL operations on DataFrames.
"""

import pandas as pd
from parquetframe.sql import sql, SQLContext


def basic_select():
    """Simple SELECT query."""
    print("=" * 60)
    print("Basic SELECT Query")
    print("=" * 60)

    users = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 28, 32],
            "city": ["NYC", "SF", "LA", "NYC", "SF"],
        }
    )

    print("\nOriginal Data:")
    print(users)

    # Simple SELECT with WHERE
    result = sql("SELECT name, age FROM users WHERE age > 28", users=users)

    print("\nQuery: SELECT name, age FROM users WHERE age > 28")
    print(result)


def aggregations():
    """Aggregation queries."""
    print("\n" + "=" * 60)
    print("Aggregation Queries")
    print("=" * 60)

    sales = pd.DataFrame(
        {
            "product": ["A", "B", "A", "C", "B", "A"],
            "region": ["North", "South", "North", "East", "South", "West"],
            "amount": [100, 150, 200, 120, 180, 90],
        }
    )

    print("\nSales Data:")
    print(sales)

    # GROUP BY with aggregation
    result = sql(
        """
        SELECT 
            product,
            COUNT(*) as total_sales,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount
        FROM sales
        GROUP BY product
        ORDER BY total_amount DESC
        """,
        sales=sales,
    )

    print("\nProduct Sales Summary:")
    print(result)


def joins():
    """JOIN operations."""
    print("\n" + "=" * 60)
    print("JOIN Operations")
    print("=" * 60)

    customers = pd.DataFrame(
        {"customer_id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]}
    )

    orders = pd.DataFrame(
        {
            "order_id": [101, 102, 103, 104],
            "customer_id": [1, 2, 1, 3],
            "amount": [250, 150, 300, 100],
        }
    )

    print("\nCustomers:")
    print(customers)
    print("\nOrders:")
    print(orders)

    # INNER JOIN
    result = sql(
        """
        SELECT 
            c.name,
            o.order_id,
            o.amount
        FROM customers c
        INNER JOIN orders o ON c.customer_id = o.customer_id
        ORDER BY o.amount DESC
        """,
        customers=customers,
        orders=orders,
    )

    print("\nCustomer Orders:")
    print(result)


def persistent_context():
    """Using SQLContext for multiple queries."""
    print("\n" + "=" * 60)
    print("Persistent SQL Context")
    print("=" * 60)

    # Create context
    ctx = SQLContext()

    # Register tables
    products = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Widget", "Gadget", "Doohickey"],
            "price": [10.00, 25.00, 15.00],
        }
    )

    inventory = pd.DataFrame({"product_id": [1, 2, 3], "quantity": [100, 50, 75]})

    ctx.register("products", products)
    ctx.register("inventory", inventory)

    print(f"\nRegistered tables: {ctx.list_tables()}")

    # Execute multiple queries
    result1 = ctx.query("SELECT * FROM products WHERE price > 12")
    print("\nExpensive products:")
    print(result1)

    result2 = ctx.query(
        """
        SELECT 
            p.name,
            p.price,
            i.quantity,
            p.price * i.quantity as total_value
        FROM products p
        JOIN inventory i ON p.id = i.product_id
    """
    )
    print("\nInventory Value:")
    print(result2)


def main():
    """Run all examples."""
    basic_select()
    aggregations()
    joins()
    persistent_context()

    print("\n" + "=" * 60)
    print("✅ All examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
