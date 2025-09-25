# AI-Powered Data Exploration

> 🤖 **NEW**: ParquetFrame now includes AI-powered natural language querying and interactive data exploration!

## Overview

ParquetFrame has evolved into a comprehensive data exploration platform that supports:
- **Parquet Data Lakes**: Recursive file discovery and unified querying
- **Database Integration**: SQLAlchemy-based multi-database support
- **AI-Powered Queries**: Natural language to SQL conversion with local LLM
- **Interactive CLI**: Rich REPL interface with session management

## Prerequisites

### Install Ollama

ParquetFrame uses [Ollama](https://ollama.ai/) for local LLM inference:

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### Start Ollama and Pull Models

```bash
# Start Ollama service
ollama serve

# In another terminal, pull a model
ollama pull llama3.2
# or for better SQL generation
ollama pull codellama
```

### Install ParquetFrame with AI Support

```bash
pip install parquetframe[ai,cli]
```

## Interactive Mode

### Parquet Data Lakes

Explore directories of parquet files with AI assistance:

```bash
pframe interactive --path ./my_data_lake/
```

Example session:
```
🚀 Welcome to ParquetFrame Interactive Mode
Data source: /Users/me/sales_data/
Type: parquet
AI enabled: Yes

✅ Connected! Found 1 table(s)

pframe:parquet🤖> \help
📚 Help

Data Exploration:
  \list, \l, \tables     List all available tables
  \describe <table>      Show detailed table schema

Querying:
  <SQL query>            Execute SQL query directly
  \ai <question>         Ask question in natural language 🤖

Session Management:
  \history               Show query history
  \save-session <file>   Save current session
  \load-session <file>   Load saved session

pframe:parquet🤖> \list
📋 Available Tables
┌────────────┬─────────┐
│ Table Name │ Type    │
├────────────┼─────────┤
│ sales_data │ Virtual │
└────────────┴─────────┘

pframe:parquet🤖> \describe sales_data
🔍 Table Schema: sales_data
┌──────────────┬───────────┬─────────┐
│ Column       │ Type      │ Nullable│
├──────────────┼───────────┼─────────┤
│ date         │ DATE      │ ✓       │
│ product_id   │ INTEGER   │ ✓       │
│ customer_id  │ INTEGER   │ ✓       │
│ amount       │ DOUBLE    │ ✓       │
│ quantity     │ INTEGER   │ ✓       │
└──────────────┴───────────┴─────────┘
📁 Files: 12
📍 Source: /Users/me/sales_data

pframe:parquet🤖> \ai what were the total sales last month?
🤖 Processing: what were the total sales last month?

📝 Generated Query:
┌─────────────────────────────────────────────────────────┐
│ SELECT SUM(amount) as total_sales                       │
│ FROM sales_data                                         │
│ WHERE date >= date_trunc('month', current_date - inte  │
│   val '1 month')                                        │
│   AND date < date_trunc('month', current_date)         │
└─────────────────────────────────────────────────────────┘

🚀 Execute this query? [Y/n]: y

┌─────────────┐
│ total_sales │
├─────────────┤
│ 125432.78   │
└─────────────┘
📊 1 rows in 45.2ms

pframe:parquet🤖> SELECT product_id, SUM(amount) as revenue FROM sales_data GROUP BY product_id ORDER BY revenue DESC LIMIT 5;

┌────────────┬──────────┐
│ product_id │ revenue  │
├────────────┼──────────┤
│ 101        │ 25431.20 │
│ 205        │ 18965.44 │
│ 156        │ 15678.91 │
│ 332        │ 12447.33 │
│ 189        │ 11982.17 │
└────────────┴──────────┘
📊 5 rows in 23.1ms

pframe:parquet🤖> \history
📚 Query History
┌───┬─────────────────────────────────────────────────────────────────┬────────┬───────────┐
│ # │ Query                                                           │ Status │ Time (ms) │
├───┼─────────────────────────────────────────────────────────────────┼────────┼───────────┤
│ 1 │ SELECT SUM(amount) as total_sales FROM sales_data WHERE date...  │ ✅     │ 45.2      │
│ 2 │ SELECT product_id, SUM(amount) as revenue FROM sales_data GR... │ ✅     │ 23.1      │
└───┴─────────────────────────────────────────────────────────────────┴────────┴───────────┘

pframe:parquet🤖> \save-session monthly_analysis
💾 Session saved to: /Users/me/.parquetframe/sessions/monthly_analysis.pkl

pframe:parquet🤖> \quit
👋 Goodbye!
```

### Database Connections

Connect to any SQL database:

```bash
# SQLite
pframe interactive --db-uri "sqlite:///northwind.db"

# PostgreSQL
pframe interactive --db-uri "postgresql://user:password@localhost:5432/ecommerce"

# MySQL
pframe interactive --db-uri "mysql+pymysql://user:password@localhost/orders"
```

Example database session:
```
pframe:database🤖> \list
📋 Available Tables
┌───────────┬──────────┐
│ Table Name│ Type     │
├───────────┼──────────┤
│ customers │ Database │
│ orders    │ Database │
│ products  │ Database │
│ suppliers │ Database │
└───────────┴──────────┘

pframe:database🤖> \ai which customers have made the most orders?
🤖 Processing: which customers have made the most orders?

📝 Generated Query:
┌─────────────────────────────────────────────────────────┐
│ SELECT c.customer_name, COUNT(o.order_id) as order_count│
│ FROM customers c                                         │
│ JOIN orders o ON c.customer_id = o.customer_id          │
│ GROUP BY c.customer_id, c.customer_name                 │
│ ORDER BY order_count DESC                               │
│ LIMIT 10                                                │
└─────────────────────────────────────────────────────────┘

🚀 Execute this query? [Y/n]: y

┌──────────────────┬─────────────┐
│ customer_name    │ order_count │
├──────────────────┼─────────────┤
│ ACME Corporation │ 45          │
│ Global Industries│ 38          │
│ Tech Solutions   │ 31          │
│ ...              │ ...         │
└──────────────────┴─────────────┘
📊 10 rows in 67.3ms
```

## Programming Interface

### DataContext API

Use the DataContext system programmatically:

```python
import asyncio
from parquetframe.datacontext import DataContextFactory

async def explore_data():
    # Connect to parquet data lake
    context = DataContextFactory.create_from_path("./sales_data/")
    await context.initialize()

    # Get schema information
    schema = context.get_schema_as_text()
    print("Schema for LLM:", schema)

    # Execute queries
    result = await context.execute("SELECT COUNT(*) as total FROM sales_data")
    print("Total records:", result.iloc[0]['total'])

    # List available tables
    tables = context.get_table_names()
    print("Available tables:", tables)

    # Get detailed table info
    table_info = context.get_table_schema("sales_data")
    print("Columns:", [col['name'] for col in table_info['columns']])

    context.close()

asyncio.run(explore_data())
```

### LLM Agent API

Use AI capabilities in your code:

```python
import asyncio
from parquetframe.datacontext import DataContextFactory
from parquetframe.ai import LLMAgent

async def ai_analysis():
    # Setup context and agent
    context = DataContextFactory.create_from_path("./ecommerce_data/")
    agent = LLMAgent(
        model_name="llama3.2",
        max_retries=2,
        use_multi_step=True,  # For complex schemas
        temperature=0.1       # More deterministic
    )

    await context.initialize()

    # Natural language queries
    queries = [
        "What are the top 5 products by revenue?",
        "Show me monthly sales trends",
        "Which customers haven't ordered in the last 6 months?",
        "What's the average order value by region?"
    ]

    for question in queries:
        print(f"\nQuestion: {question}")

        result = await agent.generate_query(question, context)

        if result.success:
            print(f"Generated SQL: {result.query}")
            print(f"Rows returned: {len(result.result)}")
            print(f"Execution time: {result.execution_time_ms:.2f}ms")
            print(f"Attempts: {result.attempts}")
        else:
            print(f"Failed: {result.error}")

    context.close()

asyncio.run(ai_analysis())
```

### Custom Examples and Training

Improve AI performance with domain-specific examples:

```python
from parquetframe.ai import LLMAgent

agent = LLMAgent()

# Add custom examples for better performance
agent.add_custom_example(
    question="show me high value customers",
    sql="SELECT customer_id, total_spent FROM customers WHERE total_spent > 10000 ORDER BY total_spent DESC"
)

agent.add_custom_example(
    question="monthly recurring revenue",
    sql="SELECT DATE_TRUNC('month', subscription_date) as month, SUM(monthly_fee) as mrr FROM subscriptions GROUP BY month ORDER BY month"
)

# Use different models for different purposes
code_agent = LLMAgent(model_name="codellama")  # Better for SQL
general_agent = LLMAgent(model_name="llama3.2")  # General purpose
```

## Advanced Features

### Multi-Step Reasoning

For databases with many tables, enable multi-step reasoning:

```python
agent = LLMAgent(use_multi_step=True)

# The agent will:
# 1. First select relevant tables for the question
# 2. Then generate SQL using only those tables
# This reduces context size and improves accuracy
```

### Self-Correction

The LLM agent automatically attempts to fix failed queries:

```python
agent = LLMAgent(max_retries=3)  # Try up to 3 corrections

# If a query fails:
# 1. Error message is sent back to the LLM
# 2. LLM generates a corrected query
# 3. Process repeats up to max_retries times
```

### Session Management

Save and restore interactive sessions:

```bash
# Save current session
pframe:parquet🤖> \save-session customer_analysis

# Later, in a new session
pframe:parquet🤖> \load-session customer_analysis
📂 Loaded session: 15 queries in history

pframe:parquet🤖> \history
# Shows all previous queries
```

## Configuration

### Model Selection

List and choose from available models:

```python
agent = LLMAgent()
available = agent.get_available_models()
print("Available models:", available)

# Switch models
agent.set_model("codellama")
```

### Performance Tuning

```python
# Faster, less creative
agent = LLMAgent(temperature=0.0)

# More creative, potentially less accurate
agent = LLMAgent(temperature=0.3)

# Disable multi-step for simple schemas
agent = LLMAgent(use_multi_step=False)

# More aggressive error correction
agent = LLMAgent(max_retries=5)
```

## Best Practices

### 1. Model Selection

- **codellama**: Best for SQL generation and complex queries
- **llama3.2**: Good general-purpose model
- **llama2**: Fallback for older systems

### 2. Query Optimization

- Use specific column names in questions: "show customer names and emails" vs "show customer data"
- Include time ranges: "sales last month" vs "recent sales"
- Be specific about sorting: "top 10 by revenue" vs "best products"

### 3. Schema Design

- Use descriptive table and column names
- Include comments in CREATE TABLE statements when possible
- Keep related data in the same table when feasible

### 4. Error Handling

```python
result = await agent.generate_query(question, context)
if result.failed:
    if "column" in result.error.lower():
        print("Hint: Check column names with \\describe table_name")
    elif "table" in result.error.lower():
        print("Hint: Check table names with \\list")
```

## Troubleshooting

### Common Issues

1. **"AI functionality not available"**
   ```bash
   # Install ollama
   brew install ollama
   ollama serve
   ollama pull llama3.2
   ```

2. **"No tables found"**
   - Check file permissions
   - Verify parquet files are valid
   - Use `\list` to see discovered tables

3. **"Database connection failed"**
   - Verify connection string format
   - Check credentials and network access
   - Test connection with a simple client first

4. **"Query execution failed"**
   - Use `\describe table_name` to verify schema
   - Check generated SQL for syntax errors
   - Enable debug logging for more details

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed logs of:
# - Schema discovery process
# - LLM prompts and responses
# - Query execution details
# - Error messages and retries
```

## Examples

### E-commerce Analysis

```bash
pframe interactive --path ./ecommerce_parquets/
```

```
pframe:parquet🤖> \ai what's our monthly recurring revenue trend?
pframe:parquet🤖> \ai which products have the highest return rate?
pframe:parquet🤖> \ai show me customer cohort analysis for Q4
```

### Log Analysis

```bash
pframe interactive --path ./web_logs/
```

```
pframe:parquet🤖> \ai what are the top 10 most visited pages?
pframe:parquet🤖> \ai show me error rate by hour of day
pframe:parquet🤖> \ai which user agents are most common?
```

### Financial Data

```bash
pframe interactive --db-uri "postgresql://user:pass@localhost/trading"
```

```
pframe:database🤖> \ai what's the portfolio performance this quarter?
pframe:database🤖> \ai show me the most volatile stocks
pframe:database🤖> \ai calculate risk-adjusted returns by sector
```

Ready to explore your data with AI? Start with `pframe interactive --help`! 🚀
