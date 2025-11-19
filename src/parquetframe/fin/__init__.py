"""
Financial Analytics Module for ParquetFrame.

Provides technical indicators and financial calculations
built on Rust-accelerated time-series operations.
"""

import pandas as pd

from parquetframe._rustic import (
    fin_bollinger_bands,
    fin_ema,
    fin_rsi,
    fin_sma,
)


class FinAccessor:
    """Accessor for financial analytics operations."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def sma(
        self, column: str, window: int, output_column: str | None = None
    ) -> pd.DataFrame:
        """
        Calculate Simple Moving Average.

        Args:
            column: Column name to calculate SMA on
            window: Window size for averaging
            output_column: Name for output column (default: {column}_sma_{window})

        Returns:
            DataFrame with SMA column added
        """
        if output_column is None:
            output_column = f"{column}_sma_{window}"

        result_array = fin_sma(self._df[column].values, window)
        df_copy = self._df.copy()
        df_copy[output_column] = result_array
        return df_copy

    def ema(
        self, column: str, span: int, output_column: str | None = None
    ) -> pd.DataFrame:
        """
        Calculate Exponential Moving Average.

        Args:
            column: Column name to calculate EMA on
            span: Span (number of periods) for EMA
            output_column: Name for output column (default: {column}_ema_{span})

        Returns:
            DataFrame with EMA column added
        """
        if output_column is None:
            output_column = f"{column}_ema_{span}"

        result_array = fin_ema(self._df[column].values, span)
        df_copy = self._df.copy()
        df_copy[output_column] = result_array
        return df_copy

    def rsi(
        self, column: str, window: int = 14, output_column: str | None = None
    ) -> pd.DataFrame:
        """
        Calculate Relative Strength Index.

        Args:
            column: Column name to calculate RSI on
            window: Window size for RSI (default: 14)
            output_column: Name for output column (default: {column}_rsi_{window})

        Returns:
            DataFrame with RSI column added (values 0-100)
        """
        if output_column is None:
            output_column = f"{column}_rsi_{window}"

        result_array = fin_rsi(self._df[column].values, window)
        df_copy = self._df.copy()
        df_copy[output_column] = result_array
        return df_copy

    def bollinger_bands(
        self,
        column: str,
        window: int = 20,
        num_std: float = 2.0,
        prefix: str | None = None,
    ) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.

        Args:
            column: Column name to calculate bands on
            window: Window size for calculation (default: 20)
            num_std: Number of standard deviations (default: 2.0)
            prefix: Prefix for output columns (default: {column}_bb)

        Returns:
            DataFrame with upper, middle, and lower band columns added
        """
        if prefix is None:
            prefix = f"{column}_bb"

        upper, middle, lower = fin_bollinger_bands(
            self._df[column].values, window, num_std
        )

        df_copy = self._df.copy()
        df_copy[f"{prefix}_upper"] = upper
        df_copy[f"{prefix}_middle"] = middle
        df_copy[f"{prefix}_lower"] = lower
        return df_copy


# Register accessor
@pd.api.extensions.register_dataframe_accessor("fin")
class FinDataFrameAccessor(FinAccessor):
    """Financial accessor for pandas DataFrame."""

    pass
