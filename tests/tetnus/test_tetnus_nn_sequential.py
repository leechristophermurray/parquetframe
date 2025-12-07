import unittest

import pytest

try:
    from parquetframe._rustic import Tensor
    import parquetframe.tetnus.nn as nn

    HAS_TENSOR = True
except (ImportError, AttributeError):
    HAS_TENSOR = False
    nn = None
    Tensor = None

pytestmark = pytest.mark.skipif(
    not HAS_TENSOR, reason="Tensor not available in Rust module"
)


class TestTetnusNNSequential(unittest.TestCase):
    def test_relu(self):
        relu = nn.ReLU()

        # Input: [-1, 0, 1]
        x = Tensor([-1.0, 0.0, 1.0], shape=[1, 3])
        y = relu(x)

        # Expected: [0, 0, 1]
        data = y.data()
        self.assertAlmostEqual(data[0], 0.0)
        self.assertAlmostEqual(data[1], 0.0)
        self.assertAlmostEqual(data[2], 1.0)

    def test_sequential(self):
        # Sequential(Linear(2, 2, bias=False), ReLU())
        # Linear weights initialized randomly, let's overwrite them for testing if possible.
        # Currently we can't overwrite weights easily without access to parameters.

        model = nn.Sequential(nn.Linear(2, 2, bias=False), nn.ReLU())

        print(model)

        input_tensor = Tensor.ones((1, 2))
        output = model(input_tensor)

        self.assertEqual(output.shape, (1, 2))

        # Check parameters
        params = model.parameters()
        self.assertEqual(
            len(params), 1
        )  # One weight matrix, no bias, ReLU has no params

    def test_sequential_training_step(self):
        # Simple training loop simulation
        model = nn.Sequential(nn.Linear(4, 4), nn.ReLU(), nn.Linear(4, 2))

        x = Tensor.randn(10, 4)
        y = model(x)

        self.assertEqual(y.shape, (10, 2))

        loss = y.sum()
        loss.backward()

        # Check if gradients are populated
        for i, p in enumerate(model.parameters()):
            self.assertTrue(p.requires_grad)
            # Gradient should be present after backward
            g = p.grad
            self.assertIsNotNone(g, f"Parameter {i} has no gradient")
