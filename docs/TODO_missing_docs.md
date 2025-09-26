# Documentation Audit - Missing Files and Issues

## Missing Files Referenced in mkdocs.yml Navigation

### AI Features Section
- [ ] `docs/ai/queries.md` - Natural Language Queries documentation
- [ ] `docs/ai/setup.md` - Local LLM Setup guide
- [ ] `docs/ai/prompts.md` - Prompt Engineering documentation

### SQL & Database Section
- [ ] `docs/sql/index.md` - SQL Support overview
- [ ] `docs/sql/duckdb.md` - DuckDB Integration guide
- [ ] `docs/sql/databases.md` - Database Connections documentation

### Genomics & BioFrame Section
- [ ] `docs/bio/index.md` - BioFrame Integration overview
- [ ] `docs/bio/operations.md` - Genomic Operations documentation
- [ ] `docs/bio/parallel.md` - Parallel Processing guide

### Workflow System Section
- [ ] `docs/workflows/advanced.md` - Advanced workflow features
- [ ] `docs/workflows/examples.md` - Workflow examples gallery
- [ ] Missing: `docs/workflows/yaml-syntax.md` - Referenced in workflow index but not in nav

### Project Assessment Section
- [ ] `docs/reports/parquetframe_assessment.md` - Comprehensive project assessment
- [ ] `docs/feature_implementation_matrix.md` - Feature implementation status matrix
- [ ] `docs/architecture_diagram.md` - Architecture visualization

## Directory Structure Creation Needed

These directories need to be created:
- `docs/ai/`
- `docs/sql/`
- `docs/bio/`
- `docs/reports/`

## Orphaned Files in Root Directory

Files that may need to be integrated into docs structure:
- `feature_implementation_matrix.md` (exists in root, referenced in nav)
- Other assessment files

## Broken Internal Links Identified (17 total)

### In workflows/index.md:
- Links to missing `yaml-syntax.md`
- Links to missing `advanced.md`
- Links to missing `examples.md`

### In api/ directory:
- Incorrect relative path references (`../cli/index.md` resolving outside docs)
- Links in api/cli.md and api/core.md need path corrections

### In tutorials/ directory:
- Multiple broken relative links (`../usage.md`, `../advanced.md`, etc.)
- Links in integration.md, performance.md, ml-pipeline.md, exploration.md

## Resolution Strategy

1. **Create missing directory structure**
2. **Create placeholder files with basic content**
3. **Fix broken relative links using correct paths**
4. **Move root-level files to appropriate docs locations**
5. **Validate all links after corrections**

## Notes

- Total missing files: 14
- Total broken internal links: 17
- Priority: Fix navigation structure first, then internal linking
