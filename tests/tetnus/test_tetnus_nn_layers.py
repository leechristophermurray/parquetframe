import parquetframe.tetnus as tt
from parquetframe.tetnus import nn


def test_embedding():
    num_embeddings = 10
    embedding_dim = 4
    embed = nn.Embedding(num_embeddings, embedding_dim)

    # Input indices: [Batch=2]
    input_indices = tt.Tensor([1.0, 5.0], [2])  # Using float as proxy for int index

    output = embed.forward(input_indices)

    assert output.shape == (2, embedding_dim)
    assert output.requires_grad

    # Check gradients flow
    loss = output.sum()
    loss.backward()

    # Weight should have gradients
    params = embed.parameters()
    assert len(params) == 1
    assert params[0].grad is not None
    assert params[0].grad.shape == (num_embeddings, embedding_dim)


def test_layer_norm():
    features = 4
    norm = nn.LayerNorm([features])

    # Input: [Batch=2, Features=4]
    x = tt.randn(2, features).requires_grad_()

    output = norm.forward(x)

    assert output.shape == (2, features)

    # Check normalization (approximate)
    # Mean should be close to beta (0), Std close to gamma (1)
    # Since we initialize gamma=1, beta=0

    loss = output.sum()
    loss.backward()

    params = norm.parameters()
    # Gamma, Beta
    assert len(params) == 2
    assert params[0].grad is not None  # Gamma
    assert params[1].grad is not None  # Beta
    assert x.grad is not None


def test_numerical_processor():
    proc = nn.NumericalProcessor()

    # Input: [Batch=3] scalar features
    x = tt.Tensor([10.0, 20.0, 30.0], [3]).requires_grad_()

    output = proc.forward(x)

    # Should reshape to [3, 1] and normalize
    assert output.shape == (3, 1)

    loss = output.sum()
    loss.backward()

    params = proc.parameters()
    assert len(params) == 2  # Gamma, Beta from LayerNorm
    assert x.grad is not None


def test_categorical_processor():
    num_cats = 5
    emb_dim = 3
    proc = nn.CategoricalProcessor(num_cats, emb_dim)

    x = tt.Tensor([0.0, 2.0, 4.0], [3])

    output = proc.forward(x)

    assert output.shape == (3, emb_dim)

    loss = output.sum()
    loss.backward()

    params = proc.parameters()
    assert len(params) == 1  # Embedding weight
    assert params[0].grad is not None


def test_sequential_integration():
    model = nn.Sequential()
    model.add(nn.NumericalProcessor())
    model.add(nn.Linear(1, 10))
    model.add(nn.ReLU())

    x = tt.Tensor([1.0, 2.0, 3.0], [3]).requires_grad_()

    output = model.forward(x)

    assert output.shape == (3, 10)

    loss = output.sum()
    loss.backward()

    # Check gradients for all layers
    for param in model.parameters():
        assert param.grad is not None
