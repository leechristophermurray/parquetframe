"""
Unit tests for cloud connectors.
"""

from unittest.mock import MagicMock, patch

import pytest

from parquetframe.cloud import (
    AzureConfig,
    CloudFactory,
    GCSConfig,
    read_parquet_cloud,
)
from parquetframe.cloud.handlers.azure import AzureHandler
from parquetframe.cloud.handlers.gcp import GCSHandler
from parquetframe.cloud.handlers.s3 import S3Handler


class TestCloudFactory:
    """Test cloud handler factory."""

    def test_get_handler_s3(self):
        handler = CloudFactory.get_handler("s3://bucket/file.parquet")
        assert isinstance(handler, S3Handler)

    def test_get_handler_gcs(self):
        handler = CloudFactory.get_handler("gs://bucket/file.parquet")
        assert isinstance(handler, GCSHandler)

    def test_get_handler_azure(self):
        handler = CloudFactory.get_handler("az://container/file.parquet")
        assert isinstance(handler, AzureHandler)

        handler = CloudFactory.get_handler("abfs://container/file.parquet")
        assert isinstance(handler, AzureHandler)

    def test_unsupported_scheme(self):
        with pytest.raises(ValueError):
            CloudFactory.get_handler("ftp://server/file.parquet")


class TestCloudHandlers:
    """Test cloud handlers (mocked)."""

    @patch("parquetframe.cloud.handlers.gcp.pd.read_parquet")
    def test_gcs_read(self, mock_read):
        handler = GCSHandler()
        handler.read_parquet("gs://bucket/data.parquet")
        mock_read.assert_called_once()

    @patch("parquetframe.cloud.handlers.azure.pd.read_parquet")
    def test_azure_read(self, mock_read):
        handler = AzureHandler()
        handler.read_parquet("az://container/data.parquet")
        mock_read.assert_called_once()

    @patch("parquetframe.cloud.factory.CloudFactory.get_handler")
    def test_unified_api(self, mock_get_handler):
        mock_handler = MagicMock()
        mock_get_handler.return_value = mock_handler

        read_parquet_cloud("s3://bucket/data.parquet")
        mock_get_handler.assert_called_with("s3://bucket/data.parquet")
        mock_handler.read_parquet.assert_called_once()


class TestCloudConfig:
    """Test cloud configuration."""

    def test_gcs_config(self):
        config = GCSConfig(project="test-proj", token="key.json")
        opts = config.to_storage_options()
        assert opts["project"] == "test-proj"
        assert opts["token"] == "key.json"

    def test_azure_config(self):
        config = AzureConfig(account_name="acc", account_key="key")
        opts = config.to_storage_options()
        assert opts["account_name"] == "acc"
        assert opts["account_key"] == "key"
