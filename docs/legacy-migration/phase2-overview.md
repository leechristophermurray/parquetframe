# ParquetFrame Phase 2 Documentation

Welcome to ParquetFrame Phase 2 documentation!

## Quick Links

- **[User Guide](legacy-migration/phase2-user-guide.md)** - Complete guide to Phase 2 features
- **[Migration Guide](legacy-migration/migration-guide.md)** - Migrate from Phase 1 to Phase 2
- **[Progress Report](../../PHASE_2_PROGRESS.md)** - Development progress and stats

## What is Phase 2?

Phase 2 is the next generation of ParquetFrame, featuring:

- **Multi-Engine Architecture**: Automatic selection between pandas, Polars, and Dask
- **Entity Framework**: Declarative persistence with Parquet/Avro backends
- **Avro Support**: Read and write Apache Avro format
- **Configuration System**: Global configuration with environment variable support
- **100% Backward Compatible**: Phase 1 code continues to work

## Quick Start

### Installation

```bash
pip install parquetframe

# Optional dependencies for Phase 2
pip install polars  # Polars engine
pip install dask[complete]  # Dask engine
pip install fastavro  # Avro support
```

### Basic Usage

```python
import parquetframe.core as pf2

# Read with automatic engine selection
df = pf2.read("data.parquet")
print(f"Using {df.engine_name} engine")

# Work with data
filtered = df[df["age"] > 30]
grouped = df.groupby("category")["value"].sum()
```

### Entity Framework

```python
from dataclasses import dataclass
from parquetframe.entity import entity

@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str
    email: str

# CRUD operations
User(1, "Alice", "alice@example.com").save()
user = User.find(1)
all_users = User.find_all()
```

### Configuration

```python
from parquetframe import set_config

# Set global configuration
set_config(
    default_engine="polars",
    pandas_threshold_mb=50.0,
    verbose=True
)
```

## Architecture

### Multi-Engine Core

Phase 2 provides a unified interface across three DataFrame engines:

```
┌─────────────────────────────────────┐
│      DataFrameProxy (Unified)       │
├─────────────────────────────────────┤
│  ┌───────┐  ┌────────┐  ┌───────┐  │
│  │Pandas │  │ Polars │  │ Dask  │  │
│  └───────┘  └────────┘  └───────┘  │
│    Eager      Lazy      Distributed │
│   <100MB    100MB-10GB    >10GB     │
└─────────────────────────────────────┘
```

### Entity Framework

Declarative persistence with automatic CRUD operations:

```
┌─────────────────────────────────────┐
│      @entity Decorator               │
├─────────────────────────────────────┤
│  ┌────────────────────────────────┐ │
│  │    EntityStore                 │ │
│  │  (CRUD Operations)             │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  Parquet/Avro Storage          │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Components

### Phase 2.1: Multi-Engine Core ✅
- DataFrameProxy for unified interface
- Intelligent engine selection
- Seamless engine conversion
- **42 tests, 100% passing**

### Phase 2.2: Avro Integration ✅
- Multi-engine Avro reader/writer
- Schema inference
- Compression support
- **16 tests, 100% passing**

### Phase 2.3: Entity-Graph Framework ✅
- `@entity` decorator for persistence
- `@rel` decorator for relationships
- CRUD operations
- Relationship resolution
- **21 tests, 100% passing**

### Phase 2.4: Configuration & UX ✅
- Global configuration system
- Environment variable support
- Context manager for temporary changes
- **31 tests, 100% passing**

### Phase 2.5: Testing & QA ✅
- End-to-end integration tests
- Benchmark suite
- >85% coverage for Phase 2 components
- **36 tests, 100% passing**

### Phase 2.6: Documentation ✅
- User guide
- Migration guide
- API reference
- Examples

## Statistics

- **Total Tests**: 146 (145 passing, 1 skipped)
- **Test Pass Rate**: 99.3%
- **Code Coverage**: >85% for Phase 2 components
- **Total Commits**: 6
- **Lines Added**: ~5,500

## Features by Component

### Multi-Engine Core
- ✅ Pandas engine support
- ✅ Polars engine support
- ✅ Dask engine support
- ✅ Automatic engine selection
- ✅ Manual engine override
- ✅ Engine conversion (to_pandas, to_polars, to_dask)
- ✅ DataFrameProxy unified interface
- ✅ Method delegation and wrapping

### I/O Support
- ✅ CSV reading
- ✅ Parquet reading/writing
- ✅ Avro reading/writing
- ✅ Format auto-detection
- ✅ Compression support
- ✅ Schema inference

### Entity Framework
- ✅ `@entity` decorator
- ✅ `@rel` decorator
- ✅ CRUD operations (save, find, find_all, find_by, delete)
- ✅ Forward relationships (one-to-many)
- ✅ Reverse relationships (many-to-one)
- ✅ Bidirectional relationships
- ✅ Parquet storage backend
- ✅ Avro storage backend

### Configuration
- ✅ Global configuration
- ✅ Environment variables
- ✅ Context manager
- ✅ Serialization/deserialization
- ✅ Engine threshold configuration
- ✅ Entity format configuration

## Performance

### Engine Selection Thresholds

- **Pandas**: < 100MB (configurable)
  - Eager execution
  - Rich ecosystem
  - Best for small datasets

- **Polars**: 100MB - 10GB (configurable)
  - Lazy evaluation
  - High performance
  - Best for medium datasets

- **Dask**: > 10GB (configurable)
  - Distributed processing
  - Scalable
  - Best for large datasets

### Benchmarks

Run benchmarks with:
```bash
pytest tests/benchmarks/bench_phase2.py --benchmark-only
```

## Examples

### Example 1: Multi-Format Pipeline

```python
import parquetframe.core as pf2

# Read from different formats
sales = pf2.read_csv("sales.csv")
customers = pf2.read_parquet("customers.parquet")
events = pf2.read_avro("events.avro")

# Convert to common engine
sales_pd = sales.to_pandas()
customers_pd = customers.to_pandas()

# Process
merged = sales_pd.native.merge(customers_pd.native, on="customer_id")
```

### Example 2: Entity Relationships

```python
from dataclasses import dataclass
from parquetframe.entity import entity, rel

@entity(storage_path="./users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str

    @rel("Post", foreign_key="user_id", reverse=True)
    def posts(self):
        pass

@entity(storage_path="./posts", primary_key="post_id")
@dataclass
class Post:
    post_id: int
    user_id: int
    title: str

    @rel("User", foreign_key="user_id")
    def author(self):
        pass

# Usage
user = User(1, "Alice")
user.save()

Post(1, 1, "Hello World").save()
Post(2, 1, "Second Post").save()

# Navigate relationships
posts = user.posts()  # [Post, Post]
author = Post.find(1).author()  # User
```

### Example 3: Configuration

```python
from parquetframe import set_config, config_context
import parquetframe.core as pf2

# Global configuration
set_config(
    default_engine="polars",
    pandas_threshold_mb=50.0
)

# All reads use this configuration
df1 = pf2.read("file1.csv")  # Uses polars
df2 = pf2.read("file2.csv")  # Uses polars

# Temporary override
with config_context(default_engine="dask"):
    df3 = pf2.read("large.csv")  # Uses dask
# Reverts to polars
```

## Compatibility

- **Python**: 3.9+
- **Phase 1**: 100% backward compatible
- **pandas**: 1.5+
- **polars**: 0.19+ (optional)
- **dask**: 2023.1+ (optional)
- **fastavro**: Latest (optional)

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

## Testing

```bash
# Run all Phase 2 tests
pytest tests/core/ tests/entity/ tests/integration/ tests/test_config.py

# Run with coverage
pytest --cov=src/parquetframe/core --cov=src/parquetframe/entity --cov=src/parquetframe/config

# Run benchmarks
pytest tests/benchmarks/ --benchmark-only
```

## License

See [LICENSE](../../LICENSE) for license information.

## Support

- **Documentation**: This directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## Roadmap

Phase 2 is feature-complete! Future enhancements:

- Performance optimizations
- Additional storage backends
- More relationship types (many-to-many)
- Schema migration tools
- Query DSL improvements
