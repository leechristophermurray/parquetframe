# Advanced Features

> Advanced functionality and patterns for power users.

## Advanced Operations

ParquetFrame provides sophisticated features for complex data processing workflows.

## Memory Management

Learn how to optimize memory usage for large datasets:

- Lazy loading strategies
- Chunked processing
- Memory-efficient transformations

## Backend Selection

Control which processing backend to use:

- Pandas for small to medium datasets
- Dask for distributed processing
- Automatic backend selection

## Summary

Advanced features enable ParquetFrame to handle complex scenarios and large-scale data processing efficiently.

## Examples

```python
import parquetframe as pf

# Advanced memory management
df = pf.read("large_file.parquet", lazy=True)

# Force specific backend
df_pandas = pf.read("data.parquet", backend="pandas")
df_dask = pf.read("data.parquet", backend="dask")

# Complex transformations
result = df.filter("column > 100").groupby("category").agg({"value": "mean"})
```

## Further Reading

- [Performance Tips](performance.md)
- [Backend Selection](backends.md)
- [Memory Management Best Practices](tutorials/performance.md)
