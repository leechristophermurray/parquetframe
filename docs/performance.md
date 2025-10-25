# Performance Tips

> Optimize ParquetFrame for maximum performance.

ParquetFrame is engineered for high performance, leveraging intelligent backend selection and a powerful Rust acceleration layer. This guide provides insights and tips to get the most out of your data processing workflows.

## 1. Intelligent Backend Selection

ParquetFrame automatically chooses the most suitable execution engine based on data size, workload characteristics, and available system resources. Understanding these backends can help you optimize further.

*   **Pandas**: Ideal for small to medium-sized datasets that fit comfortably in memory. It offers a rich API and is highly optimized for single-machine, in-memory operations.
*   **Dask**: Best suited for large datasets that exceed available memory or require distributed processing. Dask provides parallel computing capabilities, allowing you to process data across multiple cores or machines.
*   **Polars**: A high-performance DataFrame library written in Rust, offering significant speedups for many operations, especially on single-node, multi-core systems. Polars excels in memory efficiency and execution speed, often outperforming Pandas and even Dask for certain workloads.

**ParquetFrame's Auto-selection Logic**:

By default, ParquetFrame employs a memory-aware auto-selection mechanism. For instance, it might use Pandas for files under a certain size threshold (e.g., 50MB) and switch to Dask or Polars for larger files. You can influence this behavior:

```python
import parquetframe as pf

# Read a file, letting ParquetFrame choose the backend
df = pf.read("my_data.parquet")

# Force Dask backend for lazy evaluation
df_dask = pf.read("large_data.csv", islazy=True)

# Force Pandas backend
df_pandas = pf.read("small_data.json", islazy=False)

# Set a custom threshold for backend selection (e.g., use Dask/Polars for files > 100MB)
df_threshold = pf.read("data.orc", threshold_mb=100)

# Check the current backend
print(f"Is Dask backend? {df.islazy}")
print(f"Is Polars backend? {df.ispolars}")
```

## 2. Rust Acceleration

ParquetFrame's Rust backend provides **10-50x speedups** for performance-critical operations by offloading them to highly optimized Rust code. This acceleration is transparent and automatically utilized when available.

### Key Accelerated Areas:

*   **Workflow Engine**: Parallel execution of DAGs (Directed Acyclic Graphs) in workflows, with resource-aware scheduling. (10-15x speedup)
*   **Graph Algorithms**: High-performance implementations of algorithms like BFS, PageRank, and shortest paths. (15-25x speedup)
*   **I/O Operations**: Lightning-fast Parquet metadata reading, row counting, and column statistics extraction. (5-10x speedup)

### Performance Benchmarks (Illustrative)

| Operation | Python (ms) | Rust (ms) | Speedup |
|:--------------------------|:------------|:----------|:--------|
| Workflow (10 steps, parallel) | 850         | 65        | **13.1x** |
| PageRank (100K nodes)     | 2300        | 95        | **24.2x** |
| BFS (1M nodes)            | 1800        | 105       | **17.1x** |
| Parquet metadata (1GB file) | 180         | 22        | **8.2x** |
| Connected components (500K edges) | 3100        | 115       | **27.0x** |

For detailed benchmarks and how to run them on your system, refer to the [Rust Acceleration Guide](../rust-acceleration/index.md) and [Benchmark Results](../rust-acceleration/benchmark_results.md).

## 3. Memory Optimization

Efficient memory management is crucial for processing large datasets.

*   **Lazy Loading**: When using Dask or Polars, operations are often lazily evaluated, meaning data is not loaded into memory until explicitly requested (e.g., `df.compute()`, `df.collect()`). This prevents out-of-memory errors.
*   **Column Pruning**: Read only the columns you need. This significantly reduces memory footprint and I/O.
*   **Predicate Pushdown**: Apply filters as early as possible, ideally during the data loading phase. This reduces the amount of data that needs to be read and processed.

## 4. File Format Optimization

Leveraging the features of columnar file formats like Parquet can dramatically improve performance.

*   **Parquet**: Preferred format for performance. It supports:
    *   **Columnar Storage**: Only reads necessary columns.
    *   **Compression**: Reduces file size and I/O.
    *   **Statistics**: Allows for predicate pushdown without reading full data.
*   **Optimal Compression Settings**: Experiment with different compression codecs (e.g., Snappy, Gzip, Zstd) to find the best balance between file size and read/write performance for your data.

## Summary

Achieving optimal performance with ParquetFrame involves a combination of:

*   **Intelligent Backend Selection**: Letting ParquetFrame choose, or explicitly guiding it towards Pandas, Dask, or Polars.
*   **Leveraging Rust Acceleration**: For critical I/O, graph, and workflow tasks.
*   **Memory-Efficient Practices**: Using lazy loading, column pruning, and predicate pushdown.
*   **File Format Optimization**: Utilizing columnar formats like Parquet with appropriate compression.

## Examples

```python
import parquetframe as pf

# Lazy loading for large files (will use Dask or Polars based on configuration)
df_lazy = pf.read("huge_file.parquet", islazy=True)

# Read only specific columns (applies to all backends)
df_cols = pf.read("data.parquet", columns=["col1", "col2"])

# Filter during read (predicate pushdown, highly efficient for Parquet)
df_filtered = pf.read("data.parquet", filters=[("date", ">=", "2023-01-01")]).compute() # .compute() if Dask/Polars

# Using Polars explicitly for a specific task
polars_df = pf.read("another_data.csv", ispolars=True)
result = polars_df.group_by("category").agg(pf.col("value").sum()).collect()
```

## Further Reading

*   [Rust Acceleration Guide](../rust-acceleration/index.md)
*   [Multi-Engine Support](../core-features/multi-engine.md)
*   [Benchmark Results](../rust-acceleration/benchmark_results.md)
*   [I/O Fast-Paths](../rust-acceleration/io-fastpaths.md)
