# Interactive CLI Permissions Tutorial

Learn how to use Zanzibar-style permissions in ParquetFrame's Interactive CLI to manage access control for your data.

## Introduction

The Interactive CLI includes built-in support for **Zanzibar-style permissions**, a relationship-based access control (ReBAC) system inspired by Google's authorization system.

### Key Concepts

- **Subject**: The entity requesting access (e.g., `user:alice`, `group:admins`)
- **Relation**: The type of access (e.g., `viewer`, `editor`, `owner`)
- **Object**: The resource being accessed (e.g., `doc:report`, `table:sales`)

Permission format: `subject:id relation object:id`

## Getting Started

### Starting a Session with Permissions

```bash
pframe interactive --path /data/my_dataset
```

Permissions are automatically available in the interactive session.

## Basic Operations

### Granting Permissions

Grant a user permission to access a resource:

```python
%permissions grant user:alice viewer doc:quarterly_report
# Output: ✅ Granted: user:alice -> viewer -> doc:quarterly_report
```

### Checking Permissions

Verify if a user has specific access:

```python
%permissions check user:alice viewer doc:quarterly_report
# Output: ✅ Permission GRANTED: user:alice is viewer of doc:quarterly_report
```

### Listing Permissions

View all active permissions:

```python
%permissions list
```

Output table:
```
┌───────────────┬──────────┬──────────────────────────┐
│ Subject       │ Relation │ Object                   │
├───────────────┼──────────┼──────────────────────────┤
│ user:alice    │ viewer   │ doc:quarterly_report     │
│ user:bob      │ editor   │ doc:quarterly_report     │
│ user:charlie  │ owner    │ doc:quarterly_report     │
└───────────────┴──────────┴──────────────────────────┘
```

### Revoking Permissions

Remove a permission:

```python
%permissions revoke user:alice viewer doc:quarterly_report
# Output: ✅ Revoked: user:alice -> viewer -> doc:quarterly_report
```

## Common Workflows

### Workflow 1: Document Sharing

```python
# Create a report
report = %sql SELECT * FROM sales WHERE year = 2024

# Grant read access to team members
%permissions grant user:alice viewer doc:sales_2024
%permissions grant user:bob viewer doc:sales_2024

# Grant edit access to analysts
%permissions grant user:charlie editor doc:sales_2024

# Verify access
%permissions check user:alice viewer doc:sales_2024
%permissions check user:charlie editor doc:sales_2024

# List all permissions for this document
%permissions list
```

### Workflow 2: Hierarchical Access

```python
# Owner has full control
%permissions grant user:manager owner table:employee_data

# Editors can modify
%permissions grant user:hr_analyst editor table:employee_data
%permissions grant user:payroll editor table:employee_data

# Viewers can only read
%permissions grant user:intern viewer table:employee_data

# Check different levels
%permissions check user:manager owner table:employee_data
%permissions check user:hr_analyst editor table:employee_data
%permissions check user:intern viewer table:employee_data
```

### Workflow 3: Temporary Access

```python
# Grant temporary access for analysis
%permissions grant user:contractor viewer dataset:customer_analytics

# Contractor performs analysis
%sql SELECT COUNT(*) FROM customers

# Revoke after project completion
%permissions revoke user:contractor viewer dataset:customer_analytics

# Verify revocation
%permissions check user:contractor viewer dataset:customer_analytics
# Output: ❌ Permission DENIED
```

## Permission Patterns

### Role-Based Structure

Define clear roles with specific relations:

- **owner**: Full control (create, edit, delete, manage permissions)
- **editor**: Modify content (create, edit)
- **viewer**: Read-only access

### Resource Namespaces

Organize resources by type:

```python
# Documents
%permissions grant user:alice viewer doc:report2024

# Tables
%permissions grant user:bob editor table:sales

# Datasets
%permissions grant user:charlie owner dataset:analytics
```

### Group-Based Access

Use groups for team permissions:

```python
# Grant access to entire team
%permissions grant group:engineering viewer doc:architecture
%permissions grant group:data_team editor table:metrics
```

## Advanced Usage

### Permission Chains

Check permissions before data operations:

```python
# Function to validate access
def secure_query(user, table, query):
    # Check permission first
    %permissions check {user} viewer {table}
    # If granted, execute query
    return %sql {query}
```

### Audit Trail

Track permission changes:

```python
# Before granting
%permissions list

# Grant new permission
%permissions grant user:new_analyst viewer table:sensitive_data

# Verify change
%permissions list
```

## Integration with Data Operations

### Secure Data Access Pattern

```python
# 1. Check permission
%permissions check user:alice viewer table:customers

# 2. If granted, load data
customers = %sql SELECT * FROM customers WHERE region = 'EMEA'

# 3. Process with Python
summary = customers.groupby('country').agg({
    'revenue': 'sum',
    'orders': 'count'
})

# 4. Save results with permissions
%permissions grant user:manager viewer doc:emea_summary
```

## Best Practices

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Regular Audits**: Use `%permissions list` to review active permissions
3. **Clear Naming**: Use descriptive resource identifiers
4. **Document Permissions**: Track who has access to what
5. **Revoke Promptly**: Remove access when no longer needed

## Troubleshooting

### Permission Denied Errors

```python
%permissions check user:alice viewer doc:report
# Output: ❌ Permission DENIED: user:alice is NOT viewer of doc:report
```

**Solution**: Grant the required permission

```python
%permissions grant user:alice viewer doc:report
```

### Duplicate Permission Grants

Granting the same permission twice is safe - it updates the existing permission.

```python
%permissions grant user:alice viewer doc:report  # First time
%permissions grant user:alice viewer doc:report  # No error, just updates
```

## Examples

### Example 1: Team Data Access

```python
# Setup team structure
%permissions grant user:team_lead owner project:q4_analytics
%permissions grant user:analyst1 editor project:q4_analytics
%permissions grant user:analyst2 editor project:q4_analytics
%permissions grant user:intern viewer project:q4_analytics

# Verify setup
%permissions list

# Analysts can run queries
%permissions check user:analyst1 editor project:q4_analytics
data = %sql SELECT * FROM project_data
```

### Example 2: External Collaboration

```python
# Grant temporary access to external consultant
%permissions grant user:consultant viewer dataset:market_research

# Consultant verifies access
%permissions check user:consultant viewer dataset:market_research

# After project
%permissions revoke user:consultant viewer dataset:market_research
```

### Example 3: Escalating Permissions

```python
# Start with viewer
%permissions grant user:junior_analyst viewer table:experiments

# Promote to editor after training
%permissions revoke user:junior_analyst viewer table:experiments
%permissions grant user:junior_analyst editor table:experiments

# Verify new permission
%permissions check user:junior_analyst editor table:experiments
```

## Next Steps

- Explore [Magic Commands Guide](magic-commands.md) for more CLI features
- Learn about [DataFusion Integration](datafusion-integration.md) for performance
- See [Permissions System Documentation](../permissions-system/) for deep dive
