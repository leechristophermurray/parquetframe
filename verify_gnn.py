import parquetframe.tetnus as tt
import parquetframe.tetnus.graph as tg

print(f"Imported tg: {tg}")
print(f"dir(tg): {dir(tg)}")


def verify_gnn():
    print("Testing GNN components...")

    # 1. Test Graph Creation
    # In a real scenario, we'd create a pf.Graph first.
    # For this test, we'll use the static method which creates a dummy graph internally for now.
    # (Since we mocked the from_parquetframe implementation)

    # Mocking a PyAny object for the signature
    dummy_pf_graph = "dummy"
    _graph = tg.Graph.from_parquetframe(dummy_pf_graph)
    print("Graph created successfully.")

    # 2. Test GCNConv
    conv = tg.GCNConv(16, 32)
    print("GCNConv layer created.")

    # Mock inputs
    x = tt.randn([10, 16])  # 10 nodes, 16 features
    edge_index = "dummy_sparse_tensor"  # Mocked in Rust binding

    # Forward pass
    out = conv.forward(x, edge_index)
    print(f"GCNConv forward pass successful. Output type: {type(out)}")

    # 3. Test TemporalGNN
    tgnn = tg.TemporalGNN(16, 32)
    print("TemporalGNN created.")

    out_t, h_t = tgnn.forward(x, edge_index, None)
    print("TemporalGNN forward pass successful.")


if __name__ == "__main__":
    try:
        verify_gnn()
        print("\n✅ GNN Verification Passed!")
    except Exception as e:
        print(f"\n❌ GNN Verification Failed: {e}")
        exit(1)
