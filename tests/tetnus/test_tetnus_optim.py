import numpy as np
import pytest

try:
    import parquetframe.tetnus.nn as nn
    import parquetframe.tetnus.optim as optim
    from parquetframe._rustic import Tensor

    HAS_TENSOR = True
except (ImportError, AttributeError):
    HAS_TENSOR = False
    nn = None
    optim = None
    Tensor = None

pytestmark = pytest.mark.skipif(
    not HAS_TENSOR, reason="Tensor not available in Rust module"
)


def test_sgd_step():
    # y = 2x
    # w = 1.0, target = 2.0
    # Loss = (wx - y)^2
    # Let x = 1, y = 2
    # Pred = w * 1 = 1
    # Loss = (1 - 2)^2 = 1
    # dLoss/dw = 2(wx - y) * x = 2(1 - 2) * 1 = -2

    w = Tensor([1.0], [1]).requires_grad_()
    sgd = optim.SGD([w], lr=0.1)

    # Forward
    x = Tensor([1.0], [1])
    y = Tensor([2.0], [1])

    pred = w.mul(x)  # 1.0
    diff = pred.sub(y)  # -1.0
    loss = diff.mul(diff)  # 1.0

    loss.backward()

    # Check grad
    assert w.grad is not None
    # Grad should be -2.0
    np.testing.assert_allclose(w.grad.to_numpy(), [-2.0], atol=1e-5)

    # Step
    sgd.step()

    # New w = w - lr * grad = 1.0 - 0.1 * (-2.0) = 1.2
    np.testing.assert_allclose(w.to_numpy(), [1.2], atol=1e-5)

    # Zero grad
    sgd.zero_grad()
    assert w.grad is None


def test_adam_step():
    w = Tensor([1.0], [1]).requires_grad_()
    adam = optim.Adam([w], lr=0.1)

    x = Tensor([1.0], [1])
    y = Tensor([2.0], [1])

    # Loss = (w*x - y)^2 = (1-2)^2 = 1
    # Grad = -2

    pred = w.mul(x)
    loss = pred.sub(y).mul(pred.sub(y))
    loss.backward()

    adam.step()

    # Adam step is complex, just check it moved in right direction
    # w should increase because grad is negative
    assert w.to_numpy()[0] > 1.0


def test_mse_loss():
    loss_fn = nn.MSELoss()

    pred = Tensor([1.0, 2.0, 3.0], [3]).requires_grad_()
    target = Tensor([1.0, 2.0, 5.0], [3])

    # Diff: [0, 0, -2]
    # Sq: [0, 0, 4]
    # Mean: 4/3 = 1.333

    loss = loss_fn.forward(pred, target)

    np.testing.assert_allclose(loss.to_numpy(), [4.0 / 3.0], atol=1e-5)

    loss.backward()

    # Grad: 2 * diff / N
    # [0, 0, -4/3] = [0, 0, -1.333]

    np.testing.assert_allclose(pred.grad.to_numpy(), [0.0, 0.0, -4.0 / 3.0], atol=1e-5)


def test_cross_entropy_loss():
    loss_fn = nn.CrossEntropyLoss()

    # 2 samples, 3 classes
    logits = Tensor([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]], [2, 3]).requires_grad_()

    # One-hot targets
    # Sample 0: Class 2 (index 2) -> [0, 0, 1]
    # Sample 1: Class 1 (index 1) -> [0, 1, 0]
    target = Tensor([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0]], [2, 3])

    loss = loss_fn.forward(logits, target)

    loss_val = loss.to_numpy()[0]
    # Loss approx 0.907
    assert 0.8 < loss_val < 1.0

    loss.backward()
    assert logits.grad is not None


def test_simple_training_loop():
    # Linear regression: y = 2x + 1
    X = Tensor.linspace(0.0, 1.0, 10).reshape([10, 1])

    # y = 2x + 1
    # Construct y manually
    w_true = Tensor([2.0], [1])
    b_true = Tensor([1.0], [1])

    # Broadcast add needs manual broadcast for now if not auto
    # X: [10, 1], w: [1] -> need explicit mul
    # wait, core mul handles broadcasting? No, previous audits said limited.
    # But let's try.
    # X [10, 1], w_true [1] -> X * 2

    # We use MatMul for X @ W + b
    # X: [10, 1]
    # We want y: [10, 1]

    # Manual y construction
    y_data = []
    x_data = X.to_numpy().flatten()
    for x in x_data:
        y_data.append(2.0 * x + 1.0)

    y = Tensor(y_data, [10, 1])

    model = nn.Linear(1, 1)
    optimizer = optim.SGD(model.parameters(), lr=0.1)
    criterion = nn.MSELoss()

    for _ in range(300):
        optimizer.zero_grad()
        pred = model.forward(X)
        loss = criterion.forward(pred, y)
        loss.backward()
        optimizer.step()

    # Check weights
    params = model.parameters()
    w = params[0].to_numpy()

    # Bias might be index 1
    if len(params) > 1:
        b = params[1].to_numpy()
        # Relax tolerance slightly or rely on more epochs
        assert np.abs(b[0] - 1.0) < 0.15

    assert np.abs(w[0, 0] - 2.0) < 0.15
