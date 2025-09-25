# Workflow CLI Commands

ParquetFrame provides comprehensive command-line tools for workflow management, execution, and monitoring.

## `pframe workflow`

Execute, validate, or visualize YAML workflow definitions.

### Usage

```bash
pframe workflow <workflow_file> [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `workflow_file` | PATH | Yes* | Path to YAML workflow definition file |

*Required for execution/validation. Optional for `--list-steps` and `--create-example`.

### Options

#### Execution Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--variables` | `-V` | TEXT | Set workflow variables as `key=value` pairs |
| `--validate` | `-v` | FLAG | Validate workflow without executing |
| `--quiet` | `-q` | FLAG | Run in quiet mode with minimal output |

#### Workflow Management

| Option | Type | Description |
|--------|------|-------------|
| `--list-steps` | FLAG | List all available workflow step types |
| `--create-example` | PATH | Create example workflow at specified path |

#### Visualization Options

| Option | Type | Options | Description |
|--------|------|---------|-------------|
| `--visualize` | CHOICE | `graphviz`, `networkx`, `mermaid` | Generate workflow visualization |
| `--viz-output` | PATH | - | Output path for visualization file |
| `--viz-format` | CHOICE | `svg`, `png`, `pdf`, `dot` | Visualization format (default: svg) |

### Examples

#### Basic Execution

```bash
# Execute workflow
pframe workflow pipeline.yml

# Execute with variables
pframe workflow pipeline.yml --variables "input_dir=data,min_age=21"

# Quiet execution
pframe workflow pipeline.yml --quiet
```

#### Validation and Setup

```bash
# Validate workflow syntax
pframe workflow pipeline.yml --validate

# Create example workflow
pframe workflow --create-example my_pipeline.yml

# List available step types
pframe workflow --list-steps
```

#### Visualization

```bash
# Generate Graphviz SVG
pframe workflow pipeline.yml --visualize graphviz --viz-output dag.svg

# Generate Mermaid diagram
pframe workflow pipeline.yml --visualize mermaid --viz-output diagram.md

# Generate PNG with NetworkX
pframe workflow pipeline.yml --visualize networkx --viz-output graph.png
```

### Sample Output

#### Execution Output

```
[EXECUTING] Executing workflow: data_pipeline.yml
[VARIABLES] Variables: {'min_revenue': 1000, 'region': 'US'}

[STEP 1/4] load_customers (read)
✓ Loaded 50,000 rows from raw_customers.parquet (pandas backend)
Duration: 1.23s | Memory: 45.2MB

[STEP 2/4] filter_active (filter)
✓ Filtered to 32,156 rows (64.3% retention)
Duration: 0.45s | Memory: 28.9MB

[STEP 3/4] add_segments (transform)
✓ Applied transformation function
Duration: 2.18s | Memory: 31.4MB

[STEP 4/4] save_results (save)
✓ Saved 32,156 rows to customer_segments.parquet
Duration: 0.89s | Memory: 31.4MB

[SUCCESS] Workflow execution completed successfully!
Total Duration: 4.75s | Peak Memory: 45.2MB
```

#### Validation Output

```
[VALIDATING] Validating workflow: pipeline.yml

[SUCCESS] Workflow validation passed!

[SUMMARY] Workflow summary:
  • Name: Customer Data Pipeline
  • Description: Process customer data and generate insights
  • Steps: 4
  • Variables: 2

[STATS] Workflow DAG Statistics:
  • Total Steps: 4
  • Dependencies: 3
  • Is Valid DAG: True
  • Longest Path: 4
```

---

## `pframe workflow-history`

View and manage workflow execution history with detailed analytics.

### Usage

```bash
pframe workflow-history [OPTIONS]
```

### Options

#### Filtering Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--workflow-name` | `-w` | TEXT | Filter by specific workflow name |
| `--status` | `-s` | CHOICE | Filter by status: `completed`, `failed`, `running` |
| `--limit` | `-l` | INT | Limit number of records (default: 10) |

#### Display Options

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--details` | `-d` | FLAG | Show detailed execution information |
| `--stats` | | FLAG | Show aggregate statistics |

#### Management Options

| Option | Type | Description |
|--------|------|-------------|
| `--cleanup` | INT | Clean up history files older than N days |

### Examples

#### Viewing History

```bash
# Show recent executions
pframe workflow-history

# Filter by workflow name
pframe workflow-history --workflow-name "Customer Pipeline"

# Show only failed executions
pframe workflow-history --status failed --limit 5

# Detailed view of recent executions
pframe workflow-history --details --limit 3
```

#### Statistics and Analytics

```bash
# Show aggregate statistics
pframe workflow-history --stats

# Statistics for specific workflow
pframe workflow-history --workflow-name "Data Pipeline" --stats
```

#### History Management

```bash
# Clean up files older than 30 days
pframe workflow-history --cleanup 30

# Show more results
pframe workflow-history --limit 25
```

### Sample Output

#### Summary View

```
[HISTORY] Workflow Execution History

Recent Workflow Executions
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┓
┃ Execution ID               ┃ Workflow             ┃ Status    ┃ Started             ┃ Duration  ┃ Steps ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━┩
│ customer_pipeline_1698... │ Customer Pipeline    │ completed │ 2024-01-15 14:30:25 │ 4.75s     │ 4     │
│ data_etl_1698...          │ Data ETL Pipeline    │ completed │ 2024-01-15 13:45:12 │ 12.34s    │ 6     │
│ ml_training_1698...       │ ML Training Pipeline │ failed    │ 2024-01-15 12:15:33 │ 45.67s    │ 8     │
└────────────────────────────┴──────────────────────┴───────────┴─────────────────────┴───────────┴───────┘

Showing latest 10 records. Use --limit to see more.
```

#### Detailed View

```
==================================================
Execution ID: customer_pipeline_1698765425_a1b2c3d4
Workflow: Customer Data Pipeline
Status: completed
Started: 2024-01-15 14:30:25
Duration: 4.75s
Peak Memory: 45.2MB

Steps (4):
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Step            ┃ Type      ┃ Status    ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ load_customers  │ read      │ completed │ 1.23s    │
│ filter_active   │ filter    │ completed │ 0.45s    │
│ add_segments    │ transform │ completed │ 2.18s    │
│ save_results    │ save      │ completed │ 0.89s    │
└─────────────────┴───────────┴───────────┴──────────┘
```

#### Statistics View

```
Workflow Statistics - Customer Data Pipeline
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Metric              ┃ Value          ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Total Executions    │ 15             │
│ Successful          │ 13             │
│ Failed              │ 2              │
│ Success Rate        │ 86.7%          │
│ Avg Duration        │ 5.42s          │
│ Total Duration      │ 81.30s         │
└─────────────────────┴────────────────┘
```

## Error Handling

Both commands provide comprehensive error handling:

### Common Error Types

- **File Not Found**: Clear message with path verification
- **Invalid YAML**: Syntax errors with line numbers
- **Missing Dependencies**: Helpful installation instructions
- **Validation Errors**: Step configuration issues with fixes
- **Execution Failures**: Detailed error context and suggestions

### Error Examples

```bash
# Invalid workflow file
$ pframe workflow missing.yml
[ERROR] Workflow file not found: missing.yml
[TIP] Check the file path and ensure the file exists

# YAML syntax error
$ pframe workflow broken.yml
[ERROR] Invalid YAML syntax in broken.yml:
  Line 12: mapping values are not allowed here
[TIP] Check YAML indentation and syntax

# Missing visualization dependency
$ pframe workflow pipeline.yml --visualize graphviz
[ERROR] Workflow visualization requires additional dependencies
Please install with: pip install networkx graphviz matplotlib
```

## Performance Tips

- Use `--validate` to check workflows before long executions
- Leverage `--quiet` mode for automated/scripted usage
- Regular cleanup with `--cleanup` to manage disk space
- Use visualization to understand complex dependency chains
- Monitor execution history to identify performance patterns
