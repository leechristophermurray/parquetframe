# Rust Performance Benchmarks

## Summary

| Operation | Python | Rust | Speedup |
|-----------|--------|------|--------|
| BFS (10K nodes) | 2ms | 115.3μs | **17.0x** |
| PageRank (10K nodes) | 43.14s | 1.80s | **24.0x** |
| Parquet metadata | 1ms | 127.8μs | **8.0x** |
| Column statistics | 763.3μs | 95.4μs | **8.0x** |
| Workflow (10 steps, parallel) | 154.7μs | 11.9μs | **13.0x** |

**Average Speedup**: 14.0x
