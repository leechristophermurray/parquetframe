# Phase 3.5 Development Plan: GraphAr Compliance & Rust Integration

**Status**: Ready to Start
**Created**: 2025-10-21
**Branch**: `feature/graphar-permissions-storage`
**Estimated Time**: 2-3 weeks
**Target Version**: v0.4.0

---

## Executive Summary

This development plan addresses two critical objectives:

1. **GraphAr Compliance for Permissions Storage**: Refactor the Zanzibar permissions system to use GraphAr-compliant storage, enabling permissions to be stored as a separate graph structure following Apache GraphAr specifications.

2. **Rust-First Implementation Verification**: Confirm that ParquetFrame's Rust backend is used by default with graceful fallback to Python, as outlined in CONTEXT_RUSTIC.md.

---

## Current State Analysis

### ✅ Rust Integration (Verified)

**Confirmed Implementation:**
- Rust backend detection in `src/parquetframe/backends/rust_backend.py`
- `backend='auto'` defaults implemented in all algorithm operations
- Graceful fallback pattern: Try Rust → Catch exceptions → Warn → Fall back to Python
- Environment variable support: `PARQUETFRAME_DISABLE_RUST=1`
- Configuration system with `use_rust_backend: bool = True` (enabled by default)

**Implemented Algorithms:**
- Phase 1 (COMPLETE): CSR/CSC builders, BFS, DFS
- Phase 2 (COMPLETE): Parquet metadata operations
- Phase 3.3 (COMPLETE): PageRank, Dijkstra, Connected Components
- Phase 3.4 (COMPLETE): Workflow Engine Core

**Cargo Workspace Structure:**
```
crates/
├── pf-graph-core/    # Graph algorithms
├── pf-io-core/       # I/O operations
├── pf-workflow-core/ # Workflow DAG executor
└── pf-py/            # PyO3 Python bindings
```

### ❌ Permissions Storage (Non-Compliant)

**Current Issues:**
- `TupleStore.save(path)` creates a **single Parquet file** (`permissions.parquet`)
- Does NOT follow GraphAr spec (no `_metadata.yaml`, `_schema.yaml`, directory structure)
- Permissions not stored as edges in a graph structure
- Cannot be loaded with `pf.read_graph()` for analysis

**Entity Framework:**
- Uses directory-based structure but **missing** GraphAr metadata files
- No `_metadata.yaml` or `_schema.yaml` generation

---

## Required Changes

### Two-Graph Architecture

ParquetFrame will use **separate GraphAr-compliant graphs**:

#### 1. Application Data Graph (`app_graph/`)

```
kanban_data/app_graph/
├── _metadata.yaml       # Graph metadata
├── _schema.yaml         # Vertex/edge schemas
├── vertices/
│   ├── User/
│   │   └── part0.parquet
│   ├── Board/
│   ├── TaskList/
│   └── Task/
└── edges/
    ├── owns/
    ├── contains/
    └── assigned_to/
```

#### 2. Permissions Graph (`permissions_graph/`)

```
kanban_data/permissions_graph/
├── _metadata.yaml       # name: "permissions", directed: true
├── _schema.yaml         # Relation tuple schema
├── vertices/
│   ├── user/            # Subjects
│   │   └── part0.parquet
│   ├── board/           # Objects
│   ├── list/
│   └── task/
└── edges/
    ├── owner/           # Relation types as edge types
    │   └── part0.parquet (src=subject_id, dst=object_id)
    ├── editor/
    └── viewer/
```

### GraphAr Schema Design

**Metadata File (`_metadata.yaml`):**
```yaml
name: "permissions"
version: "1.0"
directed: true
description: "Zanzibar-style permission graph"
```

**Schema File (`_schema.yaml`):**
```yaml
version: "1.0"
vertices:
  user:
    properties:
      id: {type: "string", primary: true}
  board:
    properties:
      id: {type: "string", primary: true}
  list:
    properties:
      id: {type: "string", primary: true}
  task:
    properties:
      id: {type: "string", primary: true}
edges:
  owner:
    properties:
      src: {type: "string", source: true}
      dst: {type: "string", target: true}
      subject_namespace: {type: "string"}
      object_namespace: {type: "string"}
  editor:
    properties:
      src: {type: "string", source: true}
      dst: {type: "string", target: true}
      subject_namespace: {type: "string"}
      object_namespace: {type: "string"}
  viewer:
    properties:
      src: {type: "string", source: true}
      dst: {type: "string", target: true}
      subject_namespace: {type: "string"}
      object_namespace: {type: "string"}
```

---

## Development Tasks (14 Total)

### Phase 1: Analysis & Setup (Tasks 1-2)

1. **Repository Analysis and Context Review** - Understand current state
2. **Create Feature Branch** - `feature/graphar-permissions-storage`

### Phase 2: Rust Verification (Task 3)

3. **Audit Current Rust Backend Implementation** - Verify Rust-first strategy

### Phase 3: Design & Core Implementation (Tasks 4-6)

4. **Design GraphAr Permissions Schema** - Document specification
5. **Refactor TupleStore for GraphAr Compliance** - Core storage refactor
6. **Enhance Entity Framework with GraphAr Metadata Generation** - Add metadata

### Phase 4: Integration & Demo Updates (Tasks 7-8)

7. **Update PermissionManager for GraphAr Paths** - Update demo paths
8. **Refactor Todo/Kanban Demo for Two-Graph Architecture** - Separate graphs

### Phase 5: Testing & Validation (Tasks 9-10, 12)

9. **Create Comprehensive Test Suite** - GraphAr compliance tests
10. **Phase 3.5 Rust Integration Verification** - Performance benchmarks
12. **Integration Testing and Validation** - End-to-end testing

### Phase 6: Documentation & Release (Tasks 11, 13-14)

11. **Update Documentation** - Architecture, guides, API docs
13. **Create Pull Request** - Prepare for review
14. **Post-Merge Cleanup and Next Steps** - Tag release, plan Phase 4

---

## Breaking Changes

⚠️ **Permissions Storage Format Change**
- Old: Single Parquet file at `permissions.parquet`
- New: GraphAr structure at `permissions_graph/`
- Migration guide will be provided in `docs/guides/graphar_migration.md`

⚠️ **Default Permissions Path Change**
- Old: `./kanban_data/permissions`
- New: `./kanban_data/permissions_graph`

---

## Benefits

### GraphAr Compliance

✅ Standard format for permission storage
✅ Can use ParquetFrame's graph algorithms directly on permissions
✅ Permission analysis and visualization using existing tools
✅ Interoperability with external GraphAr-compatible systems

### Rust-First Implementation

✅ 5-20x speedup on graph operations
✅ 2-5x faster I/O metadata operations
✅ 30-60% lower peak memory usage
✅ True parallelism without GIL constraints

### Developer Experience

✅ Consistent architecture across all graph operations
✅ Clear separation between app data and permissions
✅ Improved testability and maintainability
✅ Better documentation and examples

---

## Success Metrics

- [ ] All permissions stored as GraphAr-compliant structures
- [ ] Both `app_graph/` and `permissions_graph/` can be loaded with `pf.read_graph()`
- [ ] All GraphAr metadata files validate correctly
- [ ] Rust backend used by default (confirmed via logs)
- [ ] Graceful fallback to Python works correctly
- [ ] All tests passing (≥85% coverage maintained)
- [ ] Migration guide completed and tested
- [ ] Documentation updated and reviewed
- [ ] Demo application working with new structure

---

## Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| Week 1 | Analysis, Design, Core Implementation | Tasks 1-6 complete |
| Week 2 | Integration, Testing, Documentation | Tasks 7-12 complete |
| Week 3 | Review, PR, Release | Tasks 13-14 complete |

**Target Completion**: End of Week 3
**Release Version**: v0.4.0

---

## Next Steps (After Phase 3.5)

Based on `CONTEXT_CONTINUING.md`, Phase 4 objectives include:

1. **Advanced Features**
   - Streaming support (Kafka/Pulsar integration)
   - Advanced visualizations (Matplotlib/Plotly)
   - Graph visualization for GraphFrame

2. **Production Hardening**
   - Cloud storage integration (S3, GCS, Azure)
   - Security & enterprise features
   - Audit logging framework
   - Data governance features

---

## Related Documents

- `CONTEXT_CONTINUING.md` - Development roadmap
- `CONTEXT_RUSTIC.md` - Rust integration strategy
- `docs/adr/0003-rust-first-integration.md` - ADR for Rust integration
- `docs/graph/index.md` - Graph engine documentation
- `examples/integration/todo_kanban/` - Demo application

---

## Git Best Practices

All commits must follow conventional commits format:

- `feat(scope): description` - New features
- `fix(scope): description` - Bug fixes
- `refactor(scope): description` - Code refactoring
- `test(scope): description` - Test additions/updates
- `docs(scope): description` - Documentation changes

Example commits:
```
feat(permissions): implement GraphAr-compliant storage for TupleStore
feat(entities): add GraphAr metadata generation to entity framework
refactor(kanban): implement two-graph architecture for app data and permissions
test: add comprehensive GraphAr compliance test suite
docs: add GraphAr compliance architecture documentation
```

---

## Contact & Support

For questions or clarifications during implementation, refer to:
- Project documentation in `docs/`
- Context files (`CONTEXT_*.md`)
- Existing test suites in `tests/`
- Architecture Decision Records in `docs/adr/`

---

**Status**: ✅ Plan Approved - Ready to Start Implementation
