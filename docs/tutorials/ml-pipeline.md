# ML Pipeline Integration

> Integrate ParquetFrame into machine learning workflows and pipelines.

## ML Pipeline Integration

ParquetFrame seamlessly integrates with machine learning frameworks and pipeline tools.

## Data Preparation

Optimize data preparation for ML workflows:
- **Feature Engineering**: Create and transform features
- **Data Splitting**: Train/validation/test splits
- **Data Validation**: Ensure data quality and consistency
- **Schema Evolution**: Handle changing data schemas

## Framework Integration

Work with popular ML frameworks:
- **Scikit-learn**: Traditional ML algorithms
- **XGBoost/LightGBM**: Gradient boosting frameworks
- **TensorFlow/PyTorch**: Deep learning frameworks
- **MLflow**: ML lifecycle management

## Pipeline Orchestration

Integrate with pipeline tools:
- **Apache Airflow**: Workflow orchestration
- **Kubeflow**: ML workflows on Kubernetes
- **MLOps platforms**: End-to-end ML platforms

## Performance Considerations

Optimize for ML workloads:
- **Efficient data loading**: Minimize data loading overhead
- **Memory management**: Handle large datasets efficiently
- **Parallel processing**: Scale feature engineering and model training

## Summary

ParquetFrame provides efficient data handling capabilities that integrate naturally with ML workflows.

## Examples

```python
import parquetframe as pf
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load and prepare ML data
df = pf.read("ml_dataset.parquet")

# Feature engineering
df['feature_ratio'] = df['feature_a'] / df['feature_b']
df['feature_log'] = pf.log(df['feature_c'])

# Prepare features and target
X = df[['feature_a', 'feature_b', 'feature_ratio', 'feature_log']]
y = df['target']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Accuracy: {accuracy:.4f}")

# Save results
results = pf.DataFrame({
    'actual': y_test,
    'predicted': predictions
})
results.save("ml_results.parquet")
```

## Further Reading

- [Integration Guide](integration.md)
- [Performance Optimization](performance.md)
- [Advanced Features](../../advanced.md)
