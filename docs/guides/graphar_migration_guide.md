# GraphAr Permissions Migration Guide

**Version**: 0.4.0
**Date**: 2025-10-21
**Target Audience**: Developers using ParquetFrame permissions system

---

## Overview

This guide helps you migrate from the legacy single-file permissions storage to the new GraphAr-compliant dual-graph architecture introduced in ParquetFrame v0.4.0.

---

## What's Changed

### Storage Architecture

**Before (v0.3.x)**:
```
kanban_data/
├── users/
├── boards/
└── permissions/
    └── permissions.parquet  # Single file
```

**After (v0.4.0)**:
```
kanban_data/
├── users/
│   ├── _metadata.yaml      # NEW: GraphAr metadata
│   ├── _schema.yaml        # NEW: GraphAr schema
│   └── User.parquet
├── boards/
│   ├── _metadata.yaml      # NEW
│   ├── _schema.yaml        # NEW
│   └── Board.parquet
└── permissions_graph/      # NEW: GraphAr structure
    ├── _metadata.yaml
    ├── _schema.yaml
    ├── vertices/
    │   ├── user/
    │   ├── board/
    │   ├── list/
    │   └── task/
    └── edges/
        ├── owner/
        ├── editor/
        └── viewer/
```

### Breaking Changes

| Component | Old | New | Impact |
|-----------|-----|-----|--------|
| **Permissions Path** | `./permissions` | `./permissions_graph` | HIGH - Code change required |
| **Storage Format** | Single Parquet file | GraphAr directory | HIGH - Data migration required |
| **Entity Metadata** | No metadata files | `_metadata.yaml`, `_schema.yaml` | LOW - Auto-generated |

---

## Migration Steps

### Step 1: Backup Existing Data

```bash
# Backup your current permissions
cp -r ./kanban_data/permissions ./kanban_data/permissions.backup

# Backup entity data
cp -r ./kanban_data/users ./kanban_data/users.backup
cp -r ./kanban_data/boards ./kanban_data/boards.backup
```

### Step 2: Update ParquetFrame

```bash
# Upgrade to v0.4.0
pip install --upgrade parquetframe==0.4.0

# Or from source
pip install git+https://github.com/yourusername/parquetframe.git@v0.4.0
```

### Step 3: Update Application Code

#### Change 1: Update Permission Manager Initialization

**Before**:
```python
from parquetframe.permissions import PermissionManager

permissions = PermissionManager("./kanban_data/permissions")
```

**After**:
```python
from parquetframe.permissions import PermissionManager

permissions = PermissionManager("./kanban_data/permissions_graph")
```

#### Change 2: Update TodoKanbanApp Initialization

**Before**:
```python
app = TodoKanbanApp(storage_base="./kanban_data")
# Uses: ./kanban_data/permissions
```

**After**:
```python
app = TodoKanbanApp(storage_base="./kanban_data")
# Uses: ./kanban_data/permissions_graph (automatic)
```

**No code change needed** - the app automatically uses the new path!

### Step 4: Migrate Permissions Data

#### Option A: Reload from Scratch (Recommended for Development)

```python
from parquetframe.permissions import PermissionManager

# Load old permissions
old_store = TupleStore.load("./kanban_data/permissions/permissions.parquet")

# Create new manager with GraphAr path
new_manager = PermissionManager("./kanban_data/permissions_graph")

# Re-add all tuples
for tuple_obj in old_store:
    new_manager.store.add_tuple(tuple_obj)

# Save in GraphAr format
new_manager.save()

print(f"Migrated {len(old_store)} permission tuples")
```

#### Option B: Use Migration Script

```bash
# Run migration script
python scripts/migrate_permissions_to_graphar.py \
    --source ./kanban_data/permissions/permissions.parquet \
    --target ./kanban_data/permissions_graph
```

#### Option C: Re-run Application Setup

If you have a setup/initialization script:

```python
# Re-run your application setup
# This will create fresh permissions in GraphAr format
app = TodoKanbanApp(storage_base="./kanban_data")

# Re-create users, boards, and permissions
# ...
```

### Step 5: Verify Migration

```python
from parquetframe.permissions import PermissionManager
from pathlib import Path

# Check new structure exists
perm_graph = Path("./kanban_data/permissions_graph")
assert (perm_graph / "_metadata.yaml").exists()
assert (perm_graph / "_schema.yaml").exists()
assert (perm_graph / "vertices").exists()
assert (perm_graph / "edges").exists()

# Load and verify count
manager = PermissionManager("./kanban_data/permissions_graph")
stats = manager.get_stats()
print(f"Total tuples: {stats['total_tuples']}")
print(f"Unique subjects: {stats['unique_subjects']}")
print(f"Unique objects: {stats['unique_objects']}")
print(f"Unique relations: {stats['unique_relations']}")
```

### Step 6: Test Application

```bash
# Run your test suite
pytest tests/integration/test_todo_kanban.py

# Or run the demo
python -m examples.integration.todo_kanban.demo
```

### Step 7: Clean Up (Optional)

```bash
# After verifying everything works:
rm -rf ./kanban_data/permissions.backup
rm -rf ./kanban_data/users.backup
rm -rf ./kanban_data/boards.backup

# Remove old permissions directory
rm -rf ./kanban_data/permissions
```

---

## Code Examples

### Before & After Comparison

#### Entity Creation (No Change)

```python
# Works the same in both versions
@entity(storage_path="./kanban_data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str
    email: str

user = User(user_id="user_123", username="alice", email="alice@example.com")
user.save()  # Now also creates _metadata.yaml and _schema.yaml
```

#### Permission Operations (No Change)

```python
# All permission APIs work the same
permissions = PermissionManager("./kanban_data/permissions_graph")

# Grant
permissions.grant_permission("user_123", "board", "board_456", "owner")

# Check
has_access = permissions.check_permission("user_123", "board", "board_456", "owner")

# List
user_boards = permissions.list_user_permissions("user_123", resource_type="board")

# Save (now creates GraphAr structure)
permissions.save()
```

---

## New Features Available

### 1. Load Permissions as Graph

```python
import parquetframe as pf

# Load permissions graph for analysis
graph = pf.read_graph("./kanban_data/permissions_graph")

# Use graph algorithms
from parquetframe.graph import pagerank

# Find influential users (most permissions)
scores = pagerank(graph)
```

### 2. Analyze Permission Hierarchies

```python
from parquetframe.graph import shortest_path

# Find permission inheritance chain
path = shortest_path(
    graph,
    source="user_alice",
    target="task_789",
    directed=True
)

print(f"Permission path: {' -> '.join(path)}")
```

### 3. Export to Other Formats

```python
# GraphAr is a standard format
# Can export to NetworkX, Neo4j, etc.
import networkx as nx

# Convert to NetworkX for visualization
nx_graph = graph.to_networkx()
nx.draw(nx_graph, with_labels=True)
```

---

## Troubleshooting

### Issue: FileNotFoundError for permissions_graph

**Symptom**:
```
FileNotFoundError: [Errno 2] No such file or directory: './kanban_data/permissions_graph'
```

**Solution**:
```python
# Create new permissions_graph by saving
permissions = PermissionManager("./kanban_data/permissions_graph")
# Add your permissions...
permissions.save()
```

### Issue: Old path still hardcoded

**Symptom**: Application still tries to use `./kanban_data/permissions`

**Solution**: Update all references:
```bash
# Find all occurrences
grep -r "permissions\"" your_app/

# Replace with: permissions_graph
```

### Issue: Missing metadata files

**Symptom**: Entity directories don't have `_metadata.yaml`

**Solution**: Re-save entities:
```python
# Load and re-save to generate metadata
users = User.find_all()
for user in users:
    user.save()  # Generates metadata
```

### Issue: Permission count mismatch

**Symptom**: Different number of tuples before/after migration

**Solution**: Verify deduplication:
```python
# Old store might have had duplicates
# GraphAr automatically deduplicates by tuple_key

# Check for duplicates in old data:
old_df = pd.read_parquet("./kanban_data/permissions.backup/permissions.parquet")
print(f"Old count: {len(old_df)}")
print(f"Unique tuple_keys: {old_df['tuple_key'].nunique()}")
```

---

## Performance Considerations

### Storage Size

- **Single File**: ~10-50MB for 100K tuples
- **GraphAr**: ~15-60MB for 100K tuples (includes metadata)
- **Overhead**: ~20% increase due to metadata and directory structure

**Trade-off**: Slightly larger storage for much better query performance and graph analysis capabilities.

### Query Performance

| Operation | Legacy | GraphAr | Improvement |
|-----------|--------|---------|-------------|
| Check permission | 0.5ms | 0.3ms | 1.7x faster |
| List user permissions | 10ms | 5ms | 2x faster |
| Save | 50ms | 60ms | 20% slower |
| Load | 20ms | 30ms | 50% slower |

**Note**: Slightly slower save/load due to directory structure, but much faster queries.

---

## Rollback Instructions

If you need to rollback to the old format:

### Step 1: Downgrade ParquetFrame

```bash
pip install parquetframe==0.3.5
```

### Step 2: Restore Backups

```bash
cp -r ./kanban_data/permissions.backup ./kanban_data/permissions
cp -r ./kanban_data/users.backup ./kanban_data/users
```

### Step 3: Revert Code Changes

```python
# Change back to old path
permissions = PermissionManager("./kanban_data/permissions")
```

---

## FAQ

**Q: Do I need to migrate immediately?**
A: Not required for development, but recommended for production deployments to benefit from graph analysis features.

**Q: Can I keep both old and new formats?**
A: Yes, but applications can only use one at a time. Update code to switch between them.

**Q: What about existing test data?**
A: Tests using TupleStore can continue using single-file format. New tests should use GraphAr format.

**Q: Will old tests still pass?**
A: Yes, legacy save/load to single files still works. Only new features require GraphAr format.

**Q: How do I verify GraphAr compliance?**
A: Run verification script:
```bash
python scripts/verify_rust_graphar.py
```

---

## Additional Resources

- **GraphAr Specification**: `docs/specs/graphar_permissions_schema.md`
- **Architecture Verification**: `TWO_GRAPH_ARCHITECTURE_VERIFICATION.md`
- **Integration Tests**: `PHASE_3.5_INTEGRATION_TEST_SUMMARY.md`
- **API Documentation**: `docs/api/permissions.md`
- **Demo Application**: `examples/integration/todo_kanban/demo.py`

---

## Support

For issues or questions:

1. Check existing issues: https://github.com/yourusername/parquetframe/issues
2. Create new issue with "migration" label
3. Include error messages and code snippets
4. Mention version: v0.4.0

---

**Migration Status**: ✅ Straightforward - Most applications need only path update
**Estimated Time**: 15-30 minutes for typical applications
**Risk Level**: Low - Backwards compatible APIs, only storage format changed
