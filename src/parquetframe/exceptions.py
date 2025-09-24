"""
Custom exceptions for ParquetFrame.
"""


class ParquetFrameError(Exception):
    """Base exception class for ParquetFrame-related errors."""

    pass


class BackendError(ParquetFrameError):
    """Exception raised when backend operations fail."""

    pass


class FileNotFoundError(ParquetFrameError):
    """Exception raised when a parquet file is not found."""

    pass


class ValidationError(ParquetFrameError):
    """Exception raised when data validation fails."""

    pass
