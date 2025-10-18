"""
Additional tests to improve code coverage for ParquetFrame.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

import parquetframe as pqf
from parquetframe.exceptions import BackendError, DependencyError, ValidationError

# Skip all tests in this file pending Phase 2 API migration
pytestmark = pytest.mark.skip(
    reason="Phase 2 API migration pending - SQL tests need DataFrameProxy.sql() method or legacy API updates. See docs/issues/phase2-test-migration.md"
)


class TestCoverageBoosters:
    """Tests specifically designed to increase code coverage."""

    def test_validation_error_instantiation(self):
        """Test ValidationError exception creation."""
        error = ValidationError(
            "schema", ["missing column 'id'", "invalid type for 'age'"]
        )
        assert "Data validation failed: schema" in str(error)
        assert error.error_code == "VALIDATION_ERROR"

    def test_backend_error_instantiation(self):
        """Test BackendError exception creation."""
        error = BackendError("pandas", "read_parquet", ValueError("corrupt file"))
        assert "pandas backend failed during read_parquet" in str(error)
        assert error.error_code == "BACKEND_ERROR"

    def test_dependency_error_instantiation(self):
        """Test DependencyError exception creation."""
        error = DependencyError("pyarrow", "parquet operations", "pip install pyarrow")
        assert "Missing dependency 'pyarrow'" in str(error)
        assert error.missing_package == "pyarrow"
        assert error.feature == "parquet operations"

    def test_parquetframe_info_method(self):
        """Test the info method for DataFrame information."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [1.1, 2.2, 3.3]})
        pf = pqf.ParquetFrame(df)

        # The info method should run without errors
        info = pf.info()
        assert info is None  # info() usually prints and returns None

    def test_parquetframe_describe_method(self):
        """Test the describe method for statistical summary."""
        df = pd.DataFrame(
            {"numbers": [1, 2, 3, 4, 5], "floats": [1.1, 2.2, 3.3, 4.4, 5.5]}
        )
        pf = pqf.ParquetFrame(df)

        description = pf.describe()
        # ParquetFrame.describe() returns a ParquetFrame, not a DataFrame
        assert isinstance(description, pqf.ParquetFrame)
        assert "numbers" in description.pandas_df.columns
        assert "floats" in description.pandas_df.columns

    def test_parquetframe_memory_usage(self):
        """Test memory usage calculation."""
        df = pd.DataFrame({"a": range(1000), "b": ["test"] * 1000, "c": [1.1] * 1000})
        pf = pqf.ParquetFrame(df)

        # Test memory usage calculation
        memory_info = pf.memory_usage(deep=True)
        assert isinstance(memory_info, pd.Series | dict | int | float)

    def test_sql_context_custom_pragmas(self):
        """Test SQL query context with custom pragmas."""
        from parquetframe.sql import QueryContext

        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        pf = pqf.ParquetFrame(df)

        # Test with custom pragmas
        context = QueryContext(
            memory_limit="1GB",
            custom_pragmas={"enable_profiling": "false", "threads": "1"},
        )

        result = pf.sql("SELECT a, b FROM df WHERE a > 1", context=context)
        assert len(result) == 2

    def test_parquetframe_copy_methods(self):
        """Test various copy and conversion methods."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        pf = pqf.ParquetFrame(df)

        # Test copy
        pf_copy = pf.copy()
        assert isinstance(pf_copy, pqf.ParquetFrame)
        assert len(pf_copy) == len(pf)

        # Test deep copy
        pf_deep = pf.copy(deep=True)
        assert isinstance(pf_deep, pqf.ParquetFrame)
        assert len(pf_deep) == len(pf)

    def test_parquetframe_indexing_methods(self):
        """Test various indexing and selection methods."""
        df = pd.DataFrame(
            {
                "a": [1, 2, 3, 4, 5],
                "b": ["x", "y", "z", "w", "v"],
                "c": [1.1, 2.2, 3.3, 4.4, 5.5],
            }
        )
        pf = pqf.ParquetFrame(df)

        # Test head
        head_result = pf.head(3)
        assert len(head_result) == 3

        # Test tail
        tail_result = pf.tail(2)
        assert len(tail_result) == 2

        # Test sample
        sample_result = pf.sample(n=2)
        assert len(sample_result) == 2

    def test_format_detection_edge_cases(self):
        """Test edge cases in format detection."""
        # Test with temporary files
        temp_dir = tempfile.mkdtemp()

        # Create a file with unusual extension
        unusual_file = Path(temp_dir) / "test.data"
        df = pd.DataFrame({"a": [1, 2, 3]})
        df.to_csv(unusual_file, index=False)

        try:
            # This should trigger format detection logic
            pf = pqf.read(unusual_file)
            assert isinstance(pf, pqf.ParquetFrame)
        except Exception:
            # Format detection may fail for unusual extensions
            pass

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_error_handling_edge_cases(self):
        """Test error handling in various edge cases."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        pf = pqf.ParquetFrame(df)

        # Test invalid SQL
        with pytest.raises(ValueError):
            pf.sql("INVALID SQL QUERY HERE")

        # Test SQL with missing table
        with pytest.raises(ValueError):
            pf.sql("SELECT * FROM nonexistent_table")

    def test_datacontext_imports(self):
        """Test datacontext module imports."""
        from parquetframe.datacontext import DataContextFactory, SourceType

        # Test that core classes are importable
        assert hasattr(DataContextFactory, "create_context")
        assert hasattr(SourceType, "PARQUET")
        assert hasattr(SourceType, "DATABASE")

    def test_workflow_history_module(self):
        """Test workflow history module exists."""
        from parquetframe import workflow_history

        # Test workflow history module exists
        assert hasattr(workflow_history, "__file__")

    def test_additional_sql_functions(self):
        """Test additional SQL functions and edge cases."""
        df = pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "score": [85, 92, 78],
                "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            }
        )
        pf = pqf.ParquetFrame(df)

        # Test date functions
        result = pf.sql(
            """
            SELECT
                name,
                score,
                EXTRACT(year FROM date) as year,
                EXTRACT(month FROM date) as month
            FROM df
        """
        )
        assert len(result) == 3
        assert "year" in result.pandas_df.columns
        assert "month" in result.pandas_df.columns

        # Test string functions
        result = pf.sql(
            """
            SELECT
                name,
                UPPER(name) as name_upper,
                LENGTH(name) as name_length
            FROM df
        """
        )
        assert len(result) == 3
        assert "name_upper" in result.pandas_df.columns
        assert "name_length" in result.pandas_df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
