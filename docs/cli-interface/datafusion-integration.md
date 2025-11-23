# DataFusion Integration Guide

Apache DataFusion is integrated into ParquetFrame's Interactive CLI to provide high-performance SQL execution for analytical workloads.

## Overview

DataFusion is a query execution framework written in Rust that excels at:
- Complex aggregations and analytics
- Window functions
- Large-scale data processing
- Query optimization

## Installation

DataFusion is an optional dependency. Install it with:

```bash
pip install parquetframe[ai]
# or
pip install datafusion>=33.0.0
```

## Usage in Interactive CLI

### Basic Query

```python
pframe interactive

# Execute with DataFusion
%df SELECT * FROM sales WHERE revenue > 1000
```

### When DataFusion is Available

The CLI automatically detects DataFusion availability:
- ✅ If installed: `%df` commands execute with DataFusion
- ❌ If not installed: Error message with installation instructions

### Checking Status

```python
# In the REPL, DataFusion status is shown at startup
# Welcome screen shows: "DataFusion: Yes" or "DataFusion: No"
```

## Performance Comparison

### Standard SQL vs DataFusion

**Standard SQL** (`%sql`):
- Uses DuckDB or pandas backend
- Good for simple queries
- Lower memory overhead

**DataFusion SQL** (`%df`):
- Optimized query execution
- Better for complex analytics
- Parallel processing
- Advanced SQL features

### Example: Complex Aggregation

```python
# Using DataFusion for better performance
%df 
SELECT 
    customer_id,
    DATE_TRUNC('month', order_date) as month,
    SUM(amount) as total_revenue,
    COUNT(*) as order_count,
    AVG(amount) as avg_order_value,
    SUM(amount) OVER (
        PARTITION BY customer_id 
        ORDER BY DATE_TRUNC('month', order_date)
    ) as running_total
FROM orders
WHERE order_date >= '2023-01-01'
GROUP BY customer_id, month
ORDER BY customer_id, month
```

## Supported SQL Features

DataFusion supports a wide range of SQL features:

### Aggregations
- Standard: `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`
- Statistical: `STDDEV`, `VARIANCE`
- Approximate: `APPROX_DISTINCT`, `APPROX_PERCENTILE`

### Window Functions
```sql
%df SELECT 
    product_id,
    revenue,
    ROW_NUMBER() OVER (ORDER BY revenue DESC) as rank,
    LAG(revenue) OVER (ORDER BY date) as prev_revenue
FROM products
```

### Common Table Expressions (CTEs)
```sql
%df 
WITH monthly_sales AS (
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(amount) as revenue
    FROM sales
    GROUP BY month
)
SELECT * FROM monthly_sales WHERE revenue > 10000
```

### Joins
```sql
%df 
SELECT 
    u.name,
    COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.name
```

## Best Practices

1. **Use for Analytics**: DataFusion shines with complex analytical queries
2. **Leverage Window Functions**: Take advantage of advanced SQL features
3. **Monitor Memory**: DataFusion loads data into memory for processing
4. **Optimize Predicates**: Use WHERE clauses early to reduce data volume

## Troubleshooting

### DataFusion Not Available

```python
%df SELECT * FROM table
# Error: ❌ DataFusion not available. Install with: pip install datafusion
```

**Solution**: Install datafusion package

### Memory Issues

If queries run out of memory:
- Add more aggressive WHERE clauses
- Limit result sets
- Use sampling for exploration

### Query Errors

DataFusion uses standard SQL but may have slight differences from other engines:
- Check type compatibility
- Verify function names
- Consult [DataFusion SQL reference](https://arrow.apache.org/datafusion/)

## Integration with Other Features

### Python Variables
```python
# Execute query
result = %df SELECT * FROM sales
# Use in Python
top_10 = result.nlargest(10, 'revenue')
```

### Permissions
```python
# Check before running expensive query
%permissions check user:current viewer table:sales
%df SELECT * FROM sales
```

## Examples

### Time Series Analysis
```python
%df
SELECT 
    DATE_TRUNC('day', timestamp) as day,
    AVG(value) as daily_avg,
    MIN(value) as daily_min,
    MAX(value) as daily_max
FROM sensor_data
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day
```

### Top-N Per Group
```python
%df
SELECT *
FROM (
    SELECT 
        category,
        product_name,
        revenue,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) as rn
    FROM products
)
WHERE rn <= 5
```

### Cohort Analysis
```python
%df
SELECT 
    DATE_TRUNC('month', signup_date) as cohort,
    DATE_TRUNC('month', purchase_date) as purchase_month,
    COUNT(DISTINCT user_id) as users
FROM user_purchases
GROUP BY cohort, purchase_month
ORDER BY cohort, purchase_month
```
