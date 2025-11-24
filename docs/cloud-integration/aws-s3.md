# Cloud S3 Integration

ParquetFrame provides seamless integration with AWS S3 and S3-compatible object stores (like MinIO).

## Features

- **Multiple Authentication Patterns**: IAM roles, environment variables, AWS profiles, and explicit credentials.
- **Backend Agnostic**: Works with pandas, Polars, and Dask backends.
- **High Performance**: Uses Rust-accelerated I/O when available (via `object_store`).
- **Automatic Fallback**: Gracefully falls back to `fsspec`/`s3fs` if Rust extensions are missing.

## Quick Start

```python
import parquetframe as pf

# Read from S3 (uses default AWS credentials)
df = pf.read_parquet_s3("s3://my-bucket/data.parquet")

# Write to S3
pf.write_parquet_s3(df, "s3://my-bucket/output.parquet")
```

## Authentication

### 1. IAM Roles (Recommended for AWS)

If running on EC2, ECS, or Lambda, use the attached IAM role. No configuration needed.

```python
df = pf.read_parquet_s3("s3://bucket/data.parquet")
```

### 2. Environment Variables

Set standard AWS environment variables:

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=wJal...
export AWS_DEFAULT_REGION=us-east-1
```

Then use the API normally:

```python
df = pf.read_parquet_s3("s3://bucket/data.parquet")
```

### 3. AWS Profiles

Use a named profile from `~/.aws/credentials`:

```python
df = pf.read_parquet_s3(
    "s3://bucket/data.parquet",
    aws_profile="production"
)
```

### 4. Explicit Credentials

Pass credentials directly (not recommended for production):

```python
df = pf.read_parquet_s3(
    "s3://bucket/data.parquet",
    aws_access_key_id="AKIA...",
    aws_secret_access_key="wJal...",
    region="us-west-2"
)
```

## Backend Selection

You can specify the backend engine (pandas, Polars, Dask) explicitly or let ParquetFrame choose automatically.

```python
# Force Polars backend
df = pf.read_parquet_s3(
    "s3://bucket/large-data.parquet",
    backend="polars"
)

# Force Dask for distributed processing
df = pf.read_parquet_s3(
    "s3://bucket/huge-data.parquet",
    backend="dask"
)
```

## S3-Compatible Stores (MinIO)

To use MinIO or other S3-compatible stores, set the `AWS_ENDPOINT_URL` environment variable or use `S3Config` directly.

```python
from parquetframe.cloud import S3Config, S3Handler

config = S3Config(
    access_key_id="minioadmin",
    secret_access_key="minioadmin",
    endpoint_url="http://localhost:9000"
)

handler = S3Handler(config)
df = handler.read_parquet("s3://my-bucket/data.parquet")
```
