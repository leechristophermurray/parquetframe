"""
Core ParquetFrame implementation.

This module contains the main ParquetFrame class that wraps pandas and Dask
DataFrames for seamless operation.
"""

import os
from pathlib import Path
from typing import Any, Optional, Union

import dask.dataframe as dd
import pandas as pd


class ParquetFrame:
    """
    A wrapper for pandas and Dask DataFrames to simplify working with parquet files.

    The class automatically switches between pandas and Dask based on file size
    or a manual flag. It delegates all standard DataFrame methods to the active
    internal dataframe.

    Examples:
        >>> import parquetframe as pqf
        >>> # Read file with automatic backend selection
        >>> pf = pqf.pf.read("data.parquet")
        >>> # Manual backend control
        >>> pf = pqf.pf.read("data", islazy=True)  # Force Dask
        >>> # Standard DataFrame operations work transparently
        >>> result = pf.groupby("column").sum()
    """

    def __init__(
        self,
        df: Optional[Union[pd.DataFrame, dd.DataFrame]] = None,
        islazy: bool = False,
    ) -> None:
        """
        Initialize the ParquetFrame.

        Args:
            df: An initial dataframe (pandas or Dask).
            islazy: If True, forces a Dask DataFrame.
        """
        self._df = df
        self._islazy = islazy
        self.DEFAULT_THRESHOLD_MB = 10

    @property
    def islazy(self) -> bool:
        """Get the current backend type (True for Dask, False for pandas)."""
        return self._islazy

    @islazy.setter
    def islazy(self, value: bool) -> None:
        """Set the backend type and convert the dataframe if necessary."""
        if value != self._islazy:
            if value:
                self.to_dask()
            else:
                self.to_pandas()

    def __repr__(self) -> str:
        """String representation of the object."""
        df_type = "Dask" if self.islazy else "pandas"
        if self._df is None:
            return f"ParquetFrame(type={df_type}, df=None)"
        return f"ParquetFrame(type={df_type}, df={self._df.__repr__()})"

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to the underlying dataframe.

        This method is called for attributes not found in the ParquetFrame instance.
        It forwards the call to the internal dataframe (_df).
        """
        if self._df is not None:
            attr = getattr(self._df, name)
            if callable(attr):

                def wrapper(*args, **kwargs):
                    result = attr(*args, **kwargs)
                    # If the result is a dataframe, wrap it in a new ParquetFrame
                    if isinstance(result, (pd.DataFrame, dd.DataFrame)):
                        return ParquetFrame(result, isinstance(result, dd.DataFrame))
                    return result

                return wrapper
            return attr
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    @classmethod
    def read(
        cls,
        file: Union[str, Path],
        threshold_mb: Optional[float] = None,
        islazy: Optional[bool] = None,
        **kwargs,
    ) -> "ParquetFrame":
        """
        Read a parquet file into a ParquetFrame.

        Automatically selects pandas or Dask based on file size, unless overridden.
        Handles file extension detection automatically.

        Args:
            file: Path to the parquet file (extension optional).
            threshold_mb: Size threshold in MB for backend selection. Defaults to 10MB.
            islazy: Force backend selection (True=Dask, False=pandas, None=auto).
            **kwargs: Additional keyword arguments for read_parquet methods.

        Returns:
            ParquetFrame instance with loaded data.

        Raises:
            FileNotFoundError: If no parquet file is found.

        Examples:
            >>> pf = ParquetFrame.read("data")  # Auto-detects .parquet/.pqt
            >>> pf = ParquetFrame.read("data.parquet", threshold_mb=50)
            >>> pf = ParquetFrame.read("data", islazy=True)  # Force Dask
        """
        file_path = cls._resolve_file_path(file)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        # Determine backend
        if islazy is not None:
            use_dask = islazy
        else:
            threshold = threshold_mb if threshold_mb is not None else 10
            use_dask = file_size_mb >= threshold

        # Read the file
        if use_dask:
            df = dd.read_parquet(file_path, **kwargs)
            print(
                f"Reading '{file_path}' as Dask DataFrame (size: {file_size_mb:.2f} MB)"
            )
        else:
            df = pd.read_parquet(file_path, **kwargs)
            print(
                f"Reading '{file_path}' as pandas DataFrame (size: {file_size_mb:.2f} MB)"
            )

        return cls(df, use_dask)

    def save(self, file: Union[str, Path], **kwargs) -> "ParquetFrame":
        """
        Save the dataframe to a parquet file.

        Automatically adds .parquet extension if not present.
        Works with both pandas and Dask dataframes.

        Args:
            file: Base name for the output file.
            **kwargs: Additional keyword arguments for to_parquet methods.

        Returns:
            Self for method chaining.

        Raises:
            TypeError: If no dataframe is loaded.

        Examples:
            >>> pf.save("output")  # Saves as output.parquet
            >>> pf.save("data.parquet", compression='snappy')
        """
        if self._df is None:
            raise TypeError("No dataframe loaded to save.")

        file_path = self._ensure_parquet_extension(file)

        if isinstance(self._df, dd.DataFrame):
            self._df.to_parquet(file_path, **kwargs)
            print(f"Dask DataFrame saved to '{file_path}'.")
        elif isinstance(self._df, pd.DataFrame):
            self._df.to_parquet(file_path, **kwargs)
            print(f"pandas DataFrame saved to '{file_path}'.")

        return self

    def to_pandas(self) -> "ParquetFrame":
        """
        Convert the internal Dask dataframe to a pandas dataframe.

        Returns:
            Self for method chaining.
        """
        if self.islazy and isinstance(self._df, dd.DataFrame):
            self._df = self._df.compute()
            self._islazy = False
            print("Converted to pandas DataFrame.")
        else:
            print("Already a pandas DataFrame.")
        return self

    def to_dask(self, npartitions: Optional[int] = None) -> "ParquetFrame":
        """
        Convert the internal pandas dataframe to a Dask dataframe.

        Args:
            npartitions: Number of partitions for the Dask dataframe.
                       Defaults to the number of CPU cores.

        Returns:
            Self for method chaining.
        """
        if not self.islazy and isinstance(self._df, pd.DataFrame):
            npart = npartitions if npartitions is not None else os.cpu_count() or 1
            self._df = dd.from_pandas(self._df, npartitions=npart)
            self._islazy = True
            print("Converted to Dask DataFrame.")
        else:
            print("Already a Dask DataFrame.")
        return self

    @staticmethod
    def _resolve_file_path(file: Union[str, Path]) -> Path:
        """
        Resolve file path and handle extension detection.

        Args:
            file: Input file path.

        Returns:
            Resolved Path object.

        Raises:
            FileNotFoundError: If no parquet file variant is found.
        """
        file_path = Path(file)

        # If extension is already present, use as-is
        if file_path.suffix in (".parquet", ".pqt"):
            if file_path.exists():
                return file_path
            else:
                raise FileNotFoundError(f"File not found: {file_path}")

        # Try different extensions
        for ext in [".parquet", ".pqt"]:
            candidate = file_path.with_suffix(ext)
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            f"No parquet file found for '{file}' (tried .parquet, .pqt)"
        )

    @staticmethod
    def _ensure_parquet_extension(file: Union[str, Path]) -> Path:
        """
        Ensure the file path has a parquet extension.

        Args:
            file: Input file path.

        Returns:
            Path with appropriate parquet extension.
        """
        file_path = Path(file)
        if file_path.suffix not in (".parquet", ".pqt"):
            return file_path.with_suffix(".parquet")
        return file_path
