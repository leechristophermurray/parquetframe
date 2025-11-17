# BioFrame Integration

ParquetFrame integrates BioFrame to support genomic interval operations with pandas/Dask backends and optional parallelization.

## Core Operations

```python
import parquetframe as pf

genes = pf.read("genes.parquet")
peaks = pf.read("chip_seq_peaks.parquet")

# Overlap (broadcast for smaller set)
overlaps = genes.bio.overlap(peaks, broadcast=True)

# Coverage per interval
coverage = genes.bio.coverage(peaks)

# Cluster nearby features
clustered = genes.bio.cluster(min_dist=1000)
```

## Parallel Patterns

- Use Dask for large datasets (engine auto‑selection or `engine="dask"`).
- Broadcast the smaller dataset for efficient joins.

## Tips

- Ensure chromosome ordering and coordinate conventions are consistent.
- Partition by chromosome for scalable operations.

## Related Categories

- **[Core Features](../core-features/index.md)**
- **[Analytics & Statistics](../analytics-statistics/index.md)**
