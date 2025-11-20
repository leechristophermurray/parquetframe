"""
Tetnus NumPy-compatible API.
Provides a NumPy-like interface for Tetnus tensors.
"""

from .. import Tensor
from .. import tetnus as _rust_tetnus


# Creation functions
def array(object):
    """Create a tensor from a list or existing data."""
    return Tensor(object)


def zeros(shape):
    """Return a new tensor of given shape and type, filled with zeros."""
    return Tensor(_rust_tetnus.zeros(shape))


def ones(shape):
    """Return a new tensor of given shape and type, filled with ones."""
    return Tensor(_rust_tetnus.ones(shape))


def arange(start, stop=None, step=1.0):
    """Return evenly spaced values within a given interval."""
    if stop is None:
        stop = start
        start = 0.0
    return Tensor(_rust_tetnus.arange(float(start), float(stop), float(step)))


def linspace(start, stop, num=50):
    """Return evenly spaced numbers over a specified interval."""
    return Tensor(_rust_tetnus.linspace(float(start), float(stop), int(num)))


def eye(n, m=None):
    """Return a 2-D tensor with ones on the diagonal and zeros elsewhere."""
    return Tensor(_rust_tetnus.eye(int(n), int(m) if m is not None else None))


def rand(*shape):
    """Random values in a given shape."""
    if len(shape) == 1 and isinstance(shape[0], list | tuple):
        shape = shape[0]
    return Tensor(_rust_tetnus.rand(list(shape)))


def randn(*shape):
    """Return a sample (or samples) from the \"standard normal\" distribution."""
    if len(shape) == 1 and isinstance(shape[0], list | tuple):
        shape = shape[0]
    return Tensor(_rust_tetnus.randn(list(shape)))


def full(shape, value):
    """Return a new tensor of given shape and type, filled with fill_value."""
    if not isinstance(shape, list | tuple):
        shape = [shape]
    return Tensor(_rust_tetnus.full(list(shape), float(value)))


# Operations
def matmul(x1, x2):
    """Matrix product of two tensors."""
    if not isinstance(x1, Tensor):
        x1 = array(x1)
    if not isinstance(x2, Tensor):
        x2 = array(x2)
    return x1 @ x2


def add(x1, x2):
    """Add arguments element-wise."""
    if not isinstance(x1, Tensor):
        x1 = array(x1)
    if not isinstance(x2, Tensor):
        x2 = array(x2)
    return x1 + x2


def multiply(x1, x2):
    """Multiply arguments element-wise."""
    if not isinstance(x1, Tensor):
        x1 = array(x1)
    if not isinstance(x2, Tensor):
        x2 = array(x2)
    return x1 * x2


def reshape(a, newshape):
    """Gives a new shape to a tensor without changing its data."""
    if not isinstance(a, Tensor):
        a = array(a)
    return a.reshape(newshape)


def transpose(a):
    """Reverse or permute the axes of a tensor; returns the modified tensor."""
    if not isinstance(a, Tensor):
        a = array(a)
    return a.T()


def sum(a):
    """Sum of array elements."""
    if not isinstance(a, Tensor):
        a = array(a)
    return a.sum()


def sin(x):
    """Trigonometric sine, element-wise."""
    if not isinstance(x, Tensor):
        x = array(x)
    return x.sin()


def cos(x):
    """Cosine element-wise."""
    if not isinstance(x, Tensor):
        x = array(x)
    return x.cos()


def tan(x):
    """Compute tangent element-wise."""
    if not isinstance(x, Tensor):
        x = array(x)
    return x.tan()


def exp(x):
    """Calculate the exponential of all elements in the input tensor."""
    if not isinstance(x, Tensor):
        x = array(x)
    return x.exp()


def log(x):
    """Natural logarithm, element-wise."""
    if not isinstance(x, Tensor):
        x = array(x)
    return x.log()


def sqrt(x):
    """Return the non-negative square-root of an array, element-wise."""
    if not isinstance(x, Tensor):
        x = array(x)
    return x.sqrt()
