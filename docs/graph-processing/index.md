# Graph Processing

ParquetFrame provides comprehensive graph processing capabilities with native support for the GraphAr format, high-performance algorithms, and seamless integration with popular graph libraries. Process million-node graphs efficiently with Rust-accelerated algorithms delivering 15-25x speedups.

## Overview

The graph processing system offers:

- **📊 GraphAr Format Support** - Industry-standard columnar graph storage
- **🚀 Rust-Accelerated Algorithms** - BFS (17x), PageRank (24x), shortest paths
- **🔄 Bidirectional Conversion** - NetworkX, igraph, pandas DataFrames
- **💾 Efficient Storage** - Compressed Parquet-based graph representation
- **📈 Scalable Operations** - Handle million-node graphs with ease
- **🎯 Rich Algorithm Library** - Traversal, centrality, community detection

## Quick Start

### Creating a Graph

```python
import parquetframe as pf
import pandas as pd

# From edge list DataFrame
edges = pd.DataFrame({
    'src': [0, 1, 2, 0],
    'dst': [1, 2, 3, 3],
    'weight': [1.0, 2.0, 1.5, 3.0]
})

graph = pf.GraphFrame.from_edges(edges, src='src', dst='dst')

# From GraphAr directory
graph = pf.GraphFrame.from_graphar("social_network/")

# From NetworkX
import networkx as nx
nx_graph = nx.karate_club_graph()
graph = pf.GraphFrame.from_networkx(nx_graph)
```

### Running Algorithms

```python
# PageRank (24x faster with Rust)
scores = graph.pagerank(alpha=0.85, max_iter=100)
print(f"Top node: {scores.idxmax()} with score {scores.max():.4f}")

# BFS traversal (17x faster with Rust)
distances = graph.bfs(source=0)
print(f"Reachable nodes: {(distances >= 0).sum()}")

# Shortest paths
paths = graph.shortest_paths(source=0, method='dijkstra')

# Connected components
components = graph.connected_components()
print(f"Found {components.nunique()} components")
```

## Key Features

### GraphAr Format

Industry-standard columnar graph storage format:

- **Efficient Storage**: Parquet-based compression
- **Fast Loading**: Selective column reading
- **Metadata Support**: Rich graph schema information
- **Interoperability**: Compatible with Apache Arrow ecosystem

[Learn more →](graphar-format.md)

### Rust Acceleration

High-performance graph algorithms:

| Algorithm | Speedup | Scale |
|-----------|---------|-------|
| PageRank | 24x | 100K+ nodes |
| BFS | 17x | 1M+ nodes |
| Shortest Paths | 18x | 500K+ edges |
| Connected Components | 27x | 1M+ edges |

[Learn more →](../rust-acceleration/graph-algorithms.md)

### Algorithm Library

**Traversal Algorithms**
- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Single-source shortest paths (Dijkstra, Bellman-Ford)

**Centrality Measures**
- PageRank
- Betweenness centrality
- Closeness centrality
- Degree centrality

**Community Detection**
- Connected components
- Strongly connected components
- Label propagation

**Graph Properties**
- Degree distribution
- Clustering coefficient
- Graph diameter

## Pages in This Section

| Page | Description |
|------|-------------|
| **[Tutorial](tutorial.md)** | Step-by-step guide to graph processing |
| **[GraphAr Format](graphar-format.md)** | GraphAr specification and usage |
| **[GraphAr Migration](graphar-migration.md)** | Migrating to GraphAr from other formats |
| **[CLI Usage](cli-usage.md)** | Command-line tools for graph operations |

## Common Use Cases

### Social Network Analysis

Analyze relationships and influence in social networks:

```python
# Load social graph
graph = pf.GraphFrame.from_graphar("social_network/")

# Find influential users
influence = graph.pagerank()
top_influencers = influence.nlargest(10)

# Community detection
communities = graph.connected_components()
```

### Knowledge Graph Processing

Query and analyze knowledge graphs:

```python
# Load knowledge graph with properties
graph = pf.GraphFrame.from_graphar("knowledge_base/")

# Find related concepts
related = graph.bfs(source="Python", max_depth=2)

# Rank entities by importance
rankings = graph.pagerank(personalization={"AI": 1.0})
```

### Dependency Analysis

Analyze software dependencies and build graphs:

```python
# Create dependency graph
edges = pd.DataFrame({
    'package': ['A', 'A', 'B', 'C'],
    'depends_on': ['B', 'C', 'D', 'D']
})

graph = pf.GraphFrame.from_edges(edges, src='package', dst='depends_on')

# Find transitive dependencies
all_deps = graph.bfs(source='A')

# Detect circular dependencies
cycles = graph.find_cycles()
```

## Performance Guidelines

### When to Use Rust Acceleration

**✅ Recommended for:**
- Graphs with 10K+ nodes
- Iterative algorithms (PageRank, label propagation)
- Repeated traversals
- Production workloads

**⚠️ May not benefit:**
- Very small graphs (<1000 nodes)
- One-time operations
- Development/prototyping

### Memory Optimization

```python
# Use efficient data types
edges = pd.DataFrame({
    'src': pd.array([...], dtype='int32'),  # Not int64
    'dst': pd.array([...], dtype='int32'),
    'weight': pd.array([...], dtype='float32')  # Not float64
})

# Load only required columns
graph = pf.GraphFrame.from_graphar(
    "large_graph/",
    vertex_columns=['id', 'label'],
    edge_columns=['src', 'dst', 'weight']
)
```

## Integration with Other Libraries

### NetworkX

```python
# ParquetFrame → NetworkX
graph = pf.GraphFrame.from_graphar("data/")
nx_graph = graph.to_networkx()

# NetworkX → ParquetFrame
graph = pf.GraphFrame.from_networkx(nx_graph)
```

### igraph

```python
# ParquetFrame → igraph
import igraph as ig
edges = graph.edges
ig_graph = ig.Graph.TupleList(
    edges=zip(edges['src'], edges['dst']),
    directed=True
)
```

### PyTorch Geometric

```python
# For GNN workflows
import torch
from torch_geometric.data import Data

# Convert to PyG format
edge_index = torch.tensor(
    [graph.edges['src'].values, graph.edges['dst'].values],
    dtype=torch.long
)

data = Data(edge_index=edge_index, num_nodes=graph.num_vertices)
```

## Related Categories

- **[Rust Acceleration](../rust-acceleration/index.md)** - High-performance graph algorithms
- **[Core Features](../core-features/index.md)** - DataFrame operations for graph data
- **[Analytics & Statistics](../analytics-statistics/index.md)** - Graph metrics and analysis
- **[YAML Workflows](../yaml-workflows/index.md)** - Graph processing pipelines

## Advanced Topics

### Custom Algorithms

Implement custom graph algorithms:

```python
def custom_traversal(graph, start_node, condition):
    """Custom BFS with filtering."""
    visited = set()
    queue = [start_node]

    while queue:
        node = queue.pop(0)
        if node in visited:
            continue

        visited.add(node)

        # Get neighbors
        neighbors = graph.neighbors(node)

        # Apply custom condition
        for neighbor in neighbors:
            if condition(graph, neighbor):
                queue.append(neighbor)

    return visited
```

### Distributed Processing

For very large graphs (billions of edges):

```python
# Partition graph by vertex ranges
for partition_id in range(num_partitions):
    partition = graph.get_partition(partition_id)

    # Process partition
    local_scores = partition.pagerank()

    # Aggregate results
    global_scores.update(local_scores)
```

## Next Steps

- **New to graphs?** Start with the [Tutorial](tutorial.md)
- **Using GraphAr?** See [GraphAr Format Guide](graphar-format.md)
- **Need performance?** Check [Rust Acceleration](../rust-acceleration/graph-algorithms.md)
- **Real examples?** Browse [Examples Gallery](../documentation-examples/examples-gallery.md)

## API Reference

For detailed API documentation, see:

- `parquetframe.GraphFrame` - Main graph class
- `parquetframe.graph.algorithms` - Algorithm implementations
- `parquetframe.graph.graphar` - GraphAr format support
- `parquetframe.graph_rust` - Rust-accelerated functions

## Error Handling

Common issues when working with graphs:

- **Schema Mismatch**: Ensure your Parquet files match `_schema.yaml`.
- **Missing Metadata**: `_metadata.yaml` is required in the graph directory.
- **Memory Errors**: Use `islazy=True` (Dask) for graphs larger than memory.
