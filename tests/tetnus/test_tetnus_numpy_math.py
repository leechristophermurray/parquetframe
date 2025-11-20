"""
Test NumPy-compatible mathematical operations.
"""

import pytest
import math


def test_sin():
    """Test sine function."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([0.0, math.pi / 2.0, math.pi], shape=[3])
    c = a.sin()

    data = c.data()
    assert abs(data[0] - 0.0) < 1e-6
    assert abs(data[1] - 1.0) < 1e-6
    assert abs(data[2] - 0.0) < 1e-6


def test_cos():
    """Test cosine function."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([0.0, math.pi / 2.0, math.pi], shape=[3])
    c = a.cos()

    data = c.data()
    assert abs(data[0] - 1.0) < 1e-6
    assert abs(data[1] - 0.0) < 1e-6
    assert abs(data[2] - (-1.0)) < 1e-6


def test_tan():
    """Test tangent function."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([0.0, math.pi / 4.0], shape=[2])
    c = a.tan()

    data = c.data()
    assert abs(data[0] - 0.0) < 1e-6
    assert abs(data[1] - 1.0) < 1e-6


def test_exp():
    """Test exponential function."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([0.0, 1.0, 2.0], shape=[3])
    c = a.exp()

    data = c.data()
    assert abs(data[0] - 1.0) < 1e-6
    assert abs(data[1] - math.e) < 1e-6
    assert abs(data[2] - (math.e * math.e)) < 1e-5


def test_log():
    """Test natural logarithm function."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([1.0, math.e, 10.0], shape=[3])
    c = a.log()

    data = c.data()
    assert abs(data[0] - 0.0) < 1e-6
    assert abs(data[1] - 1.0) < 1e-6
    assert abs(data[2] - math.log(10.0)) < 1e-6


def test_sqrt():
    """Test square root function."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([1.0, 4.0, 9.0, 16.0], shape=[4])
    c = a.sqrt()

    data = c.data()
    assert data == [1.0, 2.0, 3.0, 4.0]


def test_exp_log_inverse():
    """Test that exp and log are inverses."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([1.0, 2.0, 3.0], shape=[3])
    b = a.exp().log()

    data_a = a.data()
    data_b = b.data()

    for i in range(len(data_a)):
        assert abs(data_a[i] - data_b[i]) < 1e-5


def test_math_chain():
    """Test chaining mathematical operations."""
    import parquetframe.tetnus as pt

    a = pt.Tensor([1.0, 2.0, 3.0], shape=[3])
    b = a.sqrt().exp().log()

    # Should give approximately sqrt of original values
    data_a = a.data()
    data_b = b.data()

    for i in range(len(data_a)):
        expected = math.sqrt(data_a[i])
        assert abs(data_b[i] - expected) < 1e-5
