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


class ReLU(Module):
    """Rectified Linear Unit"""

    def __init__(self):
        self._inner = _rust_tetnus.nn.ReLU()

    def forward(self, input: Tensor) -> Tensor:
        if not isinstance(input, Tensor):
            raise TypeError("input must be a Tensor")
        out_rust = self._inner.forward(input._tensor)
        return Tensor(out_rust)

    def __repr__(self):
        return "ReLU()"


class Sequential(Module):
    """A sequential container."""

    def __init__(self, *args):
        self._inner = _rust_tetnus.nn.Sequential()
        self._modules = []
        for module in args:
            self.add(module)

    def add(self, module: Module):
        if not hasattr(module, "_inner"):
            raise TypeError(
                "Sequential currently only supports Rust-backed modules (Linear, ReLU)"
            )

        # Add to Rust sequential
        # Note: this copies/clones the module into Rust Sequential
        self._inner.add(module._inner)
        self._modules.append(module)

    def forward(self, input: Tensor) -> Tensor:
        if not isinstance(input, Tensor):
            raise TypeError("input must be a Tensor")
        out_rust = self._inner.forward(input._tensor)
        return Tensor(out_rust)

    def parameters(self):
        return [Tensor(p) for p in self._inner.parameters()]

    def __repr__(self):
        return "Sequential(\n  " + "\n  ".join(str(m) for m in self._modules) + "\n)"
