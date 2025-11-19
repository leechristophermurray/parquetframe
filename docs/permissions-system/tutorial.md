# Permissions System Tutorial

This tutorial guides you through building a **Document Management System** with granular access control using ParquetFrame's Zanzibar-style permissions engine.

## Scenario

We want to model a system where:
- **Users** can be viewers, editors, or owners of **Documents**.
- **Groups** can also have roles on documents.
- **Folders** contain documents, and permissions inherit from folders to documents.

## Prerequisites

```bash
pip install parquetframe
```

## Step 1: Initialize the Tuple Store

First, create a `TupleStore` which handles the storage and graph logic.

```python
from parquetframe.permissions import TupleStore, RelationTuple, check, list_objects, list_subjects, expand
import shutil
import os

# Initialize store
store = TupleStore()
print("Tuple Store initialized.")
```

## Step 2: Define Relationships (Tuples)

In Zanzibar, permissions are defined by **relation tuples** in the format:
`object # relation @ subject`

Let's set up our hierarchy:

1.  **Alice** is the `owner` of `folder:finance`.
2.  **Bob** is a `viewer` of `folder:finance`.
3.  `doc:budget_2024` is inside `folder:finance` (parent relationship).
4.  **Charlie** is directly an `editor` of `doc:budget_2024`.

```python
# Grant permissions on the folder
store.add_tuple(RelationTuple("folder", "finance", "owner", "user", "alice"))
store.add_tuple(RelationTuple("folder", "finance", "viewer", "user", "bob"))

# Define hierarchy: doc belongs to folder
# We use a special relation 'parent' to link objects
store.add_tuple(RelationTuple("doc", "budget_2024", "parent", "folder", "finance"))

# Direct permission on the document
store.add_tuple(RelationTuple("doc", "budget_2024", "editor", "user", "charlie"))

print("Permissions granted.")
```

## Step 3: Check Permissions

Now let's verify access. We need to define **rules** for how permissions resolve. In a full Zanzibar system, this is done via schema configuration. In ParquetFrame's lightweight mode, we can check direct relations or implement logic.

For this tutorial, we'll assume a simple model:
- `owner` implies `editor` and `viewer`.
- `editor` implies `viewer`.
- Permissions on a `parent` folder inherit to the child document.

### Simple Check (Direct)

```python
# Check if Alice is owner of the folder
is_owner = check(store, "user", "alice", "owner", "folder", "finance")
print(f"Is Alice owner of folder:finance? {is_owner}")  # True
```

### Inheritance Check (Logic)

To handle inheritance (e.g., Alice owns the folder, so she owns the doc), we can use the `expand` API or helper logic.

```python
def check_access(user, obj_ns, obj_id, relation):
    # 1. Direct check
    if check(store, "user", user, relation, obj_ns, obj_id):
        return True

    # 2. Hierarchy check (parent)
    # Find parents of the object
    parents = list_subjects(store, "parent", obj_ns, obj_id)
    for parent_ns, parent_id in parents:
        # Recursive check on parent
        if check_access(user, parent_ns, parent_id, relation):
            return True

    return False

# Check if Alice has owner access to the document (inherited)
# Note: In this simple logic, we check if Alice is owner of the parent folder
has_access = check_access("alice", "doc", "budget_2024", "owner")
print(f"Does Alice own doc:budget_2024? {has_access}")  # True
```

## Step 4: List Accessible Objects

Find all resources a user has access to.

```python
# What folders can Bob view?
folders = list_objects(store, "viewer", "folder")
# Note: list_objects returns all objects with that relation, filtering by subject requires logic or graph traversal
# For this example, we'll just list objects that HAVE a viewer relation
print(f"Objects with viewer relation: {folders}")
```

## Step 5: List Authorized Subjects

Find all users who have a specific role.

```python
# Who is an owner of the finance folder?
owners = list_subjects(store, "owner", "folder", "finance")
print(f"Owners of folder:finance: {owners}")
```

## Step 6: Expand Permissions

Visualize the permission tree to understand *why* a user has access.

```python
# Expand the 'parent' relation for the document
tree = expand(store, "folder", "finance", "parent")
# Note: expand finds objects the subject has a relation TO.
# So expand(finance_folder, parent) finds what finance_folder is a parent OF.
print("Objects that folder:finance is parent of:")
print(tree)
```

## Advanced: Groups and Nested Relations

You can treat groups as subjects too.

```python
# Create a group
store.add_tuple(RelationTuple("group", "auditors", "member", "user", "dave"))

# Grant group access to folder
store.add_tuple(RelationTuple("folder", "finance", "viewer", "group", "auditors"))
```
# Check if Dave has access (requires resolving group membership)
# This typically involves a 'rewrite' rule in schema, or recursive checks in app logic.
```

## Summary

You've built a basic permission system that supports:
- **Granular roles** (owner, editor, viewer)
- **Hierarchies** (folder -> doc)
- **Fast checks** using the underlying graph engine

## Next Steps

- Explore [Entity Framework](../entity-framework/index.md) to attach these permissions to real data classes.
- See [Graph Processing](../graph-processing/index.md) for analyzing large permission graphs.
