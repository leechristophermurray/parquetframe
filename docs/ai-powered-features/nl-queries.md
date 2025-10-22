# Natural Language Queries

Transform your data exploration workflow with ParquetFrame's AI-powered natural language query system. Ask questions about your data in plain English and get SQL queries generated automatically.

## Overview

ParquetFrame's AI query system uses local Large Language Models (via Ollama) to convert natural language questions into SQL queries. This enables intuitive data exploration without requiring SQL expertise, while maintaining privacy through local inference.

## Key Features

- **Local LLM Inference**: Privacy-preserving query generation using Ollama
- **Self-Correction**: Automatic error detection and query refinement
- **Multi-Step Reasoning**: Handles complex schemas with intelligent table selection
- **Context Awareness**: Understands your data schema for accurate queries
- **Interactive Integration**: Seamless CLI and programmatic usage

## Quick Start

### Prerequisites

1. Install Ollama and pull a model:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull a model
   ollama pull llama3.2  # or codellama for better SQL
   ```

2. Install ParquetFrame with AI support:
   ```bash
   pip install parquetframe[ai]
   ```

### Basic Usage

```python
import asyncio
import parquetframe as pf
from parquetframe.ai import LLMAgent

async def analyze_sales_data():
    # Load your data
    sales = pf.read("sales_data.parquet")

    # Create AI agent
    agent = LLMAgent(model_name="llama3.2")

    # Ask questions in natural language
    result = await agent.generate_query(
        "What are the top 5 customers by total sales amount?",
        sales
    )

    if result.success:
        print(f"Generated SQL: {result.query}")
        print(f"Results:\n{result.result}")
        print(f"Execution time: {result.execution_time_ms:.2f}ms")
    else:
        print(f"Query failed: {result.error}")

# Run the analysis
asyncio.run(analyze_sales_data())
```

## Query Examples

### Simple Data Exploration

```python
# Basic filtering
result = await agent.generate_query(
    "Show me all customers from California",
    customers_df
)

# Counting and aggregation
result = await agent.generate_query(
    "How many orders were placed last month?",
    orders_df
)

# Sorting and limiting
result = await agent.generate_query(
    "Give me the 10 most expensive products",
    products_df
)
```

### Complex Analytics

```python
# Time-based analysis
result = await agent.generate_query(
    "What is the monthly sales trend for the last year?",
    sales_df
)

# Group by operations
result = await agent.generate_query(
    "Show me average order value by customer segment",
    orders_df
)

# Advanced filtering
result = await agent.generate_query(
    "Find customers who haven't ordered in the last 6 months but had orders before that",
    customer_orders_df
)
```

### Business Intelligence Queries

```python
# Revenue analysis
result = await agent.generate_query(
    "What percentage of total revenue comes from our top 20% of customers?",
    sales_df
)

# Product performance
result = await agent.generate_query(
    "Which products have declining sales compared to last quarter?",
    product_sales_df
)

# Customer behavior
result = await agent.generate_query(
    "Show me customers with unusual purchase patterns this month",
    transactions_df
)
```

## Advanced Features

### Multi-Step Reasoning

For complex databases with many tables, enable multi-step reasoning:

```python
# Better for complex schemas
agent = LLMAgent(
    model_name="llama3.2",
    use_multi_step=True,  # Enables table selection first
    max_retries=3
)

# The agent will:
# 1. First identify relevant tables for the question
# 2. Generate focused SQL using only those tables
result = await agent.generate_query(
    "Show me customer lifetime value by acquisition channel",
    data_context
)
```

### Self-Correction

The AI agent automatically fixes failed queries:

```python
agent = LLMAgent(
    model_name="codellama",  # Better for SQL generation
    max_retries=3,          # Try up to 3 corrections
    temperature=0.1         # More deterministic
)

# If initial query fails:
# 1. Error message is analyzed
# 2. Corrected query is generated
# 3. Process repeats up to max_retries
result = await agent.generate_query(
    "Find the correlation between customer age and purchase frequency",
    customer_data
)

print(f"Query succeeded after {result.attempts} attempts")
```

### Custom Examples

Improve performance with domain-specific examples:

```python
agent = LLMAgent()

# Add examples for better performance
agent.add_custom_example(
    question="show me high value customers",
    sql="SELECT customer_id, total_spent FROM customers WHERE total_spent > 10000 ORDER BY total_spent DESC"
)

agent.add_custom_example(
    question="monthly revenue trend",
    sql="SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as revenue FROM orders GROUP BY month ORDER BY month"
)
```

## Interactive CLI Usage

Use natural language queries directly in the interactive CLI:

```bash
# Start interactive mode with AI
pframe interactive sales_data.parquet --ai

# In the interactive session:
pframe:parquet🤖> \ai what were the best selling products last quarter?

🤖 Processing: what were the best selling products last quarter?

📝 Generated Query:
SELECT product_name, SUM(quantity) as total_sold
FROM df
WHERE order_date >= '2024-07-01' AND order_date < '2024-10-01'
GROUP BY product_name
ORDER BY total_sold DESC
LIMIT 10

🚀 Execute this query? [Y/n]: y

# Results displayed automatically
```

## Model Selection

### Recommended Models

- **codellama**: Best for SQL generation and complex queries
- **llama3.2**: Good general-purpose model with strong reasoning
- **llama2**: Reliable fallback for older systems

```python
# Model-specific configurations
sql_agent = LLMAgent(model_name="codellama")    # Best for SQL
general_agent = LLMAgent(model_name="llama3.2") # General purpose

# Check available models
available_models = agent.get_available_models()
print("Available models:", available_models)
```

### Performance Tuning

```python
# Faster, more deterministic (recommended for production)
agent = LLMAgent(
    temperature=0.0,        # Deterministic output
    use_multi_step=False,   # Skip for simple schemas
    max_retries=1          # Faster execution
)

# More creative, potentially better results (for exploration)
agent = LLMAgent(
    temperature=0.3,        # More creative
    max_retries=5,         # More correction attempts
    use_multi_step=True    # Better for complex queries
)
```

## Integration with DataContext

For advanced data source management:

```python
from parquetframe.datacontext import DataContextFactory

async def advanced_ai_analysis():
    # Connect to data source (parquet files or database)
    context = DataContextFactory.create_from_path("./sales_data/")
    await context.initialize()

    # Use with AI agent
    agent = LLMAgent(model_name="llama3.2")

    # Agent understands the full schema context
    result = await agent.generate_query(
        "What's the correlation between customer demographics and purchase behavior?",
        context
    )

    if result.success:
        print(f"Found insights in {result.execution_time_ms:.2f}ms")
        display(result.result)

    context.close()

asyncio.run(advanced_ai_analysis())
```

## Best Practices

### 1. Be Specific in Questions

✅ **Good**: "Show me customers who spent more than $1000 last month"
❌ **Vague**: "Show me good customers"

### 2. Include Time Contexts

✅ **Good**: "What were the top products by revenue in Q3 2024?"
❌ **Unclear**: "What are the top products?"

### 3. Specify Metrics Clearly

✅ **Good**: "Calculate average order value by customer segment"
❌ **Ambiguous**: "Show me customer performance"

### 4. Use Domain Terms Consistently

```python
# If your data uses specific terms, use them in queries
result = await agent.generate_query(
    "Show me the conversion rate from leads to customers by marketing channel",
    crm_data  # Agent learns your schema and terminology
)
```

### 5. Validate Results

```python
# Always check the generated SQL for complex queries
result = await agent.generate_query(question, data)
if result.success:
    print(f"Generated SQL: {result.query}")
    print(f"Row count: {len(result.result)}")
    print(f"Columns: {list(result.result.columns)}")
```

## Error Handling

```python
try:
    result = await agent.generate_query("complex question", data)

    if result.success:
        # Process successful result
        analyze_results(result.result)
    else:
        # Handle query generation failure
        print(f"Query failed after {result.attempts} attempts")
        print(f"Error: {result.error}")

        # Optionally try a simpler version
        simplified_result = await agent.generate_query(
            "simplified version of question", data
        )

except Exception as e:
    print(f"Unexpected error: {e}")
```

## Troubleshooting

### Common Issues

1. **"No suitable model found"**
   ```bash
   # Pull the required model
   ollama pull llama3.2
   ```

2. **"Query generation failed"**
   ```python
   # Try a different model or simpler question
   agent = LLMAgent(model_name="codellama")  # Better for SQL
   ```

3. **"Schema context too large"**
   ```python
   # Enable multi-step reasoning for complex schemas
   agent = LLMAgent(use_multi_step=True)
   ```

4. **Slow query generation**
   ```python
   # Reduce temperature and retries for faster execution
   agent = LLMAgent(temperature=0.0, max_retries=1)
   ```

## Related Documentation

- [AI Features Overview](../ai-powered-features/index.md)
- [Local LLM Setup](setup.md)
- [Prompt Engineering](prompts.md)
- [Interactive CLI Mode](../cli-interface/interactive.md)
