# First Steps

> This section will guide you through your first steps with ParquetFrame.

## Getting Started

After installation, you can start using ParquetFrame immediately. This guide covers the essential first steps to get you productive quickly.

## Basic Workflow

1. **Loading Data**: Start by loading your first parquet file
2. **Exploring Data**: Use built-in methods to understand your dataset
3. **Simple Operations**: Perform basic transformations
4. **Saving Results**: Export your processed data

## Summary

ParquetFrame makes working with parquet files intuitive and efficient. The basic workflow involves loading, exploring, transforming, and saving data with minimal code.

## Examples

```python
import parquetframe as pf

# Load your first parquet file
df = pf.read("data.parquet")

# Explore the data
print(df.info())
print(df.head())

# Save processed data
df.save("output.parquet")
```

## Further Reading

- [Quick Start Guide](quickstart.md)
- [Basic Usage](usage.md)
- [CLI Guide](cli/index.md)
