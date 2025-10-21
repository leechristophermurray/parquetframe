# Documentation Restructure Mapping (v2.0.0a5 → Feature Tree)

**Status**: Planning Phase
**Date**: 2025-10-21
**Current Files**: 76 markdown files across 21 directories
**Target**: 14 feature category directories

---

## Overview

This document maps the current documentation structure to the new feature-tree-aligned organization. The goal is to reorganize all 76 docs into 14 main categories that match ParquetFrame's feature hierarchy.

---

## Current File → New Location Mapping

### 1. Core Features (`docs/core-features/`)

**Index**: `docs/core-features/index.md` (NEW - to be written)

**Files to Move/Rename**:
- `docs/backends.md` → `docs/core-features/multi-engine.md`
- `docs/formats.md` → `docs/core-features/file-formats.md`
- `docs/phase2/USER_GUIDE.md` → `docs/core-features/user-guide.md`
- `docs/usage.md` → `docs/core-features/basic-usage.md`
- `docs/advanced.md` → `docs/core-features/advanced-usage.md`

**Files to Create**:
- `docs/core-features/configuration.md` (extract from existing docs)
- `docs/core-features/data-types.md` (NEW)

---

### 2. Rust Acceleration (`docs/rust-acceleration/`)

**Index**: `docs/rust-acceleration/index.md` (NEW - comprehensive overview)

**Files to Move/Rename**:
- `docs/rust/index.md` → `docs/rust-acceleration/overview.md`

**Files to Create** (Priority - Phase 3.5-3.6 focus):
- `docs/rust-acceleration/architecture.md` (NEW - ~1200 words)
- `docs/rust-acceleration/io-fastpaths.md` (NEW - ~1500 words)
- `docs/rust-acceleration/graph-algorithms.md` (NEW - ~1800 words)
- `docs/rust-acceleration/workflow-engine.md` (NEW - ~1600 words)
- `docs/rust-acceleration/performance.md` (NEW - ~1400 words)
- `docs/rust-acceleration/development.md` (NEW - ~1000 words)

---

### 3. Graph Processing (`docs/graph-processing/`)

**Index**: `docs/graph-processing/index.md` (existing `docs/graph/index.md`)

**Files to Move/Rename**:
- `docs/graph/index.md` → `docs/graph-processing/index.md`
- `docs/graph/cli.md` → `docs/graph-processing/cli.md`
- `docs/graph/tutorial.md` → `docs/graph-processing/tutorial.md`
- `docs/guides/graphar_migration_guide.md` → `docs/graph-processing/graphar-migration.md`

**Files to Create**:
- `docs/graph-processing/graphar.md` (extract from index.md)
- `docs/graph-processing/adjacency.md` (NEW - CSR/CSC structures)
- `docs/graph-processing/algorithms.md` (NEW - BFS, PageRank, Dijkstra, etc.)

---

### 4. Permissions System (`docs/permissions-system/`)

**Index**: `docs/permissions-system/index.md` (existing `docs/permissions/index.md`)

**Files to Move/Rename**:
- `docs/permissions/index.md` → `docs/permissions-system/index.md`
- `docs/permissions/cli-reference.md` → `docs/permissions-system/cli-reference.md`
- `docs/specs/permissions_graphar_schema.md` → `docs/permissions-system/graphar-schema.md`
- `docs/specs/graphar_permissions_schema.md` → `docs/permissions-system/schema-spec.md`

**Files to Create**:
- `docs/permissions-system/zanzibar.md` (NEW - ReBAC concepts)
- `docs/permissions-system/apis.md` (NEW - check, expand, list_objects, list_subjects)
- `docs/permissions-system/models.md` (NEW - standard permission models)

---

### 5. Entity Framework (`docs/entity-framework/`)

**Index**: `docs/entity-framework/index.md` (NEW)

**Files to Create** (All NEW - Phase 2 feature):
- `docs/entity-framework/index.md` (~800 words)
- `docs/entity-framework/modeling.md` (~1000 words)
- `docs/entity-framework/decorators.md` (~1200 words - @entity, @rel)
- `docs/entity-framework/relationships.md` (~900 words)
- `docs/entity-framework/persistence.md` (~1100 words)

**Extract From**:
- `docs/tutorials/todo-kanban-walkthrough.md` (examples)
- `docs/api/entities.md` (API reference)

---

### 6. YAML Workflows (`docs/yaml-workflows/`)

**Index**: `docs/yaml-workflows/index.md` (existing `docs/workflows/index.md`)

**Files to Move/Rename**:
- `docs/workflows/index.md` → `docs/yaml-workflows/index.md`
- `docs/workflows/step-types.md` → `docs/yaml-workflows/step-types.md`
- `docs/workflows/yaml-syntax.md` → `docs/yaml-workflows/yaml-syntax.md`
- `docs/workflows/cli-commands.md` → `docs/yaml-workflows/cli-commands.md`
- `docs/workflows/history-analytics.md` → `docs/yaml-workflows/history-analytics.md`
- `docs/workflows/visualization.md` → `docs/yaml-workflows/visualization.md`
- `docs/workflows/advanced.md` → `docs/yaml-workflows/advanced.md`
- `docs/workflows/examples.md` → `docs/yaml-workflows/examples.md`

---

### 7. SQL Support (`docs/sql-support/`)

**Index**: `docs/sql-support/index.md` (existing `docs/sql/index.md`)

**Files to Move/Rename**:
- `docs/sql/index.md` → `docs/sql-support/index.md`
- `docs/sql/cookbook.md` → `docs/sql-support/cookbook.md`
- `docs/sql/duckdb.md` → `docs/sql-support/duckdb.md`
- `docs/sql/databases.md` → `docs/sql-support/databases.md`

**Files to Create**:
- `docs/sql-support/apis.md` (NEW - .sql() method, fluent API)
- `docs/sql-support/validation.md` (NEW - query validation, safety)

---

### 8. BioFrame Integration (`docs/bioframe-integration/`)

**Index**: `docs/bioframe-integration/index.md` (existing `docs/bio/index.md`)

**Files to Move/Rename**:
- `docs/bio/index.md` → `docs/bioframe-integration/index.md`
- `docs/bio/operations.md` → `docs/bioframe-integration/operations.md`
- `docs/bio/parallel.md` → `docs/bioframe-integration/parallel.md`

**Files to Create**:
- `docs/bioframe-integration/genomics.md` (NEW - genomic data concepts)

---

### 9. AI-Powered Features (`docs/ai-powered-features/`)

**Index**: `docs/ai-powered-features/index.md` (NEW)

**Files to Move/Rename**:
- `docs/ai-features.md` → `docs/ai-powered-features/overview.md`
- `docs/AI_USAGE.md` → `docs/ai-powered-features/usage-guide.md`
- `docs/ai/queries.md` → `docs/ai-powered-features/nl-queries.md`
- `docs/ai/setup.md` → `docs/ai-powered-features/setup.md`
- `docs/ai/prompts.md` → `docs/ai-powered-features/prompts.md`

**Files to Create**:
- `docs/ai-powered-features/index.md` (NEW - comprehensive overview)
- `docs/ai-powered-features/agents.md` (NEW - LLM agent framework)

---

### 10. CLI Interface (`docs/cli-interface/`)

**Index**: `docs/cli-interface/index.md` (existing `docs/cli/index.md`)

**Files to Move/Rename**:
- `docs/cli/index.md` → `docs/cli-interface/index.md`
- `docs/cli/installation.md` → `docs/cli-interface/installation.md`
- `docs/cli/commands.md` → `docs/cli-interface/commands.md`
- `docs/cli/interactive.md` → `docs/cli-interface/interactive.md`
- `docs/cli/batch.md` → `docs/cli-interface/batch.md`
- `docs/cli/scripts.md` → `docs/cli-interface/scripts.md`
- `docs/cli/examples.md` → `docs/cli-interface/examples.md`

---

### 11. Analytics & Statistics (`docs/analytics-statistics/`)

**Index**: `docs/analytics-statistics/index.md` (NEW)

**Files to Move/Rename**:
- `docs/analytics.md` → `docs/analytics-statistics/statistics.md`
- `docs/timeseries.md` → `docs/analytics-statistics/timeseries.md`
- `docs/benchmarks.md` → `docs/analytics-statistics/benchmarks.md`

**Files to Create**:
- `docs/analytics-statistics/index.md` (NEW)
- `docs/analytics-statistics/performance-monitoring.md` (NEW)

---

### 12. Documentation & Examples (`docs/documentation-examples/`)

**Index**: `docs/documentation-examples/index.md` (NEW)

**Files to Move/Rename**:
- `docs/tutorials/exploration.md` → `docs/documentation-examples/data-exploration.md`
- `docs/tutorials/integration.md` → `docs/documentation-examples/integration-guide.md`
- `docs/tutorials/large-data.md` → `docs/documentation-examples/large-datasets.md`
- `docs/tutorials/ml-pipeline.md` → `docs/documentation-examples/ml-pipelines.md`
- `docs/tutorials/performance.md` → `docs/documentation-examples/performance-optimization.md`
- `docs/tutorials/todo-kanban-walkthrough.md` → `docs/documentation-examples/todo-kanban-example.md`
- `docs/examples.md` → `docs/documentation-examples/examples-gallery.md`
- `docs/api/core.md` → `docs/documentation-examples/api-core.md`
- `docs/api/entities.md` → `docs/documentation-examples/api-entities.md`
- `docs/api/permissions.md` → `docs/documentation-examples/api-permissions.md`
- `docs/api/cli.md` → `docs/documentation-examples/api-cli.md`

**Files to Create**:
- `docs/documentation-examples/index.md` (NEW)
- `docs/documentation-examples/best-practices.md` (NEW)

---

### 13. Testing & Quality (`docs/testing-quality/`)

**Index**: `docs/testing-quality/index.md` (NEW)

**Files to Create** (All NEW):
- `docs/testing-quality/index.md` (~600 words)
- `docs/testing-quality/test-suites.md` (~1000 words - unit, integration, etc.)
- `docs/testing-quality/quality-standards.md` (~800 words - coverage, linting)
- `docs/testing-quality/cicd.md` (~900 words - GitHub Actions, tox)

---

### 14. Legacy & Migration (`docs/legacy-migration/`)

**Index**: `docs/legacy-migration/index.md` (NEW)

**Files to Move/Rename**:
- `docs/legacy/README.md` → `docs/legacy-migration/phase1-overview.md`
- `docs/legacy/legacy-basic-usage.md` → `docs/legacy-migration/phase1-usage.md`
- `docs/legacy/legacy-backends.md` → `docs/legacy-migration/phase1-backends.md`
- `docs/phase2/MIGRATION_GUIDE.md` → `docs/legacy-migration/phase1-to-phase2.md`
- `docs/getting-started/migration.md` → `docs/legacy-migration/migration-guide.md`
- `docs/changelog.md` → `docs/legacy-migration/changelog.md`

**Files to Create**:
- `docs/legacy-migration/index.md` (NEW)
- `docs/legacy-migration/versions.md` (NEW - version history)

---

## Getting Started Section (Special - Keep Separate)

**Location**: `docs/getting-started/`

**Files to Keep/Create**:
- `docs/installation.md` → `docs/getting-started/installation.md`
- `docs/quickstart.md` → `docs/getting-started/quickstart.md`
- `docs/first-steps.md` → `docs/getting-started/first-steps.md`

---

## Top-Level Files (Keep in `docs/`)

- `docs/index.md` - Home page (UPDATE with new navigation)
- `docs/contributing.md` - Keep as-is
- `docs/performance.md` - Keep (reference from multiple categories)

---

## Files to Archive/Remove

**Move to `docs/_archive/`**:
- `docs/issues/phase2-test-migration.md` (internal dev doc)
- `docs/adr/` directory (keep as-is, but consider linking from development section)

**Assets to Keep**:
- `docs/assets/` - All assets stay
- `docs/stylesheets/` - All stylesheets stay

---

## Documentation Gaps (Features w/o Docs)

### High Priority (Phase 3.5-3.6):
1. **Rust Workflow Engine** - Complete documentation needed
2. **Rust I/O Fast-Paths** - Implementation guide needed
3. **Rust Graph Algorithms** - Performance benchmarks needed
4. **Entity Framework** - Comprehensive guide needed (Phase 2 feature)

### Medium Priority:
5. **Configuration System** - `set_config()` API documentation
6. **Data Contexts** - Database and Parquet context docs
7. **Performance Monitoring** - Real-time metrics and dashboards

### Low Priority:
8. **Streaming Support** - (Phase 4 feature - placeholder)
9. **Cloud Integration** - (Phase 4 feature - placeholder)

---

## New Content to Write (~15,000 words)

### Rust Acceleration (Phase 3.5-3.6 Focus):
- `architecture.md` - 1,200 words
- `io-fastpaths.md` - 1,500 words
- `graph-algorithms.md` - 1,800 words
- `workflow-engine.md` - 1,600 words
- `performance.md` - 1,400 words
- `development.md` - 1,000 words
**Subtotal**: ~8,500 words

### Entity Framework:
- `index.md` - 800 words
- `modeling.md` - 1,000 words
- `decorators.md` - 1,200 words
- `relationships.md` - 900 words
- `persistence.md` - 1,100 words
**Subtotal**: ~5,000 words

### Other Categories (Index Pages):
- 12 category index pages × ~200 words = ~2,400 words

**Total New Content**: ~15,900 words

---

## Migration Strategy

### Phase 1: Setup (30 min)
1. Create 14 category directories
2. Create placeholder index.md files
3. Commit directory structure

### Phase 2: File Migration (2 hours)
1. Move files using `git mv` (preserves history)
2. Rename for consistency
3. One commit per category

### Phase 3: Link Updates (1 hour)
1. Create link update script
2. Run on all files
3. Manual verification

### Phase 4: Content Creation (8-10 hours)
1. Write Rust acceleration docs (priority)
2. Write Entity Framework docs
3. Write category index pages
4. Update README and index.md

### Phase 5: Validation (1 hour)
1. Run `mkdocs build --strict`
2. Fix warnings/errors
3. Test navigation

### Total Estimated Time: ~14 hours

---

## Success Criteria

✅ All 76 existing files migrated
✅ 14 category directories created
✅ ~15,000 words of new content written
✅ Zero broken links (`mkdocs build --strict` passes)
✅ Navigation restructured with tabs
✅ Mobile-responsive design verified
✅ Search functionality working

---

## Next Steps

1. ✅ Create this mapping document
2. ⏳ Create directory structure (Task 2)
3. ⏳ Migrate existing files (Task 3)
4. ⏳ Update mkdocs.yml (Task 4)
5. ⏳ Fix internal links (Task 5)
6. ⏳ Write new content (Tasks 6-7)
7. ⏳ Validate and commit (Tasks 8-9)

---

**Last Updated**: 2025-10-21
**Status**: Ready to proceed with Task 2 (Directory Creation)
