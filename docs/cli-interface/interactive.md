# Interactive Mode

> Use ParquetFrame's interactive CLI for exploratory data analysis.

## Interactive CLI Mode

ParquetFrame provides a powerful interactive REPL environment for data exploration and analysis. The interactive mode combines SQL querying, Python execution, LLM-powered natural language queries, and advanced magic commands.

## Features

- 🔍 **SQL Queries**: Execute SQL directly on your data
- 🤖 **AI-Powered**: Natural language to SQL translation
- 🐍 **Python Integration**: Mix SQL and Python seamlessly  
- ✨ **Magic Commands**: Jupyter-like commands for common operations
- ⚡ **DataFusion Integration**: High-performance SQL execution
- 🔐 **Permission Management**: Built-in Zanzibar-style access control
- 📚 **RAG Support**: Context-aware documentation search

## Quick Start

```bash
# Start interactive session with a Parquet directory
pframe interactive --path /path/to/data

# With database
pframe interactive --db postgresql://user:pass@localhost/db

# With AI features
pframe interactive --path /path/to/data --enable-ai
```

## Core Capabilities

### SQL Queries
Execute SQL directly:
```sql
SELECT * FROM users WHERE age > 25 LIMIT 10;
```

### Python Code
Mix Python with SQL:
```python
df = SELECT * FROM users
filtered = df[df['active'] == True]
print(f"Active users: {len(filtered)}")
```

### Natural Language (AI)
Ask questions in plain English:
```
\\ai show me top 10 customers by revenue
```

### Magic Commands
Use Jupyter-style magic commands:
```python
%sql SELECT COUNT(*) FROM orders
%df SELECT * FROM large_table  # Uses DataFusion
%permissions check user:alice viewer doc:report
%info my_dataframe
```

## Available Commands

### Meta Commands (\)
- `\help`, `\h`, `\?` - Show help
- `\list`, `\l`, `\tables` - List all tables
- `\describe`, `\d <table>` - Show table schema
- `\ai <question>` - AI-powered natural language query
- `\history` - Show query history
- `\save-session <file>` - Save current session
- `\\quit`, `\\q`, `\\exit` - Exit interactive mode
- `\\stats` - Show usage statistics
- `\\deps` - Show dependency status

### Magic Commands (%)
- `%sql <query>` - Execute SQL with default engine
- `%df <query>` - Execute SQL with DataFusion
- `%permissions <cmd>` - Manage permissions
- `%rag <question>` - Search documentation with RAG
- `%info <var>` - Show DataFrame info
- `%schema <var>` - Show schema
- `%whos` - List all variables
- `%clear` - Clear variables
- `%help` - Show magic command help

## Session Management

Sessions are automatically tracked with persistent history:

```python
# Save current session
\\save-session my_analysis

# Load previous session
\\load-session my_analysis

# Export queries as SQL script
\\save-script analysis.sql

# View usage statistics
\\stats
```

## Detailed Guides

- [Magic Commands Guide](magic-commands.md) - Complete reference for % commands
- [DataFusion Integration](datafusion-integration.md) - High-performance SQL
- [Permissions Tutorial](permissions-tutorial.md) - Access control workflows

## Summary

Interactive mode makes exploratory data analysis fast and intuitive from the command line.

## Examples

### Basic Exploration
```bash
# Start session
pframe interactive --path ./sales_data

# List tables
\\list

# Describe schema
\\describe customers

# Run query
SELECT * FROM customers WHERE country = 'USA' LIMIT 10;
```

### Advanced Workflow
```python
# Load and explore
customers = %sql SELECT * FROM customers
%info customers

# DataFusion analytics
%df SELECT 
    country,
    COUNT(*) as customer_count,
    SUM(lifetime_value) as total_value
FROM customers
GROUP BY country
ORDER BY total_value DESC

# Check permissions
%permissions check user:analyst viewer table:customers

# Python processing
top_countries = customers.nlargest(10, 'lifetime_value')
```

## Further Reading

- [CLI Overview](overview.md)
- [All Commands](commands.md)
- [Batch Processing](batch.md)
