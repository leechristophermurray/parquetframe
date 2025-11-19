# CLI Walkthrough

ParquetFrame provides a powerful Command Line Interface (CLI) for interacting with your data files without writing Python scripts.

## Basic Usage

The basic command structure is:

```bash
pf <command> [options] <file_path>
```

### Inspecting a File

Get a quick summary of a Parquet (or CSV/JSON) file:

```bash
pf inspect data.parquet
```

**Output:**
```text
File: data.parquet
Rows: 1,000,000
Columns: 5
Schema:
  - id: int64
  - user_id: string
  - amount: double
  - timestamp: datetime64[ns]
  - category: category
```

## Interactive Mode

Launch an interactive shell to explore data:

```bash
pf interactive data.parquet
```

This drops you into an IPython shell with the dataframe loaded as `df`.

```python
In [1]: df.head()
# ... shows dataframe head ...
```

## SQL Mode

Run SQL queries directly on your files using DuckDB:

```bash
pf sql "SELECT category, SUM(amount) FROM 'data.parquet' GROUP BY category"
```

You can also pipe the output:

```bash
pf sql "SELECT * FROM 'data.parquet' LIMIT 5" --format csv > output.csv
```

## AI Mode (Experimental)

Use natural language to query your data. Requires `OPENAI_API_KEY` to be set.

```bash
export OPENAI_API_KEY="sk-..."
pf ai data.parquet "What is the total revenue by category?"
```

**Output:**
```text
Thinking...
Generated SQL:
SELECT category, SUM(amount) as total_revenue FROM df GROUP BY category

Result:
   category  total_revenue
0  electronics       5430.50
1       books       2100.25
...
```

### Explaining Data

You can also ask for explanations:

```bash
pf ai data.parquet "Explain the distribution of the 'amount' column"
```

**Output:**
```text
The 'amount' column appears to be normally distributed with a mean of 50.2 and a standard deviation of 12.5. There are some outliers above 100.0.
```

## Batch Processing

Process multiple files using a YAML workflow:

```bash
pf run-workflow pipeline.yaml
```

See [YAML Workflows](../yaml-workflows/index.md) for more details.
