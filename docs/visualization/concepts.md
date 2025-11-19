# Visualization Concepts

ParquetFrame aims to provide a unified API for visualizing your data structures, particularly for complex types like Graphs and Genomic intervals.

## Philosophy

We do not reinvent the wheel. Instead, we provide convenience wrappers around best-in-class visualization libraries:

- **Matplotlib/Seaborn**: For static statistical plots.
- **Plotly/Altair**: For interactive web-based visualizations.
- **NetworkX/Cytoscape**: For graph structures.
- **IGV/JBrowse**: For genomic data (future integration).

## Convenience API (Planned)

We are designing a `.plot` accessor that intelligently dispatches to the appropriate library based on the data type.

```python
# Standard DataFrame plotting (delegates to pandas/backend)
df.pf.plot.hist("column_name")

# Graph plotting (delegates to NetworkX/matplotlib)
graph.pf.plot.network()

# Genomic track plotting (delegates to specialized renderers)
bio_frame.pf.plot.track(region="chr1:1000-2000")
```

## Graph Visualization

For `parquetframe.graph`, we support exporting to standard formats:

- **DOT**: For Graphviz.
- **GML**: For Gephi/Cytoscape.
- **JSON**: For D3.js.

```python
# Export to DOT
graph.to_dot("graph.dot")

# Quick visualize (requires matplotlib)
graph.draw()
```

## Interactive Dashboards

We recommend using **Streamlit** or **Shiny for Python** to build dashboards on top of ParquetFrame. Our optimized I/O and Rust backend make these dashboards snappy and responsive.
