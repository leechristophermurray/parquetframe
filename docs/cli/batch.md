# Batch Processing

> Process multiple files and automate workflows with ParquetFrame CLI.

## Batch Operations

The CLI supports batch processing for handling multiple files and automated workflows.

## Multi-file Processing

Process multiple files in a single command:
- Glob patterns for file selection
- Parallel processing options
- Consistent transformations across files

## Automation

- Script generation for repeatable workflows
- Configuration file support
- Integration with scheduling systems

## Performance

Batch processing optimizes performance through:
- Parallel execution
- Memory management
- Efficient I/O operations

## Summary

Batch processing capabilities make ParquetFrame suitable for production data pipelines and automated workflows.

## Examples

```bash
# Process multiple files
pframe batch "data/*.parquet" --output "processed/"

# Generate processing script
pframe run data.parquet --query "status='active'" --save-script process.py

# Run with configuration file
pframe batch --config batch_config.yaml

# Parallel processing
pframe batch "data/*.parquet" --parallel 4
```

## Further Reading

- [CLI Overview](index.md)
- [Script Generation](scripts.md)
- [CLI Examples](examples.md)
