# SQL Engine

ParquetFrame provides SQL query capabilities using Apache DataFusion (with DuckDB fallback) for high-performance analytics.

## Quick Start

```python
from parquetframe.sql import sql
import pandas as pd

# Create data
users = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35]
})

# Query with SQL
result = sql(
    "SELECT name, age FROM users WHERE age > 25",
    users=users
)
```

## Simple Queries

### SELECT with WHERE

```python
result = sql(
    "SELECT * FROM data WHERE value > 100",
    data=my_dataframe
)
```

### Aggregations

```python
result = sql(
    """
    SELECT
        category,
        COUNT(*) as count,
        SUM(amount) as total,
        AVG(amount) as average
    FROM sales
    GROUP BY category
    ORDER BY total DESC
    """,
    sales=sales_df
)
```

## Joins

### Inner Join

```python
result = sql(
    """
    SELECT
        c.name,
        o.order_id,
        o.amount
    FROM customers c
    INNER JOIN orders o ON c.id = o.customer_id
    """,
    customers=customers_df,
    orders=orders_df
)
```

### Left Join

```python
result = sql(
    """
    SELECT
        p.product_name,
        COALESCE(i.quantity, 0) as stock
    FROM products p
    LEFT JOIN inventory i ON p.id = i.product_id
    """,
    products=products_df,
    inventory=inventory_df
)
```

## Persistent Context

For multiple queries on the same tables:

```python
from parquetframe.sql import SQLContext

# Create context
ctx = SQLContext()

# Register tables
ctx.register("users", users_df)
ctx.register("orders", orders_df)

# Execute multiple queries
result1 = ctx.query("SELECT * FROM users WHERE age > 30")
result2 = ctx.query("""
    SELECT u.name, COUNT(*) as order_count
    FROM users u
    JOIN orders o ON u.id = o.user_id
    GROUP BY u.name
""")

# List tables
print(ctx.list_tables())  # ['users', 'orders']
```

## Advanced Features

### Subqueries

```python
result = sql(
    """
    SELECT *
    FROM users
    WHERE id IN (
        SELECT DISTINCT user_id
        FROM orders
        WHERE amount > 100
    )
    """,
    users=users_df,
    orders=orders_df
)
```

### Window Functions

```python
result = sql(
    """
    SELECT
        name,
        amount,
        ROW_NUMBER() OVER (ORDER BY amount DESC) as rank
    FROM sales
    """,
    sales=sales_df
)
```

## Examples

See [`examples/sql/basic_queries.py`](../../examples/sql/basic_queries.py) for complete examples including:
- Basic SELECT queries
- Aggregations with GROUP BY
- JOIN operations
- Persistent context usage

## Performance

The SQL engine uses:
- **DataFusion**: High-performance query execution with Arrow
- **DuckDB** (fallback): If DataFusion not available

Both engines provide excellent performance for analytical queries.

## Installation

```bash
# With DataFusion (recommended)
pip install datafusion

# Or with DuckDB
pip install duckdb
```

## API Reference

### sql()

```python
def sql(query: str, **tables) -> pd.DataFrame
```

Execute SQL query on DataFrames.

### SQLContext

```python
ctx = SQLContext()
ctx.register(name: str, df)
ctx.query(sql: str) -> pd.DataFrame
ctx.list_tables() -> List[str]
ctx.unregister(name: str)
```

Persistent SQL context for multiple queries.
