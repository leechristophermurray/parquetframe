# CLI Reference

The ParquetFrame permissions CLI provides powerful command-line tools for managing and querying Zanzibar-style permissions. All commands support rich terminal output with tables, JSON, and YAML formats.

## Command Structure

```bash
pframe permissions <subcommand> [arguments] [options]
```

Available subcommands:
- `check` - Verify if a subject has a relation to an object
- `expand` - Find all objects a subject can access
- `list-objects` - List objects with a specific relation
- `add` - Add permission tuples to the store

## Global Options

All permission commands support these global options:

### Store Management
- `--store PATH, -s PATH` - Path to permission tuple store (.parquet file)
- `--format FORMAT, -f FORMAT` - Output format: `text` (default), `json`, `yaml`

### Output Control
- `--limit N, -l N` - Limit number of results (default: 100 for listing commands)

---

## `pframe permissions check`

Check if a subject has a specific relation to an object.

### Syntax
```bash
pframe permissions check SUBJECT RELATION OBJECT [options]
```

### Arguments
- `SUBJECT` - Subject reference in format `namespace:id` (e.g., `user:alice`, `group:admins`)
- `RELATION` - Relation type (e.g., `viewer`, `editor`, `owner`)
- `OBJECT` - Object reference in format `namespace:id` (e.g., `doc:doc1`, `folder:shared`)

### Options
- `--store PATH, -s PATH` - Permission store file
- `--no-indirect` - Disable transitive permission checking (direct only)
- `--format FORMAT, -f FORMAT` - Output format (`text`, `json`, `yaml`)

### Examples

**Basic permission check:**
```bash
pframe permissions check user:alice viewer doc:doc1 --store permissions.parquet
```
```
✅ PERMITTED
Subject: user:alice
Relation: viewer
Object: doc:doc1
Check type: direct_and_indirect
Store contains: 1,245 permission tuples
```

**Direct permissions only:**
```bash
pframe permissions check user:bob editor folder:shared --no-indirect --store permissions.parquet
```
```
❌ DENIED
Subject: user:bob
Relation: editor
Object: folder:shared
Check type: direct_only
Store contains: 1,245 permission tuples
```

**JSON output:**
```bash
pframe permissions check user:alice viewer doc:doc1 --format json --store permissions.parquet
```
```json
{
  "subject": "user:alice",
  "relation": "viewer",
  "object": "doc:doc1",
  "permitted": true,
  "check_type": "direct_and_indirect",
  "store_size": 1245
}
```

---

## `pframe permissions expand`

Find all objects that a subject has a specific relation to.

### Syntax
```bash
pframe permissions expand SUBJECT RELATION [options]
```

### Arguments
- `SUBJECT` - Subject reference (e.g., `user:alice`, `group:engineering`)
- `RELATION` - Relation type to expand (e.g., `viewer`, `editor`)

### Options
- `--store PATH, -s PATH` - Permission store file
- `--namespace NS, -n NS` - Filter objects by namespace (e.g., `doc`, `folder`)
- `--no-indirect` - Disable transitive permission expansion
- `--limit N, -l N` - Limit number of results (default: 100)
- `--format FORMAT, -f FORMAT` - Output format (`text`, `json`, `yaml`)

### Examples

**Find all documents a user can view:**
```bash
pframe permissions expand user:alice viewer --namespace doc --store permissions.parquet
```
```
Permission Expansion Results
Subject: user:alice
Relation: viewer
Namespace filter: doc
Expansion type: direct_and_indirect
Found: 23 accessible objects

┌───────────┬───────────┬──────────────┐
│ Namespace │ Object ID │ Reference    │
├───────────┼───────────┼──────────────┤
│ doc       │ doc1      │ doc:doc1     │
│ doc       │ doc5      │ doc:doc5     │
│ doc       │ doc12     │ doc:doc12    │
│ doc       │ report1   │ doc:report1  │
└───────────┴───────────┴──────────────┘
```

**All resources a group can edit:**
```bash
pframe permissions expand group:engineering editor --limit 50 --store permissions.parquet
```

**JSON output with filtering:**
```bash
pframe permissions expand user:bob viewer --namespace doc --format json --store permissions.parquet
```
```json
{
  "subject": "user:bob",
  "relation": "viewer",
  "namespace_filter": "doc",
  "expansion_type": "direct_and_indirect",
  "total_objects": 5,
  "objects": [
    {"namespace": "doc", "object_id": "doc3"},
    {"namespace": "doc", "object_id": "doc7"},
    {"namespace": "doc", "object_id": "report2"}
  ],
  "store_size": 1245
}
```

---

## `pframe permissions list-objects`

List all objects that have a specific relation.

### Syntax
```bash
pframe permissions list-objects RELATION [options]
```

### Arguments
- `RELATION` - Relation type to list objects for (e.g., `viewer`, `editor`, `owner`)

### Options
- `--store PATH, -s PATH` - Permission store file
- `--namespace NS, -n NS` - Filter by object namespace
- `--limit N, -l N` - Limit results (default: 100)
- `--format FORMAT, -f FORMAT` - Output format (`text`, `json`, `yaml`)

### Examples

**All viewable documents:**
```bash
pframe permissions list-objects viewer --namespace doc --store permissions.parquet
```
```
Objects with 'viewer' Relation
Relation: viewer
Namespace filter: doc
Found: 87 objects

┌───────────┬────────────┬──────────────────┐
│ Namespace │ Object ID  │ Reference        │
├───────────┼────────────┼──────────────────┤
│ doc       │ annual2023 │ doc:annual2023   │
│ doc       │ budget     │ doc:budget       │
│ doc       │ guide      │ doc:guide        │
│ doc       │ manual     │ doc:manual       │
│ doc       │ report1    │ doc:report1      │
└───────────┴────────────┴──────────────────┘
```

**All owned resources:**
```bash
pframe permissions list-objects owner --limit 20 --store permissions.parquet
```

**YAML output:**
```bash
pframe permissions list-objects editor --namespace folder --format yaml --store permissions.parquet
```
```yaml
relation: editor
namespace_filter: folder
total_objects: 12
objects:
- namespace: folder
  object_id: projects
- namespace: folder
  object_id: shared
- namespace: folder
  object_id: templates
store_size: 1245
```

---

## `pframe permissions add`

Add a permission tuple to the store.

### Syntax
```bash
pframe permissions add SUBJECT RELATION OBJECT [options]
```

### Arguments
- `SUBJECT` - Subject reference (e.g., `user:alice`, `group:admins`)
- `RELATION` - Relation type (e.g., `viewer`, `editor`, `owner`)
- `OBJECT` - Object reference (e.g., `doc:doc1`, `folder:shared`)

### Options
- `--store PATH, -s PATH` - Permission store file (creates if doesn't exist)
- `--model MODEL, -m MODEL` - Use standard permission model with inheritance
  - `google_drive` - Google Drive-style permissions
  - `github_org` - GitHub organization permissions
  - `cloud_iam` - Cloud IAM-style permissions
  - `simple_rbac` - Simple role-based access control

### Examples

**Add basic permission:**
```bash
pframe permissions add user:alice viewer doc:doc1 --store permissions.parquet
```
```
✅ Permission Added
Subject: user:alice
Relation: viewer
Object: doc:doc1
Total tuples in store: 1,246
Store saved to: permissions.parquet
```

**Add permission with inheritance model:**
```bash
pframe permissions add user:bob owner project:webapp --store permissions.parquet --model google_drive
```
```
✅ Permission Added
Subject: user:bob
Relation: owner
Object: project:webapp
Model: google_drive (with inheritance)
Total tuples in store: 1,250
Store saved to: permissions.parquet
```

**Create new store with group permission:**
```bash
pframe permissions add group:engineering editor folder:shared --store new_permissions.parquet
```
```
Creating new permission store
✅ Permission Added
Subject: group:engineering
Relation: editor
Object: folder:shared
Total tuples in store: 1
Store saved to: new_permissions.parquet
```

---

## Permission Models

When using `--model` with the `add` command, the following inheritance hierarchies apply:

### Google Drive Model (`google_drive`)
```
owner → editor → commenter → viewer
```
Adding `owner` automatically grants `editor`, `commenter`, and `viewer` permissions.

### GitHub Organization Model (`github_org`)
```
admin → maintain → write → triage → read
```

### Cloud IAM Model (`cloud_iam`)
```
owner → admin → editor → viewer → user
```

### Simple RBAC Model (`simple_rbac`)
```
admin → manager → user → guest
```

---

## Working with Store Files

### Creating a New Store
```bash
# First permission creates the store
pframe permissions add user:admin owner system:config --store new_store.parquet
```

### Loading Existing Store
```bash
# All commands can load existing stores
pframe permissions check user:admin owner system:config --store existing_store.parquet
```

### Store Information
The store file is a standard Parquet file that can be:
- Loaded by any ParquetFrame operation
- Shared between applications
- Backed up and versioned
- Analyzed with standard data tools

---

## Output Formats

### Text Format (Default)
Human-readable tables and status messages with colors and formatting.

### JSON Format
Machine-readable JSON for integration with other tools:
```bash
pframe permissions check user:alice viewer doc:doc1 --format json --store permissions.parquet | jq '.permitted'
```

### YAML Format
Human and machine-readable YAML:
```bash
pframe permissions expand user:bob editor --format yaml --store permissions.parquet > user_permissions.yaml
```

---

## Common Workflows

### Setting Up Permissions for a New Project
```bash
# Create permissions store
pframe permissions add user:admin owner project:newapp --store project_permissions.parquet --model cloud_iam

# Add team permissions
pframe permissions add group:developers editor project:newapp --store project_permissions.parquet
pframe permissions add group:qa viewer project:newapp --store project_permissions.parquet

# Verify permissions
pframe permissions check user:admin owner project:newapp --store project_permissions.parquet
pframe permissions expand group:developers editor --store project_permissions.parquet
```

### Auditing User Access
```bash
# Check what a user can access
pframe permissions expand user:alice viewer --store permissions.parquet --format json > alice_access.json

# Find all editors of sensitive documents
pframe permissions list-objects editor --namespace sensitive --store permissions.parquet

# Verify specific access
pframe permissions check user:contractor viewer sensitive:financials --store permissions.parquet
```

### Debugging Permission Issues
```bash
# Check direct vs indirect permissions
pframe permissions check user:bob editor doc:secret --store permissions.parquet
pframe permissions check user:bob editor doc:secret --no-indirect --store permissions.parquet

# See all accessible objects
pframe permissions expand user:bob editor --store permissions.parquet --limit 1000

# Export full results for analysis
pframe permissions expand user:bob editor --format json --store permissions.parquet > debug_permissions.json
```

---

## Error Handling

The CLI provides clear error messages for common issues:

### Invalid Reference Format
```bash
pframe permissions check alice viewer doc:doc1
# Error: Subject must be in format 'namespace:id'
```

### Missing Store File
```bash
pframe permissions check user:alice viewer doc:doc1 --store missing.parquet
# Error: Store file not found: missing.parquet
```

### Permission Denied Results
Permission denied is not an error - it's a valid result:
```bash
pframe permissions check user:bob admin system:critical --store permissions.parquet
# ❌ DENIED (exit code 0)
```

### Store Creation
If no `--store` is specified, commands use an empty in-memory store:
```bash
pframe permissions check user:alice viewer doc:doc1
# Using empty permission store. Use --store to load permissions.
# ❌ DENIED
```
