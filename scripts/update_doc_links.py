#!/usr/bin/env python3
"""Update internal documentation links after restructure."""

import re
from pathlib import Path

# Mapping of old paths to new paths
PATH_MAPPING: dict[str, str] = {
    # Legacy files
    "phase2/README.md": "legacy-migration/phase2-user-guide.md",
    "../getting-started/migration.md": "../legacy-migration/migration-guide.md",
    "MIGRATION_GUIDE.md": "legacy-migration/migration-guide.md",
    "USER_GUIDE.md": "legacy-migration/phase2-user-guide.md",
    "API_REFERENCE.md": "documentation-examples/api-reference.md",
    "../tutorials/todo-kanban-walkthrough.md": "../documentation-examples/tutorials.md",
    "advanced.md": "phase1-advanced.md",
    "performance.md": "../analytics-statistics/benchmarking.md",
    # Graph processing files
    "graphframe.md": "index.md",
    "collections.md": "adjacency.md",
    "cli.md": "../cli-interface/commands.md",
    "tutorial.md": "tutorial.md",
    "optimization.md": "performance.md",
    "examples.md": "../documentation-examples/examples.md",
    "../api/graph.md": "../documentation-examples/api-reference.md",
}


def update_links_in_file(file_path: Path) -> bool:
    """Update links in a single file.

    Returns:
        True if file was modified, False otherwise
    """
    content = file_path.read_text(encoding="utf-8")
    updated = content

    for old_path, new_path in PATH_MAPPING.items():
        # Update markdown links [text](path)
        pattern = rf"\[([^\]]+)\]\({re.escape(old_path)}\)"
        replacement = rf"[\1]({new_path})"
        updated = re.sub(pattern, replacement, updated)

    if updated != content:
        file_path.write_text(updated, encoding="utf-8")
        return True
    return False


def main():
    """Run link updates on all markdown files."""
    docs_dir = Path("docs")
    updated_files = []

    for md_file in docs_dir.rglob("*.md"):
        if update_links_in_file(md_file):
            updated_files.append(md_file)
            print(f"✓ Updated: {md_file.relative_to(docs_dir)}")

    print(f"\n{'='*60}")
    print(f"Updated {len(updated_files)} files")

    if updated_files:
        print("\nUpdated files:")
        for f in updated_files:
            print(f"  - {f.relative_to(docs_dir)}")


if __name__ == "__main__":
    main()
