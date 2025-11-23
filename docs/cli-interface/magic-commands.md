# Interactive CLI - Magic Commands Guide

ParquetFrame's Interactive CLI provides a powerful REPL environment with Jupyter-like magic commands for efficient data exploration and analysis.

## Overview

Magic commands start with `%` and provide special functionality beyond standard SQL queries. They enable quick access to common operations without writing full commands.

## Available Magic Commands

### SQL Execution

#### `%sql <query>`
Execute SQL queries using the default engine.

```python
%sql SELECT * FROM users WHERE age > 25 LIMIT 10
```

#### `%df <query>`
Execute SQL queries using Apache DataFusion for high-performance execution.

```python
%df SELECT country, COUNT(*) as count FROM customers GROUP BY country ORDER BY count DESC
```

**When to use DataFusion:**
- Complex aggregations
- Large datasets requiring optimization
- Window functions
- Advanced SQL features

### Permission Management

#### `%permissions check <subject> <relation> <object>`
Check if a subject has a specific permission on an object.

```python
%permissions check user:alice viewer doc:report2023
# Output: ✅ Permission GRANTED: user:alice is viewer of doc:report2023
```

#### `%permissions grant <subject> <relation> <object>`
Grant a permission to a subject.

```python
%permissions grant user:bob editor doc:budget2024
# Output: ✅ Granted: user:bob -> editor -> doc:budget2024
```

#### `%permissions revoke <subject> <relation> <object>`
Revoke a permission from a subject.

```python
%permissions revoke user:bob editor doc:budget2024
# Output: ✅ Revoked: user:bob -> editor -> doc:budget2024
```

#### `%permissions list`
List all active permissions.

```python
%permissions list
# Displays table of all permission tuples
```

### RAG (Retrieval-Augmented Generation)

#### `%rag <question>`
Search documentation and knowledge base using RAG.

```python
%rag "How do I optimize query performance?"
```

### Variable Management

#### `%info <variable>`
Display detailed information about a DataFrame variable.

```python
df = %sql SELECT * FROM users
%info df
# Output: 
# df: 1,000 rows, 5 cols
#   id: int64
#   name: object
#   ...
```

#### `%schema <variable>`
Show schema of a DataFrame variable.

```python
%schema df
```

#### `%whos`
List all variables in the current session.

```python
%whos
# Output:
# Variables:
#   df: DataFrame
#   result: DataFrame
```

#### `%clear`
Clear all variables from the session.

```python
%clear
# Output: ✅ Variables cleared
```

#### `%help`
Display help for magic commands.

```python
%help
```

## Python Code Execution

The interactive CLI also supports Python code execution:

```python
# Variables persist across commands
df = %sql SELECT * FROM users
filtered = df[df['age'] > 25]
%info filtered
```

## Tips & Best Practices

1. **Use %df for heavy queries**: DataFusion excels at complex analytics
2. **Combine with Python**: Mix SQL and pandas operations seamlessly
3. **Permission checks**: Validate access before expensive operations
4. **Variable inspection**: Use %info and %whos to understand your data

## Examples

### Data Exploration Workflow
```python
# Load data
users = %sql SELECT * FROM users

# Inspect
%info users

# Complex analytics with DataFusion
%df SELECT 
    DATE_TRUNC('month', signup_date) as month,
    COUNT(*) as signups 
FROM users 
GROUP BY month 
ORDER BY month

# Check permissions before sharing
%permissions check user:alice viewer doc:user_analysis
```

### Permission Management Workflow
```python
# Grant access
%permissions grant user:alice viewer doc:sales_report
%permissions grant user:bob editor doc:sales_report

# Verify
%permissions check user:alice viewer doc:sales_report

# List all
%permissions list

# Revoke when needed
%permissions revoke user:alice viewer doc:sales_report
```
