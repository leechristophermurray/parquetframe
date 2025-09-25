# Workflow Step Types

ParquetFrame workflows support various step types for building comprehensive data processing pipelines. Each step type has specific configuration options and capabilities.

## 📖 Overview

| Step Type | Purpose | Input | Output | Key Options |
|-----------|---------|-------|--------|-------------|
| **[read](#read)** | Load data from files | File path | DataFrame | `input`, `output` |
| **[filter](#filter)** | Filter rows by conditions | DataFrame | DataFrame | `input`, `query`, `output` |
| **[select](#select)** | Select/rename columns | DataFrame | DataFrame | `input`, `columns`, `output` |
| **[groupby](#groupby)** | Aggregate operations | DataFrame | DataFrame | `input`, `groupby`, `agg`, `output` |
| **[transform](#transform)** | Custom transformations | DataFrame | DataFrame | `input`, `function`, `output` |
| **[save](#save)** | Write data to files | DataFrame | File | `input`, `output` |

---

## read

Load data from parquet files into the workflow pipeline.

### Configuration

```yaml
- name: "load_data"
  type: "read"
  input: "data.parquet"           # Path to input file
  output: "raw_data"              # Variable name for loaded data
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `input` | string | Yes | Path to input parquet file |
| `output` | string | Yes | Variable name to store loaded DataFrame |

### Advanced Options

```yaml
- name: "load_data"
  type: "read"
  input: "large_dataset.parquet"
  output: "data"
  config:
    columns: ["id", "name", "value"]    # Load specific columns only
    filters: [["status", "==", "active"]]  # PyArrow filters for efficiency
    use_threads: true                    # Enable multithreading
```

### Examples

```yaml
# Basic file loading
- name: "load_customers"
  type: "read"
  input: "customers.parquet"
  output: "customers"

# Load with column selection
- name: "load_subset"
  type: "read"
  input: "large_table.parquet"
  output: "subset"
  config:
    columns: ["customer_id", "order_date", "amount"]

# Load with filters (PyArrow predicate pushdown)
- name: "load_recent"
  type: "read"
  input: "transactions.parquet"
  output: "recent_transactions"
  config:
    filters: [["date", ">=", "2024-01-01"]]
```

---

## filter

Filter DataFrame rows based on query conditions using pandas/Dask query syntax.

### Configuration

```yaml
- name: "filter_active"
  type: "filter"
  input: "customers"              # Input DataFrame variable
  query: "status == 'active'"     # Filter condition
  output: "active_customers"      # Output variable name
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `input` | string | Yes | Input DataFrame variable name |
| `query` | string | Yes | Pandas/Dask query expression |
| `output` | string | Yes | Output DataFrame variable name |

### Query Syntax

Supports full pandas query syntax:

```yaml
# Comparison operations
query: "age > 25"
query: "status == 'active'"
query: "revenue >= 1000"

# Multiple conditions
query: "age > 25 and status == 'active'"
query: "region in ['North', 'South'] or priority == 'high'"

# String operations
query: "name.str.startswith('A')"
query: "email.str.contains('@company.com')"

# Date/datetime operations
query: "order_date >= '2024-01-01'"
query: "created_at.dt.year == 2024"
```

### Examples

```yaml
# Simple filtering
- name: "filter_adults"
  type: "filter"
  input: "customers"
  query: "age >= 18"
  output: "adult_customers"

# Complex conditions
- name: "filter_high_value"
  type: "filter"
  input: "orders"
  query: "amount > 1000 and status == 'confirmed' and region != 'test'"
  output: "high_value_orders"

# Date-based filtering
- name: "filter_recent"
  type: "filter"
  input: "transactions"
  query: "transaction_date >= '2024-01-01' and transaction_date < '2024-02-01'"
  output: "january_transactions"
```

---

## select

Select, rename, or reorder DataFrame columns.

### Configuration

```yaml
- name: "select_columns"
  type: "select"
  input: "raw_data"               # Input DataFrame
  columns: ["id", "name", "email"] # Columns to select
  output: "clean_data"            # Output variable
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `input` | string | Yes | Input DataFrame variable name |
| `columns` | list/dict | Yes | Column selection specification |
| `output` | string | Yes | Output DataFrame variable name |

### Column Selection Formats

#### List Format (Simple Selection)
```yaml
columns: ["customer_id", "name", "email", "signup_date"]
```

#### Dictionary Format (Select + Rename)
```yaml
columns:
  customer_id: "id"              # Rename customer_id to id
  full_name: "name"              # Rename full_name to name
  email_address: "email"         # Rename email_address to email
```

### Examples

```yaml
# Select specific columns
- name: "select_essentials"
  type: "select"
  input: "raw_customers"
  columns: ["id", "name", "email", "created_at"]
  output: "customer_essentials"

# Select and rename
- name: "standardize_columns"
  type: "select"
  input: "raw_data"
  columns:
    customer_id: "id"
    full_name: "name"
    email_addr: "email"
    signup_date: "created_at"
  output: "standardized_data"

# Reorder columns
- name: "reorder_columns"
  type: "select"
  input: "messy_data"
  columns: ["id", "name", "category", "value", "date"]
  output: "ordered_data"
```

---

## groupby

Perform group-by operations with aggregation functions.

### Configuration

```yaml
- name: "aggregate_sales"
  type: "groupby"
  input: "sales_data"             # Input DataFrame
  groupby: ["region", "product"]  # Grouping columns
  agg:                           # Aggregation specification
    revenue: "sum"
    orders: "count"
  output: "sales_summary"         # Output variable
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `input` | string | Yes | Input DataFrame variable name |
| `groupby` | list | Yes | List of columns to group by |
| `agg` | dict | Yes | Aggregation functions per column |
| `output` | string | Yes | Output DataFrame variable name |

### Aggregation Functions

| Function | Description | Example |
|----------|-------------|---------|
| `sum` | Sum values | `revenue: "sum"` |
| `count` | Count non-null values | `orders: "count"` |
| `mean` | Average values | `price: "mean"` |
| `min` / `max` | Minimum/maximum values | `date: "min"` |
| `std` / `var` | Standard deviation/variance | `score: "std"` |
| `first` / `last` | First/last values | `name: "first"` |

### Advanced Aggregations

```yaml
# Multiple functions per column
agg:
  revenue: ["sum", "mean", "count"]
  price: ["min", "max"]

# Named aggregations
agg:
  total_revenue: ("revenue", "sum")
  avg_price: ("price", "mean")
  order_count: ("order_id", "count")
```

### Examples

```yaml
# Sales summary by region
- name: "sales_by_region"
  type: "groupby"
  input: "sales_data"
  groupby: ["region"]
  agg:
    total_revenue: "sum"
    avg_order: "mean"
    order_count: "count"
  output: "regional_sales"

# Customer segmentation
- name: "customer_segments"
  type: "groupby"
  input: "customer_orders"
  groupby: ["customer_id"]
  agg:
    total_spent: "sum"
    order_frequency: "count"
    avg_order_value: "mean"
    first_order: "min"
    last_order: "max"
  output: "customer_metrics"

# Multi-level grouping
- name: "detailed_breakdown"
  type: "groupby"
  input: "transactions"
  groupby: ["region", "category", "month"]
  agg:
    revenue: "sum"
    units: "sum"
    transactions: "count"
  output: "detailed_summary"
```

---

## transform

Apply custom transformation functions to DataFrames.

### Configuration

```yaml
- name: "add_features"
  type: "transform"
  input: "raw_data"               # Input DataFrame
  function: "calculate_metrics"   # Transformation function name
  output: "enriched_data"         # Output variable
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `input` | string | Yes | Input DataFrame variable name |
| `function` | string | Yes | Name of transformation function |
| `output` | string | Yes | Output DataFrame variable name |
| `config` | dict | No | Parameters passed to function |

### Built-in Transformations

| Function | Description | Parameters |
|----------|-------------|------------|
| `add_row_numbers` | Add sequential row numbers | `column_name` (default: "row_number") |
| `normalize_columns` | Normalize numeric columns | `columns` (list), `method` ("min_max", "z_score") |
| `encode_categoricals` | Encode categorical columns | `columns` (list), `method` ("label", "onehot") |
| `fill_missing` | Fill missing values | `strategy` ("mean", "median", "mode", "forward", "backward") |

### Custom Functions

You can register custom transformation functions:

```python
# In your workflow setup
def add_customer_segments(df):
    """Add customer segments based on spending."""
    df = df.copy()
    df['segment'] = df['total_spent'].apply(lambda x:
        'high' if x > 1000 else 'medium' if x > 500 else 'low')
    return df

# Register the function
from parquetframe.workflows import register_transform_function
register_transform_function('add_customer_segments', add_customer_segments)
```

### Examples

```yaml
# Built-in transformation
- name: "normalize_features"
  type: "transform"
  input: "raw_features"
  function: "normalize_columns"
  config:
    columns: ["age", "income", "score"]
    method: "min_max"
  output: "normalized_features"

# Custom transformation
- name: "calculate_metrics"
  type: "transform"
  input: "customer_data"
  function: "add_customer_segments"
  output: "segmented_customers"

# Fill missing values
- name: "clean_data"
  type: "transform"
  input: "raw_data"
  function: "fill_missing"
  config:
    strategy: "mean"
    columns: ["age", "income"]
  output: "clean_data"
```

---

## save

Write DataFrame data to parquet files.

### Configuration

```yaml
- name: "save_results"
  type: "save"
  input: "processed_data"         # Input DataFrame variable
  output: "results.parquet"       # Output file path
```

### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `input` | string | Yes | Input DataFrame variable name |
| `output` | string | Yes | Output file path |
| `config` | dict | No | Additional save options |

### Advanced Configuration

```yaml
- name: "save_partitioned"
  type: "save"
  input: "large_dataset"
  output: "partitioned_data.parquet"
  config:
    partition_cols: ["year", "month"]    # Partition by columns
    compression: "snappy"               # Compression algorithm
    row_group_size: 50000              # Rows per row group
    write_index: false                 # Don't write pandas index
```

### Save Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `compression` | string | "snappy" | Compression: snappy, gzip, lz4, brotli |
| `partition_cols` | list | None | Columns to partition by |
| `row_group_size` | int | 50000 | Number of rows per row group |
| `write_index` | bool | True | Whether to write DataFrame index |
| `coerce_timestamps` | string | None | Timestamp coercion: "ms", "us" |

### Examples

```yaml
# Simple save
- name: "save_clean_data"
  type: "save"
  input: "cleaned_customers"
  output: "clean_customers.parquet"

# Partitioned save for large datasets
- name: "save_partitioned"
  type: "save"
  input: "transaction_data"
  output: "transactions_by_date.parquet"
  config:
    partition_cols: ["year", "month"]
    compression: "lz4"
    row_group_size: 100000

# Compressed save
- name: "save_compressed"
  type: "save"
  input: "large_dataset"
  output: "compressed_data.parquet"
  config:
    compression: "brotli"
    write_index: false
```

## 🔗 Step Dependencies

Steps automatically form dependencies based on input/output relationships:

```yaml
steps:
  - name: "load"         # No dependencies
    type: "read"
    input: "data.parquet"
    output: "raw"

  - name: "clean"        # Depends on "load"
    type: "filter"
    input: "raw"         # Uses output from "load"
    output: "clean"

  - name: "analyze"      # Depends on "clean"
    type: "groupby"
    input: "clean"       # Uses output from "clean"
    groupby: ["category"]
    agg: {revenue: "sum"}
    output: "summary"
```

## 🎯 Best Practices

### Naming Conventions
- Use descriptive step names: `load_customers`, `filter_active_users`
- Use consistent variable names: `customers` → `active_customers` → `customer_segments`

### Performance Optimization
- Use PyArrow filters in `read` steps for large files
- Leverage column selection to reduce memory usage
- Consider partitioning for very large outputs

### Error Handling
- Validate data at key transformation points
- Use meaningful output variable names for debugging
- Test workflows with `--validate` before execution

### Modularity
- Break complex operations into multiple steps
- Use consistent naming patterns across workflows
- Document custom transformation functions
