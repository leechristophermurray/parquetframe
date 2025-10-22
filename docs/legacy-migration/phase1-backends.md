# Backend Selection (Phase 1 - Legacy)

!!! warning "Deprecated API"
    This documentation describes the **Phase 1 API** backend selection. Phase 2 offers a more advanced multi-engine architecture with automatic selection between **pandas, Polars, and Dask**. See **[Phase 2 Multi-Engine Core](../phase2/README.md)** for details.

    **Migration Guide**: See [Phase 1 → Phase 2 Migration](../legacy-migration/migration-guide.md)

> Choose the right processing backend for your use case.

## Available Backends

ParquetFrame Phase 1 supports multiple processing backends to handle different scale requirements.

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
