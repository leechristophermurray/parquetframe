import parquetframe.tetnus as tt
import parquetframe.tetnus.llm as tl


def verify_llm_training():
    print("Testing LLM training components...")

    # 1. Test Simple Transformer Creation
    model = tl.SimpleTransformer(hidden_size=128, num_layers=2)
    print("✓ SimpleTransformer created successfully")

    # 2. Test LoRA application
    model.apply_lora(rank=4, alpha=1.0)
    print("✓ LoRA applied to model")

    # 3. Test Trainer Creation
    trainer = tl.Trainer(hidden_size=128, num_layers=2, rank=4, alpha=1.0)
    print("✓ Trainer created successfully")

    # 4. Test Training Step
    x = tt.Tensor.randn([8, 128])
    y = tt.Tensor.randn([8, 128])
    loss = trainer.train_step(x, y)
    print(f"✓ Training step executed. Loss: {loss}")

    print("\n✅ LLM Training Verification Complete!")


if __name__ == "__main__":
    try:
        verify_llm_training()
    except Exception as e:
        print(f"\n❌ LLM Training Verification Failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
