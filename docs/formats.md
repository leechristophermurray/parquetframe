# File Formats

> Working with different data formats in ParquetFrame.

## Supported Formats

ParquetFrame primarily works with Parquet files but supports reading from and writing to multiple formats.

## Parquet Format

The native format with optimal performance:
- Column-oriented storage
- Built-in compression
- Schema evolution support
- Metadata preservation

## Other Formats

- **CSV**: Read CSV files and convert to Parquet
- **JSON**: Import JSON data
- **Feather**: High-performance Arrow format
- **ORC**: Optimized Row Columnar format

## Format Conversion

Easy conversion between supported formats with optimized performance.

## Summary

While Parquet is the primary format, ParquetFrame provides flexibility to work with various data formats as needed.

## Examples

```python
import parquetframe as pf

# Read parquet (native)
df = pf.read("data.parquet")

# Read CSV and save as parquet
df = pf.read("data.csv")
df.save("data.parquet")

# Convert between formats
pf.convert("data.csv", "data.parquet")

# Read with format detection
df = pf.read("data.file")  # Auto-detects format
```

## Further Reading

- [Performance Tips](performance.md)
- [Basic Usage](usage.md)
- [Advanced Features](advanced.md)
