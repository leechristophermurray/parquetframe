"""
Test basic TETNUS tensor operations.
"""

import importlib.util

import pytest

if importlib.util.find_spec("parquetframe.tetnus") and importlib.util.find_spec(
    "parquetframe._rustic"
):
    import parquetframe.tetnus as pt  # noqa: F401
    from parquetframe._rustic import Tensor  # noqa: F401

    HAS_TENSOR = True
else:
    HAS_TENSOR = False
    pt = None

pytestmark = pytest.mark.skipif(
    not HAS_TENSOR, reason="Tensor not available in Rust module"
)


def test_import():
    """Test that we can import tetnus."""
    import parquetframe.tetnus as pt

    assert pt.Tensor is not None


def test_zeros():
    """Test creating tensor with zeros."""
    import parquetframe.tetnus as pt

    t = pt.zeros([2, 3])
    assert t.shape == (2, 3)
    assert t.ndim == 2
    assert t.size == 6

    data = t.data()
    assert all(x == 0.0 for x in data)


def test_ones():
    """Test creating tensor with ones."""
    import parquetframe.tetnus as pt

    t = pt.ones([3, 2])
    assert t.shape == (3, 2)

    data = t.data()
    assert all(x == 1.0 for x in data)


def test_from_list():
    """Test creating tensor from Python list."""
    import parquetframe.tetnus as pt

    t = pt.Tensor([[1, 2, 3], [4, 5, 6]])
    assert t.shape == (2, 3)

    data = t.data()
    assert data == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_matmul():
    """Test matrix multiplication."""
    import parquetframe.tetnus as pt

    # 2x3 @ 3x2 = 2x2
    a = pt.Tensor([[1, 2, 3], [4, 5, 6]])
    b = pt.Tensor([[1, 2], [3, 4], [5, 6]])

    c = a @ b

    assert c.shape == (2, 2)
    data = c.data()

    # [[22, 28], [49, 64]]
    assert data[0] == 22.0
    assert data[1] == 28.0
    assert data[2] == 49.0
    assert data[3] == 64.0


def test_add():
    """Test element-wise addition."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([[1, 2], [3, 4]])
    b = pt.Tensor([[5, 6], [7, 8]])

    c = a + b

    assert c.shape == (2, 2)
    data = c.data()
    assert data == [6.0, 8.0, 10.0, 12.0]


def test_mul():
    """Test element-wise multiplication."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([[2, 3], [4, 5]])
    b = pt.Tensor([[1, 2], [3, 4]])

    c = a * b

    data = c.data()
    assert data == [2.0, 6.0, 12.0, 20.0]


def test_reshape():
    """Test reshape operation."""
    import parquetframe.tetnus as pt

    t = pt.Tensor([[1, 2, 3], [4, 5, 6]])
    assert t.shape == (2, 3)

    t2 = t.reshape(3, 2)
    assert t2.shape == (3, 2)
    assert t2.size == 6


def test_transpose():
    """Test transpose operation."""
    import parquetframe.tetnus as pt

    t = pt.Tensor([[1, 2], [3, 4]])
    t_T = t.T()

    assert t_T.shape == (2, 2)
    data = t_T.data()
    # [[1, 3], [2, 4]]
    assert data == [1.0, 3.0, 2.0, 4.0]


def test_sum():
    """Test sum reduction."""
    import parquetframe.tetnus as pt

    t = pt.Tensor([[1, 2], [3, 4]])
    s = t.sum()

    assert s.shape == (1,)
    assert s.data()[0] == 10.0


def test_requires_grad():
    """Test gradient tracking."""
    import parquetframe.tetnus as pt

    t = pt.ones([2, 2])
    assert not t.requires_grad

    t2 = t.requires_grad_()
    assert t2.requires_grad


def test_autograd_simple():
    """Test simple autograd computation."""
    import parquetframe.tetnus as pt

    # Create tensors with gradient tracking
    a = pt.ones([2, 2]).requires_grad_()
    b = pt.ones([2, 2])

    # Forward pass
    c = a @ b
    loss = c.sum()

    # Backward pass
    loss.backward()

    # Check gradient is computed
    assert a.grad is not None
    assert a.grad.shape == a.shape
