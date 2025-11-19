# AWS S3 Integration

ParquetFrame provides convenient helpers for reading and writing Parquet files directly to/from AWS S3.

## Installation

To use S3 features, you need to install the optional dependencies:

```bash
pip install "parquetframe[s3]"
# OR directly
pip install s3fs boto3
```

## Configuration

ParquetFrame uses `s3fs` under the hood, which automatically picks up credentials from standard locations:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- `~/.aws/credentials` file
- IAM roles (if running on EC2/Lambda/EKS)

## Usage

### Reading from S3

```python
from parquetframe.cloud import read_parquet_s3

# Read directly from S3
df = read_parquet_s3("s3://my-bucket/data/file.parquet")

# With specific credentials (not recommended for production)
df = read_parquet_s3(
    "s3://my-bucket/data/file.parquet",
    storage_options={
        "key": "MY_KEY",
        "secret": "MY_SECRET"
    }
)
```

### Writing to S3

```python
from parquetframe.cloud import write_parquet_s3
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})

# Write to S3
write_parquet_s3(df, "s3://my-bucket/data/output.parquet")
```

## Performance Tips

- **Partitioning**: For large datasets, write partitioned datasets using `partition_cols`.
- **Compression**: Snappy is the default and recommended for S3.
- **Batching**: When writing many small files, consider combining them first to reduce S3 PUT requests.
