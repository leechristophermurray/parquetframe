# Continuing Plan (Phase 3)

This execution plan is derived from the Gap Plan. It sequences milestones, adds checklists, and defines validation and Definition of Done (DoD).

## Milestones & Checklists

### M1. Phase 3 docs sync (short)
- [x] Update docs/phase3/gap-plan-phase3.md and continuing-plan-phase3.md (sanitized)
- [x] Verify mkdocs nav/cross-links
- [x] Build with `mkdocs build --strict`
- DoD: sanitized plans in repo; build passes; no private refs

### M2. Fill high-value placeholders (short)
- [x] Author docs/yaml-workflows/advanced.md (variables, conditionals, retries/timeouts, resource hints, progress/cancel, Rust executor usage)
- [x] Author docs/sql-support/duckdb.md (registration, joins, EXPLAIN/validate, tips)
- [x] Author docs/sql-support/databases.md (URIs, auth, pooling, safe configs)
- [x] Improve docs/bioframe-integration/index.md (overlap/coverage/cluster examples)
- [x] Author docs/testing-quality/index.md (strategy; py/rust tests; coverage; ruff/black/mypy; CI)
- DoD: pages contain runnable snippets; links valid; build passes

### M3. Permissions tutorial + Entity advanced examples (short/medium)
- [x] Permissions tutorial (relation tuples, roles, expand, list_objects/list_subjects, check) integrated with example
- [x] Entity advanced (many-to-many, inheritance, queries) with runnable examples
- [x] Add to examples gallery and cross-link from indexes
- DoD: examples run locally; CI smoke tests OK

### M4. Rust distribution & contributor guide (medium)
- [x] Draft CI matrix (maturin wheels) and smoke import plan
- [x] Write contributor dev/bench guide (layout, building, cargo test/bench, pyo3 notes)
- [x] Dry-run wheel build; record results
- DoD: docs approved; issues created for CI implementation; dry-run validated

### M5. AI notebook + CLI walkthrough (medium)
- [x] Create `examples/ai-data-exploration.ipynb`
- [x] Expand CLI walkthrough with end-to-end transcript
- DoD: notebook executes; CLI steps reproducible

### M6. Cloud S3 minimal helpers + docs (medium)
- [x] Prototype `read_parquet_s3` / `write_parquet_s3` (fsspec/s3fs)
- [x] Author docs/cloud-integration/aws-s3.md (auth patterns, examples)
- DoD: helpers validated locally; doc approved; issues filed for GCS/Azure

### M7. Monitoring & Visualizations concepts (long)
- [x] Metrics surface (latency, memory, error rates); demo dashboard
- [x] Visualization convenience API design doc
- DoD: concept docs accepted; prototype issues created

## Validation Gates (all milestones)
- mkdocs build --strict
- pytest -q; cargo test -q (workspace)
- ruff check .; black --check .; mypy (relaxed)
- Examples in docs execute or are clearly marked as upcoming

## Risk Register (selected)
- Wheel matrix complexity → iterate; start with manylinux + macOS ARM/Intel; add Windows after
- S3 auth pitfalls → document env/IAM patterns clearly; provide safe defaults
- Visualization backend lock-in → API façade, extras-gated optional deps

## Labels & Tracking
- Use labels: phase3 + area (rust, docs, ai, permissions, workflows, sql, cloud)
- Conventional commits for PRs; small, focused changes

## Non-Goals (this phase)
- Distributed Rust scheduler beyond single-node
- GPU acceleration (tracked as future)
