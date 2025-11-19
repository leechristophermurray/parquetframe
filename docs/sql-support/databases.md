# Database Connections

ParquetFrame interoperates with databases via SQLAlchemy URIs for reading/writing tables alongside local files.

## Supported URIs (examples)

- Postgres: `postgresql+psycopg2://user:pass@host:5432/db`
- MySQL: `mysql+pymysql://user:pass@host:3306/db`
- SQLite: `sqlite:///path/to.db`

## Reading and Writing

```python
from parquetframe.sql import read_table, write_table

# Read a table into a DataFrameProxy
users = read_table("postgresql+psycopg2://...", table="users")

# Write results back
write_table(users, "sqlite:///analytics.db", table="active_users", if_exists="replace")
```

## Authentication and Configuration

- Prefer environment variables or secrets managers over hard‑coding credentials.
- Use read‑only roles when possible; avoid broad grants.
- Configure connection pools via SQLAlchemy engine options.

## Performance Notes

- Push filters/aggregations down to the database when feasible.
- Limit columns and rows early; paginate or chunk large transfers.

## Troubleshooting

- Verify drivers are installed (e.g., `psycopg2`, `pymysql`).
- Check SSL parameters for managed services.

## Related Documentation

- [SQL Support Overview](index.md)
- [DuckDB Integration](duckdb.md)
- [Cookbook](cookbook.md)
