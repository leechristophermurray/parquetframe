import sys
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

# Mock s3fs if not present
sys.modules["s3fs"] = MagicMock()

from parquetframe.cloud import read_parquet_s3, write_parquet_s3  # noqa: E402


class TestCloudS3(unittest.TestCase):
    @patch("pandas.read_parquet")
    def test_read_parquet_s3(self, mock_read):
        mock_read.return_value = pd.DataFrame({"a": [1]})

        df = read_parquet_s3("s3://bucket/file.parquet")

        mock_read.assert_called_once()
        args, kwargs = mock_read.call_args
        self.assertEqual(args[0], "s3://bucket/file.parquet")
        self.assertIsInstance(df, pd.DataFrame)

    @patch("pandas.DataFrame.to_parquet")
    def test_write_parquet_s3(self, mock_write):
        df = pd.DataFrame({"a": [1]})
        write_parquet_s3(df, "s3://bucket/file.parquet")

        mock_write.assert_called_once()
        args, kwargs = mock_write.call_args
        self.assertEqual(args[0], "s3://bucket/file.parquet")


if __name__ == "__main__":
    unittest.main()
