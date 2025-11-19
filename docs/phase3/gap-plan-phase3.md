# Gap Plan (Phase 3)

This document consolidates all gaps/features identified across repo code and docs.

## Scope & Current State
- Python multi-engine core (pandas/Polars/Dask) with intelligent selection and unified API
- CLI with batch, interactive, SQL, AI, workflows, benchmarking
- Rust acceleration via Cargo workspace:
  - pf-io-core (I/O fast-paths)
  - pf-graph-core (graph algorithms)
  - pf-workflow-core (parallel workflow engine)
  - pf-py (PyO3 bindings, exposed as parquetframe._rustic)
- Docs: extensive Rust Acceleration, Features, and Phase 3 planning; several placeholders to complete

---

## Gap Matrix
Legend: Priority P1 (high), P2 (medium), P3 (lower)

### P1. Rust Distribution (Wheels)
- Current
  - maturin build configured via pyproject.toml (module-name parquetframe._rustic)
  - No public wheel CI pipeline and publish documentation
- Gaps
  - Prebuilt wheels for Linux (manylinux), macOS (x86_64/aarch64), Windows
  - CI matrix and smoke tests (import test on each platform)
  - Release procedure docs (signing, auditwheel/delocate)
- Work Items
  - CI plan (.github/workflows): maturin build matrix; cache; run `python -c "import parquetframe; print(parquetframe.rust_available())"`
  - Document “Releasing Wheels” page and troubleshooting
- Dependencies
  - GitHub Actions runners; maturin; pyo3
- Acceptance Criteria
  - Dry-run produces testable wheels; docs updated; plan approved
- Risks/Mitigations
  - manylinux quirks → test with official manylinux images; constrain Rust/Arrow versions

### P1. Rust I/O Fast-Paths (Parquet/CSV/Avro)
- Current
  - `_rustic` metadata functions available (read_parquet_metadata_rust, get_parquet_row_count_rust, get_parquet_column_names_rust, get_parquet_column_stats_rust)
  - Full readers (read_parquet_fast/read_csv_fast) guarded; may be NotImplemented pending bindings
- Gaps
  - Implement `_rustic.read_parquet_fast` and `_rustic.read_csv_fast` (+ Avro) with Arrow zero-copy, GIL release, parallel read
  - Integrate with CLI and docs; robust fallback
- Work Items
  - Implement Rust fns in pf-io-core + PyO3 in pf-py; Python wrappers + tests + Criterion benchmarks; update docs/rust-acceleration/io-fastpaths.md
- Dependencies
  - arrow, parquet crates; numpy; pyo3; rayon
- Acceptance Criteria
  - Functions available; tests/benchmarks passing; CLI leverages fast-path when available
- Risks/Mitigations
  - Binary incompatibilities → pin versions; provide meaningful fallbacks and logging

### P1. Rust Workflow Engine Integration
- Current
  - Python wrappers expect `_rustic.workflow_rust_available`, `execute_step`, `create_dag`, `execute_workflow`, `workflow_metrics`
- Gaps
  - Ensure bindings exported; end-to-end example; progress/cancellation plumbing; CLI tie-in
- Work Items
  - Bindings + example workflow; smoke tests; benchmark DAG executor; update docs/workflow-engine.md
- Dependencies
  - pf-workflow-core; pyo3; rayon/crossbeam; optional tokio
- Acceptance Criteria
  - E2E run via Rust engine with progress/cancellation shown; docs updated
- Risks/Mitigations
  - Threading/GIL nuances → explicit allow_threads in bindings; deterministic tests

### P1. Permissions (Zanzibar) Tutorial
- Current
  - API surface documented; examples exist in broader docs
- Gaps
  - Cohesive tutorial + example app (relation tuples, roles, expand/list/check)
- Work Items
  - Tutorial page; sample data; commands; cross-links to CLI
- Acceptance Criteria
  - Tutorial runnable locally and referenced from permissions index

### P1. Entity Framework – Advanced Patterns
- Current
  - Decorator-based entities, relations, GraphAr integration
- Gaps
  - Many-to-many; inheritance; advanced queries
- Work Items
  - Advanced examples/tutorial; update entity index; tests for examples
- Acceptance Criteria
  - Runnable examples and clear docs

### P1. Documentation Placeholders
- Files
  - docs/yaml-workflows/advanced.md
  - docs/sql-support/duckdb.md
  - docs/sql-support/databases.md
  - docs/bioframe-integration/index.md
  - docs/testing-quality/index.md
- Work Items
  - Author/complete with runnable snippets; cross-linking; ensure mkdocs strict build passes
- Acceptance Criteria
  - All placeholders replaced; nav and links valid

### P2. AI: Notebook + CLI Walkthrough
- Gaps
  - Add `examples/ai-data-exploration.ipynb` and unify CLI walkthrough
- Work Items
  - Notebook with DataContext + LLMAgent usage; CLI transcript; screenshots optional
- Acceptance Criteria
  - Notebook executes; CLI reproducible on local env

### P2. Cloud S3 Minimal Support
- Gaps
  - Minimal helpers + docs; auth patterns (env/IAM)
- Work Items
  - `read_parquet_s3`/`write_parquet_s3` using fsspec/s3fs; docs/cloud-integration/aws-s3.md; note GCS/Azure later
- Acceptance Criteria
  - Helper functions and docs validated locally

### P2. Multi-Format Polish
- Gaps
  - Broaden examples/tests; clarify engine selection interplay across CSV/JSON/ORC/Avro
- Work Items
  - Expand tests/docs; performance notes; feature matrix update as needed
- Acceptance Criteria
  - Clear user guidance with runnable snippets

### P3. Monitoring & Metrics
- Gaps
  - Emit metrics and provide minimal dashboard
- Work Items
  - Define metrics; implement counters/timers; Streamlit/Dash prototype
- Acceptance Criteria
  - Concept doc and prototype checked in

### P3. Visualization Convenience API
- Gaps
  - `.plot()` façade that stays backend-agnostic
- Work Items
  - API design doc; extras gating; thin wrappers; examples
- Acceptance Criteria
  - Concept doc accepted; issues for prototype

### P3. Streaming Patterns
- Gaps
  - Document patterns for huge files (batch iteration, memory map) with Dask/Polars
- Work Items
  - Examples; limitations; guidance
- Acceptance Criteria
  - Concept doc + examples merged

---

## Cross-Cutting
- Docs coherence & cross-links; feature matrix reconciliation
- Release notes and versioning discipline for beta → stable

## Tracking
- Labels: phase3 + area (rust, docs, ai, permissions, workflows, sql, cloud)
- PR titles: conventional commits (e.g., `docs(phase3): ...`, `feat(io-rust): ...`)

## Validation Gates (applies broadly)
- mkdocs build --strict passes
- pytest -q green; cargo test -q green (workspace)
- ruff check .; black --check .; mypy (relaxed config) clean
