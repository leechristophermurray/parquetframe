# Backend Selection

> Choose the right processing backend for your use case.

## Available Backends

ParquetFrame supports multiple processing backends to handle different scale requirements.

## Pandas Backend

Best for:
- Small to medium datasets (< 1GB)
- Interactive analysis
- Fast single-machine processing

## Dask Backend

Best for:
- Large datasets (> 1GB)
- Distributed processing
- Memory-constrained environments

## Automatic Selection

ParquetFrame can automatically choose the optimal backend based on:
- File size
- Available memory
- System resources

## Summary

Choosing the right backend ensures optimal performance for your specific use case and data size.

## Examples

```python
import parquetframe as pf

# Automatic backend selection (recommended)
df = pf.read("data.parquet")

# Force pandas backend
df = pf.read("data.parquet", backend="pandas")

# Force dask backend
df = pf.read("data.parquet", backend="dask")

# Check which backend is being used
print(f"Using backend: {df.backend}")
```

## Further Reading

- [Performance Tips](../analytics-statistics/benchmarks.md)
- [Advanced Features](legacy-migration/phase1-overview.md)
- [Large Dataset Processing](documentation-examples/large-datasets.md)
