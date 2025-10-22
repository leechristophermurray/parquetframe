# ParquetFrame

<div align="center">
  <img src="assets/logo.svg" alt="ParquetFrame Logo" width="400" style="max-width: 100%;">
</div>

<div align="center">
  <a href="https://pypi.org/project/parquetframe/"><img src="https://badge.fury.io/py/parquetframe.svg" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/parquetframe/"><img src="https://img.shields.io/pypi/pyversions/parquetframe.svg" alt="Python Support"></a>
  <a href="https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE"><img src="https://img.shields.io/github/license/leechristophermurray/parquetframe.svg" alt="License"></a>
  <a href="https://www.rust-lang.org/"><img src="https://img.shields.io/badge/rust-accelerated-orange.svg" alt="Rust Accelerated"></a>
  <br>
  <a href="https://github.com/leechristophermurray/parquetframe/actions"><img src="https://github.com/leechristophermurray/parquetframe/workflows/Tests/badge.svg" alt="Tests"></a>
  <a href="https://codecov.io/gh/leechristophermurray/parquetframe"><img src="https://codecov.io/gh/leechristophermurray/parquetframe/branch/main/graph/badge.svg" alt="Coverage"></a>
</div>

**High-performance DataFrame library with Rust acceleration, intelligent multi-engine support, and AI-powered data exploration.**

> 🚀 **v2.0.0 Now Available**: Rust backend delivers 10-50x speedup for workflows, graphs, and I/O operations

> 🏆 **Production-Ready**: 400+ passing tests, comprehensive CI/CD, and battle-tested in production

> 🦀 **Rust-Accelerated**: Optional high-performance backend with automatic fallback to Python

!!! tip "New to ParquetFrame?"
    Start with the **[Quick Start Guide](getting-started/quickstart.md)** or explore **[Rust Acceleration](rust-acceleration/index.md)** for maximum performance.

## ✨ What's New in v2.0.0

### 🦀 Rust Acceleration

**Workflow Engine** (10-15x faster)

- Parallel DAG execution with resource-aware scheduling
- Automatic dependency resolution
- Progress tracking and cancellation support
- [Learn more →](rust-acceleration/workflow-engine.md)

**Graph Algorithms** (15-25x faster)

- CSR/CSC construction for efficient graph storage
- Parallel BFS, DFS traversal
- PageRank, Dijkstra shortest paths, connected components
- [Learn more →](rust-acceleration/graph-algorithms.md)

**I/O Operations** (5-10x faster)

- Lightning-fast Parquet metadata reading
- Instant column statistics extraction
- Zero-copy data transfer via Apache Arrow
- [Learn more →](rust-acceleration/io-fastpaths.md)

### Performance Benchmarks

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| Workflow (10 steps, parallel) | 850ms | 65ms | **13.1x** |
| PageRank (100K nodes) | 2.3s | 95ms | **24.2x** |
| BFS (1M nodes) | 1.8s | 105ms | **17.1x** |
| Parquet metadata (1GB file) | 180ms | 22ms | **8.2x** |

### Core Features

🎯 **Multi-Engine Core**: Automatic selection between pandas, Polars, and Dask

📦 **Entity Framework**: Declarative ORM-like data modeling with `@entity` decorators

🔐 **Zanzibar Permissions**: Production-grade ReBAC authorization

📊 **Graph Processing**: Apache GraphAr with Rust-accelerated algorithms

📋 **YAML Workflows**: Declarative pipeline orchestration

🤖 **AI Integration**: Local LLM support for natural language queries

⚡ **Automatic Fallback**: Works without Rust, just slower

## 🚀 Quick Start

=== "Installation"

    ```bash
    # Basic installation
    pip install parquetframe

    # With Phase 2 support (pandas, Polars, Dask, Avro)
    pip install parquetframe[phase2]

    # Full installation with all features
    pip install parquetframe[all]
    ```

=== "Phase 2: Multi-Engine"

    ```python
    import parquetframe.core as pf2

    # Automatic engine selection (pandas/Polars/Dask)
    df = pf2.read("data.parquet")  # Auto-selects best engine
    print(f"Using {df.engine_name} engine")

    # All operations work transparently
    result = df.groupby("category")["value"].sum()

    # Force specific engine
    df = pf2.read("data.csv", engine="polars")  # Use Polars
    ```

=== "Phase 2: Entity Framework"

    ```python
    from dataclasses import dataclass
    from parquetframe.entity import entity, rel

    @entity(storage_path="./data/users", primary_key="user_id")
    @dataclass
    class User:
        user_id: str
        username: str
        email: str

    # Automatic CRUD operations
    user = User("user_001", "alice", "alice@example.com")
    user.save()  # Persist to Parquet

    # Query
    user = User.find("user_001")
    all_users = User.find_all()
    ```

=== "Phase 1 (Legacy)"

    ```python
    import parquetframe as pqf

    # Phase 1 API (still supported)
    df = pqf.read("data.parquet")  # pandas/Dask switching
    result = df.groupby("column").sum()
    df.save("output")

    # Migrate to Phase 2 for new features!
    # See: phase2/MIGRATION_GUIDE.md
    ```

=== "CLI Usage"

    ```bash
    # Quick file info
    pframe info data.parquet

    # Data processing
    pframe run data.parquet --query "age > 30" --head 10

    # Interactive mode
    pframe interactive data.parquet

    # Performance benchmarking
    pframe benchmark --operations "groupby,filter"
    ```

## 🎉 What's New in Phase 2?

Phase 2 represents a major architectural evolution, transforming ParquetFrame from a pandas/Dask wrapper into a comprehensive data framework.

### New Capabilities

| Feature | Phase 1 | Phase 2 |
|---------|---------|----------|
| **Engines** | pandas, Dask | pandas, **Polars**, Dask |
| **Entity Framework** | ❌ No | ✅ `@entity` and `@rel` decorators |
| **Permissions** | ❌ No | ✅ Zanzibar ReBAC (4 APIs) |
| **Avro Support** | ❌ No | ✅ Native fastavro integration |
| **Configuration** | Basic | ✅ Global config + env vars |
| **Performance** | Good | ✅ **2-5x faster** with Polars |
| **Backward Compatible** | — | ✅ **100% compatible** |

### Featured Example: Todo/Kanban Application

See the **[Complete Walkthrough](documentation-examples/todo-kanban-example.md)** of a production-ready Kanban board system demonstrating:

- ✅ Multi-user collaboration with role-based access
- ✅ Entity Framework with `@entity` and `@rel` decorators
- ✅ Zanzibar permissions with inheritance (Board → List → Task)
- ✅ YAML workflows for ETL pipelines
- ✅ Complete source code with 38+ tests

```python
# Entity Framework example from Todo/Kanban
from dataclasses import dataclass
from parquetframe.entity import entity, rel

@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str
    email: str

    @rel("Board", foreign_key="owner_id", reverse=True)
    def boards(self):
        """Get all boards owned by this user."""
        pass

# Automatic CRUD operations
user = User("user_001", "alice", "alice@example.com")
user.save()  # Persist to Parquet
boards = user.boards()  # Navigate relationships
```

### Migration Path

- **Phase 1 users**: See the **[Migration Guide](legacy-migration/migration-guide.md)** for step-by-step instructions
- **New users**: Start directly with **[Phase 2](legacy-migration/phase2-user-guide.md)**
- **100% backward compatible**: Phase 1 code continues to work

## 🎯 Why ParquetFrame?

### The Problem

Working with dataframes in Python often means:

- **Choosing a single engine**: pandas (fast but memory-limited), Dask (scalable but slower), or Polars (fast but new)
- **Manual backend management**: Writing conditional code for different data sizes
- **No data modeling**: Treating everything as raw DataFrames without structure
- **Complex permissions**: Building authorization systems from scratch

### The Solution

ParquetFrame provides a unified framework that:

- **Automatically selects** the best engine (pandas/Polars/Dask) based on data characteristics
- **Provides entity framework** for declarative data modeling with `@entity` and `@rel` decorators
- **Includes Zanzibar permissions** for production-grade authorization
- **Maintains 100% compatibility** with Phase 1 while adding powerful new features

## 📊 Performance Benefits

- **Intelligent optimization**: Memory-aware backend selection considering file size, system resources, and file characteristics
- **Built-in benchmarking**: Comprehensive performance analysis tools to optimize your workflows
- **Memory efficiency**: Never load more data than your system can handle
- **Speed optimization**: Fast pandas operations for small datasets, scalable Dask for large ones
- **CLI performance tools**: Built-in benchmarking and analysis from the command line
- **Zero overhead**: Direct delegation to underlying libraries without performance penalty

## 🛠️ Key Concepts (Phase 1 - Legacy)

!!! info "Phase 1 API Examples"
    The examples below use the Phase 1 API which is still supported. For Phase 2 features (multi-engine with Polars, Entity Framework, Zanzibar permissions), see the **[Phase 2 Guide](legacy-migration/phase2-user-guide.md)**.

### Automatic Backend Selection

```python
import parquetframe as pqf

# Small file (< 10MB) → pandas (fast operations)
small_df = pqf.read("small_dataset.parquet")
print(type(small_df._df))  # <class 'pandas.core.frame.DataFrame'>

# Large file (> 10MB) → Dask (memory efficient)
large_df = pqf.read("large_dataset.parquet")
print(type(large_df._df))  # <class 'dask.dataframe.core.DataFrame'>
```

### Manual Control

```python
# Override automatic detection
pandas_df = pqf.read("any_file.parquet", islazy=False)  # Force pandas
dask_df = pqf.read("any_file.parquet", islazy=True)     # Force Dask

# Convert between backends
pandas_df.to_dask()    # Convert to Dask
dask_df.to_pandas()    # Convert to pandas

# Property-based control
df.islazy = True   # Convert to Dask
df.islazy = False  # Convert to pandas
```

### File Extension Handling

```python
# All of these work the same way:
df1 = pqf.read("data.parquet")  # Explicit extension
df2 = pqf.read("data.pqt")      # Alternative extension
df3 = pqf.read("data")          # Auto-detect extension

# Save with automatic extension
df.save("output")         # Saves as "output.parquet"
df.save("output.pqt")     # Saves as "output.pqt"
```

## 📋 Requirements

### Phase 2 (Recommended)
- Python 3.10+
- pandas >= 2.0.0
- dask[dataframe] >= 2023.1.0 (optional)
- polars >= 0.19.0 (optional)
- fastavro >= 1.8.0 (optional, for Avro support)
- pyarrow >= 10.0.0

### Phase 1 (Legacy)
- Python 3.9+
- pandas >= 2.0.0
- dask[dataframe] >= 2023.1.0
- pyarrow >= 10.0.0

## 📚 Documentation

### Phase 2 (Start Here!)
- **[Phase 2 Overview](legacy-migration/phase2-user-guide.md)** - Complete Phase 2 feature guide
- **[Todo/Kanban Walkthrough](documentation-examples/todo-kanban-example.md)** - Full application example
- **[Migration Guide](legacy-migration/migration-guide.md)** - Migrate from Phase 1
- **[Quick Start](getting-started/quickstart.md)** - Get up and running in minutes
- [Installation Guide](getting-started/installation.md) - Detailed installation instructions

### Features & Guides
- [CLI Guide](cli-interface/index.md) - Complete command-line interface documentation
- [Performance Tips](../analytics-statistics/benchmarks.md) - Optimize your workflows
- [Workflow System](yaml-workflows/index.md) - YAML workflow orchestration
- [Graph Processing](graph-processing/index.md) - Apache GraphAr support
- [Permissions System](permissions-system/index.md) - Zanzibar ReBAC
- [API Reference](documentation-examples/api-core.md) - Complete API documentation

### Legacy Documentation
- [Phase 1 Usage Guide](legacy-migration/phase1-usage.md) - Phase 1 API reference
- [Phase 1 Backend Selection](legacy-migration/phase1-backends.md) - pandas/Dask switching

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE) file for details.

---

**Ready to simplify your dataframe workflows?** Check out the [Quick Start Guide](getting-started/quickstart.md) to get started!
