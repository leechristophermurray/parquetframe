# ParquetFrame

This is the context for a universal wrapper for working with dataframes in python. `parquetframe` wraps pandas and dask in a variable called parquet frame (`pf`), allowing switching from one to the other through inference (based on an optional threshold set during read which defaults to 10MB) or manually switching a flag `pf.islazy`. Also, `pf.read(<file>)` will read a parquet without the need for stating the extension (checks for `.pqt` and `.parquet`). `pf.save(<file>)` will save the dataframe to parquet, while still allowing all the `to_parquet()` options/arguments as it's just a front for simplifying using parquetframe without the need for stating the extension (saves as `<file>.parquet` by default unless stated otherwise). parquetframe should still allow for dask and pandas operations as it's just a convenient dataframe handler.This library should be able to be used as a library in code, or in a terminal if installed with a `[cli]` option. so parquets could be queried and even transformed (have dask or pandas operations done) and saved to a new file- all in the terminal as if in a notebook. this cli feature would be implemented using the click python package.

To wrap pandas and Dask in a variable called parquet_frame (pf), you can create a custom class that manages an internal dataframe instance, either pandas or Dask. This class can use Python's special methods, like `__getattribute__` and `__getattr__`, to delegate calls to the underlying dataframe object.

The class will handle:

- Initialization: Storing the underlying dataframe and a flag to track whether it's a "lazy" Dask frame.

- Context Management: Providing read() and save() methods that handle file extensions and manage the dataframe type (Dask vs. pandas) based on file size or the islazy flag.

- Attribute Delegation: Automatically forwarding all other attribute and method calls to the correct internal dataframe.

## Implementation code

The following code provides a complete implementation of the ParquetFrame class (pf).

```python
import pandas as pd
import dask.dataframe as dd
import os

class ParquetFrame:
    """
    A wrapper for pandas and Dask DataFrames to simplify working with parquet files.
    
    The class automatically switches between pandas and Dask based on file size
    or a manual flag. It delegates all standard DataFrame methods to the active
    internal dataframe.
    """
    
    def __init__(self, df=None, is_lazy=False):
        """
        Initializes the ParquetFrame.

        Args:
            df (pd.DataFrame or dd.DataFrame, optional): An initial dataframe.
            is_lazy (bool): If True, forces a Dask DataFrame.
        """
        self._df = df
        self.is_lazy = is_lazy
        self.DEFAULT_THRESHOLD_MB = 10
    
    def __repr__(self):
        """String representation of the object."""
        df_type = 'Dask' if self.is_lazy else 'pandas'
        if self._df is None:
            return f"ParquetFrame(type={df_type}, df=None)"
        return f"ParquetFrame(type={df_type}, df={self._df.__repr__()})"

    def __getattribute__(self, name):
        """
        Overrides attribute access to delegate to the underlying dataframe.
        
        This method is called for all attribute lookups. It handles method
        delegation while avoiding infinite recursion.
        """
        # Exclude internal properties to prevent infinite recursion
        if name in ['_df', 'is_lazy', 'DEFAULT_THRESHOLD_MB']:
            return object.__getattribute__(self, name)
        
        # Delegate to internal dataframe if it exists
        if self._df is not None:
            attr = getattr(self._df, name, None)
            if attr:
                if callable(attr):
                    def wrapper(*args, **kwargs):
                        # Dask requires a .compute() call to get results
                        result = attr(*args, **kwargs)
                        if self.is_lazy and isinstance(result, (dd.DataFrame, dd.Series)):
                            return result
                        return result
                    return wrapper
                return attr

        # Fallback to default behavior if attribute not found
        return object.__getattribute__(self, name)

    def read(self, file, lazy_threshold_mb=None, **kwargs):
        """
        Reads a parquet file into the ParquetFrame.

        Reads as a pandas DataFrame if the file size is below the threshold,
        or as a Dask DataFrame otherwise. The threshold can be set manually.

        Args:
            file (str): The path to the parquet file ('.pqt' or '.parquet').
            lazy_threshold_mb (int, optional): Size threshold in MB. 
                Defaults to 10MB.
            **kwargs: Additional keyword arguments for `pd.read_parquet`
                or `dd.read_parquet`.
        """
        file_path = str(file)
        
        # Add extension if not present
        if not file_path.endswith(('.parquet', '.pqt')):
            if os.path.exists(f"{file_path}.parquet"):
                file_path += ".parquet"
            elif os.path.exists(f"{file_path}.pqt"):
                file_path += ".pqt"
            else:
                raise FileNotFoundError(f"No parquet file found for '{file_path}'")

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        threshold = lazy_threshold_mb if lazy_threshold_mb is not None else self.DEFAULT_THRESHOLD_MB

        if file_size_mb >= threshold:
            self._df = dd.read_parquet(file_path, **kwargs)
            self.is_lazy = True
            print(f"Reading '{file_path}' as Dask DataFrame (file size: {file_size_mb:.2f} MB)")
        else:
            self._df = pd.read_parquet(file_path, **kwargs)
            self.is_lazy = False
            print(f"Reading '{file_path}' as pandas DataFrame (file size: {file_size_mb:.2f} MB)")
        
        return self

    def save(self, file, **kwargs):
        """
        Saves the dataframe to a parquet file.

        The file extension is automatically added if not present. The method
        works for both pandas and Dask dataframes, with Dask performing
        computations before saving.

        Args:
            file (str): The base name for the output file.
            **kwargs: Additional keyword arguments for `to_parquet()`.
        """
        file_path = str(file)
        if not file_path.endswith(('.parquet', '.pqt')):
            file_path += ".parquet"

        if isinstance(self._df, dd.DataFrame):
            self._df.to_parquet(file_path, **kwargs)
            print(f"Dask DataFrame saved to '{file_path}'.")
        elif isinstance(self._df, pd.DataFrame):
            self._df.to_parquet(file_path, **kwargs)
            print(f"pandas DataFrame saved to '{file_path}'.")
        else:
            raise TypeError("No dataframe loaded to save.")

    def to_pandas(self):
        """
        Converts the internal Dask dataframe to a pandas dataframe.
        """
        if self.is_lazy:
            self._df = self._df.compute()
            self.is_lazy = False
            print("Converted to pandas DataFrame.")
        else:
            print("Already a pandas DataFrame.")
        return self

    def to_dask(self):
        """
        Converts the internal pandas dataframe to a Dask dataframe.
        """
        if not self.is_lazy and isinstance(self._df, pd.DataFrame):
            self._df = dd.from_pandas(self._df, npartitions=os.cpu_count())
            self.is_lazy = True
            print("Converted to Dask DataFrame.")
        else:
            print("Already a Dask DataFrame.")
        return self
```

Usage example
Here is how you would use the ParquetFrame class.
Setup

```python
# Create a small and large dummy parquet file for testing
small_df = pd.DataFrame({'a': range(100)})
small_df.to_parquet('small_file.parquet')

large_df = pd.DataFrame({'a': range(10_000_000)})
large_df.to_parquet('large_file.parquet')
```

Automatic inference

```python
# Read a small file (auto-detects pandas)
pf = ParquetFrame().read('small_file')
print(pf)
print(type(pf._df))

# Read a large file (auto-detects Dask)
pf = ParquetFrame().read('large_file')
print(pf)
print(type(pf._df))
```

Manual switching

```python
# Manually set to lazy (Dask)
pf = ParquetFrame().read('small_file').to_dask()
print(pf.is_lazy)

# Manually switch back to pandas (computes the result)
pf.to_pandas()
print(pf.is_lazy)

# Dask operations are lazy
pf = ParquetFrame().read('large_file')
lazy_result = pf.a.sum() # Does not compute yet
print(f"Lazy result object: {lazy_result}")
print(f"Computed result: {lazy_result.compute()}")

# Standard pandas operations work as expected
pf = ParquetFrame().read('small_file')
result = pf.a.sum()
print(f"Pandas result: {result}")
```

Saving files

```python
# Save from pandas (after reading a small file)
pf = ParquetFrame().read('small_file')
pf.save('output_small') # saves as output_small.parquet

# Save from Dask (after reading a large file)
pf = ParquetFrame().read('large_file')
pf.save('output_large') # saves as output_large.parquet
```

This implementation gives you the requested parquet_frame (pf) object, which handles dataframe type inference, file extension management, and delegation of all standard dataframe operations.

## Additional Context for Specific Features

### CLI

This library should be able to be used as a library in code, or in a terminal if installed with a `[cli]` option. so parquets could be queried and even transformed (have dask or pandas operations done) and saved to a new file- all in the terminal as if in a notebook. This cli feature would be implemented using the click python package. The cli mode should also be able to run interactively, with a cli interface which will display results like a notebook

### CLI - SAVE

In cli mode, there's an additional flag when saving which not only saves the parquet, but also saves the instructions of the session  as a python file which imports parquetframe. This should help with portability of work.

## Notes

- When developing this library/package, use git best practices (for branching, merges, etc), and conventional commits.
- Ensure we have test coverage at 95% or highter.
- LICENSE to use is an MIT liense.
- we shall publish to PyPi. and esnure we have a ci/cd pipline which does so
- We'll use uv for packaging and publishing (on github and pypi)
- Use tox to help with testing (across multiple python versions, distributions, etc).
- tox should also be used in the CI/CD pipeline
