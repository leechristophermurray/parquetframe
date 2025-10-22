# SQL Support

Execute powerful SQL queries directly on your DataFrames using ParquetFrame's integrated DuckDB engine. Combine the flexibility of SQL with the performance of pandas and Dask.

## Overview

ParquetFrame provides comprehensive SQL support through DuckDB integration, enabling you to:

- Execute SQL queries on pandas and Dask DataFrames
- Join multiple DataFrames with automatic registration
- Use advanced SQL features like window functions and CTEs
- Optimize query performance with explain plans
- Seamlessly switch between DataFrame and SQL workflows

## Key Features

- **DuckDB Engine**: Fast, analytical SQL database engine
- **Automatic DataFrame Registration**: DataFrames become SQL tables instantly
- **Multi-DataFrame JOINs**: Query across multiple datasets effortlessly
- **Backend Agnostic**: Works with both pandas and Dask DataFrames
- **Query Validation**: Built-in SQL syntax validation and safety checks
- **Performance Analysis**: Query explain plans for optimization

## Quick Start

### Installation

```bash
# Install ParquetFrame with SQL support
pip install parquetframe[sql]

# Or install everything
pip install parquetframe[all]
```

### Basic SQL Query

```python
import parquetframe as pf

# Load data
customers = pf.read("customers.parquet")

# Execute SQL query
result = customers.sql("""
    SELECT customer_id, name, age
    FROM df
    WHERE age > 30
    ORDER BY age DESC
    LIMIT 10
""")

print(result)
```

## Core SQL Operations

### Basic Queries

```python
import parquetframe as pf

# Sample data
sales = pf.read("sales_data.parquet")

# SELECT with filtering
result = sales.sql("""
    SELECT product_name, sales_amount, order_date
    FROM df
    WHERE sales_amount > 1000
    AND order_date >= '2024-01-01'
""")

# Aggregation queries
summary = sales.sql("""
    SELECT
        product_category,
        COUNT(*) as order_count,
        SUM(sales_amount) as total_revenue,
        AVG(sales_amount) as avg_order_value
    FROM df
    GROUP BY product_category
    ORDER BY total_revenue DESC
""")

# Window functions
trending = sales.sql("""
    SELECT
        product_name,
        order_date,
        sales_amount,
        SUM(sales_amount) OVER (
            PARTITION BY product_name
            ORDER BY order_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as rolling_7day_sales
    FROM df
    ORDER BY product_name, order_date
""")
```

### Multi-DataFrame JOINs

```python
# Load multiple datasets
customers = pf.read("customers.parquet")
orders = pf.read("orders.parquet")
products = pf.read("products.parquet")

# Complex JOIN query
analysis = customers.sql("""
    SELECT
        c.customer_name,
        c.customer_segment,
        COUNT(o.order_id) as total_orders,
        SUM(o.order_amount) as total_spent,
        AVG(o.order_amount) as avg_order_value,
        COUNT(DISTINCT p.product_category) as categories_purchased
    FROM df c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    LEFT JOIN products p ON o.product_id = p.product_id
    WHERE o.order_date >= '2024-01-01'
    GROUP BY c.customer_name, c.customer_segment
    HAVING total_orders > 5
    ORDER BY total_spent DESC
""", orders=orders, products=products)

print(f"Customer analysis: {len(analysis)} customers")
print(analysis.head())
```

### Advanced SQL Features

#### Common Table Expressions (CTEs)

```python
result = sales.sql("""
    WITH monthly_sales AS (
        SELECT
            DATE_TRUNC('month', order_date) as month,
            product_category,
            SUM(sales_amount) as monthly_revenue
        FROM df
        GROUP BY month, product_category
    ),
    category_trends AS (
        SELECT
            *,
            LAG(monthly_revenue) OVER (
                PARTITION BY product_category
                ORDER BY month
            ) as prev_month_revenue
        FROM monthly_sales
    )
    SELECT
        month,
        product_category,
        monthly_revenue,
        monthly_revenue - prev_month_revenue as revenue_change,
        CASE
            WHEN prev_month_revenue > 0 THEN
                (monthly_revenue - prev_month_revenue) / prev_month_revenue * 100
            ELSE NULL
        END as growth_rate
    FROM category_trends
    WHERE prev_month_revenue IS NOT NULL
    ORDER BY month, growth_rate DESC
""")
```

#### Subqueries and Analytics

```python
# Find top customers in each region
top_customers = customers.sql("""
    SELECT
        region,
        customer_name,
        total_spent,
        customer_rank
    FROM (
        SELECT
            region,
            customer_name,
            total_spent,
            ROW_NUMBER() OVER (
                PARTITION BY region
                ORDER BY total_spent DESC
            ) as customer_rank
        FROM df
        WHERE total_spent > 0
    ) ranked_customers
    WHERE customer_rank <= 3
    ORDER BY region, customer_rank
""")
```

## CLI Integration

ParquetFrame provides powerful CLI tools for SQL operations:

### Basic SQL Command

```bash
# Execute SQL query from command line
pframe sql "SELECT COUNT(*) FROM df" --file data.parquet

# Save results
pframe sql "SELECT * FROM df WHERE age > 30" \
    --file customers.parquet \
    --output filtered_customers.parquet

# JOIN multiple files
pframe sql "SELECT c.name, SUM(o.amount) as total FROM df c JOIN orders o ON c.id = o.customer_id GROUP BY c.name" \
    --file customers.parquet \
    --join "orders=orders.parquet" \
    --output customer_totals.parquet
```

### Interactive SQL Mode

```bash
# Start interactive SQL session
pframe sql --interactive --file sales_data.parquet

# In the interactive session:
SQL> SELECT product_category, AVG(sales_amount) as avg_sales
     FROM df
     GROUP BY product_category
     ORDER BY avg_sales DESC;

# Results displayed automatically with rich formatting
# Tables show with colors and proper alignment
```

### Query Validation and Explanation

```bash
# Validate SQL syntax before execution
pframe sql "SELECT * FROM df WHERE invalid_syntax" \
    --file data.parquet \
    --validate

# Show execution plan
pframe sql "SELECT * FROM df WHERE complex_condition" \
    --file data.parquet \
    --explain
```

## Multi-Format SQL Support

ParquetFrame's SQL engine supports queries across multiple file formats with automatic format detection and intelligent backend selection.

### Supported Formats

| Format | Extension | Read Support | Write Support | Special Notes |
|--------|-----------|--------------|---------------|--------------|
| **Parquet** | `.parquet`, `.pqt` | ✅ | ✅ | Optimal performance, supports nested data |
| **CSV** | `.csv` | ✅ | ✅ | Automatic delimiter detection |
| **TSV** | `.tsv` | ✅ | ✅ | Tab-separated values |
| **JSON** | `.json` | ✅ | ✅ | Supports nested structures |
| **JSON Lines** | `.jsonl`, `.ndjson` | ✅ | ✅ | Streaming-friendly format |
| **ORC** | `.orc` | ✅ | ✅ | Requires pyarrow with ORC support |

### Cross-Format Operations

```python
import parquetframe as pf

# Load different formats
users_csv = pf.read("users.csv")        # CSV format
orders_json = pf.read("orders.json")    # JSON format
products_pqt = pf.read("products.pqt")  # Parquet format

# Cross-format JOIN query
result = users_csv.sql("""
    SELECT
        u.name,
        u.email,
        COUNT(o.order_id) as order_count,
        SUM(o.amount) as total_spent,
        AVG(p.price) as avg_product_price
    FROM df u
    LEFT JOIN orders o ON u.user_id = o.user_id
    LEFT JOIN products p ON o.product_id = p.product_id
    WHERE u.active = true
    GROUP BY u.name, u.email
    HAVING order_count > 0
    ORDER BY total_spent DESC
""", orders=orders_json, products=products_pqt)

print(f"Analysis across 3 formats: {len(result)} active customers")
```

### Format-Specific Considerations

#### CSV/TSV Limitations
- No nested data structures
- Data type inference may vary
- NULL values represented as empty strings or "null"

#### JSON Advantages
- Native support for nested objects and arrays
- Preserves data types better than CSV
- Good for semi-structured data

#### Parquet Optimization
- Columnar storage for analytical queries
- Built-in compression and encoding
- Excellent for large datasets

#### ORC Compatibility
- Optimized for Hadoop ecosystems
- Strong compression and type system
- May require additional dependencies

### Performance by Format

```python
# Benchmark different formats
import time

formats = {
    'parquet': pf.read('data.parquet'),
    'csv': pf.read('data.csv'),
    'json': pf.read('data.json')
}

query = "SELECT category, AVG(value) as avg_val FROM df GROUP BY category"

for format_name, df in formats.items():
    start = time.time()
    result = df.sql(query)
    duration = time.time() - start
    print(f"{format_name}: {duration:.3f}s ({len(result)} results)")
```

### Intelligent Backend Selection

ParquetFrame automatically chooses the optimal backend based on data size:

```python
# Small files (< 100MB) → pandas (fast operations)
small_data = pf.read("small_dataset.csv")
result = small_data.sql("SELECT COUNT(*) FROM df")  # Uses pandas

# Large files (> 100MB) → Dask (memory efficient)
large_data = pf.read("huge_dataset.parquet")
result = large_data.sql("SELECT COUNT(*) FROM df")  # Uses Dask

# Manual backend control
forced_dask = pf.read("data.csv", islazy=True)      # Force Dask
forced_pandas = pf.read("data.json", islazy=False)  # Force pandas
```

## Performance and Optimization

### Query Performance Analysis

```python
from parquetframe.sql import explain_query

# Get execution plan
plan = explain_query(
    main_df=sales._df,
    query="""
        SELECT product_category, SUM(sales_amount) as total
        FROM df
        WHERE order_date >= '2024-01-01'
        GROUP BY product_category
    """
)

print("Execution Plan:")
print(plan)
```

### Performance Best Practices

```python
# 1. Filter early to reduce data size
efficient_query = sales.sql("""
    SELECT customer_id, SUM(amount) as total
    FROM df
    WHERE order_date >= '2024-01-01'  -- Filter first
    GROUP BY customer_id
    HAVING total > 1000               -- Filter after aggregation
""")

# 2. Use column selection to minimize I/O
selective_query = sales.sql("""
    SELECT customer_id, order_date, amount  -- Only needed columns
    FROM df
    WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31'
""")

# 3. Leverage indexes for JOINs (DuckDB optimizes automatically)
join_query = customers.sql("""
    SELECT c.name, o.total_amount
    FROM df c
    JOIN orders o ON c.customer_id = o.customer_id  -- Indexed JOIN
    WHERE o.order_date >= '2024-01-01'
""", orders=orders)
```

## Integration with Dask

SQL operations work seamlessly with Dask DataFrames:

```python
# Large dataset with Dask
large_sales = pf.read("huge_sales_data.parquet", islazy=True)

# DuckDB will compute Dask DataFrame automatically
with warnings.catch_warnings():
    warnings.simplefilter("ignore")  # Suppress Dask computation warning

    result = large_sales.sql("""
        SELECT
            product_category,
            DATE_TRUNC('month', order_date) as month,
            SUM(sales_amount) as monthly_sales
        FROM df
        WHERE order_date >= '2023-01-01'
        GROUP BY product_category, month
        ORDER BY month, monthly_sales DESC
    """)

print(f"Result type: {type(result._df)}")
print(f"Rows: {len(result)}")
```

## Error Handling and Safety

ParquetFrame includes built-in safety features:

```python
from parquetframe.sql import validate_sql_query

# Query validation
query = "SELECT * FROM df WHERE age > 30"
if validate_sql_query(query):
    print("Query is valid")
    result = df.sql(query)
else:
    print("Invalid query syntax")

# Automatic warnings for potentially dangerous operations
try:
    # This will warn but not fail (operates on in-memory data)
    result = df.sql("DROP TABLE df")
except Exception as e:
    print(f"Query failed: {e}")

# Error handling with detailed messages
try:
    result = customers.sql("""
        SELECT invalid_column
        FROM df
        WHERE nonexistent_table.id = 1
    """)
except ValueError as e:
    print(f"SQL Error: {e}")
    # Provides helpful context for debugging
```

## Advanced Use Cases

### Time Series Analysis

```python
time_series = sales.sql("""
    SELECT
        DATE_TRUNC('day', order_date) as date,
        SUM(sales_amount) as daily_sales,
        AVG(SUM(sales_amount)) OVER (
            ORDER BY DATE_TRUNC('day', order_date)
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as moving_avg_7d,
        SUM(sales_amount) - LAG(SUM(sales_amount)) OVER (
            ORDER BY DATE_TRUNC('day', order_date)
        ) as daily_change
    FROM df
    WHERE order_date >= '2024-01-01'
    GROUP BY DATE_TRUNC('day', order_date)
    ORDER BY date
""")
```

### Cohort Analysis

```python
cohort_analysis = customers.sql("""
    WITH customer_cohorts AS (
        SELECT
            customer_id,
            DATE_TRUNC('month', first_order_date) as cohort_month,
            DATE_TRUNC('month', order_date) as order_month
        FROM df
    ),
    cohort_sizes AS (
        SELECT
            cohort_month,
            COUNT(DISTINCT customer_id) as cohort_size
        FROM customer_cohorts
        GROUP BY cohort_month
    )
    SELECT
        c.cohort_month,
        c.order_month,
        COUNT(DISTINCT c.customer_id) as active_customers,
        s.cohort_size,
        COUNT(DISTINCT c.customer_id)::FLOAT / s.cohort_size as retention_rate,
        EXTRACT(MONTH FROM AGE(c.order_month, c.cohort_month)) as period_number
    FROM customer_cohorts c
    JOIN cohort_sizes s ON c.cohort_month = s.cohort_month
    GROUP BY c.cohort_month, c.order_month, s.cohort_size
    ORDER BY c.cohort_month, c.order_month
""", orders=orders)
```

### Statistical Analysis

```python
stats_analysis = sales.sql("""
    SELECT
        product_category,
        COUNT(*) as sample_size,
        AVG(sales_amount) as mean_sales,
        STDDEV(sales_amount) as std_dev,
        MIN(sales_amount) as min_sales,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY sales_amount) as q1,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sales_amount) as median,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY sales_amount) as q3,
        MAX(sales_amount) as max_sales,
        (PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY sales_amount) -
         PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY sales_amount)) as iqr
    FROM df
    GROUP BY product_category
    ORDER BY mean_sales DESC
""")
```

## Migration from Other Tools

### From pandas

```python
# Before (pandas)
import pandas as pd

df = pd.read_parquet("data.parquet")
result = df.groupby('category').agg({
    'amount': ['sum', 'mean', 'count']
}).round(2)

# After (ParquetFrame SQL)
import parquetframe as pf

df = pf.read("data.parquet")
result = df.sql("""
    SELECT
        category,
        ROUND(SUM(amount), 2) as total_amount,
        ROUND(AVG(amount), 2) as avg_amount,
        COUNT(*) as count_records
    FROM df
    GROUP BY category
    ORDER BY total_amount DESC
""")
```

### From Spark SQL

```python
# Spark SQL patterns work directly in ParquetFrame
result = df.sql("""
    SELECT
        customer_id,
        product_category,
        SUM(amount) as total_spent,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY SUM(amount) DESC
        ) as category_rank
    FROM df
    GROUP BY customer_id, product_category
""")
```

## Troubleshooting

### Common Issues

1. **"No such table: df"**
   ```python
   # Ensure DataFrame is loaded
   df = pf.read("data.parquet")
   result = df.sql("SELECT * FROM df")  # 'df' is the default table name
   ```

2. **"Column not found"**
   ```python
   # Check column names
   print(df.columns)
   # Use backticks for special column names
   result = df.sql("SELECT `column-with-hyphens` FROM df")
   ```

3. **"Memory error with large datasets"**
   ```python
   # Use Dask for large data
   large_df = pf.read("huge_file.parquet", islazy=True)
   # Process in chunks or add filtering
   result = large_df.sql("SELECT * FROM df WHERE date >= '2024-01-01' LIMIT 10000")
   ```

4. **"Slow JOIN performance"**
   ```python
   # Add filters before JOINs
   result = customers.sql("""
       SELECT c.name, o.amount
       FROM (
           SELECT * FROM df WHERE region = 'US'  -- Filter first
       ) c
       JOIN orders o ON c.customer_id = o.customer_id
   """, orders=orders)
   ```

## Best Practices

1. **Use Descriptive Table Aliases**
   ```python
   # Good
   result = customers.sql("""
       SELECT c.name, o.total
       FROM df c
       JOIN orders o ON c.id = o.customer_id
   """, orders=orders)
   ```

2. **Filter Early and Often**
   ```python
   # Filter before expensive operations
   result = sales.sql("""
       SELECT product_id, AVG(amount)
       FROM df
       WHERE order_date >= '2024-01-01'  -- Filter first
       GROUP BY product_id
       HAVING AVG(amount) > 100         -- Filter after aggregation
   """)
   ```

3. **Use Parameterized Queries for Safety**
   ```python
   # While DuckDB operates on in-memory data, still good practice
   start_date = '2024-01-01'
   min_amount = 1000

   query = f"""
       SELECT * FROM df
       WHERE order_date >= '{start_date}'
       AND amount >= {min_amount}
   """
   result = df.sql(query)
   ```

4. **Test Queries on Small Samples**
   ```python
   # Test on sample first
   sample = df.sql("SELECT * FROM df LIMIT 1000")
   test_result = sample.sql("your complex query here")

   # Then run on full dataset
   if test_result is not None:
       full_result = df.sql("your complex query here")
   ```

## Related Documentation

- [DuckDB Integration](duckdb.md) - Advanced DuckDB features and optimization
- [Database Connections](databases.md) - Connect to external databases
- [Backend Selection](../legacy-migration/phase1-backends.md) - Choose between pandas and Dask
- [CLI Guide](../cli-interface/index.md) - Command-line SQL operations
- [Performance Optimization](../performance.md) - General performance tips
