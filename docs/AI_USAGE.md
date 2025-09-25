# AI-Powered Query Guide

This guide covers using ParquetFrame's AI features for natural language data queries.

## Setup

### Prerequisites

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai) or:
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Install ParquetFrame with AI support**:
   ```bash
   pip install parquetframe[ai]
   ```

3. **Start Ollama and pull a model**:
   ```bash
   # Start Ollama service
   ollama serve

   # In another terminal, pull a model
   ollama pull llama3.2  # or codellama, mistral, etc.
   ```

## Basic Usage

### Python API

```python
import asyncio
import parquetframe as pf
from parquetframe.ai import LLMAgent

async def main():
    # Load your data
    sales_data = pf.read("sales_data.parquet")

    # Create AI agent
    agent = LLMAgent(model_name="llama3.2")

    # Ask questions in natural language
    result = await agent.generate_query(
        "Show me the top 10 customers by total sales amount",
        sales_data
    )

    if result.success:
        print("Generated SQL:")
        print(result.query)
        print("\nResults:")
        print(result.result.head())
    else:
        print(f"Error: {result.error}")

# Run the async function
asyncio.run(main())
```

### CLI Usage

```bash
# Interactive mode with AI
pframe interactive sales_data.parquet --ai

# Direct queries
pframe query "What are the top selling products?" --file sales_data.parquet --ai

# Check dependencies
pframe deps
```

## Query Examples

### Basic Queries

```python
# Simple selection
result = await agent.generate_query(
    "Show me all customers from New York",
    customers_df
)

# Filtering with conditions
result = await agent.generate_query(
    "Find all orders with amount greater than 1000",
    orders_df
)

# Counting records
result = await agent.generate_query(
    "How many unique customers do we have?",
    customers_df
)
```

### Aggregation Queries

```python
# Group by and sum
result = await agent.generate_query(
    "What is the total sales amount by region?",
    sales_df
)

# Average calculations
result = await agent.generate_query(
    "What's the average order value per customer?",
    orders_df
)

# Complex aggregations
result = await agent.generate_query(
    "Show me monthly sales trends for the last year",
    sales_df
)
```

### Advanced Queries

```python
# Ranking and top-N
result = await agent.generate_query(
    "Who are the top 5 customers by lifetime value?",
    customer_orders_df
)

# Date-based queries
result = await agent.generate_query(
    "Show me sales performance by quarter",
    sales_df
)

# Complex filtering
result = await agent.generate_query(
    "Find customers who haven't ordered in the last 6 months",
    customer_orders_df
)
```

## Interactive CLI Mode

When using `pframe interactive --ai`, you get enhanced capabilities:

### Special Commands

```bash
# In interactive mode:
\\help     # Show available commands
\\deps     # Check AI dependencies
\\ai       # Toggle AI mode
\\quit     # Exit session

# AI queries (just type naturally):
show me all users from California
what is the average age by department?
how many orders were placed last month?
```

### Example Session

```bash
$ pframe interactive sales.parquet --ai

🚀 Welcome to ParquetFrame Interactive Mode
Data source: sales.parquet
Type: parquet
AI enabled: Yes

Type \help for available commands

pframe:parquet🤖> show me the top 5 products by sales

🤖 Generating SQL query...
Generated: SELECT product_name, SUM(sales_amount) as total_sales
          FROM df GROUP BY product_name
          ORDER BY total_sales DESC LIMIT 5

   product_name  total_sales
0        Widget      125000.0
1        Gadget       98500.0
2     Doohickey       87200.0
3        Thingamajig    76800.0
4        Whatsit       65300.0

pframe:parquet🤖> what about by profit margin?

🤖 Generating SQL query...
Generated: SELECT product_name,
                 AVG((sales_amount - cost) / sales_amount * 100) as avg_margin
          FROM df
          GROUP BY product_name
          ORDER BY avg_margin DESC LIMIT 5

# Results displayed...

pframe:parquet🤖> \quit
👋 Goodbye!
```

## Configuration Options

### Model Selection

```python
# Different models for different use cases
agent_fast = LLMAgent(model_name="llama3.2")       # Fast, good for simple queries
agent_smart = LLMAgent(model_name="codellama")     # Better for complex SQL
agent_custom = LLMAgent(model_name="mistral")      # Alternative option

# Custom parameters
agent = LLMAgent(
    model_name="llama3.2",
    temperature=0.1,      # Lower = more deterministic
    max_retries=3,        # Retry failed queries
    use_multi_step=True   # Better for complex queries
)
```

### Query Customization

```python
# The agent automatically:
# 1. Analyzes your data schema
# 2. Generates appropriate SQL
# 3. Executes the query
# 4. Returns results with error handling

# Self-correction example
result = await agent.generate_query(
    "Show me average sales by city",  # Might initially reference wrong column
    sales_df
)
# Agent will retry with corrected column names if first attempt fails
```

## Best Practices

### 1. Clear and Specific Questions

```python
# Good
"Show me the top 10 customers by total purchase amount"

# Better
"Show me the top 10 customers by total purchase amount in 2023"

# Best
"Show me the top 10 customers by total purchase amount in 2023, including their email addresses"
```

### 2. Provide Context

```python
# If your data has specific business context, mention it
"Show me products with low inventory (less than 50 units)"
"Find customers at risk of churning (no orders in 90+ days)"
"Identify seasonal trends in our sales data"
```

### 3. Error Handling

```python
async def safe_query(agent, question, data):
    try:
        result = await agent.generate_query(question, data)

        if result.success:
            return result.result
        else:
            print(f"Query failed: {result.error}")
            # Maybe try a simpler version of the question
            return None

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

## Troubleshooting

### Common Issues

**"AI features are disabled"**
- Ensure ollama is installed and running
- Check that you have a model pulled: `ollama list`
- Verify installation: `pip install parquetframe[ai]`

**"Model not found"**
- Pull the model: `ollama pull llama3.2`
- Check available models: `ollama list`

**"Query generation failed"**
- Try rephrasing your question
- Check that your data has the columns you're asking about
- Use simpler language

**"Connection refused"**
- Start ollama service: `ollama serve`
- Check if running on different port

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show:
# - Generated prompts
# - Model responses
# - SQL generation process
# - Error details
```

### Performance Tips

1. **Use appropriate models**: `llama3.2` for speed, `codellama` for complex SQL
2. **Keep questions focused**: Multiple simple queries vs. one complex query
3. **Cache common patterns**: Save frequently used queries
4. **Monitor resource usage**: Large models need more RAM/CPU

## Advanced Features

### Multi-step Queries

For complex questions, enable multi-step processing:

```python
agent = LLMAgent(use_multi_step=True)

result = await agent.generate_query(
    "Compare monthly sales between this year and last year, showing percentage growth",
    sales_df
)
```

### Custom Prompts

```python
from parquetframe.ai.prompts import QueryPromptBuilder

# Customize prompt templates for domain-specific queries
builder = QueryPromptBuilder()
custom_prompt = builder.build_for_context(
    schema=df.get_schema_as_text(),
    main_table="sales_data",
    additional_context="This is e-commerce sales data with seasonal patterns"
)
```

### Integration with Workflows

```python
# In YAML workflows, you can use AI queries
# workflow.yml:
# steps:
#   - name: ai_analysis
#     type: ai_query
#     question: "What are our best performing product categories?"
#     output: category_analysis.parquet
```

## Examples by Domain

### E-commerce Analytics

```python
# Customer analysis
await agent.generate_query("Who are our most valuable customers?", customers_df)
await agent.generate_query("What's the customer lifetime value by segment?", orders_df)

# Product performance
await agent.generate_query("Which products have the highest return rate?", returns_df)
await agent.generate_query("Show seasonal trends for each product category", sales_df)

# Business insights
await agent.generate_query("Calculate conversion rate by marketing channel", sessions_df)
```

### Financial Analysis

```python
# Revenue analysis
await agent.generate_query("Show monthly recurring revenue growth", subscriptions_df)
await agent.generate_query("What's our churn rate by customer segment?", customers_df)

# Cost analysis
await agent.generate_query("Break down operating costs by department", expenses_df)
```

### Operations Analytics

```python
# Performance metrics
await agent.generate_query("What's our order fulfillment time by region?", orders_df)
await agent.generate_query("Show inventory turnover by product", inventory_df)

# Quality metrics
await agent.generate_query("Calculate defect rate by production line", quality_df)
```

Remember: The AI agent works best when your questions are clear, specific, and related to the actual data structure in your parquet files!
