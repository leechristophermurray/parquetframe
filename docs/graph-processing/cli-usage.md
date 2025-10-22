# Graph CLI Reference

The ParquetFrame CLI provides powerful command-line tools for inspecting, analyzing, and working with graph data in Apache GraphAr format.

## Commands

### `pf graph info`

Inspect graph properties, schema, and statistics.

#### Syntax

```bash
pf graph info [OPTIONS] PATH
```

#### Arguments

- `PATH`: Path to GraphAr directory containing graph data

#### Options

- `--detailed` / `-d`: Show detailed graph statistics including degree distribution
- `--format FORMAT` / `-f FORMAT`: Output format (default: table)
  - `table`: Human-readable table format
  - `json`: JSON format for programmatic use
  - `yaml`: YAML format for configuration
- `--backend BACKEND` / `-b BACKEND`: Force backend selection
  - `auto`: Automatic selection based on file size (default)
  - `pandas`: Force pandas backend
  - `dask`: Force Dask backend
- `--validate` / `--no-validate`: Enable/disable schema validation (default: enabled)
- `--load-adjacency`: Preload adjacency structures for degree statistics
- `--help`: Show command help

#### Examples

##### Basic Usage

```bash
# Show basic graph information
pf graph info social_network/
```

Output:
```
Graph Information
=================
Name: social_network
Version: 1.0
Directed: Yes
Description: Social network with friendship connections

Vertices: 1,250 (type: person)
Edges: 3,742 (type: friendship)
Backend: pandas (files < 10MB threshold)
```

##### Detailed Statistics

```bash
# Show detailed statistics with degree distribution
pf graph info social_network/ --detailed
```

Output:
```
Graph Information
=================
Name: social_network
Version: 1.0
Directed: Yes
Description: Social network with friendship connections

Data Summary
============
Vertices: 1,250 (type: person)
├─ Properties: id (int64), name (string), age (int32), status (string)
├─ Age distribution: min=18, max=65, mean=34.2
└─ Status: active=892 (71.4%), inactive=358 (28.6%)

Edges: 3,742 (type: friendship)
├─ Properties: src (int64), dst (int64), weight (float64), timestamp (datetime64)
├─ Weight distribution: min=0.1, max=1.0, mean=0.67
└─ Connection density: 0.48%

Degree Statistics
=================
Out-degree: min=0, max=28, mean=5.2, std=4.1
In-degree: min=0, max=24, mean=5.2, std=3.8
Top 5 most connected users:
├─ user_123: 28 connections
├─ user_456: 26 connections
├─ user_789: 24 connections
├─ user_234: 22 connections
└─ user_567: 21 connections

Backend: pandas (3.2MB total, threshold=10MB)
```

##### JSON Output

```bash
# Output as JSON for programmatic processing
pf graph info social_network/ --format json
```

Output:
```json
{
  "graph": {
    "name": "social_network",
    "version": "1.0",
    "directed": true,
    "description": "Social network with friendship connections"
  },
  "vertices": {
    "count": 1250,
    "types": ["person"],
    "properties": {
      "id": {"type": "int64", "primary": true},
      "name": {"type": "string"},
      "age": {"type": "int32"},
      "status": {"type": "string"}
    }
  },
  "edges": {
    "count": 3742,
    "types": ["friendship"],
    "properties": {
      "src": {"type": "int64", "source": true},
      "dst": {"type": "int64", "target": true},
      "weight": {"type": "float64"},
      "timestamp": {"type": "datetime64"}
    }
  },
  "backend": {
    "type": "pandas",
    "file_size_mb": 3.2,
    "threshold_mb": 10.0
  },
  "validation": {
    "enabled": true,
    "schema_valid": true
  }
}
```

##### Force Dask Backend

```bash
# Use Dask backend for large graph analysis
pf graph info web_crawl/ --backend dask --detailed
```

##### Disable Schema Validation

```bash
# Skip validation for performance on trusted data
pf graph info large_graph/ --no-validate --format json
```

## Use Cases

### Graph Discovery

Quickly understand the structure and properties of an unknown graph dataset:

```bash
# Start with basic info
pf graph info mystery_graph/

# Get detailed analysis if promising
pf graph info mystery_graph/ --detailed --format json > analysis.json
```

### Data Quality Assessment

Validate graph data integrity and schema compliance:

```bash
# Check schema validation
pf graph info dataset/ --validate

# Examine data distributions for anomalies
pf graph info dataset/ --detailed | grep -A 10 "distribution"
```

### Performance Planning

Determine optimal backend for graph processing:

```bash
# Check current backend selection
pf graph info data/ --format json | jq '.backend'

# Test with different backends
pf graph info data/ --backend pandas  # Fast for small graphs
pf graph info data/ --backend dask     # Scalable for large graphs
```

### Monitoring and Reporting

Generate reports for graph datasets:

```bash
# Daily monitoring
pf graph info production_graph/ --format json > daily_stats.json

# Human-readable reports
pf graph info production_graph/ --detailed > graph_report.txt
```

### Batch Processing

Process multiple graph directories:

```bash
#!/bin/bash
# Analyze all graph datasets
for dir in graphs/*/; do
    echo "Analyzing $dir"
    pf graph info "$dir" --format json > "reports/$(basename $dir).json"
done
```

### Development Workflow

Validate graphs during development:

```bash
# Quick validation during development
pf graph info test_data/ --no-validate  # Skip validation for speed

# Full validation before deployment
pf graph info test_data/ --detailed --validate
```

## Error Handling

The CLI provides clear error messages for common issues:

### Invalid GraphAr Directory

```bash
pf graph info invalid_directory/
```

Output:
```
Error: GraphAr directory not found: invalid_directory/
```

### Missing Metadata

```bash
pf graph info directory_without_metadata/
```

Output:
```
Error: Required metadata file not found: directory_without_metadata/_metadata.yaml
```

### Schema Validation Errors

```bash
pf graph info corrupted_data/ --validate
```

Output:
```
Error: Schema validation failed
├─ Missing required metadata fields: ['version']
├─ Invalid property type in vertices/person: expected int64, got object
└─ Edge data missing required columns: ['src', 'dst']
```

### Backend Selection Issues

```bash
pf graph info huge_dataset/ --backend pandas
```

Output:
```
Warning: Large dataset (2.3GB) may exceed pandas memory limits
Consider using --backend dask or increasing --threshold-mb
```

## Integration

### Scripting

Use CLI output in scripts:

```bash
#!/bin/bash
# Check if graph is ready for processing
INFO=$(pf graph info data/ --format json)
VERTEX_COUNT=$(echo "$INFO" | jq '.vertices.count')

if [ "$VERTEX_COUNT" -gt 10000 ]; then
    echo "Large graph detected, using Dask pipeline"
    python process_large_graph.py --backend dask
else
    echo "Small graph, using pandas pipeline"
    python process_small_graph.py --backend pandas
fi
```

### CI/CD Integration

Validate graph data in continuous integration:

```yaml
# .github/workflows/validate-graphs.yml
- name: Validate graph data
  run: |
    for graph in data/graphs/*/; do
      pf graph info "$graph" --validate --format json || exit 1
    done
```

### Monitoring Integration

Export metrics to monitoring systems:

```bash
# Export to Prometheus/Grafana
pf graph info production_graph/ --format json | \
  jq '{vertices: .vertices.count, edges: .edges.count}' | \
  curl -X POST -d @- http://monitoring:9091/metrics/parquetframe_graph
```

## Configuration

### Environment Variables

- `PF_GRAPH_BACKEND`: Default backend (`auto`, `pandas`, `dask`)
- `PF_GRAPH_THRESHOLD_MB`: Default size threshold for backend selection
- `PF_GRAPH_VALIDATE`: Default validation setting (`true`, `false`)

```bash
# Set defaults
export PF_GRAPH_BACKEND=dask
export PF_GRAPH_THRESHOLD_MB=50
export PF_GRAPH_VALIDATE=true

# Commands use these defaults
pf graph info data/  # Uses Dask backend with 50MB threshold
```

### Configuration File

Create `~/.parquetframe/config.yaml`:

```yaml
graph:
  default_backend: dask
  threshold_mb: 25
  validate_schema: true
  detailed_by_default: false
  preferred_format: json
```

## See Also

- [Graph Engine Overview](index.md)
- [GraphAr Format Guide](graphar-format.md)
- [Performance Tuning](performance.md)
- [Python API Reference](../documentation-examples/api-reference.md)
