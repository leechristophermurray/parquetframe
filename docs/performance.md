# Performance Tips

> Optimize ParquetFrame for maximum performance.

## Performance Optimization

Getting the best performance out of ParquetFrame requires understanding when to use different approaches.

## Memory Optimization

- Use lazy loading for large files
- Choose appropriate chunk sizes
- Monitor memory usage during processing

## Backend Selection

- Pandas: Fast for small to medium datasets
- Dask: Better for large datasets or distributed processing
- Auto-selection: Let ParquetFrame choose the optimal backend

## File Format Optimization

- Column pruning to read only necessary columns
- Predicate pushdown for filtering
- Optimal compression settings

## Summary

Performance optimization in ParquetFrame involves choosing the right backend, optimizing memory usage, and leveraging parquet format features.

## Examples

```python
import parquetframe as pf

# Lazy loading for large files
df = pf.read("huge_file.parquet", lazy=True)

# Read only specific columns
df = pf.read("data.parquet", columns=["col1", "col2"])

# Filter during read (predicate pushdown)
df = pf.read("data.parquet", filters=[("date", ">=", "2023-01-01")])
```

## Further Reading

- [Advanced Features](phase1-advanced.md)
- [Legacy Backend Selection](legacy/legacy-backends.md)
- [Benchmarks](benchmarks.md)
