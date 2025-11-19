# Repository Inventory (Phase 3)

High-level map of key areas to help contributors find code, docs, and examples.

## Top-Level
- `pyproject.toml`: Python packaging, extras, tooling config
- `Cargo.toml`: Rust workspace members and shared dependencies
- `mkdocs.yml`: Site configuration and navigation
- `docs/`: User and developer documentation (MkDocs Material)
- `examples/`: Python and YAML workflow examples
- `crates/`: Rust workspace

## Rust Workspace (`crates/`)
- `pf-graph-core`: Graph algorithms and related utilities
- `pf-io-core`: Accelerated I/O paths
- `pf-workflow-core`: Parallel DAG workflow engine (examples under this crate)
- `pf-py`: PyO3 bridge and Python-facing module integration

## Examples (`examples/`)
- `integration/todo_kanban/`: End-to-end example app (models, permissions, workflows)
- `rust/`: Python drivers for Rust-backed features (graph, IO, workflow)
- `workflows/*.yml`: Standalone YAML workflow examples
- `phase2/`: Multi-engine demos and conversions

## Documentation (`docs/`)
- AI features: `docs/ai-powered-features/` (setup + usage)
- Permissions system: `docs/permissions-system/`
- YAML workflows: `docs/yaml-workflows/`
- SQL support: `docs/sql-support/`
- Graph processing: `docs/graph-processing/`
- BioFrame integration: `docs/bioframe-integration/`
- Development: `docs/architecture.md`, `docs/feature_implementation_matrix.md`, ADRs

## Navigation Additions (Phase 3)
- `docs/phase3/`: Durable planning documents, guidelines, templates, and metadata

## Build and Preview
- Build site: `mkdocs build`
- Serve locally: `mkdocs serve`

## Notes
- Keep private planning files out of version control; publish sanitized, commit-friendly docs under `docs/phase3/`
