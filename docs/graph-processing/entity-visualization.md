# Entity Graph Visualization

ParquetFrame's Entity Framework supports interactive graph visualization using NetworkX and PyVis. Visualize your entity relationships to explore data connections and structures.

## Installation

```bash
# Core visualization (NetworkX)
pip install networkx

# Interactive HTML visualizations (optional)
pip install pyvis

# Graphviz export (optional)
pip install pydot
```

## Quick Start

```python
from parquetframe.entity import entity, rel, entities_to_networkx, visualize_with_pyvis
from dataclasses import dataclass

# Define entities
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    name: str

    @rel("Post", foreign_key="author_id", reverse=True)
    def posts(self):
        pass

# Load entities
users = User.find_all()

# Create graph
G = entities_to_networkx(users, max_depth=2)

# Visualize
visualize_with_pyvis(G, "users_graph.html")
# Opens an interactive graph in your browser!
```

---

## API Reference

### `entities_to_networkx()`

Convert entities to a NetworkX directed graph.

```python
entities_to_networkx(
    entities: list[Any],
    include_relationships: bool = True,
    max_depth: int = 1,
) -> nx.DiGraph
```

**Parameters:**
- `entities`: List of entity instances to convert
- `include_relationships`: Whether to follow relationship edges
- `max_depth`: Maximum relationship depth to traverse

**Returns:** NetworkX DiGraph

**Example:**
```python
import networkx as nx
from parquetframe.entity import entities_to_networkx

users = User.find_all()
G = entities_to_networkx(users, max_depth=2)

print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")

# NetworkX analysis
print(f"Connected components: {nx.number_weakly_connected_components(G)}")
```

### `visualize_with_pyvis()`

Create interactive HTML visualization.

```python
visualize_with_pyvis(
    graph: nx.DiGraph,
    output_path: str | Path = "entity_graph.html",
    height: str = "750px",
    width: str = "100%",
    notebook: bool = False,
) -> str
```

**Parameters:**
- `graph`: NetworkX graph to visualize
- `output_path`: Path to save HTML file
- `height`: Height of visualization
- `width`: Width of visualization
- `notebook`: Display in Jupyter notebook

**Returns:** Path to generated HTML file

**Example:**
```python
from parquetframe.entity import entities_to_networkx, visualize_with_pyvis

G = entities_to_networkx(users)
html_file = visualize_with_pyvis(G, "interactive_graph.html")

# Open in browser:
import webbrowser
webbrowser.open(html_file)
```

### `export_to_graphviz()`

Export graph to Graphviz DOT format.

```python
export_to_graphviz(
    graph: nx.DiGraph,
    output_path: str | Path = "entity_graph.dot",
) -> str
```

**Parameters:**
- `graph`: NetworkX graph to export
- `output_path`: Path to save DOT file

**Returns:** Path to generated DOT file

**Example:**
```python
from parquetframe.entity import entities_to_networkx, export_to_graphviz

G = entities_to_networkx(users)
dot_file = export_to_graphviz(G, "graph.dot")

# Render with Graphviz:
# dot -Tpng graph.dot -o graph.png
# dot -Tsvg graph.dot -o graph.svg
```

---

## Complete Example

```python
from dataclasses import dataclass
from datetime import datetime
from parquetframe.entity import entity, rel
from parquetframe.entity import entities_to_networkx, visualize_with_pyvis

# Define entity model
@entity(storage_path="./data/users", primary_key="user_id")
@dataclass
class User:
    user_id: str
    username: str

    @rel("Board", foreign_key="owner_id", reverse=True)
    def boards(self):
        pass

@entity(storage_path="./data/boards", primary_key="board_id")
@dataclass
class Board:
    board_id: str
    owner_id: str
    name: str

    @rel("User", foreign_key="owner_id")
    def owner(self):
        pass

    @rel("Task", foreign_key="board_id", reverse=True)
    def tasks(self):
        pass

@entity(storage_path="./data/tasks", primary_key="task_id")
@dataclass
class Task:
    task_id: str
    board_id: str
    title: str
    status: str

    @rel("Board", foreign_key="board_id")
    def board(self):
        pass

# Create sample data
user1 = User("u1", "alice")
user1.save()

board1 = Board("b1", "u1", "Project Alpha")
board1.save()

Task("t1", "b1", "Setup project", "done").save()
Task("t2", "b1", "Write code", "in_progress").save()
Task("t3", "b1", "Deploy", "todo").save()

# Visualize
users = User.find_all()
G = entities_to_networkx(users, max_depth=2)

# Create interactive visualization
visualize_with_pyvis(
    G,
    "project_graph.html",
    height="800px",
    width="100%"
)

print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
print("Open project_graph.html in your browser to explore!")
```

---

## Graph Analysis with NetworkX

Once you have a NetworkX graph, you can perform various analyses:

### Basic Metrics

```python
import networkx as nx

G = entities_to_networkx(users)

# Node and edge counts
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")

# Density
print(f"Density: {nx.density(G):.3f}")

# Connected components
print(f"Weakly connected: {nx.number_weakly_connected_components(G)}")
```

### find_paths

```python
# Find shortest path between entities
user_node = "User:u1"
task_node = "Task:t5"

if nx.has_path(G, user_node, task_node):
    path = nx.shortest_path(G, user_node, task_node)
    print(f"Path: {' -> '.join(path)}")
```

### Degree Analysis

```python
# Find most connected entities
degrees = dict(G.degree())
top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]

print("Most connected entities:")
for node, degree in top_nodes:
    print(f"  {node}: {degree} connections")
```

---

## Customization

### Filter Entities Before Visualization

```python
# Only visualize active users
active_users = [u for u in User.find_all() if getattr(u, 'active', True)]
G = entities_to_networkx(active_users)
```

### Control Depth

```python
# Shallow graph (only direct relationships)
G_shallow = entities_to_networkx(users, max_depth=1)

# Deep graph (up to 3 levels)
G_deep = entities_to_networkx(users, max_depth=3)
```

### Entity-Only (No Relationships)

```python
# Just show entities as nodes, no edges
G = entities_to_networkx(users, include_relationships=False)
```

---

## Use Cases

### 1. Data Exploration

Quickly understand your entity relationships:

```python
# Load a subset of data
recent_users = User.find_by(created_after="2024-01-01")

# Visualize their ecosystem
G = entities_to_networkx(recent_users, max_depth=2)
visualize_with_pyvis(G, "new_users.html")
```

### 2. Debugging Relationships

Identify broken or unexpected connections:

```python
G = entities_to_networkx(users)

# Find isolated entities
isolated = list(nx.isolates(G))
print(f"Isolated entities: {isolated}")

# Find entities with no incoming edges
sources = [n for n in G.nodes() if G.in_degree(n) == 0]
print(f"Source entities: {sources}")
```

### 3. Documentation

Generate visual documentation of your data model:

```python
# Create one instance of each entity type
sample_entities = [
    User("sample", "Sample User"),
    Board("sample", "sample", "Sample Board"),
    Task("sample", "sample", "Sample Task", "todo"),
]

G = entities_to_networkx(sample_entities, include_relationships=True)
export_to_graphviz(G, "data_model.dot")
```

---

## Performance Tips

1. **Limit depth** for large graphs:
   ```python
   G = entities_to_networkx(entities, max_depth=1)  # Faster
   ```

2. **Filter entities** before visualization:
   ```python
   important_users = User.find_by(role="admin")
   G = entities_to_networkx(important_users)
   ```

3. **Sample large datasets**:
   ```python
   all_users = User.find_all()
   sample = all_users[:100]  # First 100
   G = entities_to_networkx(sample)
   ```

---

## See Also

- [Entity Framework](index.md) - Entity system overview
- [Advanced Queries](advanced-queries.md) - Relationship querying
- [NetworkX Documentation](https://networkx.org/) - Graph analysis
- [PyVis Documentation](https://pyvis.readthedocs.io/) - Interactive visualizations
