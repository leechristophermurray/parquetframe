"""
Test NumPy-compatible tensor creation functions.
"""

import pytest


def test_arange_basic():
    """Test tensor creation with arange."""
    import parquetframe.tetnus as pt

    t = pt.arange(0.0, 10.0, 2.0)
    assert t.shape == (5,)
    data = t.data()
    assert data == [0.0, 2.0, 4.0, 6.0, 8.0]


def test_arange_negative_step():
    """Test arange with negative step."""
    import parquetframe.tetnus as pt

    t = pt.arange(10.0, 0.0, -2.0)
    assert t.shape == (5,)
    data = t.data()
    assert data == [10.0, 8.0, 6.0, 4.0, 2.0]


def test_arange_error():
    """Test arange with invalid step."""
    import parquetframe.tetnus as pt

    with pytest.raises(ValueError):
        pt.arange(0.0, 10.0, 0.0)


def test_linspace():
    """Test linspace tensor creation."""
    import parquetframe.tetnus as pt

    t = pt.linspace(0.0, 1.0, 5)
    assert t.shape == (5,)
    data = t.data()

    # Check endpoints
    assert abs(data[0] - 0.0) < 1e-6
    assert abs(data[-1] - 1.0) < 1e-6


def test_linspace_single():
    """Test linspace with single value."""
    import parquetframe.tetnus as pt

    t = pt.linspace(5.0, 10.0, 1)
    assert t.shape == (1,)
    assert abs(t.data()[0] - 5.0) < 1e-6


def test_eye_square():
    """Test square identity matrix."""
    import parquetframe.tetnus as pt

    t = pt.eye(3, None)
    assert t.shape == (3, 3)
    data = t.data()

    # Check diagonal elements
    assert data[0] == 1.0  # (0, 0)
    assert data[4] == 1.0  # (1, 1)
    assert data[8] == 1.0  # (2, 2)

    # Check off-diagonal
    assert data[1] == 0.0  # (0, 1)
    assert data[3] == 0.0  # (1, 0)


def test_eye_rectangular():
    """Test rectangular identity matrix."""
    import parquetframe.tetnus as pt

    t = pt.eye(2, 3)
    assert t.shape == (2, 3)
    data = t.data()

    assert data[0] == 1.0  # (0, 0)
    assert data[4] == 1.0  # (1, 1)


def test_rand():
    """Test random tensor creation."""
    import parquetframe.tetnus as pt

    t = pt.rand([100])
    assert t.shape == (100,)
    data = t.data()

    # Check values in [0, 1)
    assert all(0.0 <= x < 1.0 for x in data)

    # Check not all the same
    assert len(set(data)) > 50  # At least some variety


def test_randn():
    """Test normal distribution random tensor."""
    import parquetframe.tetnus as pt

    t = pt.randn([1000])
    assert t.shape == (1000,)
    data = t.data()

    # Check approximately normal distribution
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std = variance**0.5

    # Mean should be near 0, std near 1
    assert abs(mean) < 0.2
    assert abs(std - 1.0) < 0.2


def test_full():
    """Test tensor filled with constant value."""
    import parquetframe.tetnus as pt

    t = pt.full([2, 3], 3.14)
    assert t.shape == (2, 3)
    data = t.data()

    assert all(abs(x - 3.14) < 1e-6 for x in data)


def test_full_multidimensional():
    """Test full with multidimensional shape."""
    import parquetframe.tetnus as pt

    t = pt.full([2, 3, 4], -1.5)
    assert t.shape == (2, 3, 4)
    assert t.size == 24
    data = t.data()

    assert all(abs(x - (-1.5)) < 1e-6 for x in data)
