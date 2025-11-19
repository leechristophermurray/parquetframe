from typing import Any

import pandas as pd

try:
    import s3fs
except ImportError:
    s3fs = None

try:
    import boto3
except ImportError:
    boto3 = None


def _check_s3fs():
    if s3fs is None:
        raise ImportError(
            "s3fs is required for S3 operations. Install it with `pip install s3fs` or `pip install parquetframe[s3]`."
        )


def read_parquet_s3(
    path: str, storage_options: dict[str, Any] | None = None, **kwargs
) -> pd.DataFrame:
    """
    Read a Parquet file from S3.

    Args:
        path: S3 path (e.g., s3://bucket/file.parquet)
        storage_options: Options for s3fs (e.g., {'key': '...', 'secret': '...'})
        **kwargs: Additional arguments passed to pandas.read_parquet

    Returns:
        pd.DataFrame
    """
    _check_s3fs()
    return pd.read_parquet(path, storage_options=storage_options, **kwargs)


def write_parquet_s3(
    df: pd.DataFrame, path: str, storage_options: dict[str, Any] | None = None, **kwargs
) -> None:
    """
    Write a DataFrame to a Parquet file on S3.

    Args:
        df: DataFrame to write
        path: S3 path (e.g., s3://bucket/file.parquet)
        storage_options: Options for s3fs
        **kwargs: Additional arguments passed to pandas.to_parquet
    """
    _check_s3fs()
    df.to_parquet(path, storage_options=storage_options, **kwargs)
