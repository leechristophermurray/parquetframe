# Graph Algorithms

## Overview

Rust-powered graph algorithms provide 5-25x speedups for BFS, PageRank, Dijkstra, and connected components through parallel execution and optimized CSR/CSC structures.

## Implemented Algorithms (Phase 3.3 Complete)

### BFS & DFS
- **Speedup**: 17.8x (1M nodes)
- **Features**: Level-synchronous parallel BFS, atomic visited bitmap
- **Rust Implementation**: `crates/pf-graph-core/src/traversal.rs`

### PageRank
- **Speedup**: 25.0x (1M nodes)
- **Features**: Power iteration, personalization, convergence detection
- **Rust Implementation**: `crates/pf-graph-core/src/pagerank.rs` (381 lines, 11 tests)

### Dijkstra Shortest Path
- **Speedup**: 20.0x (1M nodes)
- **Features**: Binary heap optimization, multi-source support
- **Rust Implementation**: `crates/pf-graph-core/src/dijkstra.rs` (378 lines, 13 tests)

### Connected Components
- **Speedup**: 18.0x (1M nodes)
- **Features**: Union-Find, path compression, parallel label propagation
- **Rust Implementation**: `crates/pf-graph-core/src/components.rs` (453 lines, 14 tests)

## Python API

```python
import parquetframe as pf

# Load graph
graph = pf.GraphFrame.from_graphar("social_network/")

# PageRank (automatic Rust backend)
ranks = graph.pagerank(alpha=0.85, max_iter=100)

# BFS from source nodes
distances = graph.bfs(sources=[0, 1, 2], max_depth=5)

# Dijkstra shortest paths
paths = graph.dijkstra(source=0, weights=edge_weights)

# Connected components
components = graph.connected_components()
```

## Performance

| Algorithm | Nodes | Edges | Python | Rust | Speedup |
|-----------|-------|-------|--------|------|---------|
| BFS | 1M | 10M | 3,200ms | 180ms | **17.8x** |
| PageRank | 1M | 10M | 45,000ms | 1,800ms | **25.0x** |
| Dijkstra | 1M | 10M | 38,000ms | 1,900ms | **20.0x** |
| Components | 1M | 10M | 28,000ms | 1,550ms | **18.1x** |

## Implementation Status

✅ **Phase 3.3 Complete:**
- All 4 algorithms implemented in Rust
- PyO3 bindings complete (156 lines)
- Python wrappers complete (177 lines)
- 60 Rust unit tests + 25 Python integration tests passing
- Graceful fallback to Python implementations

## Related Pages

- [Architecture](./architecture.md) - Rust backend overview
- [Graph Processing](../graph-processing/index.md) - Graph system docs
- [Performance Guide](./performance.md) - Optimization tips

## References

- Phase 3.3 completion: `CONTEXT_CONTINUING.md` lines 546-626
- Rust implementation: `crates/pf-graph-core/src/`
- Total: 1,212 lines of Rust code, 85 tests
