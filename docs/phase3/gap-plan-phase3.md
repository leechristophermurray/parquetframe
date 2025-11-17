# Gap Plan (Phase 3)

Focused, actionable gap analysis aligned with v2.0.0-beta and the current repository state. All items are commit-safe and avoid private planning references.

## Legend
- Status: NS (Not Started), P (Planned), IP (In Progress), D (Done)
- Priority: P1 (high), P2 (medium), P3 (lower)

---

## 1) Rust Acceleration Distribution (P1, Status: P)
- Gaps
  - Prebuilt wheels (Linux manylinux, macOS x86_64/aarch64, Windows) not yet published
  - Release CI for maturin build/test/signing not documented in docs
- Work Items
  - Define CI matrix for wheels (maturin) and smoke tests; verify `pyo3/extension-module` wheels import on all platforms
  - Document release procedure and troubleshooting (link from Rust Acceleration → Architecture)
- Acceptance Criteria
  - CI plan and docs exist; dry-run release produces testable wheels; installation docs updated

## 2) Rust I/O Fast-Paths (Parquet/CSV/Avro) (P1, Status: P)
- Current State
  - Metadata paths are wired via `_rustic` (read_parquet_metadata_rust, get_row_count, column names/stats)
  - Full readers in Python wrappers check for `_rustic` functions and raise NotImplementedError if missing
- Gaps
  - Implement and export `_rustic.read_parquet_fast` and `_rustic.read_csv_fast` (+ Avro) with Arrow zero-copy, GIL release, and parallelism
  - Unify CLI fast-path usage and document graceful fallback
- Work Items
  - Implement Rust functions and PyO3 bindings; add Python wrappers/tests/benchmarks; update docs/rust-acceleration/io-fastpaths.md with current status
- Acceptance Criteria
  - Fast-path functions available and covered by tests/benchmarks; CLI and docs reflect behavior/fallback

## 3) Rust Workflow Engine Integration (P1, Status: IP)
- Current State
  - Python bindings export `_rustic.workflow_rust_available`, `create_dag`, `execute_workflow`, `workflow_metrics` and support progress/cancellation hooks; Python step_handler is wired for real step execution
- Gaps
  - CLI tie-in (optional) for invoking workflows with progress; additional examples; performance benchmarking docs
- Work Items
  - Add CLI workflow subcommands (optional), more examples; benchmark DAG executor; update docs where needed
- Acceptance Criteria
  - End-to-end workflow executes via Rust engine with progress/cancellation and custom step handlers; docs updated; optional CLI usage documented

## 4) Entity Framework – Advanced Patterns (P1, Status: P)
- Gaps
  - Many-to-many relationships, inheritance, richer query examples
- Work Items
  - Author advanced examples/tutorial; add runnable snippets and cross-links from entity-framework index
- Acceptance Criteria
  - Docs include advanced scenarios with runnable examples

## 5) Permissions (Zanzibar/ReBAC) Tutorial (P1, Status: P)
- Gaps
  - End-to-end tutorial with realistic scenario (relation tuples, roles, expand, list_objects/list_subjects, check)
- Work Items
  - Tutorial + example app integration (e.g., Todo/Kanban); link from permissions-system index and examples gallery
- Acceptance Criteria
  - Tutorial runs locally and is discoverable from the permissions section

## 6) Documentation Placeholders (P1, Status: P)
- Files to complete
  - `docs/yaml-workflows/advanced.md`
  - `docs/sql-support/duckdb.md`
  - `docs/sql-support/databases.md`
  - `docs/bioframe-integration/index.md`
  - `docs/testing-quality/index.md`
- Acceptance Criteria
  - Each placeholder replaced with concrete guidance, examples, and links; `mkdocs build --strict` passes

## 7) AI-Powered Exploration: Notebook + CLI Walkthrough (P2, Status: P)
- Gaps
  - Executable notebook and unified CLI walkthrough
- Work Items
  - Add `examples/ai-data-exploration.ipynb`; expand CLI examples with an end-to-end session
- Acceptance Criteria
  - Notebook executes locally; CLI steps reproducible

## 8) Cloud Storage Integration (S3-first) (P2, Status: NS)
- Gaps
  - Minimal S3 read/write utilities and docs (auth patterns, env/IAM)
- Work Items
  - Prototype `read_parquet_s3` / `write_parquet_s3`; author `docs/cloud-integration/aws-s3.md`; note GCS/Azure follow-on
- Acceptance Criteria
  - Docs approved; minimal helpers validated; follow-up issues for other providers

## 9) Multi-Format Polish (CSV/JSON/ORC/Avro) (P2, Status: P)
- Gaps
  - Broaden examples/tests, clarify engine selection interactions and options
- Work Items
  - Extend tests/docs; performance notes; update feature matrix if needed
- Acceptance Criteria
  - Clear user guidance and tests for all supported formats

## 10) Real-time Monitoring & Metrics (P3, Status: NS)
- Gaps
  - Expose basic metrics (latency, memory, error rates) and a simple dashboard
- Work Items
  - Define metrics surface and a small demo (e.g., Streamlit/Dash)
- Acceptance Criteria
  - Concept doc & minimal demo checked in; issues created for productionization

## 11) Visualization Convenience API (P3, Status: NS)
- Gaps
  - Lightweight `.plot()` layer without locking users to a single backend
- Work Items
  - Propose API surface, extras gating, and examples; keep backend-agnostic
- Acceptance Criteria
  - Concept doc approved; issues filed for prototype

## 12) Streaming Capabilities (P3, Status: NS)
- Gaps
  - Streaming/batch-iterative patterns for very large files
- Work Items
  - Document patterns with Dask/Polars; examples and limitations
- Acceptance Criteria
  - Concept doc + examples; issues for future enhancements

---

## Risk Notes
- Wheel publishing matrix and manylinux nuances may require iteration
- S3 auth patterns must be clearly documented to avoid misconfiguration
- Visualization API should avoid vendor lock-in and heavy deps by default

## Tracking
- Each item maps to issues/PRs labeled by area (rust, docs, ai, permissions, workflows, sql, cloud) and phase3; links added in PR descriptions
