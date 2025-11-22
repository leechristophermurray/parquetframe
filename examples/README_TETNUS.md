# Tetnus Workflow Integration Examples

This directory contains example YAML workflows demonstrating tetnus ML integration with `pf-workflow-core`.

## tetnus_workflow.yml

End-to-end ML pipeline showing:
- Model training with `tetnus.train`
- Feature importance via `tetnus.attention`
- Edge TPU compilation with `tetnus.compile`
- Inference with `tetnus.infer`

## Status

**Phase 7a (Current):** Stub implementations only
- Workflow YAML demonstrates intended API
- Executors compile but don't execute
- Full implementation in Phase 7b

## Usage (Future)

```bash
# Run the workflow (when Phase 7b is complete)
pf workflow run examples/tetnus_workflow.yml
```

## Workflow Steps

### 1. `tetnus.train`
Train a model from ParquetFrame data.

**Config:**
- `model_type`: TabularTransformer, GNN, or LoRALLM
- `target_column`: Column to predict
- `hyperparameters`: Learning rate, epochs, etc.

### 2. `tetnus.attention`
Extract attention maps for model interpretability.

**Config:**
- `model_path`: Path to trained model
- `output_path`: Where to save attention maps

### 3. `tetnus.compile`
Compile model for Edge TPU deployment.

**Config:**
- `target`: Deployment target (google-coral)
- `quantization`: PTQ parameters

### 4. `tetnus.infer`
Run inference on new data.

**Config:**
- `model_path`: Path to model
- `input_data`: Data to run inference on
