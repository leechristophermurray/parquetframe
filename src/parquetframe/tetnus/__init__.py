"""
Tetnus: DataFrame-Native ML Framework

A high-performance machine learning framework built on Arrow-native tensors
with automatic differentiation.
"""

# Core tensor operations
# Core tensor operations
from parquetframe import _rustic

# Access the Rust submodule
try:
    _rust_tetnus = _rustic.tetnus
    Tensor = _rust_tetnus.Tensor
except AttributeError:
    # Fallback for when extension is not compiled/available (e.g. during linting)
    _rust_tetnus = None
    Tensor = None

# Neural network layers
from . import nn, optim

# High-level API
from .api import Model, dataframe_to_tensor

__all__ = [
    "Tensor",
    "nn",
    "optim",
    "Model",
    "dataframe_to_tensor",
]


# Tensor class removed to avoid redefinition
class _TensorPlaceholder:
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
            self._tensor = _rust_tetnus.from_list(data, shape)
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
        return Tensor(_rust_tetnus.zeros(shape))

    @staticmethod
    def ones(shape):
        """Create tensor filled with ones."""
        return Tensor(_rust_tetnus.ones(shape))

    @staticmethod
    def randn(*shape):
        """Create tensor with random values from standard normal distribution."""
        if len(shape) == 1 and isinstance(shape[0], list | tuple):
            shape = shape[0]
        return Tensor(_rust_tetnus.randn(list(shape)))

    @staticmethod
    def linspace(start, stop, num=50):
        """Create tensor with linearly spaced values."""
        return Tensor(_rust_tetnus.linspace(float(start), float(stop), int(num)))

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
        _rust_tetnus.backward(self._tensor)

    def to_numpy(self):
        """Convert to NumPy array."""
        return self._tensor.to_numpy()

    # Operations
    def __matmul__(self, other):
        """Matrix multiplication: a @ b"""
        result = _rust_tetnus.matmul(self._tensor, other._tensor)
        return Tensor(result)

    def __add__(self, other):
        """Element-wise addition: a + b"""
        result = _rust_tetnus.add(self._tensor, other._tensor)
        return Tensor(result)

    def __sub__(self, other):
        """Element-wise subtraction: a - b"""
        result = _rust_tetnus.sub(self._tensor, other._tensor)
        return Tensor(result)

    def __mul__(self, other):
        """Element-wise multiplication: a * b"""
        result = _rust_tetnus.mul(self._tensor, other._tensor)
        return Tensor(result)

    def __truediv__(self, other):
        """Element-wise division: a / b"""
        result = _rust_tetnus.div(self._tensor, other._tensor)
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
        result = _rust_tetnus.reshape(self._tensor, list(shape))
        return Tensor(result)

    def T(self):
        """Transpose (2D tensors only)."""
        result = _rust_tetnus.transpose(self._tensor)
        return Tensor(result)

    def transpose(self, *args):
        """Transpose tensor. Currently alias for T() for 2D."""
        return self.T()

    def sum(self):
        """Sum all elements."""
        result = _rust_tetnus.sum(self._tensor)
        return Tensor(result)

    def mean(self):
        """Mean of all elements."""
        result = _rust_tetnus.mean(self._tensor)
        return Tensor(result)

    def sin(self):
        """Element-wise sine."""
        result = _rust_tetnus.sin(self._tensor)
        return Tensor(result)

    def cos(self):
        """Element-wise cosine."""
        result = _rust_tetnus.cos(self._tensor)
        return Tensor(result)

    def tan(self):
        """Element-wise tangent."""
        result = _rust_tetnus.tan(self._tensor)
        return Tensor(result)

    def exp(self):
        """Element-wise exponential."""
        result = _rust_tetnus.exp(self._tensor)
        return Tensor(result)

    def log(self):
        """Element-wise natural logarithm."""
        result = _rust_tetnus.log(self._tensor)
        return Tensor(result)

    def sqrt(self):
        """Element-wise square root."""
        result = _rust_tetnus.sqrt(self._tensor)
        return Tensor(result)

    def __repr__(self):
        return f"Tensor(shape={self.shape}, requires_grad={self.requires_grad})"


# Alias for NumPy-like API
# Alias for NumPy-like API
if Tensor is not None:
    zeros = Tensor.zeros
    ones = Tensor.ones
else:
    zeros = _TensorPlaceholder.zeros
    ones = _TensorPlaceholder.ones


# New NumPy-compatible creation functions
def arange(start, stop, step=1.0):
    """Create tensor with evenly spaced values."""
    if _rust_tetnus is not None:
        return Tensor(_rust_tetnus.arange(float(start), float(stop), float(step)))
    return _TensorPlaceholder.zeros([1])  # Mock fallback


def linspace(start, stop, num=50):
    """Create tensor with linearly spaced values."""
    if _rust_tetnus is not None:
        return Tensor(_rust_tetnus.linspace(float(start), float(stop), int(num)))
    return _TensorPlaceholder.zeros([1])  # Mock fallback


def eye(n, m=None):
    """Create identity matrix."""
    if _rust_tetnus is not None:
        return Tensor(_rust_tetnus.eye(int(n), int(m) if m is not None else None))
    return _TensorPlaceholder.zeros([n, n])  # Mock fallback


def rand(*shape):
    """Create tensor filled with random values [0, 1)."""
    if len(shape) == 1 and isinstance(shape[0], list | tuple):
        shape = shape[0]
    if _rust_tetnus is not None:
        return Tensor(_rust_tetnus.rand(list(shape)))
    return _TensorPlaceholder.zeros(list(shape))  # Mock fallback


def randn(*shape):
    """Create tensor with random values from standard normal distribution."""
    if len(shape) == 1 and isinstance(shape[0], list | tuple):
        shape = shape[0]
    if _rust_tetnus is not None:
        return Tensor(_rust_tetnus.randn(list(shape)))
    return _TensorPlaceholder.zeros(list(shape))  # Mock fallback


def full(shape, value):
    """Create tensor filled with a constant value."""
    if not isinstance(shape, list | tuple):
        shape = [shape]
    """Create tensor filled with a constant value."""
    if not isinstance(shape, list | tuple):
        shape = [shape]
    if _rust_tetnus is not None:
        return Tensor(_rust_tetnus.full(list(shape), float(value)))
    return _TensorPlaceholder.zeros(list(shape))  # Mock fallback


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
# Expose submodules
# Expose graph module from Rust
import sys  # noqa: E402

from . import numpy  # noqa: E402

try:
    graph = _rust_tetnus.graph
    sys.modules["parquetframe.tetnus.graph"] = graph
except AttributeError:
    # Fallback or warning if graph module is not available
    pass

# Expose llm module from Rust
try:
    llm = _rust_tetnus.llm
    sys.modules["parquetframe.tetnus.llm"] = llm
except AttributeError:
    # Fallback or warning if llm module is not available
    pass

# Expose edge module from Rust
try:
    edge = _rust_tetnus.edge
    sys.modules["parquetframe.tetnus.edge"] = edge
except AttributeError:
    # Fallback or warning if edge module is not available
    pass

__all__.append("graph")
__all__.append("llm")
__all__.append("edge")

if Tensor is None:
    Tensor = _TensorPlaceholder
