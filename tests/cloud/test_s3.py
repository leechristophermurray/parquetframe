"""
Unit tests for S3 integration.
"""

import os
from unittest.mock import MagicMock, patch

from parquetframe.cloud import S3Handler, read_parquet_s3, write_parquet_s3
from parquetframe.cloud.config import S3Config


class TestS3Config:
    """Test S3 configuration."""

    def test_from_env(self):
        """Test loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "AWS_ACCESS_KEY_ID": "test_key",
                "AWS_SECRET_ACCESS_KEY": "test_secret",
                "AWS_DEFAULT_REGION": "us-west-2",
            },
        ):
            config = S3Config.from_env()
            assert config.access_key_id == "test_key"
            assert config.secret_access_key == "test_secret"
            assert config.region == "us-west-2"

    def test_from_profile(self):
        """Test loading from AWS profile."""
        with patch("parquetframe.cloud.config.boto3") as mock_boto:
            mock_session = MagicMock()
            mock_creds = MagicMock()
            mock_creds.access_key = "profile_key"
            mock_creds.secret_key = "profile_secret"
            mock_creds.token = "profile_token"
            mock_session.get_credentials.return_value = mock_creds
            mock_session.region_name = "eu-central-1"
            mock_boto.Session.return_value = mock_session

            config = S3Config.from_profile("prod")

            assert config.access_key_id == "profile_key"
            assert config.profile_name == "prod"
            assert config.region == "eu-central-1"

    def test_to_storage_options(self):
        """Test conversion to storage options."""
        config = S3Config(
            access_key_id="key",
            secret_access_key="secret",
            session_token="token",
            endpoint_url="http://minio:9000",
        )

        options = config.to_storage_options()
        assert options["key"] == "key"
        assert options["secret"] == "secret"
        assert options["token"] == "token"
        assert options["client_kwargs"]["endpoint_url"] == "http://minio:9000"


class TestS3Handler:
    """Test S3 handler operations."""

    @patch("parquetframe.cloud.s3.S3Handler._check_rust_s3")
    def test_init_rust_check(self, mock_check):
        """Test Rust availability check."""
        mock_check.return_value = True
        handler = S3Handler()
        assert handler._rust_available is True

    @patch("parquetframe.cloud.s3.pd.read_parquet")
    def test_read_parquet_pandas_fallback(self, mock_read):
        """Test fallback to pandas read_parquet."""
        handler = S3Handler()
        handler._rust_available = False  # Force fallback

        handler.read_parquet("s3://bucket/file.parquet", backend="pandas")

        mock_read.assert_called_once()
        args, kwargs = mock_read.call_args
        assert args[0] == "s3://bucket/file.parquet"
        assert "storage_options" in kwargs

    @patch("parquetframe.cloud.s3.S3Handler._read_rust")
    def test_read_parquet_rust(self, mock_read_rust):
        """Test Rust read path."""
        handler = S3Handler()
        handler._rust_available = True

        handler.read_parquet("s3://bucket/file.parquet")
        mock_read_rust.assert_called_once()


class TestUserAPI:
    """Test user-facing API functions."""

    @patch("parquetframe.cloud.S3Handler")
    def test_read_parquet_s3(self, mock_handler_cls):
        """Test read_parquet_s3 function."""
        mock_handler = MagicMock()
        mock_handler_cls.return_value = mock_handler

        read_parquet_s3(
            "s3://bucket/data.parquet",
            aws_access_key_id="key",
            aws_secret_access_key="secret",
        )

        mock_handler_cls.assert_called_once()
        mock_handler.read_parquet.assert_called_once()

    @patch("parquetframe.cloud.S3Handler")
    def test_write_parquet_s3(self, mock_handler_cls):
        """Test write_parquet_s3 function."""
        mock_handler = MagicMock()
        mock_handler_cls.return_value = mock_handler
        df = MagicMock()

        write_parquet_s3(df, "s3://bucket/out.parquet", aws_profile="dev")

        mock_handler.write_parquet.assert_called_once_with(
            df, "s3://bucket/out.parquet"
        )
