"""
Tabular Data Regression Example with Tetnus

Demonstrates using Tetnus for regression on tabular data with DataFrames.
"""

import numpy as np
import pandas as pd
from parquetframe.tetnus import Model, dataframe_to_tensor, nn


def create_sample_data():
    """Create synthetic tabular dataset."""
    # Generate features
    n_samples = 200
    X = pd.DataFrame(
        {
            "feature1": np.random.randn(n_samples),
            "feature2": np.random.randn(n_samples),
            "feature3": np.random.randn(n_samples),
        }
    )

    # Generate target (linear combination + noise)
    y = pd.DataFrame(
        {
            "target": (
                2 * X["feature1"]
                + 0.5 * X["feature2"]
                - X["feature3"]
                + np.random.randn(n_samples) * 0.1
            )
        }
    )

    return X, y


def main():
    """Train regression model on tabular data."""
    print("Creating dataset...")
    X_df, y_df = create_sample_data()

    # Split train/test
    split_idx = 150
    X_train, X_test = X_df[:split_idx], X_df[split_idx:]
    y_train, y_test = y_df[:split_idx], y_df[split_idx:]

    print(f"Training set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")

    # Convert DataFrames to Tensors
    print("\nConverting to tensors...")
    X_train_tensor = dataframe_to_tensor(X_train)
    y_train_tensor = dataframe_to_tensor(y_train)
    X_test_tensor = dataframe_to_tensor(X_test)

    # Create model
    print("\nBuilding model...")
    model = Model([nn.Linear(3, 16), nn.ReLU(), nn.Linear(16, 1)])

    # Train
    print("\nTraining...")
    model.fit(X_train_tensor, y_train_tensor, epochs=50, lr=0.01)

    # Evaluate
    print("\nEvaluating...")
    predictions = model.predict(X_test_tensor)

    # Calculate MSE
    y_test_np = y_test.values
    mse = np.mean((predictions - y_test_np) ** 2)
    print(f"Test MSE: {mse:.4f}")

    print("\nSample predictions:")
    for i in range(5):
        print(f"  True: {y_test_np[i, 0]:.2f}, Predicted: {predictions[i, 0]:.2f}")

    print("Done!")


if __name__ == "__main__":
    main()
