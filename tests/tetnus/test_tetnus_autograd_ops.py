import math

import parquetframe.tetnus as tt


def test_add_grad():
    a = tt.ones([2]).requires_grad_()
    b = tt.ones([2]).requires_grad_()
    # c = a + b = [2, 2]
    c = tt.add(a, b)
    # loss = sum(c) = 4
    loss = tt.sum(c)

    tt.backward(loss)

    # dL/da = 1, dL/db = 1
    grad_a = a.grad.data()
    grad_b = b.grad.data()

    assert grad_a == [1.0, 1.0]
    assert grad_b == [1.0, 1.0]


def test_sub_grad():
    a = tt.ones([2]).requires_grad_()
    b = tt.ones([2]).requires_grad_()
    # c = a - b = [0, 0]
    c = tt.sub(a, b)
    loss = tt.sum(c)

    tt.backward(loss)

    # dL/da = 1, dL/db = -1
    grad_a = a.grad.data()
    grad_b = b.grad.data()

    assert grad_a == [1.0, 1.0]
    assert grad_b == [-1.0, -1.0]


def test_mul_grad():
    a = tt.full([2], 2.0).requires_grad_()
    b = tt.full([2], 3.0).requires_grad_()
    # c = a * b = [6, 6]
    c = tt.mul(a, b)
    loss = tt.sum(c)

    tt.backward(loss)

    # L = sum(a * b)
    # dL/da = b
    # dL/db = a

    grad_a = a.grad.data()
    grad_b = b.grad.data()

    assert grad_a == [3.0, 3.0]
    assert grad_b == [2.0, 2.0]


def test_div_grad():
    a = tt.full([2], 6.0).requires_grad_()
    b = tt.full([2], 2.0).requires_grad_()
    # c = a / b = [3, 3]
    c = tt.div(a, b)
    loss = tt.sum(c)

    tt.backward(loss)

    # L = sum(a / b)
    # dL/da = 1/b
    # dL/db = -a/b^2

    grad_a = a.grad.data()
    grad_b = b.grad.data()

    # dL/da = 1/2 = 0.5
    assert grad_a == [0.5, 0.5]

    # dL/db = -6/4 = -1.5
    assert grad_b == [-1.5, -1.5]


def test_mean_grad():
    a = tt.new([1.0, 2.0, 3.0, 4.0], [4]).requires_grad_()
    # mean = 2.5
    m = tt.mean(a)

    tt.backward(m)

    # dL/da = 1/N = 0.25
    grad_a = a.grad.data()

    assert len(grad_a) == 4
    for g in grad_a:
        assert abs(g - 0.25) < 1e-6


def test_unary_sin_grad():
    # L = sin(x)
    # dL/dx = cos(x)
    x = tt.new([0.0, math.pi / 2, math.pi], [3]).requires_grad_()
    y = tt.sin(x)
    loss = tt.sum(y)

    tt.backward(loss)

    grads = x.grad.data()
    # cos(0) = 1
    # cos(pi/2) = 0
    # cos(pi) = -1

    assert abs(grads[0] - 1.0) < 1e-6
    assert abs(grads[1] - 0.0) < 1e-6
    assert abs(grads[2] - (-1.0)) < 1e-6


def test_complex_graph():
    # f(x) = (x + 2) * 3
    x = tt.ones([1]).requires_grad_()
    two = tt.full([1], 2.0)
    three = tt.full([1], 3.0)

    a = tt.add(x, two)
    b = tt.mul(a, three)

    tt.backward(b)

    # df/dx = 3
    assert x.grad.data()[0] == 3.0
