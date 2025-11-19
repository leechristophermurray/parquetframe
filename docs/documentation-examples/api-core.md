# Core API Reference

> Complete API reference for ParquetFrame core functionality.

## Core Classes

### ParquetFrame

The main class for working with parquet data.

::: parquetframe.ParquetFrame
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Core Functions

### Reading Data

Functions for loading data from various sources.

::: parquetframe.read
    options:
      show_root_heading: true
      show_source: true

### Writing Data

Functions for saving data to various formats.

## Data Processing

### Filtering and Selection

Methods for filtering and selecting data.

### Aggregation

Methods for data aggregation and grouping.

### Transformation

Methods for data transformation and feature engineering.

## Summary

The core API provides comprehensive functionality for data loading, processing, and saving with optimal performance.

## Examples

```python
import parquetframe as pf

# Create ParquetFrame instance
df = pf.ParquetFrame()

# Load data
df = pf.read("data.parquet")

# Process data
filtered = df.filter("column > 100")
grouped = df.groupby("category").sum()

# Save results
df.save("output.parquet")
```

## Further Reading

- [CLI API Reference](../cli-interface/commands.md)
- [Quick Start](../getting-started/quickstart.md)
- [Examples Gallery](examples-gallery.md)
