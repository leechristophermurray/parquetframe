# DuckDB Integration

DuckDB provides an in‑process SQL engine with excellent Parquet and DataFrame support. ParquetFrame integrates DuckDB to run SQL over one or more DataFrames.

## Quick Start

```python
import parquetframe as pf

customers = pf.read("customers.parquet")
orders = pf.read("orders.parquet")

result = customers.sql(
    """
    SELECT c.name, SUM(o.amount) AS total
    FROM df c JOIN orders o ON c.customer_id = o.customer_id
    WHERE c.status = 'active'
    GROUP BY c.name
    ORDER BY total DESC
    """,
    orders=orders,
)
print(result.head())
```

## CLI

```bash
pframe sql "SELECT COUNT(*) FROM df" --file data.parquet
pframe sql --interactive --file data.parquet
```

## Registration Model

- The primary DataFrame is available as `df`.
- Additional DataFrames are passed as keyword args (e.g., `orders=orders`) and referenced by table name.
- Dask backends auto‑compute inputs as needed.

## Validation and EXPLAIN

```python
from parquetframe.sql import explain
plan = explain(customers, "SELECT * FROM df LIMIT 5")
print(plan)
```

CLI:

```bash
pframe sql "SELECT * FROM df LIMIT 5" --file data.parquet --explain
```

## Tips and Performance

- Project only required columns in the SELECT and JOINs.
- Use filters early to reduce data size before joins.
- For large datasets, consider Parquet partitioning and predicate pushdown.

## Troubleshooting

- Ensure `duckdb` extra installed: `pip install parquetframe[sql]`.
- For mixed backends, let ParquetFrame convert Dask to pandas for execution when necessary.

## Related Documentation

- [SQL Support Overview](index.md)
- [Database Connections](databases.md)
- [Cookbook](cookbook.md)
