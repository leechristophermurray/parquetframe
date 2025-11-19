# DataFrame Engine Selection Matrix

ParquetFrame automatically selects the optimal DataFrame backend (Pandas, Polars, or Dask) based on your data size, operation type, and system resources. This document explains the selection logic and how to customize it.

## Quick Reference

| Data Size | Default Engine | Rationale |
|-----------|----------------|-----------|
| < 100 MB | **Pandas** | Fast startup, minimal overhead, excellent for small datasets |
| 100 MB - 10 GB | **Polars** | Memory-efficient, highly optimized, good for medium datasets |
| > 10 GB | **Dask** | Distributed processing, handles datasets larger than memory |

> [!NOTE]
> These are default thresholds. ParquetFrame uses a sophisticated scoring system that considers multiple factors, not just size.

---

## How Engine Selection Works

ParquetFrame uses a **weighted scoring system** with 5 factors:

### Scoring Breakdown

| Factor | Weight | Description |
|--------|--------|-------------|
| **Size Fit** | 40% | How well data size matches engine's optimal range |
| **Memory Efficiency** | 25% | Estimated memory usage vs. available system memory |
| **Performance Score** | 20% | Engine's general performance characteristics |
| **Lazy Evaluation** | 10% | Match between user preference and engine capability |
| **Operation Type** | 5% | Reserved for operation-specific optimizations |

### Size-Based Scoring

Each engine has an optimal size range:

```python
# Pandas
optimal_size_range = (0, 100 * 1024 * 1024)  # 0-100 MB

# Polars
optimal_size_range = (10 * 1024 * 1024, 10 * 1024 * 1024 * 1024)  # 10 MB - 10 GB

# Dask
optimal_size_range = (100 * 1024 * 1024, float('inf'))  # 100 MB+
```

**Scoring logic:**
- **Perfect fit** (data within range): Score = 1.0
- **Too small** (oversized engine): Score = max(0.3, data_size/min_size)
- **Too large** (undersized engine): Score = max(0.1, max_size/data_size)

### Memory Efficiency Scoring

Considers available system memory and each engine's memory footprint:

```python
memory_efficiency:
  - Pandas: 1.0 (baseline)
  - Polars: 1.5 (50% more efficient)
  - Dask: 2.0 (2x more efficient with chunking)
```

**Formula:**
```python
estimated_usage = data_size / memory_efficiency
memory_ratio = estimated_usage / (available_memory * 0.8)  # 80% safety margin

if memory_ratio <= 0.5:
    score = 1.0  # Excellent fit
elif memory_ratio <= 1.0:
    score = 1.0 - (memory_ratio - 0.5) * 2  # Linear decrease
else:
    score = max(0.1, 1.0 / memory_ratio)  # Heavy penalty for overflow
```

---

## Configuration

### Environment Variables

Override default thresholds:

```bash
export PARQUETFRAME_PANDAS_THRESHOLD_MB=200
export PARQUETFRAME_POLARS_THRESHOLD_MB=20000
export PARQUETFRAME_ENGINE=polars  # Force specific engine
```

### Python API

```python
from parquetframe import set_config

# Adjust thresholds
set_config(
    pandas_threshold_mb=200,
    polars_threshold_mb=20_000
)

# Force an engine globally
set_config(default_engine="polars")
```

### Per-Operation Override

```python
from parquetframe import read
from parquetframe.config import config_context

# Temporarily use Dask for a large file
with config_context(default_engine="dask"):
    df = read("huge_file.parquet")
```

---

## Engine Characteristics

### Pandas

**Best for:** Small to medium datasets (< 100 MB), exploratory analysis, prototyping

**Pros:**
- Fast startup time
- Mature ecosystem
- Rich functionality
- Universal compatibility

**Cons:**
- Single-threaded by default
- Entire dataset in memory
- Performance degrades with large data

**Optimal Size Range:** 0 - 100 MB

### Polars

**Best for:** Medium to large datasets (10 MB - 10 GB), production workloads

**Pros:**
- Highly optimized (Rust core)
- Memory-efficient
- Parallel by default
- Lazy evaluation support

**Cons:**
- Newer ecosystem
- Fewer integrations than Pandas
- Learning curve for lazy API

**Optimal Size Range:** 10 MB - 10 GB
**Memory Efficiency:** 1.5x better than Pandas

### Dask

**Best for:** Very large datasets (> 10 GB), distributed computing, datasets larger than memory

**Pros:**
- Handles out-of-core data
- Distributed processing
- Familiar Pandas-like API
- Scales to clusters

**Cons:**
- Higher overhead for small data
- More complex setup
- Lazy evaluation learning curve

**Optimal Size Range:** 100 MB+
**Memory Efficiency:** 2x better than Pandas (chunking)

---

## Advanced: Direct Engine Selection

For advanced users who want full control:

```python
from parquetframe.core import EngineRegistry

registry = EngineRegistry()

# Get available engines
engines = registry.list_engines()
print(engines)  # ['pandas', 'polars', 'dask']

# Select engine manually
engine = registry.get_engine("polars")
df = engine.read_parquet("data.parquet")
```

---

## Troubleshooting

### "No available engines found"

**Cause:** None of the DataFrame libraries are installed.

**Solution:**
```bash
pip install pandas  # Install at least one engine
# or
pip install polars
# or
pip install dask[dataframe]
```

### Engine selection seems wrong

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('parquetframe.core.heuristics').setLevel(logging.DEBUG)
```

You'll see scoring output like:
```
DEBUG:parquetframe.core.heuristics:Engine pandas score: 0.723
DEBUG:parquetframe.core.heuristics:Engine polars score: 0.891
DEBUG:parquetframe.core.heuristics:Selected engine: polars (score: 0.891)
```

### Force disable automatic selection

```python
set_config(default_engine="pandas")  # Always use Pandas
```

---

## Performance Tips

1. **Right-size your thresholds** for your typical workload
2. **Install `psutil`** for accurate memory-based selection:
   ```bash
   pip install psutil
   ```
3. **Use Polars for production** datasets in the 1-10 GB range
4. **Reserve Dask** for truly large datasets or distributed computing
5. **Pandas is fine** for small data and quick scripts

---

## References

- Implementation: [`src/parquetframe/core/heuristics.py`](file:///Users/temp/Documents/Projects/parquetframe/src/parquetframe/core/heuristics.py)
- Configuration: [`src/parquetframe/config.py`](file:///Users/temp/Documents/Projects/parquetframe/src/parquetframe/config.py)
- Engine base: [`src/parquetframe/core/base.py`](file:///Users/temp/Documents/Projects/parquetframe/src/parquetframe/core/base.py)
