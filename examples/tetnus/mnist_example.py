"""
MNIST Classification Example with Tetnus

Demonstrates using Tetnus for image classification on the MNIST dataset.
"""

import numpy as np

from parquetframe.tetnus import Model, nn


def load_mnist_sample():
    """
    Load a small sample of MNIST data for demonstration.

    In production, you would use:
        from sklearn.datasets import fetch_openml
        mnist = fetch_openml('mnist_784', version=1)
    """
    # Create synthetic data for demo
    # 100 samples, 784 features (28x28 images)
    X_train = np.random.randn(100, 784).astype(np.float32) / 10
    y_train = np.random.randint(0, 10, (100, 10)).astype(np.float32)

    X_test = np.random.randn(20, 784).astype(np.float32) / 10
    y_test = np.random.randint(0, 10, (20, 10)).astype(np.float32)

    return X_train, y_train, X_test, y_test


def main():
    """Train MNIST classifier."""
    print("Loading MNIST data...")
    X_train, y_train, X_test, y_test = load_mnist_sample()

    print(f"Training set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")

    # Create model
    print("\nBuilding model...")
    model = Model(
        [
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 10),
        ]
    )

    # Train
    print("\nTraining...")
    model.fit(X_train, y_train, epochs=20, lr=0.001)

    # Evaluate
    print("\nEvaluating...")
    predictions = model.predict(X_test)
    print(f"Predictions shape: {predictions.shape}")
    print("Done!")


if __name__ == "__main__":
    main()
