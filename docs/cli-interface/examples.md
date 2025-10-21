# CLI Examples

This page showcases real-world examples of using the ParquetFrame CLI for various data processing tasks.

## Data Exploration

### Quick File Inspection

```bash
# Get basic information about a dataset
pframe info customer_data.parquet
```

Output:
```
File Information: customer_data.parquet
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property            ┃ Value                               ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ File Size           │ 15,234,567 bytes (14.53 MB)        │
│ Recommended Backend │ Dask (lazy)                         │
└─────────────────────┴─────────────────────────────────────┘
```

### Data Preview and Statistics

```bash
# Quick data preview
pframe run sales_data.parquet --head 10

# Statistical summary
pframe run sales_data.parquet --describe

# Data types and null information
pframe run sales_data.parquet --info
```

## Data Filtering

### Simple Filters

```bash
# Filter by single condition
pframe run users.parquet --query "age >= 18" --head 20

# Filter by multiple conditions
pframe run orders.parquet \
  --query "status == 'completed' and total > 100" \
  --head 15
```

### Complex Filtering

```bash
# String operations and date filtering
pframe run transactions.parquet \
  --query "customer_type.str.contains('premium') and date >= '2024-01-01'" \
  --columns "customer_id,amount,date" \
  --head 50
```

### Regional Analysis

```bash
# Multi-value filtering
pframe run sales.parquet \
  --query "region in ['North America', 'Europe'] and revenue > 50000" \
  --describe
```

## Data Processing Pipelines

### Customer Segmentation

```bash
# Identify high-value customers
pframe run customer_data.parquet \
  --query "total_purchases > 1000 and last_purchase_days < 30" \
  --columns "customer_id,name,email,total_purchases,last_purchase_days" \
  --output "high_value_customers.parquet" \
  --save-script "customer_segmentation.py"
```

Generated script (`customer_segmentation.py`):
```python
# Auto-generated script from ParquetFrame CLI session
from parquetframe import ParquetFrame
import parquetframe as pqf

pf = ParquetFrame.read('customer_data.parquet', threshold_mb=10.0, islazy=None)
pf = pf.query('total_purchases > 1000 and last_purchase_days < 30')
pf = pf[['customer_id', 'name', 'email', 'total_purchases', 'last_purchase_days']]
pf.save('high_value_customers.parquet', save_script='customer_segmentation.py')
```

### Sales Analysis

```bash
# Analyze sales performance by region
pframe run quarterly_sales.parquet \
  --query "quarter == 'Q4' and year == 2024" \
  --columns "region,product_category,revenue,units_sold" \
  --output "q4_2024_analysis.parquet"
```

### Data Quality Check

```bash
# Find incomplete records
pframe run user_profiles.parquet \
  --query "email.isnull() or phone.isnull() or address.isnull()" \
  --output "incomplete_profiles.parquet"
```

## Interactive Sessions

### Exploratory Data Analysis

```bash
pframe interactive dataset.parquet
```

Interactive session:
```python
>>> # Explore data structure
>>> pf.info()
>>> pf.head()

>>> # Find interesting patterns
>>> age_dist = pf.groupby('age_group')['revenue'].agg(['mean', 'count'])
>>> print(age_dist)

>>> # Create derived columns
>>> pf_enhanced = pf.copy()
>>> pf_enhanced['revenue_per_unit'] = pf_enhanced['revenue'] / pf_enhanced['units']

>>> # Save results
>>> age_dist.save('age_revenue_analysis.parquet', save_script='eda_session.py')
>>> exit()
```

### Data Cleaning Session

```bash
pframe interactive messy_data.parquet
```

Cleaning workflow:
```python
>>> # Check data quality
>>> pf.isnull().sum()

>>> # Remove duplicates
>>> clean_data = pf.drop_duplicates(subset=['user_id'])

>>> # Fix data types
>>> clean_data['signup_date'] = pd.to_datetime(clean_data['signup_date'])

>>> # Filter valid records
>>> valid_data = clean_data.query('age > 0 and age < 120')

>>> # Save cleaned dataset
>>> valid_data.save('cleaned_data.parquet', save_script='data_cleaning.py')
```

## Backend Optimization

### Force Pandas for Small Operations

```bash
# Use pandas for fast aggregations on small data
pframe run daily_metrics.parquet \
  --force-pandas \
  --query "date == '2024-09-24'" \
  --describe
```

### Force Dask for Memory Efficiency

```bash
# Use Dask for large dataset operations
pframe run huge_dataset.parquet \
  --force-dask \
  --query "category == 'electronics'" \
  --sample 1000 \
  --output "electronics_sample.parquet"
```

### Custom Threshold

```bash
# Set custom size threshold (25MB)
pframe run medium_data.parquet \
  --threshold 25 \
  --query "status == 'active'" \
  --head 100
```

## Advanced Use Cases

### Time Series Analysis

```bash
# Extract recent time series data
pframe run sensor_data.parquet \
  --query "timestamp >= '2024-09-01' and sensor_type == 'temperature'" \
  --columns "timestamp,sensor_id,value,location" \
  --output "recent_temperature.parquet"
```

### A/B Testing Analysis

```bash
# Compare test groups
pframe run experiment_data.parquet \
  --query "experiment_id == 'homepage_v2'" \
  --columns "user_id,variant,conversion,revenue" \
  --describe
```

### Log Analysis

```bash
# Analyze error logs
pframe run application_logs.parquet \
  --query "level == 'ERROR' and timestamp >= '2024-09-20'" \
  --columns "timestamp,message,module,user_id" \
  --head 50 \
  --output "recent_errors.parquet"
```

## Batch Processing Workflows

### Multi-step Processing

```bash
#!/bin/bash
# Daily data processing pipeline

echo "Step 1: Extract new data"
pframe run raw_data.parquet \
  --query "date == '$(date -d yesterday +%Y-%m-%d)'" \
  --output "yesterday_data.parquet"

echo "Step 2: Clean and validate"
pframe run yesterday_data.parquet \
  --query "user_id.notnull() and amount > 0" \
  --output "clean_yesterday.parquet"

echo "Step 3: Generate summary"
pframe run clean_yesterday.parquet \
  --describe \
  --save-script "daily_summary_$(date +%Y%m%d).py"

echo "Processing complete!"
```

### Data Migration

```bash
# Convert and filter data during migration
pframe run legacy_format.parquet \
  --query "migration_status.isnull()" \
  --columns "id,name,email,created_at,metadata" \
  --output "migrated_users.parquet" \
  --save-script "migration_script.py"
```

## Integration Examples

### Pre-ML Pipeline

```bash
# Prepare data for machine learning
pframe run raw_features.parquet \
  --query "label.notnull() and feature_quality > 0.8" \
  --columns "user_id,feature_1,feature_2,feature_3,label" \
  --output "ml_dataset.parquet"
```

### Reporting Pipeline

```bash
# Generate daily report data
pframe run transactions.parquet \
  --query "date >= '2024-09-01' and date <= '2024-09-30'" \
  --columns "date,category,amount,region" \
  --describe \
  --save-script "monthly_report_generation.py"
```

## Tips and Tricks

### Combining Multiple Operations

```bash
# Complex pipeline with multiple transformations
pframe run ecommerce_data.parquet \
  --query "order_status == 'completed' and total > 50" \
  --columns "customer_id,product_id,category,total,order_date" \
  --head 1000 \
  --output "completed_orders_sample.parquet" \
  --save-script "order_analysis.py"
```

### Using Environment Variables

```bash
# Dynamic date filtering using environment variables
export ANALYSIS_DATE="2024-09-24"
pframe run daily_data.parquet \
  --query "date == '$ANALYSIS_DATE'" \
  --output "analysis_$ANALYSIS_DATE.parquet"
```

### Debugging Queries

```bash
# Test query on small sample first
pframe run large_dataset.parquet \
  --sample 100 \
  --query "complex_condition_here"

# Then run on full dataset
pframe run large_dataset.parquet \
  --query "complex_condition_here" \
  --output "filtered_results.parquet"
```

These examples demonstrate the versatility and power of the ParquetFrame CLI for various data processing scenarios. The CLI excels at quick exploration, data filtering, pipeline automation, and interactive analysis tasks.
