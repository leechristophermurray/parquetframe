# Integration Guide

> Integrate ParquetFrame with your existing data stack and workflows.

## Integration Patterns

ParquetFrame is designed to integrate seamlessly with popular data tools and frameworks.

## Python Ecosystem

Integration with core Python data tools:
- **Pandas**: Native compatibility and conversion
- **NumPy**: Array operations and computations
- **Scikit-learn**: Machine learning pipelines
- **Matplotlib/Seaborn**: Data visualization

## Big Data Ecosystem

Work with distributed computing frameworks:
- **Dask**: Distributed processing
- **Apache Spark**: Large-scale data processing
- **Ray**: Distributed machine learning

## Database Integration

Connect with databases and data warehouses:
- SQL query support
- Database connectors
- Data pipeline integration

## Cloud Platforms

Deploy on cloud platforms:
- AWS S3 and Lambda
- Google Cloud Storage and Functions
- Azure Blob Storage and Functions

## Summary

ParquetFrame's flexible architecture enables integration across the entire data ecosystem.

## Examples

```python
import parquetframe as pf
import pandas as pd
from sklearn.model_selection import train_test_split

# Integration with pandas
df = pf.read("data.parquet")
pandas_df = df.to_pandas()

# Machine learning pipeline
X = df[['feature1', 'feature2', 'feature3']]
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Database integration
df = pf.read("data.parquet")
df.to_sql("processed_data", connection_string)

# Cloud storage
df = pf.read("s3://bucket/data.parquet")
df.save("s3://bucket/processed/output.parquet")
```

## Further Reading

- [Advanced Features](../advanced.md)
- [Performance Tips](../performance.md)
- [ML Pipeline Integration](ml-pipeline.md)
