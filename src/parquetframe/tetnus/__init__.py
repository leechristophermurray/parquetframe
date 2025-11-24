"""
Tetnus: DataFrame-Native ML Framework

A high-performance machine learning framework built on Arrow-native tensors
with automatic differentiation.
"""

# Core tensor operations
from parquetframe._rustic import Tensor

# Neural network layers
from . import nn
from . import optim

# High-level API
from .api import Model, dataframe_to_tensor

__all__ = [
    "Tensor",
    "nn",
    "optim",
    "Model",
    "dataframe_to_tensor",
]


class Tensor:
    """
    High-level Tensor wrapper providing NumPy-like interface. Examples:
        >>> import parquetframe.tetnus as pt
        >>> a = pt.Tensor.zeros([2, 3])
        >>> b = pt.Tensor.ones([3, 2])
        >>> c = a @ b  # Matrix multiplication
        >>> c.sum().backward()  # Compute gradients
    """

    def __init__(self, data, shape=None):
        """
        Create tensor from data. Args:
            data: List or nested list of numbers
            shape: Optional shape (inferred if not provided)
        """
        if isinstance(data, list):
            if shape is None:
                # Infer shape from nested list
                shape = self._infer_shape(data)
            self._tensor = tetnus.from_list(data, shape)
        else:
            # Assume it's already a Rust tensor
            self._tensor = data

    @staticmethod
    def _infer_shape(data):
        """Infer shape from nested list."""
        shape = []
        current = data
        while isinstance(current, list):
            shape.append(len(current))
            if current:
                current = current[0]
            else:
                break
        return shape

    @staticmethod
    def zeros(shape):
        """Create tensor filled with zeros."""
        return Tensor(tetnus.zeros(shape))

    @staticmethod
    def ones(shape):
        """Create tensor filled with ones."""
        return Tensor(tetnus.ones(shape))

    @staticmethod
    def randn(*shape):
        """Create tensor with random values from standard normal distribution."""
        if len(shape) == 1 and isinstance(shape[0], list | tuple):
            shape = shape[0]
        return Tensor(tetnus.randn(list(shape)))

    @staticmethod
    def linspace(start, stop, num=50):
        """Create tensor with linearly spaced values."""
        return Tensor(tetnus.linspace(float(start), float(stop), int(num)))

    @property
    def shape(self):
        """Tensor shape."""
        return tuple(self._tensor.shape)

    @property
    def ndim(self):
        """Number of dimensions."""
        return self._tensor.ndim

    @property
    def size(self):
        """Total number of elements."""
        return self._tensor.numel

    @property
    def grad(self):
        """Gradient tensor (if computed)."""
        grad_tensor = self._tensor.grad
        if grad_tensor is None:
            return None
        return Tensor(grad_tensor)

    @property
    def requires_grad(self):
        """Whether this tensor requires gradient."""
        return self._tensor.requires_grad

    def requires_grad_(self):
        """Enable gradient tracking (in-place)."""
        self._tensor = self._tensor.requires_grad_()
        return self

    def data(self):
        """Get tensor data as Python list."""
        return self._tensor.data()

    def backward(self):
        """Compute gradients via backpropagation."""
        tetnus.backward(self._tensor)

    def to_numpy(self):
        """Convert to NumPy array."""
        return self._tensor.to_numpy()

    # Operations
    def __matmul__(self, other):
        """Matrix multiplication: a @ b"""
        result = tetnus.matmul(self._tensor, other._tensor)
        return Tensor(result)

    def __add__(self, other):
        """Element-wise addition: a + b"""
        result = tetnus.add(self._tensor, other._tensor)
        return Tensor(result)

    def __sub__(self, other):
        """Element-wise subtraction: a - b"""
        result = tetnus.sub(self._tensor, other._tensor)
        return Tensor(result)

    def __mul__(self, other):
        """Element-wise multiplication: a * b"""
        result = tetnus.mul(self._tensor, other._tensor)
        return Tensor(result)

    def __truediv__(self, other):
        """Element-wise division: a / b"""
        result = tetnus.div(self._tensor, other._tensor)
        return Tensor(result)

    def add(self, other):
        return self + other

    def sub(self, other):
        return self - other

    def mul(self, other):
        return self * other

    def div(self, other):
        return self / other

    def reshape(self, *shape):
        """Reshape tensor."""
        if len(shape) == 1 and isinstance(shape[0], list | tuple):
            shape = shape[0]
        result = tetnus.reshape(self._tensor, list(shape))
        return Tensor(result)

    def T(self):
        """Transpose (2D tensors only)."""
        result = tetnus.transpose(self._tensor)
        return Tensor(result)

    def transpose(self, *args):
        """Transpose tensor. Currently alias for T() for 2D."""
        return self.T()

    def sum(self):
        """Sum all elements."""
        result = tetnus.sum(self._tensor)
        return Tensor(result)

    def mean(self):
        """Mean of all elements."""
        result = tetnus.mean(self._tensor)
        return Tensor(result)

    def sin(self):
        """Element-wise sine."""
        result = tetnus.sin(self._tensor)
        return Tensor(result)

    def cos(self):
        """Element-wise cosine."""
        result = tetnus.cos(self._tensor)
        return Tensor(result)

    def tan(self):
        """Element-wise tangent."""
        result = tetnus.tan(self._tensor)
        return Tensor(result)

    def exp(self):
        """Element-wise exponential."""
        result = tetnus.exp(self._tensor)
        return Tensor(result)

    def log(self):
        """Element-wise natural logarithm."""
        result = tetnus.log(self._tensor)
        return Tensor(result)

    def sqrt(self):
        """Element-wise square root."""
        result = tetnus.sqrt(self._tensor)
        return Tensor(result)

    def __repr__(self):
        return f"Tensor(shape={self.shape}, requires_grad={self.requires_grad})"


# Alias for NumPy-like API
zeros = Tensor.zeros
ones = Tensor.ones


# New NumPy-compatible creation functions
def arange(start, stop, step=1.0):
    """Create tensor with evenly spaced values."""
    return Tensor(tetnus.arange(float(start), float(stop), float(step)))


def linspace(start, stop, num=50):
    """Create tensor with linearly spaced values."""
    return Tensor(tetnus.linspace(float(start), float(stop), int(num)))


def eye(n, m=None):
    """Create identity matrix."""
    return Tensor(tetnus.eye(int(n), int(m) if m is not None else None))


def rand(*shape):
    """Create tensor filled with random values [0, 1)."""
    if len(shape) == 1 and isinstance(shape[0], list | tuple):
        shape = shape[0]
    return Tensor(tetnus.rand(list(shape)))


def randn(*shape):
    """Create tensor with random values from standard normal distribution."""
    if len(shape) == 1 and isinstance(shape[0], list | tuple):
        shape = shape[0]
    return Tensor(tetnus.randn(list(shape)))


def full(shape, value):
    """Create tensor filled with a constant value."""
    if not isinstance(shape, list | tuple):
        shape = [shape]
    return Tensor(tetnus.full(list(shape), float(value)))


__all__ = [
    "Tensor",
    "zeros",
    "ones",
    "arange",
    "linspace",
    "eye",
    "rand",
    "randn",
    "full",
    "numpy",
    "nn",
]

# Expose submodules
# Expose submodules
# Expose graph module from Rust
import sys

from . import nn, numpy

try:
    graph = tetnus.graph
    sys.modules["parquetframe.tetnus.graph"] = graph
except AttributeError:
    # Fallback or warning if graph module is not available
    pass

# Expose llm module from Rust
try:
    llm = tetnus.llm
    sys.modules["parquetframe.tetnus.llm"] = llm
except AttributeError:
    # Fallback or warning if llm module is not available
    pass

# Expose edge module from Rust
try:
    edge = tetnus.edge
    sys.modules["parquetframe.tetnus.edge"] = edge
except AttributeError:
    # Fallback or warning if edge module is not available
    pass

__all__.append("graph")
__all__.append("llm")
__all__.append("edge")
