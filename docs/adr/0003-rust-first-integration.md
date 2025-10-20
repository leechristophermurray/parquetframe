# ADR-0003: Rust-First Integration Strategy

**Status**: Proposed

**Date**: 2025-01-20

**Deciders**: ParquetFrame Core Team

**Technical Story**: Integrating Rust as a performance-critical backend while maintaining Python ergonomics and 100% backward compatibility

## Context and Problem Statement

ParquetFrame has successfully implemented Phase 2 with multi-engine support (pandas, Polars, Dask), achieving 2-5x performance improvements. However, certain operations remain CPU-bound and memory-intensive, particularly:

1. **Graph Operations**: Adjacency structure building (CSR/CSC), BFS/DFS traversals, PageRank iterations on graphs with 10M+ edges
2. **I/O Operations**: Parquet/Avro metadata parsing, predicate pushdown preparation, columnar filtering
3. **Transform Kernels**: Boolean masking, type-safe arithmetic, reductions across large Arrow buffers
4. **Workflow Orchestration**: DAG execution, concurrency management, resource scheduling

While Python engines provide good performance, they hit fundamental limitations:
- **GIL Constraints**: Python's Global Interpreter Lock limits true parallelism
- **Memory Overhead**: Python objects have significant memory overhead (24-56 bytes per object)
- **Type Safety**: Runtime type checking adds overhead and potential for errors
- **Performance Ceiling**: Even with optimized libraries, Python can't match systems languages

Users working with large-scale data (100M+ rows, 10GB+ files, complex graph traversals) need:
- **5-20x speedups** on graph algorithms
- **2-5x faster** I/O metadata operations
- **3-10x improvements** on columnar transforms
- **30-60% lower** peak memory usage

## Decision Drivers

### Performance Requirements
- **Large Dataset Support**: Efficient handling of 1B+ edge graphs, 100GB+ Parquet files
- **Memory Efficiency**: Reduce memory overhead for graph structures and large dataframes
- **Parallel Scalability**: Utilize multi-core processors effectively without GIL constraints
- **Predictable Performance**: Consistent, deterministic performance characteristics

### Technical Requirements
- **Backward Compatibility**: 100% API compatibility with existing Phase 2 code
- **Graceful Degradation**: Automatic fallback to Python when Rust unavailable
- **Zero-Copy Interop**: Efficient data exchange via Arrow/NumPy without serialization overhead
- **Production Ready**: Enterprise-grade error handling, logging, and monitoring

### Development Experience
- **Modern Toolchain**: Leverage Rust's type system, borrow checker, and cargo ecosystem
- **PyO3 Integration**: Seamless Python bindings with automatic type conversion
- **Incremental Adoption**: Phase-by-phase migration, not big-bang rewrite
- **Developer Friendly**: Clear documentation, examples, and onboarding guides

### Project Standards
- **Conventional Commits**: All commits follow conventional commit format
- **Git Best Practices**: Feature branch workflow with descriptive commits
- **Test Coverage**: Maintain ≥85% coverage for Rust components
- **Documentation**: Comprehensive API docs, tutorials, and migration guides

## Decision

We will **integrate Rust as a 4th engine** alongside pandas, Polars, and Dask, with Rust serving as the **preferred backend for performance-critical operations** while maintaining full Python fallback.

### Implementation Approach

**1. Rust-First with Transparent Fallback**

```python
# Default behavior - uses Rust when available, falls back to Python
import parquetframe as pf

graph = pf.GraphFrame.from_edges(edges)  # Uses Rust CSR builder
distances = graph.bfs(source=0)          # Uses Rust BFS algorithm
df = pf.read_parquet("large_file.pqt")   # Uses Rust metadata parser

# Environment variable to disable Rust globally
export PARQUETFRAME_DISABLE_RUST=1       # Falls back to Python

# Explicit backend control
graph = pf.GraphFrame.from_edges(edges, engine='rust')     # Rust only
graph = pf.GraphFrame.from_edges(edges, engine='pandas')   # Pure Python
```

**2. Architecture: Cargo Workspace + PyO3**

```
parquetframe/
├── crates/
│   ├── pf-graph-core/     # Graph algorithms (CSR/CSC, BFS, PageRank)
│   ├── pf-io-core/         # I/O operations (Parquet/Avro metadata)
│   ├── pf-workflow-core/   # Workflow DAG executor
│   └── pf-py/              # PyO3 Python bindings
├── src/parquetframe/
│   ├── backends/
│   │   └── rust_backend.py # Detection and fallback logic
│   └── ...
└── Cargo.toml              # Workspace configuration
```

**3. Data Interchange: Zero-Copy via Arrow**

- **Primary**: Arrow RecordBatch / Arrays (zero-copy between Rust ↔ Python)
- **Secondary**: NumPy arrays (single copy to Arrow, then zero-copy)
- **Graph Data**: Typed buffers (offsets, indices, weights) via memoryview

**4. Phased Rollout**

| Phase | Component | Version | Timeline |
|-------|-----------|---------|----------|
| **Phase 0** | Foundation & Build Infrastructure | v1.1.0 | 1 week |
| **Phase 1** | Graph Core (CSR/CSC, BFS, DFS) | v1.2.0 | 2-3 weeks |
| **Phase 2** | I/O Fast-Paths (Metadata, Filters) | v1.3.0 | 2-3 weeks |
| **Phase 3** | Advanced Algorithms (PageRank, Dijkstra) | v1.4.0 | 2-3 weeks |
| **Phase 4** | Transform Kernels (Filters, Projections) | v1.5.0 | 2-3 weeks |
| **Phase 5** | Workflow Executor (DAG, Concurrency) | v1.6.0 | 2-3 weeks |
| **Phase 6** | Entity Persistence & Polish | v2.0.0 | 2-3 weeks |

**v2.0.0 Target**: Rust-first by default, delivering 5-20x performance improvements

### Concurrency Strategy

- **Rayon**: Data parallelism for CPU-bound operations (configurable thread pool)
- **Tokio**: Async/await for I/O-bound operations (optional, feature-gated)
- **GIL Release**: `Python::allow_threads` for long-running Rust operations
- **Thread Control**: Respect `RAYON_NUM_THREADS` and `PARQUETFRAME_RUST_THREADS` environment variables

## Alternatives Considered

### Alternative A: Pure Python Optimization (Rejected)

**Approach**: Focus on optimizing pure Python with NumPy, Numba, and better algorithms.

**Pros**:
- No additional build complexity
- No new languages for contributors
- Easier deployment (no Rust toolchain)

**Cons**:
- **Performance Ceiling**: Can't match Rust's performance (max 2-3x improvements)
- **GIL Limitations**: True parallelism impossible
- **Memory Overhead**: Python object overhead remains
- **Maintenance**: Complex NumPy/Numba code harder to maintain than clear Rust

**Why Rejected**: Can't achieve target 5-20x performance improvements

### Alternative B: Cython Implementation (Rejected)

**Approach**: Use Cython to compile performance-critical paths to C.

**Pros**:
- Closer to Python syntax
- Good NumPy integration
- Proven technology (used by pandas, scikit-learn)

**Cons**:
- **Syntax Complexity**: Cython's type annotation syntax is verbose and error-prone
- **Memory Safety**: Manual memory management, no borrow checker
- **Tooling**: Weaker tooling compared to Rust (cargo, clippy, rustfmt)
- **Async Support**: Poor async/await support compared to Tokio
- **Maintenance**: Cython code harder to read/maintain than Rust

**Why Rejected**: Rust provides better developer experience and safety guarantees

### Alternative C: C++ Extensions (Rejected)

**Approach**: Write C++ extensions using pybind11.

**Pros**:
- Maximum performance potential
- Mature ecosystem (Arrow C++, Parquet C++)
- Good interoperability

**Cons**:
- **Memory Safety**: Manual memory management, no borrow checker
- **Build Complexity**: CMake, compiler flags, platform dependencies
- **Async Support**: No native async/await (requires external libraries)
- **Modern Features**: C++20 adoption slower than Rust
- **Learning Curve**: C++ complexity higher than Rust for contributors

**Why Rejected**: Rust provides memory safety without runtime overhead

### Alternative D: Rust-First Integration (Selected) ✅

**Approach**: Integrate Rust via PyO3 with automatic fallback to Python.

**Pros**:
- **Performance**: Achieves target 5-20x improvements
- **Memory Safety**: Borrow checker prevents memory errors at compile time
- **Concurrency**: Native parallelism without GIL constraints
- **Modern Toolchain**: Cargo, clippy, rustfmt, excellent IDE support
- **Zero-Copy**: Arrow support enables efficient data exchange
- **Async/Await**: Tokio provides production-grade async runtime
- **Backward Compatibility**: Transparent fallback maintains compatibility
- **Growing Ecosystem**: Python/Rust integration increasingly common (Polars, Ruff, uv)

**Cons**:
- **Build Complexity**: Requires Rust toolchain for development
- **Learning Curve**: Contributors need to learn Rust (mitigated by gradual adoption)
- **Binary Distribution**: Need to build wheels for multiple platforms (handled by maturin + CI)

**Why Selected**: Best long-term solution for performance, safety, and maintainability

## Consequences

### Positive Consequences

✅ **Dramatic Performance Improvements**: 5-20x speedups on graph operations, 2-5x on I/O

✅ **Memory Efficiency**: 30-60% lower peak memory usage on large workloads

✅ **True Parallelism**: Multi-core utilization without GIL constraints

✅ **Memory Safety**: Borrow checker prevents entire classes of bugs

✅ **Modern Toolchain**: Cargo, clippy, rustfmt provide excellent developer experience

✅ **Future-Proof**: Rust adoption growing in data science (Polars, uv, Ruff)

✅ **Competitive Advantage**: Positions ParquetFrame as high-performance alternative to pure Python libraries

### Negative Consequences

❌ **Build Complexity**: Contributors need Rust toolchain installed

❌ **Learning Curve**: New contributors must learn Rust basics

❌ **CI/CD Complexity**: Need to build Rust wheels for multiple platforms

❌ **Debugging**: Cross-language debugging more complex

### Neutral Consequences

⚪ **Binary Wheels**: Increased wheel size (~5-10MB per platform) - acceptable tradeoff

⚪ **Development Time**: Initial Rust implementation slower, but faster iteration long-term

⚪ **Maintenance**: Two languages to maintain, but Rust code more maintainable than equivalent Python

### Risk Mitigation

**Risk: Low Rust Adoption by Contributors**

- *Mitigation*: Comprehensive Rust onboarding guide with examples
- *Mitigation*: Core team maintains Rust code, Python contributions remain primary
- *Mitigation*: Clear separation: Rust for performance, Python for features
- *Mitigation*: 3-6 month transition period for team to learn Rust

**Risk: Build/Deployment Complexity**

- *Mitigation*: Maturin simplifies Python packaging with Rust
- *Mitigation*: Pre-built wheels for all major platforms (manylinux, macOS, Windows)
- *Mitigation*: Fallback to pure Python if Rust wheels unavailable
- *Mitigation*: CI/CD automation for wheel building (GitHub Actions)

**Risk: Performance Regression**

- *Mitigation*: Comprehensive benchmark suite comparing Rust vs Python
- *Mitigation*: CI fails on >10% performance regression
- *Mitigation*: Property-based testing (hypothesis + quickcheck)
- *Mitigation*: Golden-result tests ensure correctness

**Risk: Cross-Language Debugging Difficulty**

- *Mitigation*: Extensive logging at Python/Rust boundary
- *Mitigation*: Environment variable for verbose Rust logging (`PARQUETFRAME_RUST_LOG=debug`)
- *Mitigation*: Clear error messages with context
- *Mitigation*: Separate Rust unit tests from Python integration tests

## Implementation Checklist

### Phase 0: Foundation (v1.1.0) - 1 week

- [ ] Create ADR documenting Rust integration decision
- [ ] Setup Cargo workspace with 4 crates (graph-core, io-core, workflow-core, py)
- [ ] Configure maturin for PyO3 Python bindings
- [ ] Implement `rust_backend.py` detection with fallback logic
- [ ] Update `.gitignore` for Rust artifacts
- [ ] Add Rust toolchain configuration (`.rust-toolchain.toml`)
- [ ] Update CI/CD for Rust checks and wheel builds
- [ ] Add benchmarking framework
- [ ] Documentation: README section, rust-integration.md guide

### Phase 1: Graph Core (v1.2.0) - 2-3 weeks

- [ ] Implement CSR/CSC adjacency builders in Rust
- [ ] Implement BFS/DFS traversal algorithms
- [ ] PyO3 bindings with automatic backend selection
- [ ] Integration with existing GraphFrame API
- [ ] Comprehensive parity tests vs pandas/networkx
- [ ] Benchmarks showing 5-10x improvements

### Phase 2-6: Progressive Rollout (v1.3.0-2.0.0) - 12-15 weeks

- [ ] I/O fast-paths (Parquet/Avro metadata)
- [ ] Advanced graph algorithms (PageRank, Dijkstra, Connected Components)
- [ ] Transform kernels (filters, projections, groupby)
- [ ] Workflow DAG executor with concurrency
- [ ] Entity persistence optimizations
- [ ] Complete documentation and migration guide

## Related Decisions

This ADR builds on:
- **ADR-0001**: Next-Generation Architecture (Phase 2 multi-engine framework)
- **ADR-0002**: Make Phase 2 Default API (v1.0.0 multi-engine release)

This ADR informs:
- Future ADRs about specific Rust component implementations
- Version 2.0.0 release planning (Rust-first by default)

## References

- [CONTEXT_RUSTIC.md](../../CONTEXT_RUSTIC.md) - Detailed Rust integration roadmap
- [PyO3 Documentation](https://pyo3.rs/) - Python-Rust bindings
- [Maturin Documentation](https://www.maturin.rs/) - Building Python wheels with Rust
- [Apache Arrow Rust](https://docs.rs/arrow/) - Arrow implementation in Rust
- [Rayon Documentation](https://docs.rs/rayon/) - Data parallelism in Rust
- [Polars](https://www.pola.rs/) - Reference: Successful Python library with Rust backend

## Success Metrics

This decision will be considered successful when:

1. **Performance**: Achieve 5-20x speedups on graph operations (measured in benchmarks)
2. **Memory**: Reduce peak memory usage by 30-60% on large datasets
3. **Compatibility**: 100% backward compatibility maintained (all existing tests pass)
4. **Adoption**: ≥50% of operations use Rust backend when wheels installed
5. **Quality**: Zero correctness regressions (Rust produces identical results to Python)
6. **Developer Experience**: Rust contribution guide has ≥80% positive feedback
7. **Deployment**: Pre-built wheels available for all major platforms (Linux, macOS, Windows, x86_64, arm64)
8. **Coverage**: Rust code maintains ≥85% test coverage

## Timeline

- **v1.1.0** (Week 1): Phase 0 Foundation - Build infrastructure complete
- **v1.2.0** (Week 4): Phase 1 Graph Core - CSR/CSC + BFS/DFS complete
- **v1.3.0** (Week 7): Phase 2 I/O - Parquet/Avro metadata fast-paths
- **v1.4.0** (Week 10): Phase 3 Algorithms - PageRank, Dijkstra, Components
- **v1.5.0** (Week 13): Phase 4 Transforms - Filters, projections, groupby
- **v1.6.0** (Week 16): Phase 5 Workflows - DAG executor with concurrency
- **v2.0.0** (Week 19): Phase 6 Complete - Rust-first by default

**Total Estimated Time**: 14-19 weeks (~3.5-5 months)

---

**Status**: Proposed

**Implementation**: Ready to start with Phase 0

**Next Review**: After Phase 0 completion (v1.1.0 release)
