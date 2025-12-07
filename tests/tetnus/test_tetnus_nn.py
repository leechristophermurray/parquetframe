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


class TestTetnusNN(unittest.TestCase):
    def test_linear(self):
        # Create Linear layer
        # in_features=4, out_features=2
        linear = nn.Linear(4, 2, True)

        # Create input tensor [Batch=1, In=4]
        input_tensor = Tensor.ones((1, 4))

        # Forward pass (using __call__)
        output = linear(input_tensor)

        self.assertEqual(output.shape, (1, 2))
        self.assertEqual(output.ndim, 2)
        self.assertIsInstance(output, Tensor)

    def test_parameters(self):
        linear = nn.Linear(4, 2)
        params = linear.parameters()
        self.assertEqual(len(params), 2)  # weight + bias

        # params are Tensor objects
        weight = params[0]
        bias = params[1]

        self.assertEqual(weight.shape, (2, 4))  # [Out, In]
        self.assertEqual(bias.shape, (2,))  # [Out]


if __name__ == "__main__":
    unittest.main()
