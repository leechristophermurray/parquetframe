import parquetframe.tetnus as tt
import parquetframe.tetnus.llm as tl


def verify_llm():
    print("Testing LLM components...")

    # 1. Test LoRA Layer Creation
    lora = tl.LoRALinear(in_features=768, out_features=768, rank=8, alpha=1.0)
    print("LoRALinear layer created successfully.")

    # 2. Test LoRA Forward Pass
    x = tt.Tensor.randn([4, 768])
    y = lora.forward(x)
    print(f"LoRA forward pass successful. Output type: {type(y)}")

    print("\nLLM verification complete.")


if __name__ == "__main__":
    try:
        verify_llm()
        print("\n✅ LLM Verification Passed!")
    except Exception as e:
        print(f"\n❌ LLM Verification Failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
