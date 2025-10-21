# Task 1.1: GraphFrame Backend Integration - Analysis

**Status**: ✅ MOSTLY COMPLETE - Integration Already Done!
**Date**: 2025-10-21
**Scope**: Review existing integration and add convenience methods

---

## 🎉 Current State: Integration Already Complete!

### ✅ What's Already Working

1. **Rust Backend Fully Integrated** (`src/parquetframe/graph/rust_backend.py`):
   - ✅ `build_csr_rust()` - CSR adjacency builder
   - ✅ `build_csc_rust()` - CSC adjacency builder
   - ✅ `bfs_rust()` - Breadth-first search
   - ✅ `dfs_rust()` - Depth-first search
   - ✅ `pagerank_rust()` - PageRank algorithm
   - ✅ `dijkstra_rust()` - Shortest paths
   - ✅ `connected_components_rust()` - Connected components
   - ✅ `is_rust_available()` - Backend detection
   - ✅ `get_rust_version()` - Version info

2. **Algorithm Files with Backend Selection** (auto/pandas/dask/rust):
   - ✅ `pagerank.py` - Complete with Rust integration
   - ✅ `shortest_path.py` - Complete with Rust integration
   - ✅ `components.py` - Complete with Rust integration
   - ✅ All support `backend='auto'|'rust'|'pandas'|'dask'` parameter
   - ✅ Automatic fallback from Rust to Python on errors

3. **CSR/CSC Adjacency Already Uses Rust**:
   - ✅ `adjacency.py` line 176-186: Tries Rust first, falls back to Python
   - ✅ Both `CSRAdjacency` and `CSCAdjacency` benefit from Rust

4. **GraphFrame Class Exists** (`src/parquetframe/graph/__init__.py`):
   - ✅ Basic structure with vertices, edges, metadata
   - ✅ `csr_adjacency` and `csc_adjacency` properties (lazy-loaded)
   - ✅ Methods: `degree()`, `neighbors()`, `has_edge()`, `subgraph()`
   - ⚠️ Missing: Direct algorithm methods (`pagerank()`, `dijkstra()`, etc.)

---

## 🎯 What Needs to Be Done for Task 1.1

### Priority 1: Add Convenience Methods to GraphFrame (1-2 hours)

**Goal**: Make algorithms accessible directly from GraphFrame instance

**Implementation**: Add methods to `GraphFrame` class in `__init__.py`:

```python
def pagerank(self, alpha=0.85, tol=1e-6, max_iter=100,
             weight_column=None, personalized=None,
             backend='auto') -> pd.DataFrame:
    """Compute PageRank scores using power iteration."""
    from .algo.pagerank import pagerank
    return pagerank(self, alpha, tol, max_iter, weight_column,
                   personalized, backend=backend)

def shortest_path(self, sources, weight_column=None,
                  backend='auto', include_unreachable=True) -> pd.DataFrame:
    """Find shortest paths from source vertices."""
    from .algo.shortest_path import shortest_path
    return shortest_path(self, sources, weight_column,
                        backend=backend,
                        include_unreachable=include_unreachable)

def connected_components(self, method='weak', backend='auto',
                        max_iter=50) -> pd.DataFrame:
    """Find connected components."""
    from .algo.components import connected_components
    return connected_components(self, method, backend=backend,
                               max_iter=max_iter)
```

**Files to Modify**:
- `src/parquetframe/graph/__init__.py` (add methods)

### Priority 2: Add `from_edges()` Class Method (30 minutes)

**Goal**: Enable direct graph construction from edge lists

```python
@classmethod
def from_edges(cls, sources, targets, num_vertices=None,
               edge_weights=None, vertex_data=None,
               edge_data=None, directed=True,
               engine='auto') -> 'GraphFrame':
    """
    Create GraphFrame directly from edge lists.

    Args:
        sources: Source vertex IDs (array-like)
        targets: Target vertex IDs (array-like)
        num_vertices: Total vertices (inferred if None)
        edge_weights: Optional edge weights
        vertex_data: Optional vertex properties DataFrame
        edge_data: Optional edge properties DataFrame
        directed: Whether graph is directed
        engine: Backend engine ('auto', 'rust', 'pandas')

    Returns:
        GraphFrame instance

    Examples:
        >>> sources = [0, 1, 2]
        >>> targets = [1, 2, 0]
        >>> graph = GraphFrame.from_edges(sources, targets)
        >>> print(graph)
        GraphFrame(3 vertices, 3 edges, directed)
    """
    # Implementation: Build edges DataFrame, create adjacency
    # Use Rust backend if engine='rust' or 'auto'
```

**Files to Modify**:
- `src/parquetframe/graph/__init__.py` (add classmethod)

### Priority 3: Update Exports and __all__ (15 minutes)

**Goal**: Ensure proper module exports

```python
__all__ = [
    "GraphFrame",
    "read_graph",
    "CSRAdjacency",
    "CSCAdjacency",
    # Algorithm functions (for direct import)
    "pagerank",
    "shortest_path",
    "connected_components",
]
```

**Files to Modify**:
- `src/parquetframe/graph/__init__.py` (update __all__)
- `src/parquetframe/graph/algo/__init__.py` (update exports)

### Priority 4: Add Tests for New Methods (1-2 hours)

**Goal**: Verify convenience methods work correctly

**Test Files to Create/Update**:
- `tests/graph/test_graphframe_methods.py` (new)
- Test `graph.pagerank()`, `graph.shortest_path()`, `graph.connected_components()`
- Test `GraphFrame.from_edges()` with different parameters
- Test backend selection (`engine='rust'`, `engine='pandas'`)

---

## 📊 Task 1.1 Completion Checklist

- [ ] **Step 1**: Add `pagerank()` method to GraphFrame class
- [ ] **Step 2**: Add `shortest_path()` / `dijkstra()` methods to GraphFrame
- [ ] **Step 3**: Add `connected_components()` method to GraphFrame
- [ ] **Step 4**: Add `bfs()` and `dfs()` convenience methods
- [ ] **Step 5**: Implement `GraphFrame.from_edges()` classmethod
- [ ] **Step 6**: Update module exports (`__all__`)
- [ ] **Step 7**: Write tests for new methods
- [ ] **Step 8**: Update docstrings with examples
- [ ] **Step 9**: Run existing tests to ensure backward compatibility
- [ ] **Step 10**: Commit changes

---

## 🧪 Testing Strategy

### Unit Tests
```python
def test_graphframe_pagerank():
    """Test graph.pagerank() method with Rust backend."""
    sources = [0, 1, 2]
    targets = [1, 2, 0]
    graph = GraphFrame.from_edges(sources, targets)

    # Test with auto backend
    ranks = graph.pagerank(backend='auto')
    assert len(ranks) == 3
    assert 'vertex' in ranks.columns
    assert 'rank' in ranks.columns

    # Test with explicit Rust backend
    if is_rust_available():
        ranks_rust = graph.pagerank(backend='rust')
        np.testing.assert_allclose(ranks['rank'], ranks_rust['rank'])

def test_graphframe_from_edges():
    """Test GraphFrame.from_edges() classmethod."""
    sources = [0, 0, 1]
    targets = [1, 2, 2]

    graph = GraphFrame.from_edges(sources, targets, num_vertices=3)
    assert graph.num_vertices == 3
    assert graph.num_edges == 3
    assert graph.is_directed == True
```

### Integration Tests
```python
def test_backend_integration_pagerank():
    """Test PageRank with all backends."""
    graph = create_test_graph()  # Helper function

    # Compare results across backends
    ranks_auto = graph.pagerank(backend='auto')
    ranks_pandas = graph.pagerank(backend='pandas')

    if is_rust_available():
        ranks_rust = graph.pagerank(backend='rust')
        # Verify Rust matches pandas (within tolerance)
        np.testing.assert_allclose(
            ranks_rust['rank'].values,
            ranks_pandas['rank'].values,
            rtol=1e-5
        )
```

---

## 🎯 Success Criteria for Task 1.1

1. ✅ **Convenience Methods**: All algorithms callable via `graph.method()`
2. ✅ **from_edges() Support**: Can create graphs directly from arrays
3. ✅ **Backend Selection**: `engine='rust'|'pandas'|'auto'` works correctly
4. ✅ **Backward Compatibility**: All existing tests still pass
5. ✅ **Documentation**: Methods have comprehensive docstrings with examples
6. ✅ **Tests**: New methods have 100% test coverage

---

## 📝 Implementation Notes

### Key Design Decisions

1. **Thin Wrapper Pattern**: GraphFrame methods should be thin wrappers around algorithm functions
   - Keeps logic in algorithm modules
   - GraphFrame provides convenience/ergonomics

2. **Default Backend**: Use `'auto'` as default (prefer Rust, fallback to pandas)
   - Maximizes performance out of the box
   - No breaking changes for existing code

3. **Parameter Forwarding**: Pass through all algorithm parameters
   - Don't hide functionality
   - Users can access all algorithm options

### Example Usage (After Implementation)

```python
import parquetframe as pf

# Create graph from edge list
sources = [0, 0, 1, 2]
targets = [1, 2, 2, 0]
graph = pf.GraphFrame.from_edges(sources, targets)

# Compute PageRank (uses Rust automatically)
ranks = graph.pagerank(alpha=0.85)
print(ranks.nlargest(5, 'rank'))

# Find shortest paths
paths = graph.shortest_path(sources=[0], weight_column='weight')
print(paths[paths['distance'] < float('inf')])

# Find connected components
components = graph.connected_components()
print(components.groupby('component_id').size())

# Force specific backend
ranks_rust = graph.pagerank(backend='rust')  # Requires Rust
ranks_pandas = graph.pagerank(backend='pandas')  # Pure Python
```

---

## 🚀 Estimated Time

- **Step 1-4** (Add methods): 1 hour
- **Step 5** (from_edges): 30 minutes
- **Step 6** (Exports): 15 minutes
- **Step 7-8** (Tests & docs): 1.5 hours
- **Step 9** (Validation): 30 minutes
- **Step 10** (Commit): 15 minutes

**Total**: ~3.5 hours (Half day)

---

## ✅ Status: READY TO IMPLEMENT

**Next Action**: Begin Step 1 - Add `pagerank()` method to GraphFrame class

**Files to Modify**:
1. `src/parquetframe/graph/__init__.py` - Add methods
2. `tests/graph/test_graphframe_methods.py` - New test file
3. `src/parquetframe/graph/algo/__init__.py` - Update exports
