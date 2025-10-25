# Natural Language Queries

Transform your data exploration workflow with ParquetFrame's AI-powered natural language query system. Ask questions about your data in plain English and get SQL queries generated automatically.

## Overview

ParquetFrame's AI query system uses local Large Language Models (via Ollama) to convert natural language questions into SQL queries. This enables intuitive data exploration without requiring SQL expertise, while maintaining privacy through local inference.

## Key Features

*   **Local LLM Inference**: Privacy-preserving query generation using Ollama, ensuring your data remains on your machine.
*   **Self-Correction**: Automatic error detection and query refinement, where the LLM attempts to fix failed queries based on execution feedback.
*   **Multi-Step Reasoning**: Handles complex schemas by intelligently selecting relevant tables before generating the final query, improving accuracy and reducing context size.
*   **Context Awareness**: Understands your data schema (table and column names, data types) to generate accurate and relevant queries.
*   **Interactive Integration**: Seamlessly integrated into both the CLI and programmatic Python API for flexible usage.

## Quick Start

### Prerequisites

1.  **Install Ollama and pull a model**:
    ```bash
    # Install Ollama (follow instructions for your OS)
    curl -fsSL https://ollama.ai/install.sh | sh

    # Pull a model (e.g., llama3.2 for general use, or codellama for better SQL generation)
    ollama pull llama3.2
    ```

2.  **Install ParquetFrame with AI support**:
    ```bash
    pip install parquetframe[ai]
    ```

### Basic Usage (Python API)

```python
import asyncio
import parquetframe as pf
from parquetframe.ai import LLMAgent

async def analyze_sales_data():
    # Load your data (ParquetFrame automatically detects format and backend)
    sales_df = pf.read("sales_data.parquet")

    # Create an AI agent instance
    agent = LLMAgent(model_name="llama3.2")

    # Ask questions in natural language
    question = "What are the top 5 customers by total sales amount?"
    print(f"Question: {question}")

    result = await agent.generate_query(
        question,
        sales_df # Pass the DataFrame as context
    )

    if result.success:
        print(f"Generated SQL: {result.query}")
        print(f"Results:\n{result.result.head()}") # Display top rows of the result
        print(f"Execution time: {result.execution_time_ms:.2f}ms")
    else:
        print(f"Query failed: {result.error}")

# Run the asynchronous analysis
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
    "Find customers who haven\'t ordered in the last 6 months but had orders before that",
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

For complex databases with many tables or intricate schemas, enabling multi-step reasoning can significantly improve the LLM\'s ability to generate accurate queries.

```python
agent = LLMAgent(
    model_name="llama3.2",
    use_multi_step=True,  # Enables multi-step reasoning
    max_retries=3         # Allows for self-correction in multiple steps
)

# When `use_multi_step` is enabled, the agent will:
# 1. First, identify the most relevant tables for the natural language question.
# 2. Then, generate the SQL query using only the context of those selected tables.
# This approach reduces the cognitive load on the LLM and improves accuracy.
result = await agent.generate_query(
    "Show me customer lifetime value by acquisition channel",
    data_context # Pass a DataContext object for multi-table queries
)
```

### Self-Correction

ParquetFrame\'s LLM agent is designed to be resilient. If a generated query fails upon execution, the error message is fed back to the LLM, which then attempts to generate a corrected query.

```python
agent = LLMAgent(
    model_name="codellama",  # Often better for SQL generation and self-correction
    max_retries=3,          # The agent will try up to 3 corrections
    temperature=0.1         # Lower temperature for more deterministic corrections
)

# If the initial query fails, the agent will attempt to self-correct.
result = await agent.generate_query(
    "Find the correlation between customer age and purchase frequency",
    customer_data
)

print(f"Query succeeded after {result.attempts} attempts")
```

### Custom Examples

Improve the LLM agent\'s performance and accuracy for domain-specific queries by providing custom examples (question-SQL pairs). This acts as a form of few-shot learning.

```python
agent = LLMAgent()

# Add custom examples for better performance on specific query patterns
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

Use natural language queries directly in the interactive CLI (`pframe interactive`) for a seamless data exploration experience.

```bash
# Start interactive mode with AI enabled, pointing to your data
pframe interactive sales_data.parquet --ai

# In the interactive session, use the \ai command:
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

# Results will be displayed automatically in a formatted table.
```

## Model Selection

### Recommended Models

*   **`codellama`**: Generally recommended for optimal SQL generation and handling complex queries due to its code-focused training.
*   **`llama3.2`**: A good general-purpose model suitable for a wide range of questions, offering strong reasoning capabilities.
*   **`llama2`**: A reliable fallback option for systems with limited resources or specific compatibility needs.

```python
# You can specify the model when initializing the agent
sql_agent = LLMAgent(model_name="codellama")
general_agent = LLMAgent(model_name="llama3.2")

# Check available models from your Ollama instance
available_models = agent.get_available_models()
print("Available models:", available_models)
```

### Performance Tuning

Adjust LLM parameters to balance performance, creativity, and accuracy:

```python
# For faster, more deterministic (less creative) SQL generation, recommended for production
agent = LLMAgent(
    temperature=0.0,        # Lower temperature for more predictable output
    use_multi_step=False,   # Disable for simpler schemas to reduce latency
    max_retries=1           # Fewer retries for faster execution
)

# For more creative, potentially better results (for exploration or complex, ambiguous questions)
agent = LLMAgent(
    temperature=0.3,        # Higher temperature for more diverse output
    max_retries=5,          # More correction attempts for resilience
    use_multi_step=True     # Enable for complex queries involving multiple tables
)
```

## Integration with DataContext

For advanced data source management, the `LLMAgent` integrates seamlessly with ParquetFrame\'s `DataContext` system. This allows the agent to understand the full schema context of various data sources (Parquet files, databases) and generate more accurate queries.

```python
import asyncio
from parquetframe.datacontext import DataContextFactory
from parquetframe.ai import LLMAgent

async def advanced_ai_analysis():
    # Connect to a data source (e.g., a directory of Parquet files or a database URI)
    context = DataContextFactory.create_from_path("./sales_data/")
    await context.initialize()

    # Initialize AI agent
    agent = LLMAgent(model_name="llama3.2")

    # The agent now understands the full schema context provided by the DataContext
    question = "What\'s the correlation between customer demographics and purchase behavior?"
    result = await agent.generate_query(
        question,
        context # Pass the DataContext object
    )

    if result.success:
        print(f"Found insights in {result.execution_time_ms:.2f}ms")
        # display(result.result) # Uncomment to display results
    else:
        print(f"Query failed: {result.error}")

    context.close()

asyncio.run(advanced_ai_analysis())
```

## Best Practices

### 1. Be Specific in Questions

*   ✅ **Good**: "Show me customers who spent more than $1000 last month"
*   ❌ **Vague**: "Show me good customers"

### 2. Include Time Contexts

*   ✅ **Good**: "What were the top products by revenue in Q3 2024?"
*   ❌ **Unclear**: "What are the top products?"

### 3. Specify Metrics Clearly

*   ✅ **Good**: "Calculate average order value by customer segment"
*   ❌ **Ambiguous**: "Show me customer performance"

### 4. Use Domain Terms Consistently

If your data uses specific terminology, use those terms in your natural language queries. The LLM agent will learn from the provided schema and examples.

```python
# Example: If your CRM data uses 'marketing_channel'
result = await agent.generate_query(
    "Show me the conversion rate from leads to customers by marketing_channel",
    crm_data
)
```

### 5. Validate Results

Always review the generated SQL and the resulting DataFrame, especially for complex queries, to ensure they align with your intent.

```python
result = await agent.generate_query(question, data)
if result.success:
    print(f"Generated SQL: {result.query}")
    print(f"Row count: {len(result.result)}")
    print(f"Columns: {list(result.result.columns)}")
```

## Error Handling

Implement robust error handling in your programmatic usage to manage query generation and execution failures gracefully.

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

        # Optionally, try a simpler version of the question
        simplified_result = await agent.generate_query(
            "simplified version of question", data
        )

except Exception as e:
    print(f"An unexpected error occurred during AI query: {e}")
```

## Troubleshooting

### Common Issues

1.  **"No suitable model found"**
    *   **Solution**: Ensure you have pulled the required model using `ollama pull <model_name>`.

2.  **"Query generation failed"**
    *   **Solution**: Try a different model (e.g., `codellama` for SQL). Simplify your question. Increase `max_retries` for self-correction.

3.  **"Schema context too large"**
    *   **Solution**: Enable multi-step reasoning (`use_multi_step=True`) for complex schemas to reduce the context size sent to the LLM.

4.  **Slow query generation**
    *   **Solution**: Reduce `temperature` and `max_retries` for faster, more deterministic execution. Consider using a smaller, faster LLM if available.

## Related Documentation

*   [AI Features Overview](./overview.md) - General introduction to ParquetFrame\'s AI capabilities.
*   [Local LLM Setup](./setup.md) - Detailed guide on setting up Ollama and LLMs.
*   [Prompt Engineering](./prompts.md) - Understanding how prompts are constructed for the LLM.
*   [Interactive CLI Mode](../cli-interface/interactive.md) - More details on the interactive command-line interface.
