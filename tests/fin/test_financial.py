"""
Unit tests for Financial Analytics module.
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest


class TestFinAccessor:
    """Test Financial Accessor."""

    @pytest.fixture
    def df(self):
        """Create sample DataFrame."""
        return pd.DataFrame(
            {"close": [10.0, 11.0, 12.0, 11.0, 13.0, 14.0, 15.0, 14.0, 13.0, 12.0]}
        )

    @patch("parquetframe.fin.fin_sma")
    def test_sma(self, mock_sma, df):
        """Test Simple Moving Average."""
        # Mock return value
        mock_sma.return_value = np.array([10.0] * 10)

        # Call method
        result = df.fin.sma("close", window=3)

        # Verify
        assert "close_sma_3" in result.columns
        mock_sma.assert_called_once()
        args, _ = mock_sma.call_args
        np.testing.assert_array_equal(args[0], df["close"].values)
        assert args[1] == 3

    @patch("parquetframe.fin.fin_ema")
    def test_ema(self, mock_ema, df):
        """Test Exponential Moving Average."""
        mock_ema.return_value = np.array([10.0] * 10)

        result = df.fin.ema("close", span=3)

        assert "close_ema_3" in result.columns
        mock_ema.assert_called_once()

    @patch("parquetframe.fin.fin_rsi")
    def test_rsi(self, mock_rsi, df):
        """Test Relative Strength Index."""
        mock_rsi.return_value = np.array([50.0] * 10)

        result = df.fin.rsi("close", window=14)

        assert "close_rsi_14" in result.columns
        mock_rsi.assert_called_once()

    @patch("parquetframe.fin.fin_bollinger_bands")
    def test_bollinger_bands(self, mock_bb, df):
        """Test Bollinger Bands."""
        # Mock returns tuple (upper, middle, lower)
        mock_bb.return_value = (
            np.array([12.0] * 10),
            np.array([10.0] * 10),
            np.array([8.0] * 10),
        )

        result = df.fin.bollinger_bands("close", window=20)

        assert "close_bb_upper" in result.columns
        assert "close_bb_middle" in result.columns
        assert "close_bb_lower" in result.columns
        mock_bb.assert_called_once()

    def test_custom_output_names(self, df):
        """Test custom output column names."""
        with patch("parquetframe.fin.fin_sma") as mock_sma:
            mock_sma.return_value = np.array([0.0] * 10)
            result = df.fin.sma("close", window=3, output_column="my_sma")
            assert "my_sma" in result.columns

        with patch("parquetframe.fin.fin_ema") as mock_ema:
            mock_ema.return_value = np.array([0.0] * 10)
            result = df.fin.ema("close", span=3, output_column="my_ema")
            assert "my_ema" in result.columns

        with patch("parquetframe.fin.fin_rsi") as mock_rsi:
            mock_rsi.return_value = np.array([0.0] * 10)
            result = df.fin.rsi("close", window=14, output_column="my_rsi")
            assert "my_rsi" in result.columns

        with patch("parquetframe.fin.fin_bollinger_bands") as mock_bb:
            mock_bb.return_value = (np.zeros(10), np.zeros(10), np.zeros(10))
            result = df.fin.bollinger_bands("close", prefix="my_bb")
            assert "my_bb_upper" in result.columns
