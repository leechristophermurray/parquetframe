# ParquetFrame Phase 2 Examples

Comprehensive examples demonstrating Phase 2 features including multi-engine support, Avro format, engine conversion, and entity framework.

## Overview

Phase 2 introduces powerful new capabilities:

- **Multi-Engine Architecture**: Automatic selection between pandas, Polars, and Dask
- **Avro Format Support**: Read/write Apache Avro with schema inference
- **Engine Conversion**: Seamlessly switch between engines
- **Entity Framework**: Declarative persistence with @entity decorator

## Examples

### 1. Engine Selection (`engine_selection.py`)

Demonstrates automatic engine selection based on data size and manual override.

**Features:**
- Automatic engine selection (pandas/Polars/Dask)
- Manual engine specification
- Global configuration
- Performance comparison
- Engine characteristics

**Run:**
```bash
python examples/phase2/engine_selection.py
```

**Key Concepts:**
```python
import parquetframe.core_v2 as pf2

# Automatic selection based on file size
df = pf2.read("data.parquet")  # Auto-selects best engine
print(f"Using {df.engine_name} engine")

# Manual override
df_pandas = pf2.read("data.parquet", engine="pandas")
df_polars = pf2.read("data.parquet", engine="polars")
df_dask = pf2.read("data.parquet", engine="dask")

# Global configuration
from parquetframe import set_config
set_config(default_engine="polars", pandas_threshold_mb=50)
```

### 2. Avro Format Support (`avro_roundtrip.py`)

Demonstrates Apache Avro format read/write capabilities.

**Features:**
- Reading and writing Avro files
- Automatic schema inference
- Manual schema specification
- Compression codecs (deflate, snappy)
- Timestamp and datetime handling

**Requirements:**
```bash
pip install fastavro  # Required
pip install cramjam   # Optional, for snappy compression
```

**Run:**
```bash
python examples/phase2/avro_roundtrip.py
```

**Key Concepts:**
```python
# Write to Avro (schema inferred)
df.to_avro("output.avro", codec="deflate")

# Read from Avro
df = pf2.read("data.avro")

# Custom schema
schema = {
    "type": "record",
    "name": "Employee",
    "fields": [
        {"name": "id", "type": "long"},
        {"name": "name", "type": "string"}
    ]
}
df.to_avro("output.avro", schema=schema)
```

### 3. Multi-Engine Conversion (`multi_engine_conversion.py`)

Demonstrates seamless conversion between different DataFrame engines.

**Features:**
- Converting between pandas/Polars/Dask
- Lazy vs eager evaluation
- Performance optimization tips
- Engine-specific features
- Best practices

**Run:**
```bash
python examples/phase2/multi_engine_conversion.py
```

**Key Concepts:**
```python
# Start with pandas
df = pf2.read("data.parquet", engine="pandas")

# Convert to Polars for complex transformations
df_polars = df.to_polars()

# Use Dask for large-scale processing
df_dask = df.to_dask()

# Convert back to pandas for final analysis
df_final = df_dask.to_pandas()

# Access native engine for specific features
df.native.plot()  # pandas-specific plotting
```

### 4. Entity Framework (`entity_framework_demo.py`)

Demonstrates declarative persistence using the @entity decorator.

**Features:**
- @entity decorator for dataclasses
- CRUD operations (Create, Read, Update, Delete)
- Entity relationships
- Parquet and Avro storage backends
- Data validation

**Run:**
```bash
python examples/phase2/entity_framework_demo.py
```

**Key Concepts:**
```python
from dataclasses import dataclass
from parquetframe.entity import entity, rel

# Define entity
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    username: str
    email: str
    age: int

# CRUD operations
user = User(user_id=1, username="alice", email="alice@example.com", age=25)
user.save()  # Create/Update

found = User.find(1)  # Read by ID
all_users = User.find_all()  # Read all
active = User.find_by(active=True)  # Query

User.delete(1)  # Delete

# Relationships
@entity(storage_path="./data/orders", primary_key="order_id")
@dataclass
class Order:
    order_id: int
    customer_id: int
    product: str

User.orders = rel(Order, foreign_key="customer_id", rel_type="one-to-many")
```

## Quick Start

1. **Install Phase 2 dependencies:**
   ```bash
   pip install pandas  # Required
   pip install polars  # Optional, for Polars engine
   pip install dask[complete]  # Optional, for Dask engine
   pip install fastavro  # Optional, for Avro support
   ```

2. **Run all examples:**
   ```bash
   # Engine selection
   python examples/phase2/engine_selection.py

   # Avro support
   python examples/phase2/avro_roundtrip.py

   # Engine conversion
   python examples/phase2/multi_engine_conversion.py

   # Entity framework
   python examples/phase2/entity_framework_demo.py
   ```

## Engine Selection Guide

| Data Size | Recommended Engine | Rationale |
|-----------|-------------------|-----------|
| < 100 MB | pandas | Fast startup, immediate results |
| 100 MB - 10 GB | Polars | Lazy evaluation, query optimization |
| > 10 GB | Dask | Out-of-core, distributed processing |

## Format Comparison

| Format | Best For | Pros | Cons |
|--------|----------|------|------|
| Parquet | Analytics | Columnar, excellent compression | Not for streaming |
| Avro | Data Exchange | Schema evolution, compact | Row-oriented |
| CSV | Compatibility | Universal support | Large size, no schema |

## Best Practices

### Engine Selection
- Let Phase 2 auto-select for most cases
- Use pandas for interactive analysis
- Use Polars for complex ETL pipelines
- Use Dask when data exceeds memory

### Performance
- Filter data early to reduce size
- Minimize engine conversions
- Use lazy evaluation when possible
- Partition large datasets appropriately

### Storage
- Use Parquet for analytics workloads
- Use Avro for data exchange and evolution
- Configure compression based on use case
- Organize data with meaningful paths

## Troubleshooting

### Polars Not Available
If you see "Polars not installed":
```bash
pip install polars
```

### Dask Not Available
If you see "Dask not installed":
```bash
pip install dask[complete]
```

### Avro Support Missing
If you see "fastavro required":
```bash
pip install fastavro
pip install cramjam  # Optional, for snappy
```

### Memory Issues
- Switch to Dask engine for large datasets
- Use partitioning to process data in chunks
- Increase swap space or use cloud resources

## Next Steps

- Read the [Phase 2 User Guide](../../docs/phase2/USER_GUIDE.md)
- Check the [Migration Guide](../../docs/phase2/MIGRATION_GUIDE.md)
- Explore the [API Reference](../../docs/phase2/)
- Review [Phase 2 Progress](../../PHASE_2_PROGRESS.md)

## Feedback

Have questions or suggestions? Open an issue on GitHub!
