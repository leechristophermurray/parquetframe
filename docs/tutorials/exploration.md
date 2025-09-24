# Data Exploration

> Learn how to explore and understand your data with ParquetFrame.

## Getting Started with Data Exploration

Data exploration is the first step in any data analysis workflow. ParquetFrame provides intuitive tools for understanding your datasets.

## Basic Exploration

Start with basic data inspection:
- Dataset overview and structure
- Data types and statistics
- Missing value analysis
- Distribution analysis

## Advanced Exploration

Dive deeper with advanced techniques:
- Correlation analysis
- Pattern detection
- Outlier identification
- Data quality assessment

## Visualization Integration

ParquetFrame works seamlessly with visualization libraries for interactive exploration.

## Summary

Effective data exploration with ParquetFrame helps you understand your data and guide your analysis decisions.

## Examples

```python
import parquetframe as pf

# Load data for exploration
df = pf.read("sales_data.parquet")

# Basic exploration
print(df.info())
print(df.describe())
print(df.head(10))

# Check data quality
missing_data = df.isnull().sum()
data_types = df.dtypes

# Explore relationships
correlation_matrix = df.corr()

# Filter and explore subsets
high_sales = df[df['sales'] > 1000]
```

## Further Reading

- [Basic Usage](../usage.md)
- [Advanced Features](../advanced.md)
- [Performance Optimization](performance.md)