# AI-Powered Data Exploration

> 🤖 **NEW**: ParquetFrame now includes AI-powered natural language querying and interactive data exploration, bringing the power of Large Language Models (LLMs) directly to your dataframes!

## Overview

ParquetFrame has evolved into a comprehensive data exploration platform that seamlessly integrates AI capabilities to simplify data analysis. This feature allows users to interact with their data using natural language, transforming complex questions into executable queries. The AI integration is built around:

* **DataContext**: A unified abstraction for various data sources (Parquet data lakes, SQL databases).
* **LLM Agent**: An intelligent agent that converts natural language questions into SQL queries.
* **Interactive CLI**: A rich REPL interface that provides an intuitive environment for AI-driven data exploration.

## Prerequisites

### 1. Install Ollama

ParquetFrame leverages [Ollama](https://ollama.ai/) for local, privacy-preserving LLM inference. This means your data never leaves your machine.

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### 2. Start Ollama and Pull Models

After installing Ollama, start its service and download the desired LLM models. For SQL generation, `codellama` is often recommended.

```bash
# Start the Ollama service (run in a separate terminal or as a background process)
ollama serve

# In another terminal, pull a model (e.g., llama3.2 or codellama)
ollama pull llama3.2
# For better SQL generation, consider:
ollama pull codellama
```

### 3. Install ParquetFrame with AI Support

Ensure you install ParquetFrame with the `ai` and `cli` extras:

```bash
pip install parquetframe[ai,cli]
```

## AI Query Flow

```mermaid
graph TD
    User[User Input: Natural Language Question] --> CLI[ParquetFrame CLI / Python API]
    CLI --> DataContext[DataContext<br/>**Schema & Data Source**]
    DataContext --> LLMAgent[LLM Agent<br/>**pf.ai.LLMAgent**]
    LLMAgent --> Ollama[Ollama LLM<br/>**Local Inference**]
    Ollama --> LLMAgent
    LLMAgent --> GeneratedSQL[Generated SQL Query]
    GeneratedSQL --> UserApproval{User Approval?}
    UserApproval --> |Yes| DataContext
    UserApproval --> |No| End[End Interaction]
    DataContext --> QueryExecution[Query Execution<br/>**DuckDB/Backend**]
    QueryExecution --> Results[Results Displayed to User]

    style User fill:#e1f5fe,stroke:#333,stroke-width:2px
    style CLI fill:#f3e5f5,stroke:#9c27b0,stroke-width:1px
    style DataContext fill:#c8e6c9,stroke:#81c784,stroke-width:1px
    style LLMAgent fill:#ffe0b2,stroke:#ff9800,stroke-width:1px
    style Ollama fill:#e0f2f7,stroke:#00bcd4,stroke-width:1px
    style GeneratedSQL fill:#fff3e0,stroke:#ffc107,stroke-width:1px
    style UserApproval fill:#fce4ec,stroke:#e91e63,stroke-width:1px
    style QueryExecution fill:#e8f5e9,stroke:#4caf50,stroke-width:1px
    style Results fill:#e1f5fe,stroke:#333,stroke-width:2px
    style End fill:#bbdefb,stroke:#2196f3,stroke-width:1px
```

## Interactive Mode

ParquetFrame's interactive CLI (`pframe interactive`) provides a rich REPL experience with integrated AI capabilities. It supports both Parquet data lakes and various SQL databases.

### Parquet Data Lakes

Explore directories containing Parquet files with AI assistance. ParquetFrame automatically discovers files and unifies their schemas into a virtual table.

```bash
pframe interactive --path ./my_data_lake/
```

Example session:

```shell
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

Connect to any SQL database supported by SQLAlchemy, and use AI to query it:

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

ParquetFrame's AI capabilities are also accessible programmatically, allowing you to integrate natural language querying into your Python applications.

### DataContext API

Use the `DataContext` system to abstract over different data sources:

```python
import asyncio
from parquetframe.datacontext import DataContextFactory

async def explore_data():
    # Connect to a parquet data lake
    context = DataContextFactory.create_from_path("./sales_data/")
    await context.initialize()

    # Get schema information for LLM consumption
    schema = context.get_schema_as_text()
    print("Schema for LLM:", schema)

    # Execute SQL queries directly
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

Use the `LLMAgent` to generate and execute queries from natural language questions:

```python
import asyncio
from parquetframe.datacontext import DataContextFactory
from parquetframe.ai import LLMAgent

async def ai_analysis():
    # Setup context and LLM agent
    context = DataContextFactory.create_from_path("./ecommerce_data/")
    agent = LLMAgent(
        model_name="llama3.2",
        max_retries=2,          # Allow up to 2 retries for self-correction
        use_multi_step=True,    # Enable multi-step reasoning for complex schemas
        temperature=0.1         # Lower temperature for more deterministic SQL generation
    )

    await context.initialize()

    # Define a list of natural language questions
    queries = [
        "What are the top 5 products by revenue?",
        "Show me monthly sales trends",
        "Which customers haven't ordered in the last 6 months?",
        "What's the average order value by region?"
    ]

    for question in queries:
        print(f"\nQuestion: {question}")

        # Generate and execute the query
        result = await agent.generate_query(question, context)

        if result.success:
            print(f"Generated SQL: {result.query}")
            print(f"Rows returned: {len(result.result)}")
            print(f"Execution time: {result.execution_time_ms:.2f}ms")
            print(f"Attempts: {result.attempts}")
            # print(result.result.head()) # Uncomment to see results
        else:
            print(f"Failed: {result.error}")

    context.close()

asyncio.run(ai_analysis())
```

### Custom Examples and Training

Improve the LLM agent's performance and accuracy for domain-specific queries by providing custom examples.

```python
from parquetframe.ai import LLMAgent

agent = LLMAgent()

# Add custom examples (question-SQL pairs)
agent.add_custom_example(
    question="show me high value customers",
    sql="SELECT customer_id, total_spent FROM customers WHERE total_spent > 10000 ORDER BY total_spent DESC"
)

agent.add_custom_example(
    question="monthly recurring revenue",
    sql="SELECT DATE_TRUNC('month', subscription_date) as month, SUM(monthly_fee) as mrr FROM subscriptions GROUP BY month ORDER BY month"
)

# You can also use different models for different purposes
code_agent = LLMAgent(model_name="codellama")  # Often better for SQL generation
general_agent = LLMAgent(model_name="llama3.2")  # Good for general-purpose questions
```

## Advanced Features

### Multi-Step Reasoning

For databases with a large number of tables or complex schemas, enabling multi-step reasoning can significantly improve the LLM's ability to generate accurate queries.

```python
agent = LLMAgent(use_multi_step=True)

# When use_multi_step is True, the agent will:
# 1. First, identify and select the most relevant tables for the given question.
# 2. Then, generate the SQL query using only the selected tables.
# This approach reduces the context size provided to the LLM, improving accuracy and reducing token usage.
```

### Self-Correction

ParquetFrame's LLM agent is designed to be resilient. If a generated query fails upon execution, the error message is fed back to the LLM, which then attempts to generate a corrected query.

```python
agent = LLMAgent(max_retries=3)  # The agent will try up to 3 corrections

# If an initial query fails:
# 1. The execution error message is captured.
# 2. This error, along with the original question and failed query, is sent back to the LLM.
# 3. The LLM generates a corrected query based on the feedback.
# 4. This process repeats up to `max_retries` times or until a successful query is generated.
```

### Session Management

The interactive CLI allows you to save and restore your session, including query history and context, for seamless continuation of your analysis.

```bash
# Save the current interactive session
pframe:parquet🤖> \save-session customer_analysis

# Later, in a new terminal or after restarting
pframe:parquet🤖> \load-session customer_analysis
📂 Loaded session: 15 queries in history

pframe:parquet🤖> \history
# Shows all previous queries and their results
```

## Configuration

### Model Selection

List available Ollama models and switch between them programmatically:

```python
from parquetframe.ai import LLMAgent

agent = LLMAgent()
available_models = agent.get_available_models()
print("Available models:", available_models)

# Switch to a different model
agent.set_model("codellama")
```

### Performance Tuning

Adjust LLM parameters to balance performance, creativity, and accuracy:

```python
# For faster, more deterministic (less creative) SQL generation
agent = LLMAgent(temperature=0.0)

# For more creative, potentially less accurate responses (higher temperature)
agent = LLMAgent(temperature=0.3)

# Disable multi-step reasoning for simpler schemas to reduce latency
agent = LLMAgent(use_multi_step=False)

# Increase retry attempts for more aggressive error correction
agent = LLMAgent(max_retries=5)
```

## Best Practices

### 1. Model Selection

* **`codellama`**: Generally recommended for optimal SQL generation and handling complex queries.
* **`llama3.2`**: A good general-purpose model suitable for a wide range of questions.
* **`llama2`**: A viable fallback option for systems with limited resources or specific compatibility needs.

### 2. Query Optimization

* **Be Specific**: Use precise column names and table references in your questions (e.g., "show customer names and emails" instead of "show customer data").
* **Include Constraints**: Specify time ranges (e.g., "sales last month" vs. "recent sales") and filtering criteria.
* **Clarify Aggregations/Sorting**: Clearly state desired aggregations (e.g., "total sales") and sorting preferences (e.g., "top 10 by revenue").

### 3. Schema Design

* **Descriptive Naming**: Use clear and descriptive names for tables and columns.
* **Comments**: Include comments in your `CREATE TABLE` statements (if applicable) to provide additional context for the LLM.
* **Normalization**: A well-normalized schema generally leads to better query generation.

### 4. Error Handling

Implement robust error handling in your programmatic usage to provide helpful feedback to users.

```python
result = await agent.generate_query(question, context)
if result.failed:
    if "column" in result.error.lower():
        print("Hint: The LLM might have used an incorrect column name. Check available columns with \describe table_name in the CLI.")
    elif "table" in result.error.lower():
        print("Hint: The LLM might have referenced an unknown table. Check available tables with \list in the CLI.")
    else:
        print(f"An unexpected error occurred: {result.error}")
```

## Troubleshooting

### Common Issues

1. **"AI functionality not available"**
    * **Solution**: Ensure Ollama is installed, running (`ollama serve`), and you have pulled at least one model (`ollama pull llama3.2`). Also, verify ParquetFrame was installed with `[ai]` extra (`pip install parquetframe[ai,cli]`).

2. **"No tables found"**
    * **Solution**: Check file permissions for your data directory. Verify that Parquet files are valid. In the CLI, use `\list` to see discovered tables.

3. **"Database connection failed"**
    * **Solution**: Verify your database connection string format. Check credentials and network access. Test the connection with a simple client (e.g., `psql`, `sqlite3`) first.

4. **"Query execution failed"**
    * **Solution**: Use `\describe table_name` in the CLI to verify the schema. Examine the generated SQL for syntax errors. Enable debug logging for more detailed error messages.

### Debug Mode

Enable verbose logging to gain deeper insights into the AI agent's operations and query execution:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed logs of:
# - Schema discovery process
# - LLM prompts and responses (including intermediate steps for multi-step reasoning)
# - Generated SQL queries
# - Query execution details and any errors
# - Self-correction attempts
```

## Examples

### E-commerce Analysis

```bash
pframe interactive --path ./ecommerce_parquets/
```

```
pframe:parquet🤖> \ai what\'s our monthly recurring revenue trend?
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
pframe:database🤖> \ai what\'s the portfolio performance this quarter?
pframe:database🤖> \ai show me the most volatile stocks
pframe:database🤖> \ai calculate risk-adjusted returns by sector
```

Ready to explore your data with AI? Start with `pframe interactive --help`! 🚀
