# Breaking Changes: ParquetFrame v1.0.0

**Version**: 1.0.0
**Release Date**: TBD
**Migration Guide**: See [docs/phase2/MIGRATION_GUIDE.md](docs/phase2/MIGRATION_GUIDE.md)

---

## Overview

ParquetFrame version 1.0.0 makes **Phase 2 multi-engine API the default**. This is a breaking change that affects the primary import path and API surface.

### What Changed

Phase 2, which was previously accessed via `import parquetframe.core_v2 as pf2`, is now the default when you `import parquetframe as pf`. Phase 2 provides:

- **Multi-Engine Support**: Automatic selection between pandas, Polars, and Dask
- **Better Performance**: 2-5x improvements on medium-scale datasets
- **Intelligent Backend Selection**: Automatic engine choice based on data characteristics
- **Apache Avro Support**: Read and write Avro format natively
- **Entity-Graph Framework**: Declarative persistence with `@entity` decorator

### Why This Change?

1. **User Experience**: Eliminates confusion between Phase 1 and Phase 2
2. **Performance**: Users get best-in-class performance by default
3. **Future-Proof**: Enables continued evolution without namespace baggage
4. **Industry Standard**: Follows standard deprecation practices

---

## Breaking Changes Summary

| Aspect | Phase 1 (Old) | Phase 2 (New) | Breaking? |
|--------|---------------|---------------|-----------|
| **Main Class** | `ParquetFrame` | `DataFrameProxy` | ✅ Yes |
| **Backend Property** | `df.islazy` (bool) | `df.engine_name` (str) | ✅ Yes |
| **DataFrame Access** | `df.df` | `df.native` | ✅ Yes |
| **Backend Parameter** | `islazy=True/False` | `engine="pandas"/"polars"/"dask"` | ✅ Yes |
| **Available Engines** | pandas, Dask | pandas, Polars, Dask | ⚠️ New |
| **Import Path** | `import parquetframe as pf` | `import parquetframe as pf` | ⚠️ Same path, different API |
| **read() Function** | Returns `ParquetFrame` | Returns `DataFrameProxy` | ✅ Yes |
| **Avro Support** | Not available | Fully supported | ⚠️ New |

---

## Detailed Breaking Changes

### 1. Main Class Changed

**Impact**: HIGH - Affects all code using default imports

**Before (Phase 1):**
```python
import parquetframe as pf

df = pf.read("data.csv")
type(df)  # <class 'parquetframe.core.ParquetFrame'>
```

**After (Phase 2):**
```python
import parquetframe as pf

df = pf.read("data.csv")
type(df)  # <class 'parquetframe.core_v2.frame.DataFrameProxy'>
```

**Migration**:
- If you check `isinstance(df, ParquetFrame)`, update to `DataFrameProxy`
- If you rely on specific ParquetFrame methods, verify they exist in DataFrameProxy
- Most operations work identically due to method delegation

---

### 2. Backend Detection Property

**Impact**: HIGH - Affects conditional logic based on backend

**Before (Phase 1):**
```python
import parquetframe as pf

df = pf.read("data.csv")

if df.islazy:
    print("Using Dask")
    result = df.df.compute()
else:
    print("Using pandas")
    result = df.df
```

**After (Phase 2):**
```python
import parquetframe as pf

df = pf.read("data.csv")

if df.engine_name == "dask":
    print("Using Dask")
    result = df.native.compute()
elif df.engine_name == "polars":
    print("Using Polars")
    result = df.native.collect()  # Polars lazy evaluation
else:
    print("Using pandas")
    result = df.native
```

**Migration**:
- Replace `if df.islazy:` with `if df.engine_name == "dask":`
- Replace `if not df.islazy:` with `if df.engine_name == "pandas":`
- Add handling for `df.engine_name == "polars"` if using automatic selection

---

### 3. DataFrame Access Property

**Impact**: MEDIUM - Affects code accessing underlying DataFrame

**Before (Phase 1):**
```python
import parquetframe as pf

df = pf.read("data.csv")
native_df = df.df  # Access pandas or Dask DataFrame
```

**After (Phase 2):**
```python
import parquetframe as pf

df = pf.read("data.csv")
native_df = df.native  # Access pandas, Polars, or Dask DataFrame
```

**Migration**:
- Find all uses of `.df` and replace with `.native`
- Search: `\.df\b` (regex to find `.df` not followed by alphanumeric)
- Replace: `.native`

---

### 4. Backend Selection Parameters

**Impact**: MEDIUM - Affects explicit backend control

**Before (Phase 1):**
```python
import parquetframe as pf

# Force pandas
df_pandas = pf.read("data.csv", islazy=False)

# Force Dask
df_dask = pf.read("data.csv", islazy=True)
```

**After (Phase 2):**
```python
import parquetframe as pf

# Force pandas
df_pandas = pf.read("data.csv", engine="pandas")

# Force Dask
df_dask = pf.read("data.csv", engine="dask")

# Force Polars (new!)
df_polars = pf.read("data.csv", engine="polars")
```

**Migration**:
- Replace `islazy=False` with `engine="pandas"`
- Replace `islazy=True` with `engine="dask"`
- Consider using `engine="polars"` for medium-sized datasets (100MB-10GB)

---

### 5. Threshold Parameters

**Impact**: LOW - Configuration interface changed

**Before (Phase 1):**
```python
import parquetframe as pf

# Set threshold at call site
df = pf.read("data.csv", threshold_mb=50)
```

**After (Phase 2):**
```python
import parquetframe as pf
from parquetframe import set_config

# Set globally (recommended)
set_config(pandas_threshold_mb=50.0, polars_threshold_mb=100.0)

# Or override at call site
df = pf.read("data.csv", engine="pandas")  # Explicit engine
```

**Migration**:
- Move threshold configuration to `set_config()` for global settings
- Use explicit `engine=` parameter for per-call overrides
- Remove `threshold_mb=` parameter (no longer supported)

---

### 6. Method Availability

**Impact**: LOW - Most methods work identically

Most DataFrame methods work the same way due to method delegation. However, some ParquetFrame-specific methods may differ:

**Phase 1 Specific Methods** (Removed in Phase 2):
- `to_pandas()`: Still available but behavior slightly different
- `to_dask()`: Still available but behavior slightly different
- `save()`: Removed - use `.native.to_parquet()` instead

**Phase 2 New Methods**:
- `to_polars()`: Convert to Polars engine
- `to_avro()`: Write Avro format (via AvroWriter)

---

### 7. Return Types in Method Chaining

**Impact**: LOW - Affects method chaining and type hints

**Before (Phase 1):**
```python
import parquetframe as pf

result: pf.ParquetFrame = pf.read("data.csv").head(10)
```

**After (Phase 2):**
```python
import parquetframe as pf
from parquetframe.core_v2 import DataFrameProxy

result: DataFrameProxy = pf.read("data.csv").head(10)
```

**Migration**:
- Update type hints from `ParquetFrame` to `DataFrameProxy`
- Update type guards: `isinstance(obj, ParquetFrame)` → `isinstance(obj, DataFrameProxy)`

---

## Migration Strategies

### Strategy 1: Use Legacy Module (Quick Fix)

**Best For**: Existing projects needing quick compatibility

Update your imports to use the legacy module:

```python
# Before
import parquetframe as pf

# After
from parquetframe.legacy import ParquetFrame
# or
import parquetframe.legacy as pf
```

**Note**: This triggers deprecation warnings and will be removed in v2.0.0

---

### Strategy 2: Gradual Migration (Recommended)

**Best For**: Most projects with time to migrate

1. **Keep working code on legacy**:
   ```python
   from parquetframe.legacy import ParquetFrame as pf
   ```

2. **Migrate new code to Phase 2**:
   ```python
   import parquetframe as pf  # New Phase 2 API
   ```

3. **Migrate existing code incrementally**:
   - Replace `.islazy` with `.engine_name`
   - Replace `.df` with `.native`
   - Replace `islazy=` with `engine=`
   - Update type hints

4. **Test thoroughly** after each module migration

---

### Strategy 3: Full Migration (Clean Slate)

**Best For**: New projects or thorough refactoring

Systematically update all code to Phase 2:

```bash
# Find all occurrences
grep -r "\.islazy" src/
grep -r "\.df\b" src/
grep -r "islazy=" src/

# Replace with Phase 2 equivalents
# .islazy → .engine_name == "dask"
# .df → .native
# islazy=True → engine="dask"
# islazy=False → engine="pandas"
```

---

## Common Migration Patterns

### Pattern 1: Simple Read/Write

**Before:**
```python
import parquetframe as pf

df = pf.read("input.csv")
df = df[df["age"] > 30]
df.save("output.parquet")
```

**After:**
```python
import parquetframe as pf

df = pf.read("input.csv")
filtered = df[df["age"] > 30]
filtered.native.to_parquet("output.parquet")
```

---

### Pattern 2: Explicit Backend Control

**Before:**
```python
import parquetframe as pf

# Force Dask for large file
df = pf.read("large.csv", islazy=True)
result = df.groupby("category").sum()
result = result.compute()
```

**After:**
```python
import parquetframe as pf

# Auto-select or force Dask
df = pf.read("large.csv", engine="dask")
result = df.groupby("category").sum()
result = result.compute()  # Still needed for Dask
```

---

### Pattern 3: Backend Detection

**Before:**
```python
import parquetframe as pf

df = pf.read("data.csv")
if df.islazy:
    df = df.to_pandas()
# Now definitely pandas
```

**After:**
```python
import parquetframe as pf

df = pf.read("data.csv")
if df.engine_name != "pandas":
    df = df.to_pandas()
# Now definitely pandas
```

---

### Pattern 4: DataFrame Operations

**Before:**
```python
import parquetframe as pf
import pandas as pd

pf_df = pf.read("data.csv")
pd_df = pf_df.df  # Get pandas DataFrame

# Pandas operations
result = pd_df.groupby("category").agg({"value": ["mean", "sum"]})
```

**After:**
```python
import parquetframe as pf
import pandas as pd

pf_df = pf.read("data.csv")
native_df = pf_df.native  # Get underlying DataFrame

# Ensure it's pandas if needed
if pf_df.engine_name != "pandas":
    pf_df = pf_df.to_pandas()
    native_df = pf_df.native

# Pandas operations
result = native_df.groupby("category").agg({"value": ["mean", "sum"]})
```

---

## Deprecation Timeline

| Version | Status | Phase 1 Access | Deprecation Warnings |
|---------|--------|----------------|----------------------|
| **0.5.3** | Old | Default `import parquetframe` | None |
| **1.0.0** | Current | `parquetframe.legacy` module | Yes, on legacy use |
| **1.x** | Transition | `parquetframe.legacy` module | Yes, on legacy use |
| **2.0.0** | Future | Removed entirely | N/A |

**Timeline Estimate**:
- **Version 1.0.0**: Released TBD (Phase 2 default, Phase 1 deprecated)
- **Version 1.x**: 6-12 months (transition period with warnings)
- **Version 2.0.0**: TBD (Phase 1 removed entirely)

---

## Testing Your Migration

### Unit Tests

Update your test fixtures and assertions:

```python
# Before
def test_read_file():
    df = pf.read("test.csv")
    assert isinstance(df, pf.ParquetFrame)
    assert not df.islazy

# After
from parquetframe.core_v2 import DataFrameProxy

def test_read_file():
    df = pf.read("test.csv")
    assert isinstance(df, DataFrameProxy)
    assert df.engine_name == "pandas"
```

### Integration Tests

Test backend selection logic:

```python
def test_engine_selection():
    small_df = pf.read("small_10mb.csv")
    assert small_df.engine_name == "pandas"

    medium_df = pf.read("medium_500mb.csv")
    assert medium_df.engine_name == "polars"

    large_df = pf.read("large_20gb.csv")
    assert large_df.engine_name == "dask"
```

### Performance Tests

Verify Phase 2 performance improvements:

```python
import time

def test_phase2_performance():
    # Should use Polars for medium files (faster than Phase 1 pandas)
    start = time.time()
    df = pf.read("medium_file.csv")
    result = df.groupby("category")["value"].sum()
    elapsed = time.time() - start

    assert df.engine_name == "polars"
    assert elapsed < BASELINE_TIME * 0.5  # Should be 2x faster
```

---

## Frequently Asked Questions

### Q: Can I still use Phase 1?

**A**: Yes, during the transition period (v1.x), Phase 1 is available via `parquetframe.legacy`. It will be removed in v2.0.0.

```python
from parquetframe.legacy import ParquetFrame
```

### Q: What if my code breaks with Phase 2?

**A**: Use the legacy module as a temporary fix, then migrate gradually:

1. Switch to `parquetframe.legacy`
2. Migrate one module at a time to Phase 2
3. Test thoroughly after each migration

### Q: Will Phase 2 slow down my small datasets?

**A**: No, Phase 2 uses pandas for small datasets (<100MB) by default, same as Phase 1.

### Q: Do I need to install Polars?

**A**: No, Polars is optional. If not installed, Phase 2 falls back to pandas or Dask.

```bash
# Optional: Install Polars for better performance
pip install polars
```

### Q: How do I check which engine is being used?

**A**: Use the `engine_name` property:

```python
df = pf.read("data.csv")
print(f"Using {df.engine_name} engine")  # "pandas", "polars", or "dask"
```

### Q: Can I force a specific engine?

**A**: Yes, use the `engine` parameter:

```python
df = pf.read("data.csv", engine="pandas")  # Force pandas
df = pf.read("data.csv", engine="polars")  # Force Polars
df = pf.read("data.csv", engine="dask")    # Force Dask
```

### Q: How do I configure thresholds globally?

**A**: Use `set_config()`:

```python
from parquetframe import set_config

set_config(
    pandas_threshold_mb=50.0,   # Use pandas up to 50MB
    polars_threshold_mb=100.0   # Use Polars from 50MB-100GB
)
```

---

## Getting Help

- **Documentation**: [docs/phase2/](docs/phase2/)
- **Migration Guide**: [docs/phase2/MIGRATION_GUIDE.md](docs/phase2/MIGRATION_GUIDE.md)
- **Examples**: [examples/phase2/](examples/phase2/)
- **ADR**: [docs/adr/0002-make-phase2-default-api.md](docs/adr/0002-make-phase2-default-api.md)
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions

---

## Benefits of Migrating

✅ **Performance**: 2-5x improvements on medium-scale datasets
✅ **Flexibility**: Three DataFrame engines instead of two
✅ **Simplicity**: Single, clear import path
✅ **Features**: Avro support, entity-graph framework
✅ **Future-Proof**: Continued development on Phase 2

---

**Version**: 1.0.0
**Last Updated**: 2025-10-18
**Status**: Active - Phase 1 deprecated, Phase 2 default
