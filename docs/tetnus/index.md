# Tetnus: DataFrame-Native ML Framework

Tetnus is a high-performance machine learning framework built on Arrow-native tensors with automatic differentiation.

## Overview

Tetnus provides:
- **Arrow-native tensors**: Zero-copy integration with DataFrames
- **Automatic differentiation**: Full autograd support
- **Neural network layers**: Linear, ReLU, Sequential, Embedding
- **Optimizers**: SGD, Adam
- **Simple API**: Easy model training and prediction

## Quick Start

```python
from parquetframe.tetnus import Model, nn
import numpy as np

# Create data
X = np.random.randn(100, 10).astype(np.float32)
y = np.random.randn(100, 1).astype(np.float32)

# Build model
model = Model([
    nn.Linear(10, 64),
    nn.ReLU(),
    nn.Linear(64, 1)
])

# Train
model.fit(X, y, epochs=20, lr=0.01)

# Predict
predictions = model.predict(X)
```

## DataFrame Integration

### Converting DataFrames to Tensors

```python
import pandas as pd
from parquetframe.tetnus import dataframe_to_tensor

df = pd.DataFrame({
    'feature1': [1.0, 2.0, 3.0],
    'feature2': [4.0, 5.0, 6.0]
})

# Convert to tensor
tensor = dataframe_to_tensor(df)
```

## Examples

### Image Classification (MNIST)

See [`examples/tetnus/mnist_example.py`](../../examples/tetnus/mnist_example.py) for a complete example.

### Tabular Regression

See [`examples/tetnus/tabular_example.py`](../../examples/tetnus/tabular_example.py) for DataFrame-based regression.

## Architecture

Tetnus is built on Rust for maximum performance:
- **tetnus-core**: Tensor operations and autograd
- **tetnus-nn**: Neural network layers
- **tetnus-optim**: Optimization algorithms

All operations support automatic differentiation via PyO3 bindings.

## API Reference

### Model Class

```python
class Model:
    \"\"\"High-level model wrapper.\"\"\"
    
    def __init__(self, layers: List)
    def fit(self, X, y, epochs=10, lr=0.01, verbose=True)
    def predict(self, X)
```

### Neural Network Layers

```python
from parquetframe.tetnus import nn

nn.Linear(in_features, out_features)
nn.ReLU()
nn.Sequential(*layers)
nn.Embedding(num_embeddings, embedding_dim)
nn.LayerNorm(normalized_shape)
```

### Optimizers

```python
from parquetframe.tetnus import optim

optim.SGD(parameters, lr=0.01)
optim.Adam(parameters, lr=0.001)
```

## Performance

Tetnus tensors are Arrow-native, enabling:
- **Zero-copy** conversion from DataFrames
- **GPU acceleration** (when available)
- **Automatic parallelization** for CPU operations
