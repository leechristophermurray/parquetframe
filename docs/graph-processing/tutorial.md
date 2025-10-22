# Graph Processing Tutorial

This tutorial demonstrates how to get started with ParquetFrame's graph processing capabilities using the Apache GraphAr format.

## Prerequisites

Make sure you have ParquetFrame installed with graph support:

```bash
pip install parquetframe[all]
```

## Creating Your First Graph

### 1. Prepare Graph Data

First, let's create some sample graph data using pandas:

```python
import pandas as pd
import parquetframe as pf
from pathlib import Path

# Create sample social network data
users_data = pd.DataFrame({
    'id': [0, 1, 2, 3, 4],
    'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
    'age': [25, 30, 35, 28, 32],
    'city': ['NYC', 'SF', 'LA', 'NYC', 'SF']
})

connections_data = pd.DataFrame({
    'src': [0, 0, 1, 1, 2, 3, 4],
    'dst': [1, 2, 2, 3, 3, 4, 0],
    'weight': [0.8, 0.6, 0.9, 0.7, 0.5, 0.9, 0.6],
    'timestamp': pd.to_datetime([
        '2024-01-01', '2024-01-02', '2024-01-03',
        '2024-01-04', '2024-01-05', '2024-01-06', '2024-01-07'
    ])
})

print("Sample data created:")
print(f"Users: {len(users_data)} rows")
print(f"Connections: {len(connections_data)} rows")
```

### 2. Create GraphAr Directory Structure

```python
# Create GraphAr directory structure
graph_dir = Path("my_social_network")
graph_dir.mkdir(exist_ok=True)

# Create vertices directory
vertices_dir = graph_dir / "vertices" / "person"
vertices_dir.mkdir(parents=True, exist_ok=True)

# Create edges directory
edges_dir = graph_dir / "edges" / "friendship"
edges_dir.mkdir(parents=True, exist_ok=True)

# Save vertex data
users_data.to_parquet(
    vertices_dir / "part0.parquet",
    engine="pyarrow",
    index=False
)

# Save edge data
connections_data.to_parquet(
    edges_dir / "part0.parquet",
    engine="pyarrow",
    index=False
)

print("Graph data files created")
```

### 3. Create Metadata and Schema Files

```python
import yaml

# Create metadata file
metadata = {
    'name': 'my_social_network',
    'version': '1.0',
    'directed': True,
    'description': 'Tutorial social network graph'
}

with open(graph_dir / "_metadata.yaml", "w") as f:
    yaml.dump(metadata, f, default_flow_style=False)

# Create schema file
schema = {
    'version': '1.0',
    'vertices': {
        'person': {
            'properties': {
                'id': {'type': 'int64', 'primary': True},
                'name': {'type': 'string'},
                'age': {'type': 'int32'},
                'city': {'type': 'string'}
            }
        }
    },
    'edges': {
        'friendship': {
            'properties': {
                'src': {'type': 'int64', 'source': True},
                'dst': {'type': 'int64', 'target': True},
                'weight': {'type': 'float64'},
                'timestamp': {'type': 'datetime64'}
            }
        }
    }
}

with open(graph_dir / "_schema.yaml", "w") as f:
    yaml.dump(schema, f, default_flow_style=False)

print("GraphAr metadata and schema created")
print(f"Graph directory: {graph_dir.absolute()}")
```

## Loading and Exploring Graph Data

### 1. Basic Graph Loading

```python
import parquetframe as pf

# Load the graph
graph = pf.read_graph("my_social_network/")
print(f"Loaded graph: {graph.num_vertices} vertices, {graph.num_edges} edges")
print(f"Graph is directed: {graph.is_directed}")
print(f"Backend: {'Dask' if graph.vertices.islazy else 'pandas'}")
```

### 2. Accessing Vertex and Edge Data

```python
# Access vertex data as DataFrame
users = graph.vertices.data
print("Users data:")
print(users)
print(f"Vertex properties: {graph.vertex_properties}")

# Access edge data as DataFrame
friendships = graph.edges.data
print("\nFriendships data:")
print(friendships)
print(f"Edge properties: {graph.edge_properties}")
```

### 3. Standard DataFrame Operations

```python
# Query vertices
young_users = users.query("age < 30")
print(f"Users under 30: {len(young_users)}")
print(young_users[['name', 'age', 'city']])

# Query edges
strong_friendships = friendships.query("weight > 0.7")
print(f"Strong friendships (weight > 0.7): {len(strong_friendships)}")

# Group operations
users_by_city = users.groupby('city').size()
print("Users by city:")
print(users_by_city)
```

## Working with Adjacency Structures

### 1. Create Adjacency Structures

```python
from parquetframe.graph.adjacency import CSRAdjacency, CSCAdjacency

# Create CSR adjacency (optimized for outgoing edges)
csr = CSRAdjacency.from_edge_set(graph.edges)
print(f"CSR adjacency: {csr.num_vertices} vertices, {csr.num_edges} edges")

# Create CSC adjacency (optimized for incoming edges)
csc = CSCAdjacency.from_edge_set(graph.edges)
print(f"CSC adjacency: {csc.num_vertices} vertices, {csc.num_edges} edges")
```

### 2. Graph Analysis

```python
# Analyze user connections
print("User connection analysis:")
for user_id in range(graph.num_vertices):
    user_name = users.loc[users['id'] == user_id, 'name'].iloc[0]

    # Outgoing connections (who this user is connected to)
    outgoing = csr.neighbors(user_id)
    out_degree = csr.degree(user_id)

    # Incoming connections (who is connected to this user)
    incoming = csc.predecessors(user_id)
    in_degree = csc.degree(user_id)

    print(f"{user_name} (id={user_id}):")
    print(f"  → Connects to {out_degree} users: {list(outgoing)}")
    print(f"  ← Connected by {in_degree} users: {list(incoming)}")
```

### 3. Advanced Graph Operations

```python
# Find mutual connections
def find_mutual_friends(user1_id, user2_id):
    friends1 = set(csr.neighbors(user1_id))
    friends2 = set(csr.neighbors(user2_id))
    mutual = friends1.intersection(friends2)
    return list(mutual)

# Check specific connections
user1_name = users.loc[users['id'] == 0, 'name'].iloc[0]
user2_name = users.loc[users['id'] == 1, 'name'].iloc[0]
mutual = find_mutual_friends(0, 1)

print(f"Mutual friends between {user1_name} and {user2_name}: {mutual}")

# Check if connection exists
has_connection = csr.has_edge(0, 1)
print(f"Direct connection from {user1_name} to {user2_name}: {has_connection}")
```

## Using the CLI

### 1. Basic Graph Inspection

```bash
# Basic graph information
pf graph info my_social_network/
```

### 2. Detailed Analysis

```bash
# Detailed statistics with degree distribution
pf graph info my_social_network/ --detailed
```

### 3. Different Output Formats

```bash
# JSON output for programmatic use
pf graph info my_social_network/ --format json

# Save analysis to file
pf graph info my_social_network/ --detailed --format json > graph_analysis.json
```

## Advanced Examples

### 1. Large Graph Processing

```python
# For large graphs, force Dask backend
large_graph = pf.read_graph("web_crawl/", islazy=True)
print(f"Large graph backend: {'Dask' if large_graph.vertices.islazy else 'pandas'}")

# Process in chunks for memory efficiency
if large_graph.vertices.islazy:
    # Use Dask operations
    degree_stats = large_graph.edges.data.groupby('src').size().compute()
else:
    # Use pandas operations
    degree_stats = large_graph.edges.data.groupby('src').size()
```

### 2. Graph Filtering and Subgraphs

```python
# Filter graph data
active_users = users.query("city in ['NYC', 'SF']")
active_user_ids = set(active_users['id'])

# Create subgraph with only active users
subgraph_edges = friendships[
    friendships['src'].isin(active_user_ids) &
    friendships['dst'].isin(active_user_ids)
]

print(f"Original graph: {len(users)} users, {len(friendships)} connections")
print(f"Filtered graph: {len(active_users)} users, {len(subgraph_edges)} connections")

# Create adjacency for subgraph
from parquetframe.graph.data import EdgeSet
from parquetframe.core import ParquetFrame

subgraph_edge_set = EdgeSet(
    data=ParquetFrame(subgraph_edges),
    edge_type='friendship',
    properties={'weight': 'float64', 'timestamp': 'datetime64'}
)

subgraph_csr = CSRAdjacency.from_edge_set(subgraph_edge_set)
```

### 3. Graph Metrics Calculation

```python
# Calculate basic graph metrics
def calculate_graph_metrics(csr_adj):
    metrics = {}

    # Degree distribution
    degrees = [csr_adj.degree(i) for i in range(csr_adj.num_vertices)]
    metrics['avg_degree'] = sum(degrees) / len(degrees)
    metrics['max_degree'] = max(degrees)
    metrics['min_degree'] = min(degrees)

    # Density
    max_edges = csr_adj.num_vertices * (csr_adj.num_vertices - 1)
    metrics['density'] = csr_adj.num_edges / max_edges

    return metrics

metrics = calculate_graph_metrics(csr)
print("Graph metrics:")
for key, value in metrics.items():
    print(f"  {key}: {value:.3f}")
```

## Best Practices

### 1. Backend Selection

```python
# Let ParquetFrame automatically choose backend
auto_graph = pf.read_graph("data/")  # Automatic selection

# Force pandas for small graphs (faster)
small_graph = pf.read_graph("small_data/", islazy=False)

# Force Dask for large graphs (scalable)
large_graph = pf.read_graph("big_data/", islazy=True)

# Custom threshold
medium_graph = pf.read_graph("data/", threshold_mb=50)  # Dask if >50MB
```

### 2. Schema Validation

```python
# Enable validation (default - safer but slower)
validated_graph = pf.read_graph("data/", validate_schema=True)

# Disable validation for trusted data (faster)
trusted_graph = pf.read_graph("trusted_data/", validate_schema=False)
```

### 3. Memory Management

```python
# For memory-constrained environments
import gc

# Process graph in steps
graph = pf.read_graph("large_graph/", islazy=True)

# Compute statistics incrementally
vertex_stats = graph.vertices.data.describe()
if hasattr(vertex_stats, 'compute'):
    vertex_stats = vertex_stats.compute()

# Clean up when done
del graph
gc.collect()
```

## Next Steps

- Explore the [Graph API Reference](index.md) for detailed documentation
- Learn about [GraphAr format](graphar-format.md) specifications
- Check out [Advanced Examples](../documentation-examples/examples-gallery.md) for real-world use cases
- Read about [Performance Optimization](index.md) techniques

## Troubleshooting

### Common Issues

1. **Schema validation errors**: Check that your parquet files match the schema in `_schema.yaml`
2. **Missing metadata**: Ensure both `_metadata.yaml` and `_schema.yaml` files exist
3. **Backend selection**: Use `--backend` flag to override automatic selection
4. **Memory issues**: Try `islazy=True` to force Dask backend for large graphs

### Getting Help

- Use `pf graph info --help` for CLI help
- Check [error handling documentation](index.md#error-handling)
- Report issues on [GitHub](https://github.com/leechristophermurray/parquetframe)
