# Documentation Contribution Guidelines (Phase 3)

These guidelines ensure a consistent, high-quality documentation experience.

## Style and Structure
- Use MkDocs Material conventions already configured in `mkdocs.yml`
- Prefer concise headings, overviews, and runnable examples
- Cross-link related sections using relative links (e.g., `../yaml-workflows/index.md`)

## Content Hygiene
- Do not reference local-only planning or private documents
- Keep all public plans under `docs/phase3/`
- Keep examples minimal, runnable, and version-appropriate

## Commit Discipline
- Use Conventional Commits, e.g.:
  - `docs(phase3): add gap plan and continuing plan`
  - `docs(permissions): add tutorial with examples`
- Make small, focused commits with clear intent

## Validation
- Build docs locally: `mkdocs build`
- Preview locally: `mkdocs serve`
- Fix broken links and unresolved references before opening PRs

## Templates
- Use the templates in `docs/phase3/templates/` to keep planning docs consistent

## Review
- Request review from maintainers of the affected area (rust, ai, permissions, workflows, sql)
- Address feedback promptly and keep changes scoped
