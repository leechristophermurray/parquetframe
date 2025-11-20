"""
Neural Network module for Tetnus.
"""

from .. import Tensor
from .. import tetnus as _rust_tetnus


class Module:
    """Base class for all neural network modules."""

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def forward(self, *args, **kwargs):
        raise NotImplementedError

    def parameters(self):
        """Return list of parameters."""
        return []


class Linear(Module):
    """Applies a linear transformation to the incoming data: y = xA^T + b"""

    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        self._inner = _rust_tetnus.nn.Linear(in_features, out_features, bias)
        self.in_features = in_features
        self.out_features = out_features

    def forward(self, input: Tensor) -> Tensor:
        if not isinstance(input, Tensor):
            raise TypeError("input must be a Tensor")

        # Call Rust forward with inner PyTensor
        out_rust = self._inner.forward(input._tensor)
        return Tensor(out_rust)

    def parameters(self):
        # Return wrapped Tensors
        return [Tensor(p) for p in self._inner.parameters()]

    def __repr__(self):
        return (
            f"Linear(in_features={self.in_features}, out_features={self.out_features})"
        )
