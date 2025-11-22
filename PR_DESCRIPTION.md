# feat(tetnus): Implement Phases 4-6 - GNNs, LLM Fine-Tuning, and Edge AI

## Summary

This PR implements three major phases of the Tetnus framework:
- **Phase 4:** DataFrame-Native Graph Neural Networks
- **Phase 5:** LLM Fine-Tuning with LoRA
- **Phase 6:** Edge AI with Google Coral TPU Support

## Changes

### Phase 4: DataFrame-Native GNNs (`tetnus.graph`)

**New Crate:** `crates/tetnus-graph`
- `Graph` struct with `from_parquetframe()` bridge for DataFrame integration
- `SparseTensor` for efficient adjacency matrix representation
- `GCNConv` layer implementing graph convolution: $H^{(l+1)} = \sigma(\tilde{D}^{-1/2}\tilde{A}\tilde{D}^{-1/2} H^{(l)} W^{(l)})$
- `TemporalGNN` combining GNN with RNN for time-series graphs
- Full Python bindings via `parquetframe.tetnus.graph`

**Testing:** `verify_gnn.py` - All components verified ✅

### Phase 5: LLM Fine-Tuning (`tetnus.llm`)

**New Crate:** `crates/tetnus-llm`
- `LoRALinear` layer with low-rank adaptation: $W' = W + \alpha B A$
  - Reduces trainable parameters from $d \times k$ to $(d+k) \times r$
- `SimpleTransformer` model with LoRA support
- `Trainer` class for fine-tuning pipeline
- `ModelConfig` for transformer configuration
- Full Python bindings via `parquetframe.tetnus.llm`

**Testing:** `verify_llm.py` and `verify_llm_training.py` - All tests passing ✅

### Phase 6: Edge AI & Google Coral (`tetnus.edge`)

**New Crate:** `crates/tetnus-coral-driver`
- Rust FFI bindings for `libedgetpu.so` with RAII safety
- Mock implementation for development without hardware
- Conditional compilation via `coral-hardware` feature flag

**Quantization Infrastructure:** `crates/tetnus-nn/src/quantization.rs`
- Post-training quantization (PTQ) for int8 conversion
- Asymmetric quantization: maps float32 range to [-128, 127]
- Formula: $q = \text{round}(x / s - z)$, $x = (q + z) \cdot s$
- 4/4 unit tests passing ✅

**Python Bindings:** `parquetframe.tetnus.edge`
- `EdgeModel.load(path)` - Load TFLite models
- `EdgeModel.invoke(input, output_size)` - Run inference

## Dependencies

- Downgraded `arrow` and `parquet` to `53.3.0` for DataFusion compatibility
- Added `serde` to `tetnus-llm` for configuration serialization
- Fixed `tetnus-nn` optim module export

## Testing

```bash
# Run all tetnus tests
cargo test -p tetnus-graph
cargo test -p tetnus-llm
cargo test -p tetnus-nn quantization
cargo test -p tetnus-coral-driver

# Python verification
python verify_gnn.py
python verify_llm.py
python verify_llm_training.py
```

**Status:** All tests passing ✅ (minor unused import warnings only)

## Deferred

- **ONNX Export:** Complex feature deferred to future PR
- **Phase 7 (Workflow Integration):** Separate PR for cleaner review

## Related Issues

Implements functionality described in `CONTEXT_TETNUS.md` Phases 4, 5, and 6.

## Checklist

- [x] Code compiles without errors
- [x] All tests passing
- [x] Python bindings functional
- [x] Pre-commit hooks satisfied
- [x] Documentation updated (walkthrough.md)
- [x] Conventional commits used

## Commits

1. `b2fcfc4` - Phase 4 & 5 initial implementation (GNNs + LoRA)
2. `6925860` - Phase 5 completion (LLM training infrastructure)
3. `7463334` - Phase 6 Coral driver (FFI + mock)
4. `9127e07` - Quantization (PTQ with int8)
5. `4746057` - Edge Python bindings

---

**Review Notes:** This is a substantial feature addition (~800+ lines). Each phase builds on tetnus-core and integrates with the existing DataFrame-native philosophy. The implementation prioritizes mathematical correctness and type safety.
