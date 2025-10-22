# Graph Engine

ParquetFrame's graph engine provides high-performance graph data processing capabilities with support for the Apache GraphAr columnar format. The engine enables efficient storage, loading, and analysis of large-scale graph data using familiar pandas/Dask APIs.

## Overview

The graph engine implements a three-layer architecture:

1. **GraphFrame**: High-level graph interface with vertex/edge access and algorithms
2. **VertexSet/EdgeSet**: Typed collections with schema validation and property access
3. **Adjacency Structures**: Optimized CSR/CSC representations for graph traversal

## Key Features

- **Apache GraphAr Support**: Full compliance with GraphAr columnar format specification
- **Intelligent Backend Selection**: Automatic pandas/Dask switching based on graph size
- **Schema Validation**: Type checking and property validation for graph data
- **Adjacency Optimization**: Memory-efficient CSR/CSC structures for fast neighbor lookups
- **CLI Integration**: Command-line tools for graph inspection and analysis

## Quick Start

### Basic Graph Loading

```python
import parquetframe as pf

# Load GraphAr format graph
graph = pf.read_graph("social_network/")
print(f"Loaded graph: {graph.num_vertices} vertices, {graph.num_edges} edges")

# Access vertex and edge data
users = graph.vertices
friendships = graph.edges

# Query graph data
active_users = users.data.query("status == 'active'")
recent_connections = friendships.data.query("timestamp > '2024-01-01'")
```

### Graph Inspection with CLI

```bash
# Inspect graph properties
pf graph info social_network/

# With detailed statistics
pf graph info social_network/ --detailed --format json

# Select backend
pf graph info large_graph/ --backend dask
```

### Working with Adjacency Structures

```python
from parquetframe.graph.adjacency import CSRAdjacency

# Create adjacency structure from edges
csr = CSRAdjacency.from_edge_set(graph.edges)

# Fast neighbor lookups
neighbors = csr.neighbors(user_id=123)
degree = csr.degree(user_id=123)

# Check edge existence
has_connection = csr.has_edge(source=123, target=456)
```

## Graph Data Structure

### GraphFrame

The central graph interface providing:

- **Unified Access**: Single entry point for vertices, edges, and metadata
- **Property Inspection**: Schema-aware property access and validation
- **Backend Flexibility**: Seamless pandas/Dask switching
- **Algorithm Integration**: Foundation for graph algorithms and analytics

```python
# Graph properties
print(f"Directed: {graph.is_directed}")
print(f"Vertex properties: {graph.vertex_properties}")
print(f"Edge properties: {graph.edge_properties}")

# Backend management
if graph.vertices.islazy:
    print("Using Dask backend for large graph")
else:
    print("Using pandas backend for efficient processing")
```

### VertexSet and EdgeSet

Strongly-typed collections with:

- **Schema Validation**: Automatic type checking and property validation
- **Flexible Loading**: Support for multiple parquet files and directories
- **Property Access**: Named property columns with metadata
- **Query Interface**: Standard DataFrame operations

```python
# Vertex operations
person_vertices = VertexSet.from_parquet("vertices/person/")
print(f"Loaded {len(person_vertices)} people")
adults = person_vertices.data.query("age >= 18")

# Edge operations
friendship_edges = EdgeSet.from_parquet("edges/friendship/")
strong_ties = friendship_edges.data.query("weight > 0.8")
```

## GraphAr Format Support

Full compliance with [Apache GraphAr specification](https://graphar.apache.org/):

### Directory Structure

```
social_network/
├── _metadata.yaml      # Graph metadata (name, directed, etc.)
├── _schema.yaml        # Property schemas and types
├── vertices/           # Vertex data by type
│   ├── person/
│   │   └── part0.parquet
│   └── organization/
│       └── part0.parquet
└── edges/              # Edge data by type
    ├── friendship/
    │   └── part0.parquet
    └── employment/
        └── part0.parquet
```

### Metadata Format

```yaml
# _metadata.yaml
name: "social_network"
version: "1.0"
directed: true
description: "Social network graph with people and organizations"
```

### Schema Format

```yaml
# _schema.yaml
version: "1.0"
vertices:
  person:
    properties:
      id: {type: "int64", primary: true}
      name: {type: "string"}
      age: {type: "int32"}
edges:
  friendship:
    properties:
      src: {type: "int64", source: true}
      dst: {type: "int64", target: true}
      weight: {type: "float64"}
```

## Performance and Optimization

### Backend Selection

The graph engine automatically selects the optimal backend:

```python
# Automatic selection based on file size
small_graph = pf.read_graph("small_network/")        # Uses pandas
large_graph = pf.read_graph("web_graph/")           # Uses Dask

# Manual backend control
fast_graph = pf.read_graph("data/", islazy=False)    # Force pandas
scalable_graph = pf.read_graph("data/", islazy=True) # Force Dask

# Custom thresholds
graph = pf.read_graph("data/", threshold_mb=50)      # Dask if >50MB
```

### Memory-Efficient Adjacency

CSR/CSC structures provide optimal memory usage and query performance:

```python
from parquetframe.graph.adjacency import CSRAdjacency, CSCAdjacency

# Out-degree optimized (CSR)
csr = CSRAdjacency.from_edge_set(edges)
neighbors = csr.neighbors(vertex_id)     # O(degree) lookup
out_degree = csr.degree(vertex_id)       # O(1) lookup

# In-degree optimized (CSC)
csc = CSCAdjacency.from_edge_set(edges)
predecessors = csc.predecessors(vertex_id) # O(in_degree) lookup
in_degree = csc.degree(vertex_id)          # O(1) lookup
```

## Advanced Features

### Schema Validation

Comprehensive type checking and validation:

```python
# Enable validation (default)
graph = pf.read_graph("data/", validate_schema=True)

# Disable for performance
graph = pf.read_graph("large_data/", validate_schema=False)

# Custom property validation
vertices = VertexSet.from_parquet(
    "vertices/user/",
    properties={"age": "int32", "name": "string"},
    schema=custom_schema
)
```

### Error Handling

Robust error handling for invalid GraphAr data:

```python
try:
    graph = pf.read_graph("invalid_data/")
except GraphArError as e:
    print(f"GraphAr format error: {e}")
except GraphArValidationError as e:
    print(f"Schema validation failed: {e}")
except FileNotFoundError as e:
    print(f"Directory not found: {e}")
```

## Examples and Use Cases

### Social Network Analysis

```python
# Load social network
social_graph = pf.read_graph("social_network/")

# Find influential users (high degree)
csr = CSRAdjacency.from_edge_set(social_graph.edges)
degrees = [csr.degree(i) for i in range(social_graph.num_vertices)]
influential_users = social_graph.vertices.data[
    social_graph.vertices.data.index.isin(
        pd.Series(degrees).nlargest(10).index
    )
]

# Analyze connection patterns
friendship_weights = social_graph.edges.data['weight']
print(f"Average friendship strength: {friendship_weights.mean():.2f}")
```

### Knowledge Graph Processing

```python
# Load knowledge graph
knowledge_graph = pf.read_graph("knowledge_base/")

# Query entity relationships
entities = knowledge_graph.vertices.data
relations = knowledge_graph.edges.data

# Find entities with specific properties
organizations = entities.query("type == 'organization'")
strong_relations = relations.query("confidence > 0.9")
```

### Web Graph Analysis

```python
# Load web graph (uses Dask automatically for large data)
web_graph = pf.read_graph("web_crawl/", threshold_mb=10)

# Analyze link structure
if web_graph.vertices.islazy:
    print("Processing large web graph with Dask")
    page_counts = web_graph.vertices.data.groupby('domain').size().compute()
else:
    page_counts = web_graph.vertices.data.groupby('domain').size()

print(f"Top domains: {page_counts.nlargest(5)}")
```

## API Reference

- [GraphFrame API](index.md) - Main graph interface
- [VertexSet/EdgeSet API](adjacency.md) - Typed graph collections
- [Adjacency API](adjacency.md) - CSR/CSC adjacency structures
- [GraphAr Reader API](graphar.md) - Apache GraphAr format support
- [CLI Reference](../cli-interface/commands.md) - Command-line tools

## See Also

- [Getting Started Tutorial](tutorial.md)
- [GraphAr Format Guide](graphar-format.md)
- [Performance Optimization](performance.md)
- [Advanced Examples](../documentation-examples/examples.md)
