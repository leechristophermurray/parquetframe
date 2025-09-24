# Working with Large Datasets

This tutorial covers strategies for efficiently processing large parquet files using ParquetFrame's automatic backend switching and manual optimization techniques.

## Understanding Backend Selection

ParquetFrame automatically selects the optimal backend based on file size:

- **Files < 10MB**: pandas (fast, in-memory processing)
- **Files ≥ 10MB**: Dask (memory-efficient, distributed processing)

## Scenario 1: Large File Analysis

Let's work with a large e-commerce dataset (2GB+):

### CLI Approach

```bash
# First, inspect the file
pframe info large_ecommerce_data.parquet
```

Expected output:
```
File Information: large_ecommerce_data.parquet
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property            ┃ Value                               ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Size           │ 2,147,483,648 bytes (2.00 GB)      │
│ Recommended Backend │ Dask (lazy)                         │
└─────────────────────┴─────────────────────────────────────┘
```

### Processing Large Data

```bash
# Process with automatic Dask backend
pframe run large_ecommerce_data.parquet \
  --query "order_value > 100 and customer_segment == 'premium'" \
  --columns "customer_id,order_date,order_value,product_category" \
  --sample 1000 \
  --output "premium_customers_sample.parquet"
```

### Python Library Approach

```python
import parquetframe as pqf

# Automatic backend selection
pf = pqf.ParquetFrame.read('large_ecommerce_data.parquet')
print(f"Backend: {'Dask' if pf.islazy else 'pandas'}")

# Process in chunks with Dask
filtered = pf.query("order_value > 100 and customer_segment == 'premium'")
result = filtered[['customer_id', 'order_date', 'order_value', 'product_category']]

# Get sample for exploration
sample = result.sample(1000)
if sample.islazy:
    sample_df = sample._df.compute()
else:
    sample_df = sample._df
    
print(sample_df.head())
```

## Scenario 2: Memory-Constrained Processing

When working with extremely large files on limited memory systems:

### Force Dask for Smaller Files

```bash
# Force Dask even for smaller files
pframe run medium_data.parquet \
  --force-dask \
  --query "status == 'active'" \
  --describe
```

### Streaming Processing

```python
import parquetframe as pqf

# Force Dask backend for memory efficiency
pf = pqf.ParquetFrame.read('huge_dataset.parquet', islazy=True)

# Process in streaming fashion
daily_aggregates = pf.groupby(['date', 'region'])['revenue'].sum()

# Compute and save results
daily_aggregates.save('daily_revenue_by_region.parquet')
```

## Scenario 3: Interactive Exploration of Large Data

### CLI Interactive Session

```bash
pframe interactive large_dataset.parquet
```

In the interactive session:
```python
>>> # Check current backend
>>> print(f"Using {'Dask' if pf.islazy else 'pandas'}")
>>> 
>>> # Get data overview without loading everything
>>> print(f"Total partitions: {pf._df.npartitions}")
>>> 
>>> # Quick statistical overview
>>> pf.describe().compute()
>>> 
>>> # Sample exploration
>>> sample = pf.sample(10000)
>>> sample_pd = sample.to_pandas()  # Convert to pandas for fast exploration
>>> 
>>> # Analyze sample
>>> sample_pd.groupby('category')['price'].agg(['mean', 'count'])
```

## Performance Optimization Tips

### 1. Optimal Partitioning

```python
import parquetframe as pqf

# Read large file
pf = pqf.ParquetFrame.read('large_data.parquet', islazy=True)

# Check current partitioning
print(f"Current partitions: {pf._df.npartitions}")

# Repartition if needed for better performance
if pf.islazy:
    # Increase partitions for better parallelism
    pf._df = pf._df.repartition(npartitions=20)
```

### 2. Efficient Filtering

```bash
# Apply filters early to reduce data movement
pframe run large_dataset.parquet \
  --query "date >= '2024-01-01' and status == 'active'" \  # Filter first
  --columns "user_id,date,amount" \                        # Then select columns
  --sample 5000
```

### 3. Column Selection

```python
# Select only needed columns early
pf = pqf.ParquetFrame.read('wide_dataset.parquet')

# Instead of loading all columns and then selecting
# bad_approach = pf._df[['col1', 'col2']]

# Better: select during read
pf_optimized = pqf.ParquetFrame.read(
    'wide_dataset.parquet', 
    columns=['col1', 'col2', 'col3']
)
```

## Scenario 4: Batch Processing Pipeline

### Shell Script for Daily Processing

```bash
#!/bin/bash
# large_data_pipeline.sh

DATE=$(date -d yesterday +%Y-%m-%d)
INPUT_FILE="raw_data_${DATE}.parquet"
OUTPUT_DIR="processed_data"

echo "Processing data for $DATE"

# Step 1: Basic filtering and cleaning
pframe run "$INPUT_FILE" \
  --query "timestamp >= '$DATE' and user_id.notnull()" \
  --output "$OUTPUT_DIR/clean_${DATE}.parquet"

# Step 2: Generate daily metrics
pframe run "$OUTPUT_DIR/clean_${DATE}.parquet" \
  --columns "user_id,event_type,value,timestamp" \
  --output "$OUTPUT_DIR/metrics_${DATE}.parquet" \
  --save-script "$OUTPUT_DIR/metrics_script_${DATE}.py"

# Step 3: Create summary report
pframe run "$OUTPUT_DIR/metrics_${DATE}.parquet" \
  --describe \
  --save-script "$OUTPUT_DIR/summary_${DATE}.py"

echo "Processing complete for $DATE"
```

## Memory Management

### Monitor Memory Usage

```python
import psutil
import parquetframe as pqf

# Monitor memory before processing
initial_memory = psutil.virtual_memory().percent
print(f"Initial memory usage: {initial_memory}%")

# Process with Dask for memory efficiency
pf = pqf.ParquetFrame.read('large_file.parquet', islazy=True)

# Process in chunks
result = pf.query("amount > 1000").groupby('category').sum()

# Memory after processing
final_memory = psutil.virtual_memory().percent
print(f"Final memory usage: {final_memory}%")
```

### Cleanup Resources

```python
# Explicitly clean up when done
if pf.islazy:
    # Close Dask client if needed
    from dask.distributed import get_client
    try:
        client = get_client()
        client.close()
    except:
        pass

# Clear variables
del pf, result
```

## Error Handling for Large Files

### Common Issues and Solutions

```python
import parquetframe as pqf

try:
    pf = pqf.ParquetFrame.read('problematic_large_file.parquet')
except MemoryError:
    print("File too large for pandas, forcing Dask...")
    pf = pqf.ParquetFrame.read('problematic_large_file.parquet', islazy=True)
    
except FileNotFoundError:
    print("File not found, checking alternative locations...")
    # Handle missing files
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Fallback processing
```

### CLI Error Recovery

```bash
# If normal processing fails, try with Dask
if ! pframe run huge_file.parquet --query "status == 'active'"; then
    echo "Normal processing failed, trying with Dask..."
    pframe run huge_file.parquet --force-dask --query "status == 'active'"
fi
```

## Best Practices Summary

1. **File Size Awareness**: Let ParquetFrame choose the backend automatically
2. **Early Filtering**: Apply filters before column selection
3. **Column Selection**: Only read necessary columns
4. **Chunked Processing**: Use Dask for operations on large datasets
5. **Memory Monitoring**: Keep track of memory usage during processing
6. **Error Handling**: Plan for memory and processing failures
7. **Batch Processing**: Use CLI for automated pipelines
8. **Interactive Exploration**: Use samples for initial data exploration

This approach ensures efficient processing of large datasets while maintaining flexibility and performance.