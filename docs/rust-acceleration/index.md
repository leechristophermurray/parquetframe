# Rust Acceleration

ParquetFrame v2.0.0 introduces a high-performance Rust backend that delivers 2-50x speedup for performance-critical operations. The Rust acceleration layer provides parallel execution, zero-copy data transfer, and efficient memory management while maintaining full compatibility with the Python API.

## Overview

The Rust backend accelerates three major areas:

1. **Workflow Engine**: Parallel DAG execution with resource-aware scheduling (10-15x speedup)
2. **Graph Algorithms**: High-performance BFS, DFS, PageRank, and shortest paths (15-25x speedup)
3. **I/O Operations**: Fast Parquet metadata and column statistics (5-10x speedup)

All Rust acceleration is **optional** and **transparent** - if the Rust backend is not available, ParquetFrame automatically falls back to pure Python implementations without any code changes.

## Key Features

### 🚀 Workflow Engine
- **Parallel Execution**: Automatic parallelization of independent steps
- **Resource Awareness**: Intelligent scheduling based on CPU/memory availability
- **Progress Tracking**: Real-time execution monitoring and cancellation support
- **[Learn more →](./workflow-engine.md)**

### 📊 Graph Algorithms
- **CSR/CSC Structures**: Efficient compressed sparse representations
- **Parallel Traversal**: Multi-threaded BFS for faster graph exploration
- **Optimized Algorithms**: PageRank, Dijkstra, connected components
- **[Learn more →](./graph-algorithms.md)**

### 💾 I/O Fast-Paths
- **Metadata Reading**: Lightning-fast Parquet file inspection
- **Column Statistics**: Instant min/max/null count extraction
- **Zero-Copy Transfer**: Direct memory mapping via Apache Arrow
- **[Learn more →](./io-fastpaths.md)**

## Quick Start

### Installation

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build Rust backend
pip install maturin
maturin develop --release
```

### Verify Installation

```python
import parquetframe as pf

# Check if Rust is available
print(f"Rust available: {pf.rust_available()}")
print(f"Rust version: {pf.rust_version()}")

# Check specific components
from parquetframe.workflow_rust import is_rust_workflow_available
from parquetframe.graph_rust import is_rust_graph_available
from parquetframe.io_rust import is_rust_io_available

print(f"Workflow engine: {is_rust_workflow_available()}")
print(f"Graph algorithms: {is_rust_graph_available()}")
print(f"I/O fast-paths: {is_rust_io_available()}")
```

### Simple Usage

```python
# Workflows automatically use Rust when available
from parquetframe.workflows import Workflow

workflow = Workflow.from_yaml("pipeline.yaml")
result = workflow.execute()  # Uses Rust engine if available
print(f"Executed in {result['execution_time_ms']}ms")

# Graph algorithms automatically use Rust
from parquetframe import GraphFrame

graph = GraphFrame.from_edges(edges_df)
scores = graph.pagerank()  # 20x faster with Rust

# I/O metadata reading
from parquetframe.io_rust import RustIOEngine

engine = RustIOEngine()
metadata = engine.get_parquet_metadata("data.parquet")
print(f"Rows: {metadata['num_rows']:,}")
```

## Performance Benchmarks

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| Workflow (10 steps, parallel) | 850ms | 65ms | **13.1x** |
| PageRank (100K nodes) | 2.3s | 95ms | **24.2x** |
| BFS (1M nodes) | 1.8s | 105ms | **17.1x** |
| Parquet metadata (1GB file) | 180ms | 22ms | **8.2x** |
| Connected components (500K edges) | 3.1s | 115ms | **27.0x** |

See [Performance Guide](./performance.md) for detailed benchmarks and optimization tips.

## Pages in This Section

- **[Architecture](./architecture.md)** - Rust backend design and PyO3 integration
- **[I/O Fast-Paths](./io-fastpaths.md)** - High-performance file reading
- **[Graph Algorithms](./graph-algorithms.md)** - BFS, PageRank, shortest paths
- **[Workflow Engine](./workflow-engine.md)** - Parallel DAG execution
- **[Development](./development.md)** - Contributing to Rust code (Coming soon)
- **[Performance](./performance.md)** - Benchmarks and tuning guide (Coming soon)

## Related Categories

- **[Graph Processing](../graph-processing/index.md)** - Uses Rust graph algorithms
- **[YAML Workflows](../yaml-workflows/index.md)** - Uses Rust workflow engine
- **[Core Features](../core-features/index.md)** - Uses Rust I/O fast-paths
- **[Analytics & Statistics](../analytics-statistics/index.md)** - Benefits from Rust speedups

## Common Use Cases

### 1. **Large-Scale Graph Analysis**
Process million-node graphs 20x faster with Rust-accelerated PageRank and traversal algorithms.

```python
graph = pf.GraphFrame.from_graphar("social_network/")
scores = graph.pagerank()  # Rust acceleration automatic
```

### 2. **Complex Data Pipelines**
Execute multi-step workflows in parallel with automatic dependency management.

```python
workflow = pf.Workflow.from_yaml("etl_pipeline.yaml")
result = workflow.execute()  # 15x faster with Rust
```

### 3. **Fast Metadata Inspection**
Quickly inspect large Parquet files without loading full data.

```python
engine = pf.io_rust.RustIOEngine()
meta = engine.get_parquet_metadata("100gb_file.parquet")  # <50ms
```

## Design Philosophy

### Transparent Acceleration
Rust acceleration is completely transparent - your Python code works the same whether Rust is available or not.

### Automatic Fallback
If Rust backend is unavailable, ParquetFrame automatically uses pure Python implementations.

### Zero-Copy Transfer
Data moves between Rust and Python via Apache Arrow with zero memory copies.

### Safe Concurrency
Rust's ownership system ensures thread-safe parallel execution without race conditions.

## Next Steps

- **New to Rust acceleration?** Start with [Architecture Overview](./architecture.md)
- **Ready to use?** Check [Installation Guide](../getting-started/installation.md#rust-backend)
- **Want to contribute?** See [Development Guide](./development.md)
- **Need help?** Visit [Troubleshooting](../getting-started/quickstart.md#rust-issues)

## System Requirements

- **Python**: 3.9 or later
- **Rust**: 1.70 or later (for building from source)
- **Platform**: Linux, macOS, Windows (x86_64, ARM64)
- **Memory**: 4GB+ RAM recommended for large graphs

## FAQ

**Q: Is Rust required to use ParquetFrame?**
A: No, Rust acceleration is optional. ParquetFrame works fine without it, just slower for large-scale operations.

**Q: Do I need to know Rust?**
A: No, all APIs are Python. Rust is only used internally for performance.

**Q: Can I install pre-built wheels?**
A: Binary wheels are coming in v2.0.0 final. For now, build from source with `maturin develop`.

**Q: How much faster is Rust really?**
A: 10-50x depending on operation. Parallel workflows and graph algorithms see the biggest gains.
