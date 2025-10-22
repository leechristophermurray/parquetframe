#!/usr/bin/env python3
"""Fix broken documentation links comprehensively."""

import re
from pathlib import Path

# Common broken link patterns and their corrections
LINK_FIXES: dict[str, str] = {
    # Old paths that need updating
    "tutorials/todo-kanban-walkthrough.md": "documentation-examples/todo-kanban-example.md",
    "phase2/MIGRATION_GUIDE.md": "legacy-migration/migration-guide.md",
    "quickstart.md": "getting-started/quickstart.md",
    "installation.md": "getting-started/installation.md",
    "cli/index.md": "cli-interface/index.md",
    "workflows/index.md": "yaml-workflows/index.md",
    "graph/index.md": "graph-processing/index.md",
    "permissions/index.md": "permissions-system/index.md",
    "api/core.md": "documentation-examples/api-core.md",
    "legacy/legacy-basic-usage.md": "legacy-migration/phase1-usage.md",
    "legacy/legacy-backends.md": "legacy-migration/phase1-backends.md",
    # Phase 1/2 references
    "phase1-advanced.md": "legacy-migration/phase1-overview.md",
    "backends.md": "legacy-migration/phase1-backends.md",
    "advanced.md": "legacy-migration/phase1-overview.md",
    "usage.md": "legacy-migration/phase1-usage.md",
    # AI features
    "../ai-features.md": "../ai-powered-features/index.md",
    "ai-features.md": "ai-powered-features/index.md",
    "../cli/interactive.md": "../cli-interface/interactive.md",
    "cli/interactive.md": "cli-interface/interactive.md",
    "queries.md": "nl-queries.md",
    # Analytics
    "../analytics-statistics/benchmarking.md": "../analytics-statistics/benchmarks.md",
    "analytics-statistics/benchmarking.md": "analytics-statistics/benchmarks.md",
    "benchmarks.md": "analytics-statistics/benchmarks.md",
    # Graph processing
    "adjacency.md": "graphar-format.md",
    "graphar.md": "graphar-format.md",
    "performance.md": "index.md",
    # Examples and tutorials
    "tutorials/large-data.md": "documentation-examples/large-datasets.md",
    "../documentation-examples/examples.md": "../documentation-examples/examples-gallery.md",
    # Permissions
    "getting-started.md": "index.md",
    "models.md": "schema-spec.md",
    "api-reference.md": "cli-reference.md",
    # SQL
    "../backends.md": "../legacy-migration/phase1-backends.md",
    "../cli/index.md": "../cli-interface/index.md",
    # Documentation examples
    "cli/commands.md": "cli-interface/commands.md",
    "user-guide/quickstart.md": "getting-started/quickstart.md",
    "user-guide/entities.md": "entity-framework/index.md",
    "phase2/USER_GUIDE.md": "legacy-migration/phase2-user-guide.md",
    "api/entities.md": "documentation-examples/api-entities.md",
    "api/permissions.md": "documentation-examples/api-permissions.md",
    # Context files (remove these links)
    "../../CONTEXT_RUSTIC.md": "",
    "../CONTEXT_RUSTIC.md": "",
    "../../PHASE_2_PROGRESS.md": "",
    "../../CONTRIBUTING.md": "contributing.md",
    # License and external
    "../../LICENSE": "https://github.com/leechristophermurray/parquetframe/blob/main/LICENSE",
    "../examples/": "documentation-examples/examples-gallery.md",
}


def fix_links_in_file(file_path: Path) -> tuple[bool, set[str]]:
    """Fix links in a single file.

    Returns:
        Tuple of (was_modified, unfixed_links)
    """
    content = file_path.read_text(encoding="utf-8")
    updated = content
    unfixed = set()

    for old_pattern, new_pattern in LINK_FIXES.items():
        # Handle removal of CONTEXT links
        if not new_pattern:
            # Remove the entire link
            pattern = rf"\[([^\]]+)\]\({re.escape(old_pattern)}\)"
            if re.search(pattern, updated):
                updated = re.sub(pattern, r"\1 (removed broken link)", updated)
                continue

        # Normal link replacement
        pattern = rf"\[([^\]]+)\]\({re.escape(old_pattern)}\)"
        if re.search(pattern, updated):
            replacement = rf"[\1]({new_pattern})"
            updated = re.sub(pattern, replacement, updated)

    # Look for remaining broken links (for reporting)
    broken_patterns = [
        r"\[([^\]]+)\]\(((?:\.\.\/)+[^\)]+\.md)\)",  # Relative paths
        r"\[([^\]]+)\]\(([^:\)]+\.md)\)",  # Simple paths
    ]
    for pattern in broken_patterns:
        matches = re.findall(pattern, updated)
        for match in matches:
            if len(match) >= 2:
                link = match[1]
                # Skip if it's a known good pattern
                if not any(
                    good in link
                    for good in [
                        "getting-started/",
                        "core-features/",
                        "rust-acceleration/",
                        "graph-processing/",
                        "permissions-system/",
                        "yaml-workflows/",
                        "cli-interface/",
                        "legacy-migration/",
                    ]
                ):
                    unfixed.add(link)

    if updated != content:
        file_path.write_text(updated, encoding="utf-8")
        return True, unfixed
    return False, unfixed


def main():
    """Run link fixes on all markdown files."""
    docs_dir = Path("docs")
    updated_files = []
    all_unfixed = set()

    for md_file in docs_dir.rglob("*.md"):
        # Skip CONTEXT and WARP files
        if "CONTEXT" in md_file.name or "WARP" in md_file.name:
            continue

        modified, unfixed = fix_links_in_file(md_file)
        if modified:
            updated_files.append(md_file)
            print(f"✓ Updated: {md_file.relative_to(docs_dir)}")
        if unfixed:
            all_unfixed.update(unfixed)

    print(f"\n{'='*60}")
    print(f"Updated {len(updated_files)} files")

    if all_unfixed:
        print(f"\n⚠  {len(all_unfixed)} unique link patterns still need manual review:")
        for link in sorted(all_unfixed)[:20]:  # Show first 20
            print(f"  - {link}")
        if len(all_unfixed) > 20:
            print(f"  ... and {len(all_unfixed) - 20} more")


if __name__ == "__main__":
    main()
