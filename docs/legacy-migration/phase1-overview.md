# Legacy Documentation (Phase 1)

!!! warning "Deprecated API"
    This documentation describes ParquetFrame **Phase 1**, which is now in legacy maintenance mode. New projects should use **Phase 2** for access to the latest features and improvements.

## About Phase 1

Phase 1 was the original ParquetFrame API that provided intelligent pandas/Dask backend switching with automatic file size detection. While still functional and maintained, it lacks the advanced features available in Phase 2.

## Why Migrate to Phase 2?

Phase 2 offers significant improvements over Phase 1:

| Feature | Phase 1 | Phase 2 |
|---------|---------|---------|
| **Engines** | pandas, Dask | pandas, Dask, **Polars** |
| **Entity Framework** | ❌ No | ✅ `@entity` and `@rel` decorators |
| **Permissions** | ❌ No | ✅ Zanzibar-style ReBAC |
| **Avro Support** | ❌ No | ✅ Native fastavro integration |
| **Configuration** | Basic | ✅ Global config with env vars |
| **Performance** | Good | ✅ 2-5x faster with Polars |

## Quick Comparison

### Phase 1 API
```python
import parquetframe as pqf

# Automatic backend selection
df = pqf.read("data.parquet")

# Manual backend control
df.islazy = True  # Switch to Dask
df.to_pandas()    # Convert to pandas

# Save
df.save("output.parquet")
```

### Phase 2 API
```python
import parquetframe.core as pf2
from parquetframe.entity import entity, rel
from dataclasses import dataclass

# Multi-engine with automatic selection
df = pf2.read("data.parquet")  # Auto-selects pandas/Polars/Dask

# Entity Framework
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str
    email: str

# Create and save
user = User(1, "Alice", "alice@example.com")
user.save()

# Retrieve
user = User.find(1)
all_users = User.find_all()
```

## Migration Guide

For a comprehensive guide on migrating from Phase 1 to Phase 2, see the **[Phase 2 Migration Guide](../legacy-migration/migration-guide.md)**.

### Migration Strategies

1. **Keep Phase 1** - Continue using Phase 1 if it meets your needs
2. **Gradual Migration** - Migrate incrementally, using both APIs side-by-side
3. **Full Migration** - Switch entirely to Phase 2 for new features

## Phase 1 Documentation

- **[Basic Usage](legacy-basic-usage.md)** - Core Phase 1 functionality
- **[Backend Selection](legacy-backends.md)** - Pandas/Dask switching logic

## Getting Help

- **Phase 2 Documentation**: [Overview](../phase2/README.md)
- **Migration Guide**: [Phase 1 → Phase 2](../legacy-migration/migration-guide.md)
- **Examples**: [Todo/Kanban Walkthrough](../documentation-examples/tutorials.md)
- **GitHub Issues**: [Report Issues](https://github.com/leechristophermurray/parquetframe/issues)

---

**Note**: Phase 1 will continue to receive bug fixes and security updates, but new features will only be added to Phase 2.
