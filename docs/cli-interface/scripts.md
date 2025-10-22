# Script Generation

> Generate Python scripts from CLI commands for reproducible workflows.

## Automatic Script Generation

ParquetFrame can automatically generate Python scripts from your CLI operations.

## Script Types

Generate different types of scripts:
- **Standalone scripts**: Self-contained Python files
- **Jupyter notebooks**: Interactive analysis notebooks
- **Workflow scripts**: Integration with workflow engines

## Reproducibility

Generated scripts ensure:
- Reproducible analysis
- Version control compatibility
- Easy sharing and collaboration

## Customization

Control script generation with:
- Template customization
- Comment inclusion
- Error handling patterns

## Summary

Script generation bridges the gap between interactive CLI usage and production Python code.

## Examples

```bash
# Generate script while processing
pframe run data.parquet --query "age > 25" --save-script analysis.py

# Generate notebook
pframe run data.parquet --head 100 --save-notebook exploration.ipynb

# Custom template
pframe run data.parquet --filter active --save-script pipeline.py --template production
```

## Further Reading

- [CLI Overview](index.md)
- [Batch Processing](batch.md)
- [CLI Examples](../documentation-examples/examples.md)
