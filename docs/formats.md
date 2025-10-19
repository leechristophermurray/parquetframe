# Multi-Format Support

> Comprehensive file format support in ParquetFrame with automatic detection and intelligent backend selection.

## Overview

ParquetFrame supports multiple data formats with automatic format detection, intelligent backend selection (pandas vs Dask), and seamless format conversion. All formats work consistently with the same API.

## Supported Formats

### **Parquet** (.parquet, .pqt)

**Primary format** with optimal performance:
- ✅ Column-oriented storage for fast analytics
- ✅ Built-in compression (snappy, gzip, lz4)
- ✅ Schema evolution and metadata preservation
- ✅ Native support for complex data types
- ✅ Excellent compression ratios

```python
import parquetframe as pf

# Read parquet files
pf_data = pf.ParquetFrame.read("data.parquet")
pf_data = pf.ParquetFrame.read("data.pqt")
pf_data = pf.ParquetFrame.read("data")  # Auto-detects .parquet extension
```

### **CSV** (.csv, .tsv)

**Tabular data** with flexible options:
- ✅ Automatic delimiter detection (comma for .csv, tab for .tsv)
- ✅ Header detection and custom column names
- ✅ Data type inference and custom dtype specification
- ✅ Large file support with Dask backend
- ✅ Memory-efficient reading with chunking

```python
# Read CSV files
pf_data = pf.ParquetFrame.read("data.csv")  # Auto-detects CSV format
pf_data = pf.ParquetFrame.read("data.tsv")  # Tab-separated values

# Custom CSV options
pf_data = pf.ParquetFrame.read("data.csv", sep=";", header=0)
pf_data = pf.ParquetFrame.read("data.csv", dtype={"age": "int32"})
```

### **JSON** (.json, .jsonl, .ndjson)

**Structured data** with nested object support:
- ✅ Regular JSON arrays and objects
- ✅ JSON Lines format for streaming data
- ✅ Newline-delimited JSON (NDJSON)
- ✅ Automatic format detection based on extension
- ✅ Nested data flattening options

```python
# Read different JSON formats
pf_data = pf.ParquetFrame.read("data.json")    # Regular JSON
pf_data = pf.ParquetFrame.read("data.jsonl")   # JSON Lines
pf_data = pf.ParquetFrame.read("data.ndjson")  # Newline-delimited JSON

# Custom JSON options
pf_data = pf.ParquetFrame.read("data.json", orient="records")
```

### **ORC** (.orc)

**Optimized Row Columnar** format:
- ✅ High compression ratios
- ✅ Built-in indexing and statistics
- ✅ Schema evolution support
- ✅ Integration with big data ecosystems
- ⚠️ Requires pyarrow with ORC support

```python
# Read ORC files (requires pyarrow)
pf_data = pf.ParquetFrame.read("data.orc")

# Install ORC support: pip install pyarrow
```

## Automatic Format Detection

ParquetFrame automatically detects file formats based on extensions:

```python
import parquetframe as pf

# All of these work automatically
csv_data = pf.ParquetFrame.read("sales.csv")      # Detects CSV
json_data = pf.ParquetFrame.read("events.jsonl")   # Detects JSON Lines
parquet_data = pf.ParquetFrame.read("users.pqt")   # Detects Parquet
orc_data = pf.ParquetFrame.read("logs.orc")        # Detects ORC
```

## Manual Format Override

Override automatic detection when needed:

```python
# Read .txt file as CSV
data = pf.ParquetFrame.read("data.txt", format="csv")

# Force specific format
data = pf.ParquetFrame.read("ambiguous.data", format="json")
```

## Intelligent Backend Selection

ParquetFrame automatically chooses between pandas and Dask based on:
- **File size**: Large files (>100MB default) use Dask
- **Manual control**: Force backend with `islazy` parameter
- **Memory constraints**: Dask for memory-efficient processing

```python
# Automatic backend selection
small_data = pf.ParquetFrame.read("small.csv")     # Uses pandas
large_data = pf.ParquetFrame.read("huge.csv")      # Uses Dask automatically

# Manual backend control
forced_dask = pf.ParquetFrame.read("data.csv", islazy=True)   # Force Dask
forced_pandas = pf.ParquetFrame.read("data.csv", islazy=False) # Force pandas

# Custom threshold
data = pf.ParquetFrame.read("data.csv", threshold_mb=50)  # Dask if >50MB
```

## Format Conversion

Seamlessly convert between formats:

```python
import parquetframe as pf

# Read CSV, work with data, save as Parquet
data = pf.ParquetFrame.read("source.csv")
processed = data.query("age > 25").groupby("category").sum()
processed.save("result.parquet")

# Chain operations across formats
result = (pf.ParquetFrame.read("data.json")
          .query("status == 'active'")
          .groupby("region").mean())
result.save("summary.parquet")
```

## Error Handling

Robust error handling for different scenarios:

```python
try:
    # Attempt to read with auto-detection
    data = pf.ParquetFrame.read("data.unknown")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Format error: {e}")

# Graceful handling of missing dependencies
try:
    orc_data = pf.ParquetFrame.read("data.orc")
except ImportError:
    print("ORC support requires: pip install pyarrow")
```

## Performance Considerations

### File Size Recommendations

- **Small files (<10MB)**: Any format works well with pandas
- **Medium files (10MB-1GB)**: Parquet recommended for best performance
- **Large files (>1GB)**: Parquet + Dask for memory efficiency
- **Streaming data**: JSON Lines (.jsonl) for append-friendly workflows

### Format-Specific Performance

| Format | Read Speed | Write Speed | Compression | Use Case |
|--------|------------|-------------|-------------|----------|
| Parquet | ⚡️ Fastest | ⚡️ Fastest | 🚀 Excellent | Analytics, long-term storage |
| CSV | 🐌 Slow | 🐌 Slow | ❌ None | Data exchange, human-readable |
| JSON | 🐌 Slow | 🐌 Slow | ❌ None | APIs, nested data |
| ORC | ⚡️ Fast | ⚡️ Fast | 🚀 Excellent | Big data, Hive compatibility |

### Memory Usage

```python
# Memory-efficient reading of large files
big_data = pf.ParquetFrame.read("huge.csv", islazy=True)  # Uses Dask

# Process in chunks to avoid memory issues
for chunk in big_data.iterrows(chunksize=10000):
    process_chunk(chunk)
```

## Best Practices

### Format Selection Guidelines

1. **For Analytics**: Use Parquet for best performance and compression
2. **For Data Exchange**: CSV for wide compatibility
3. **For APIs/Web**: JSON for structured data
4. **For Big Data**: ORC when integrating with Hadoop ecosystem

### File Organization

```python
# Good: Organize by format and purpose
raw_data/
  └── csv/
      ├── daily_sales.csv
      └── customer_data.csv
processed_data/
  └── parquet/
      ├── sales_summary.parquet
      └── customer_analysis.parquet
```

### Data Type Consistency

```python
# Ensure consistent data types across formats
csv_data = pf.ParquetFrame.read("data.csv", dtype={
    "id": "int64",
    "created_at": "datetime64[ns]",
    "amount": "float64"
})

# Save with preserved types
csv_data.save("data.parquet")  # Types maintained
```

## Advanced Usage

### Custom Format Parameters

```python
# CSV with custom parameters
data = pf.ParquetFrame.read("data.csv",
                           sep="|",           # Custom delimiter
                           header=1,          # Header on row 1
                           names=["a", "b"],  # Custom column names
                           skiprows=2,        # Skip first 2 rows
                           nrows=1000)        # Read only 1000 rows

# JSON with specific orientation
data = pf.ParquetFrame.read("data.json", orient="index")
```

### Path Pattern Matching

```python
# Read multiple files with patterns
import glob

all_csvs = []
for file in glob.glob("data/*.csv"):
    df = pf.ParquetFrame.read(file)
    all_csvs.append(df)

# Combine into single dataset
combined = pf.ParquetFrame(pd.concat([df._df for df in all_csvs]))
```

## Troubleshooting

### Common Issues

**File Not Found**:
```python
# ParquetFrame checks multiple extensions
data = pf.ParquetFrame.read("myfile")  # Tries .parquet, .pqt automatically
```

**Mixed Data Types**:
```python
# Specify dtypes explicitly
data = pf.ParquetFrame.read("mixed.csv", dtype={"mixed_col": "str"})
```

**Large File Memory Issues**:
```python
# Force Dask for large files
data = pf.ParquetFrame.read("huge.csv", islazy=True)
```

**Missing Dependencies**:
```bash
# Install all format dependencies
pip install parquetframe[formats]  # Future enhancement

# Or install specific dependencies
pip install pyarrow  # For ORC support
```

## Summary

ParquetFrame's multi-format support provides:

- ✅ **Seamless Integration**: Same API across all formats
- ✅ **Automatic Detection**: Smart format recognition
- ✅ **Performance Optimization**: Backend selection based on file size
- ✅ **Error Resilience**: Graceful handling of missing dependencies
- ✅ **Flexible Configuration**: Custom parameters for each format

Choose the right format for your use case, and let ParquetFrame handle the complexity of reading, processing, and converting between formats efficiently.

## Further Reading

- [Performance Benchmarks](performance.md)
- [Legacy Basic Usage Guide](legacy/legacy-basic-usage.md)
- [Advanced Analytics](advanced.md)
- [Legacy Backend Selection](legacy/legacy-backends.md)
