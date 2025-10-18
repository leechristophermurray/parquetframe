# Phase 1.2 Technical Design: Graph Traversal Algorithms

**Status**: Active Development
**Phase**: 1.2 - Graph Traversal Algorithms
**Branch**: `feature/graph-engine-phase1.2-traversals`
**Target Version**: 0.6.0

## Overview

Phase 1.2 builds on the solid GraphAr foundation from Phase 1.1 to implement core graph traversal algorithms with intelligent pandas/Dask backend selection. This design maintains the project's architectural principles while delivering high-performance graph processing capabilities.

## Algorithms & API Surface

### Core Algorithms

1. **Breadth-First Search (BFS)**
   - Single/multi-source traversal
   - Depth-limited search
   - Pandas baseline + Dask-optimized frontier expansion

2. **Depth-First Search (DFS)**
   - Iterative implementation (avoid recursion limits)
   - Forest traversal support
   - Discovery/finish times tracking

3. **Shortest Path**
   - Unweighted: BFS delegation
   - Weighted: Dijkstra's algorithm (pandas)
   - Multi-source support

4. **Connected Components**
   - Weak connectivity for directed graphs
   - Pandas: Union-find/repeated BFS
   - Dask: Min-label propagation

5. **PageRank**
   - Power iteration method
   - Personalized PageRank support
   - Dangling node handling

### API Architecture

```python
# Functional API (primary)
from parquetframe.graph.algo import bfs, dfs, shortest_path, connected_components, pagerank

# GraphFrame convenience methods (delegates to functional API)
graph.bfs(sources=[1, 2], max_depth=3)
graph.pagerank(alpha=0.85, max_iter=100)
```

## Data Contracts

### Input Parameters

**Common Parameters:**
- `graph: GraphFrame` - Source graph object
- `sources: int | list[int] | None` - Starting vertex/vertices
- `directed: bool | None` - Graph directionality (auto-detected from GraphFrame)
- `backend: Literal['auto', 'pandas', 'dask'] | None` - Backend selection
- `weight_column: str | None` - Edge weight column name

**Algorithm-Specific:**
- `max_depth: int | None` - BFS/DFS depth limit
- `max_iter: int` - Iteration limit (PageRank, components)
- `tol: float` - Convergence tolerance (PageRank)
- `alpha: float` - Damping factor (PageRank)

### Output Schemas

All algorithms return pandas/Dask DataFrames with stable column schemas:

**BFS Output:**
```
vertex: int64          # Vertex ID
distance: int64        # Distance from source
predecessor: int64     # Previous vertex in path (nullable)
layer: int64           # BFS layer/level
```

**DFS Output:**
```
vertex: int64          # Vertex ID
predecessor: int64     # Previous vertex (nullable)
discovery_time: int64  # Discovery timestamp
finish_time: int64     # Finish timestamp
component_id: int64    # Connected component ID
```

**Shortest Path Output:**
```
vertex: int64          # Vertex ID
distance: float64      # Distance from source (inf for unreachable)
predecessor: int64     # Previous vertex in shortest path (nullable)
```

**Connected Components Output:**
```
vertex: int64          # Vertex ID
component_id: int64    # Component identifier
```

**PageRank Output:**
```
vertex: int64          # Vertex ID
rank: float64          # PageRank score
```

## Backend Selection Policy

### Automatic Selection
- **Pandas**: Graphs < 100MB total size OR vertex/edge data already in pandas
- **Dask**: Large graphs OR explicit user request
- **Hybrid**: Use pandas for algorithms, Dask for data management

### Algorithm-Specific Policies

**BFS:**
- **Pandas**: Standard queue-based BFS with CSR adjacency
- **Dask**: Level-synchronous frontier expansion with DataFrame joins

**DFS:**
- **Pandas**: Iterative stack-based implementation
- **Dask**: Not implemented - falls back to pandas with warning

**Shortest Path:**
- **Pandas**: Dijkstra with heapq for weighted, BFS for unweighted
- **Dask**: Not implemented for weighted - falls back to pandas

**Connected Components:**
- **Pandas**: Union-find or repeated BFS
- **Dask**: Min-label propagation with iterative DataFrame operations

**PageRank:**
- **Pandas**: Standard power iteration with dense operations
- **Dask**: Distributed power iteration with DataFrame operations

## Performance & Memory Considerations

### Memory Usage
- **CSR/CSC Adjacency**: O(V + E) memory overhead
- **Algorithm State**: O(V) for distance/visited arrays
- **Dask Chunks**: Configurable partition sizes for scalability

### Iteration Limits
- **Default Limits**: PageRank (100), Components (50)
- **Convergence**: Early stopping with configurable tolerance
- **Timeout**: No explicit timeouts - rely on iteration limits

### Reproducibility
- **Deterministic**: All algorithms produce consistent results
- **Randomization**: None in Phase 1.2 (future: randomized algorithms)
- **Seeding**: Not applicable for current algorithms

## CLI Integration

### New Commands

```bash
pf graph bfs <graph_path> --sources 1,2,3 --max-depth 5
pf graph dfs <graph_path> --sources 1 --forest
pf graph shortest-path <graph_path> --sources 1 --weight-column distance
pf graph components <graph_path> --method weak
pf graph pagerank <graph_path> --alpha 0.85 --max-iter 100
```

### Shared CLI Options

**Input/Output:**
- `<graph_path>` - GraphAr directory path
- `--output, -o` - Output file path (parquet/csv)
- `--format` - Output format (parquet, csv, json)

**Algorithm Parameters:**
- `--sources` - Comma-separated source vertices
- `--max-depth` - Maximum traversal depth
- `--max-iter` - Maximum iterations
- `--weight-column` - Edge weight column name

**Backend Control:**
- `--backend` - Force backend (auto/pandas/dask)
- `--npartitions` - Dask partition count
- `--scheduler` - Dask scheduler address

**Behavior:**
- `--directed/--undirected` - Override graph directionality
- `--include-unreachable` - Include disconnected vertices
- `--verbose, -v` - Detailed progress output

## Testing Strategy

### Coverage Objectives
- **Maintain**: 45%+ overall coverage
- **Target**: 60%+ for new algorithm modules
- **Focus**: Edge cases and backend switching

### Test Matrix

**Unit Tests:**
- **Small Graphs**: Chain, star, cycle, disconnected
- **Edge Cases**: Empty graph, single vertex, self-loops
- **Parameters**: All algorithm parameters and combinations
- **Backends**: Pandas/Dask parity validation

**Integration Tests:**
- **CLI Commands**: All new graph subcommands
- **GraphFrame Methods**: Convenience method delegation
- **Large Graphs**: Performance and memory usage

**Performance Tests:**
- **Benchmark Suite**: Algorithmic complexity validation
- **Memory Profiling**: Memory usage patterns
- **Backend Comparison**: Pandas vs Dask performance

### Test Fixtures

**Graph Factories:**
```python
@pytest.fixture
def small_chain_graph():
    """Linear chain: 0->1->2->3->4"""

@pytest.fixture
def star_graph():
    """Star topology: center connected to all others"""

@pytest.fixture
def disconnected_graph():
    """Multiple components for testing"""
```

## Module Organization

```
src/parquetframe/graph/algo/
├── __init__.py              # Public API exports
├── traversal.py             # BFS, DFS implementations
├── shortest_path.py         # Shortest path algorithms
├── components.py            # Connected components
├── pagerank.py              # PageRank algorithm
└── utils.py                 # Shared utilities
```

## Implementation Phases

### Phase 1: Core Implementation (Week 1)
1. **Scaffolding**: Create module structure
2. **BFS Pandas**: Basic breadth-first search
3. **DFS Pandas**: Iterative depth-first search
4. **Tests**: Unit tests for core functionality

### Phase 2: Advanced Features (Week 2)
1. **BFS Dask**: Level-synchronous implementation
2. **Shortest Path**: Unweighted + weighted variants
3. **Components**: Union-find + label propagation
4. **Tests**: Backend switching validation

### Phase 3: Integration (Week 3)
1. **PageRank**: Power iteration both backends
2. **GraphFrame Methods**: Convenience wrappers
3. **CLI Commands**: All graph subcommands
4. **Documentation**: API docs and examples

### Phase 4: Polish (Week 4)
1. **Performance**: Adjacency caching and optimization
2. **Error Handling**: Robust validation and messages
3. **Testing**: Comprehensive coverage
4. **Release Prep**: Version bump and changelog

## Success Criteria

**Functional Requirements:**
- ✅ All 5 core algorithms implemented
- ✅ Pandas backend for all algorithms
- ✅ Dask optimization for BFS, components, PageRank
- ✅ GraphFrame convenience methods
- ✅ CLI integration with all subcommands

**Quality Requirements:**
- ✅ 45%+ test coverage maintained
- ✅ All existing tests pass
- ✅ Conventional commits and clean git history
- ✅ Comprehensive documentation
- ✅ Performance benchmarks

**Integration Requirements:**
- ✅ Backend selection respects existing patterns
- ✅ Error handling consistent with project standards
- ✅ CLI follows established UX patterns
- ✅ Material theme documentation integration

## Risk Mitigation

**Performance Risks:**
- **Adjacency Rebuild**: Cache CSR/CSC structures across calls
- **Memory Usage**: Chunked processing for large graphs
- **Dask Overhead**: Smart fallback to pandas when beneficial

**Complexity Risks:**
- **Algorithm Correctness**: Comprehensive unit tests with known outputs
- **Backend Parity**: Test identical results across pandas/Dask
- **Edge Cases**: Explicit handling of empty/disconnected graphs

**Integration Risks:**
- **API Changes**: Maintain backward compatibility
- **CLI Consistency**: Follow established patterns and option naming
- **Documentation**: Keep examples up-to-date with implementation

---

**Next**: Begin implementation with module scaffolding and BFS pandas baseline.
