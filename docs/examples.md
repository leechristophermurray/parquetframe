# Examples

Real-world examples showing how to use ParquetFrame in common scenarios.

## Data Processing Pipeline

```python
import parquetframe as pqf
from pathlib import Path

def process_sales_data():
    """Complete sales data processing pipeline."""

    # Read raw sales data (auto-selects backend)
    sales = pqf.read("raw_sales_data.parquet")
    print(f"Loaded {len(sales)} sales records using {('Dask' if sales.islazy else 'pandas')}")

    # Clean and process data
    cleaned_sales = (sales
        .dropna(subset=['customer_id', 'amount'])
        .query("amount > 0")
        .query("date >= '2023-01-01'"))

    # Generate summary statistics
    summary = (cleaned_sales
        .groupby(['region', 'product_category'])
        .agg({
            'amount': ['sum', 'mean', 'count'],
            'customer_id': 'nunique'
        })
        .round(2))

    # Save results
    summary.save("sales_summary_by_region")

    return summary

# Run the pipeline
result = process_sales_data()
print("✅ Sales processing completed!")
```

## Batch File Processing

```python
import parquetframe as pqf
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_process_directory(input_dir: str, output_dir: str, pattern: str = "*.parquet"):
    """Process all parquet files in a directory."""

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    files_processed = 0
    total_rows = 0

    for file_path in input_path.glob(pattern):
        logger.info(f"Processing {file_path.name}")

        try:
            # Read with automatic backend selection
            df = pqf.read(file_path)

            # Apply transformations
            processed = (df
                .dropna()
                .query("status == 'active'")
                .groupby('category')
                .sum()
                .reset_index())

            # Save processed data
            output_file = output_path / f"processed_{file_path.stem}"
            processed.save(output_file)

            files_processed += 1
            total_rows += len(processed)

            logger.info(f"✅ Processed {file_path.name}: {len(processed)} rows")

        except Exception as e:
            logger.error(f"❌ Failed to process {file_path.name}: {e}")

    logger.info(f"🎉 Batch processing complete: {files_processed} files, {total_rows} total rows")

# Usage
batch_process_directory("raw_data", "processed_data")
```

## Memory-Efficient Large File Processing

```python
import parquetframe as pqf
from dask.diagnostics import ProgressBar

def process_large_dataset(file_path: str, sample_size: float = 0.1):
    """Process large datasets efficiently using Dask."""

    # Force Dask for large file processing
    df = pqf.read(file_path, islazy=True)
    print(f"Loaded large dataset with {df.npartitions} partitions")

    # Work with sample for exploration
    print("Creating sample for analysis...")
    sample = df.sample(frac=sample_size)
    sample_pandas = sample.to_pandas()

    # Analyze sample
    print("Sample analysis:")
    print(f"- Shape: {sample_pandas.shape}")
    print(f"- Memory usage: {sample_pandas.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print(f"- Data types: {sample_pandas.dtypes.value_counts().to_dict()}")

    # Process full dataset with progress bar
    print("Processing full dataset...")
    with ProgressBar():
        # Compute aggregations on full dataset
        summary = (df
            .groupby(['region', 'product'])
            .agg({'sales': 'sum', 'quantity': 'sum'})
            .compute())

    # Save results
    summary_pf = pqf.ParquetFrame(summary)
    summary_pf.save("large_dataset_summary")

    return summary

# Process a large file
summary = process_large_dataset("huge_sales_data.parquet", sample_size=0.05)
```

## Time Series Analysis

```python
import parquetframe as pqf
import pandas as pd

def analyze_time_series(data_path: str):
    """Analyze time series data with automatic backend selection."""

    # Read time series data
    df = pqf.read(data_path)

    # Ensure datetime column is properly typed
    if df.islazy:
        # For Dask, convert timestamp
        df._df['timestamp'] = dd.to_datetime(df._df['timestamp'])
    else:
        # For pandas, convert timestamp
        df._df['timestamp'] = pd.to_datetime(df._df['timestamp'])

    # Daily aggregations
    daily_metrics = (df
        .groupby(df._df.timestamp.dt.date)
        .agg({
            'value': ['mean', 'sum', 'std'],
            'count': 'sum'
        }))

    # Monthly trends
    monthly_trends = (df
        .groupby(df._df.timestamp.dt.to_period('M'))
        .agg({
            'value': ['mean', 'sum'],
            'count': 'sum'
        }))

    # Handle Dask computation if needed
    if df.islazy:
        daily_metrics = daily_metrics.compute()
        monthly_trends = monthly_trends.compute()

    # Save results
    pqf.ParquetFrame(daily_metrics).save("daily_metrics")
    pqf.ParquetFrame(monthly_trends).save("monthly_trends")

    return daily_metrics, monthly_trends

# Analyze time series
daily, monthly = analyze_time_series("sensor_data.parquet")
```

## Machine Learning Workflow

```python
import parquetframe as pqf
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import pandas as pd

def ml_pipeline(data_path: str):
    """Complete ML pipeline with ParquetFrame."""

    # Load data with automatic backend selection
    df = pqf.read(data_path)
    print(f"Loaded data using {'Dask' if df.islazy else 'pandas'} backend")

    # For large datasets, take a sample
    if df.islazy and len(df) > 100000:
        print("Large dataset detected, sampling 50% for ML training")
        df = df.sample(frac=0.5)

    # Convert to pandas for sklearn compatibility
    if df.islazy:
        df.to_pandas()

    # Feature engineering
    features = (df
        .dropna()
        .assign(
            # Create new features
            value_per_unit=lambda x: x['total_value'] / x['quantity'],
            is_weekend=lambda x: pd.to_datetime(x['date']).dt.weekday >= 5
        ))

    # Prepare features and target
    feature_cols = ['value_per_unit', 'quantity', 'is_weekend', 'region_encoded']
    X = features[feature_cols]._df
    y = features['target']._df

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    print("Training model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    print("Model Performance:")
    print(classification_report(y_test, y_pred))

    # Save feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    pqf.ParquetFrame(feature_importance).save("feature_importance")

    return model, feature_importance

# Run ML pipeline
model, importance = ml_pipeline("ml_training_data.parquet")
```

## ETL Pipeline with Error Handling

```python
import parquetframe as pqf
from pathlib import Path
import logging
from typing import List, Dict

def robust_etl_pipeline(
    input_files: List[str],
    output_dir: str,
    transformations: Dict[str, callable]
):
    """Robust ETL pipeline with comprehensive error handling."""

    logger = logging.getLogger(__name__)
    results = []
    errors = []

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for file_path in input_files:
        try:
            logger.info(f"Processing {file_path}")

            # Read data with automatic backend selection
            df = pqf.read(file_path)
            original_count = len(df)

            # Apply transformations
            for transform_name, transform_func in transformations.items():
                logger.debug(f"Applying {transform_name}")
                df = transform_func(df)

            # Validate results
            if len(df) == 0:
                logger.warning(f"No data remaining after transformations for {file_path}")
                continue

            # Save processed data
            output_file = output_path / f"processed_{Path(file_path).stem}"
            df.save(output_file)

            # Track results
            result = {
                'file': file_path,
                'original_rows': original_count,
                'processed_rows': len(df),
                'backend': 'Dask' if df.islazy else 'pandas',
                'status': 'success'
            }
            results.append(result)
            logger.info(f"✅ Successfully processed {file_path}")

        except FileNotFoundError as e:
            error = {'file': file_path, 'error': f"File not found: {e}", 'type': 'FileError'}
            errors.append(error)
            logger.error(f"❌ File not found: {file_path}")

        except Exception as e:
            error = {'file': file_path, 'error': str(e), 'type': type(e).__name__}
            errors.append(error)
            logger.error(f"❌ Error processing {file_path}: {e}")

    # Save processing report
    import pandas as pd
    if results:
        results_df = pqf.ParquetFrame(pd.DataFrame(results))
        results_df.save(output_path / "processing_report")

    if errors:
        errors_df = pqf.ParquetFrame(pd.DataFrame(errors))
        errors_df.save(output_path / "processing_errors")

    logger.info(f"ETL Pipeline completed: {len(results)} success, {len(errors)} errors")
    return results, errors

# Define transformations
transformations = {
    'clean_nulls': lambda df: df.dropna(),
    'filter_positive': lambda df: df.query("amount > 0"),
    'add_derived_fields': lambda df: df.assign(
        amount_category=lambda x: pd.cut(x.amount, bins=[0, 100, 500, float('inf')],
                                        labels=['low', 'medium', 'high'])
    )
}

# Run ETL pipeline
input_files = ["file1.parquet", "file2.parquet", "file3.parquet"]
results, errors = robust_etl_pipeline(input_files, "etl_output", transformations)
```

## Performance Comparison

```python
import parquetframe as pqf
import time
import pandas as pd

def performance_comparison(file_path: str):
    """Compare performance between pandas and Dask backends."""

    print(f"Performance comparison for: {file_path}")
    print("=" * 50)

    # Test pandas backend
    start_time = time.time()
    df_pandas = pqf.read(file_path, islazy=False)
    load_time_pandas = time.time() - start_time

    start_time = time.time()
    result_pandas = df_pandas.groupby('category').sum()
    process_time_pandas = time.time() - start_time

    # Test Dask backend
    start_time = time.time()
    df_dask = pqf.read(file_path, islazy=True)
    load_time_dask = time.time() - start_time

    start_time = time.time()
    result_dask = df_dask.groupby('category').sum()
    if df_dask.islazy:
        result_dask = result_dask.compute()
    process_time_dask = time.time() - start_time

    # Report results
    print(f"File size: {os.path.getsize(file_path) / (1024**2):.1f} MB")
    print(f"Rows: {len(df_pandas):,}")
    print(f"Columns: {len(df_pandas.columns)}")
    print()
    print("Performance Results:")
    print(f"Pandas - Load: {load_time_pandas:.2f}s, Process: {process_time_pandas:.2f}s")
    print(f"Dask   - Load: {load_time_dask:.2f}s, Process: {process_time_dask:.2f}s")

    # Memory usage comparison
    if hasattr(df_pandas._df, 'memory_usage'):
        pandas_memory = df_pandas._df.memory_usage(deep=True).sum() / (1024**2)
        print(f"Pandas memory usage: {pandas_memory:.1f} MB")

# Run performance comparison
performance_comparison("benchmark_data.parquet")
```

These examples demonstrate ParquetFrame's versatility in handling various data processing scenarios while automatically optimizing for performance and memory usage.
