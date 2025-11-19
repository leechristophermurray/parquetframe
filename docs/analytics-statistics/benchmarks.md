# Benchmarks

> Performance benchmarks and comparisons.

## Performance Benchmarks

ParquetFrame provides built-in benchmarking tools to measure and optimize performance.

## Built-in Benchmarking

Use the integrated benchmark suite to:
- Test read/write performance
- Compare backends
- Measure memory usage
- Profile operations

## Benchmark Results

Performance comparisons across different:
- File sizes
- Data types
- Operations
- Backends

## Running Benchmarks

Execute benchmarks in your environment to understand performance characteristics.

## Summary

Benchmarking helps you understand ParquetFrame's performance characteristics and optimize for your specific use cases.

## Examples

```python
import parquetframe as pf

# Run built-in benchmark
benchmark = pf.benchmark.run()

# Benchmark specific operations
benchmark.test_read_performance("data.parquet")
benchmark.compare_backends("large_data.parquet")

# Custom benchmark
result = pf.benchmark.custom(
    operations=["read", "filter", "groupby"],
    file_size="1GB"
)
```

## Further Reading

- [Performance Tips](../analytics-statistics/benchmarks.md)
- [Backend Selection](../legacy-migration/phase1-backends.md)
- [Advanced Features](../legacy-migration/phase1-overview.md)
