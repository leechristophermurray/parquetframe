# Continuing Plan (Phase 3)

Execution plan to close v2.0.0-beta gaps with clear milestones, acceptance criteria, and validation gates.

## Milestones

### M1: Phase 3 docs sync (short)
- Tasks
  - Ensure sanitized planning docs under `docs/phase3/` reflect current scope (Gap Plan + Continuing Plan)
  - Verify navigation and cross-links
- Acceptance Criteria
  - `mkdocs build --strict` passes; Phase 3 appears in nav; links valid; no private files referenced

### M2: Fill high-value placeholders (short)
- Tasks
  - Author: `docs/yaml-workflows/advanced.md`
  - Author: `docs/sql-support/duckdb.md`, `docs/sql-support/databases.md`
  - Improve: `docs/bioframe-integration/index.md`, `docs/testing-quality/index.md`
- Acceptance Criteria
  - Pages contain runnable patterns and cross-links; build passes

### M3: Permissions tutorial + Entity advanced examples (short/medium)
- Tasks
  - Add permissions tutorial (relation tuples, roles, expand, list_objects/list_subjects, check)
  - Author entity framework advanced examples (many-to-many, inheritance, queries)
- Acceptance Criteria
  - Examples run locally; referenced from index pages and examples gallery

### M4: Rust distribution & contributor guide (medium)
- Tasks
  - Document CI matrix for maturin wheels; add contributor development/benchmarking guide
  - Dry-run wheel build + import smoke tests (documented)
- Acceptance Criteria
  - Docs approved; issues created for CI implementation; dry-run validated

### M5: AI example notebook + CLI walkthrough (medium)
- Tasks
  - Add `examples/ai-data-exploration.ipynb`; unify CLI walkthrough
- Acceptance Criteria
  - Notebook executes end-to-end; CLI steps reproducible

### M6: Cloud (S3) minimal helpers + docs (medium)
- Tasks
  - Author `docs/cloud-integration/aws-s3.md`; outline `read_parquet_s3`/`write_parquet_s3`
- Acceptance Criteria
  - Doc approved; minimal helpers validated; follow-up issues for GCS/Azure

### M7: Monitoring & Visualizations concepts (long)
- Tasks
  - Draft metrics exposure + dashboard concept; propose visualization convenience API
- Acceptance Criteria
  - Concept docs accepted; prototype issues filed

## Quality Gates
- MkDocs Material style and consistent headings
- Internal links maintained; no references to private/local planning files
- Conventional commits for documentation changes

## Validation
- Build: `mkdocs build --strict`
- Local review: `mkdocs serve`
- Link checks: run a link checker and fix broken references
- Optional: smoke `pytest -q` and `cargo test -q` for referenced examples
