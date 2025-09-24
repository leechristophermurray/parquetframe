"""
Tests for the performance benchmarking module.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from parquetframe.benchmark import (
    BenchmarkResult,
    PerformanceBenchmark,
    run_comprehensive_benchmark,
)


class TestBenchmarkResult:
    def test_benchmark_result_creation(self):
        """Test basic BenchmarkResult creation."""
        result = BenchmarkResult(
            operation="Read 1K rows",
            backend="pandas",
            execution_time=0.1,
            memory_peak=50.0,
            memory_end=45.0,
            file_size_mb=1.0,
            success=True,
        )

        assert result.operation == "Read 1K rows"
        assert result.backend == "pandas"
        assert result.execution_time == 0.1
        assert result.memory_peak == 50.0
        assert result.file_size_mb == 1.0
        assert result.success is True
        assert result.error is None

    def test_benchmark_result_string_representation(self):
        """Test string representation of BenchmarkResult."""
        result = BenchmarkResult(
            operation="Test Op",
            backend="pandas",
            execution_time=0.123,
            memory_peak=25.5,
            memory_end=20.0,
            file_size_mb=5.0,
            success=True,
        )

        str_repr = str(result)
        assert "✓ Test Op (pandas): 0.123s, 25.5MB peak" == str_repr

        # Test failure case
        result_fail = BenchmarkResult(
            operation="Failed Op",
            backend="Dask",
            execution_time=0.0,
            memory_peak=0.0,
            memory_end=0.0,
            file_size_mb=1.0,
            success=False,
            error="Test error",
        )

        str_repr_fail = str(result_fail)
        assert "✗ Failed Op (Dask): 0.000s, 0.0MB peak" == str_repr_fail


class TestPerformanceBenchmark:
    def test_performance_benchmark_creation(self):
        """Test PerformanceBenchmark initialization."""
        benchmark = PerformanceBenchmark(verbose=False)
        assert benchmark.verbose is False
        assert benchmark.console is None
        assert benchmark.results == []

        benchmark_verbose = PerformanceBenchmark(verbose=True)
        assert benchmark_verbose.verbose is True
        assert benchmark_verbose.console is not None

    def test_create_test_data(self):
        """Test test data creation."""
        benchmark = PerformanceBenchmark(verbose=False)

        df = benchmark.create_test_data(rows=100, cols=6)
        assert len(df) == 100
        assert len(df.columns) == 6

        # Check column types
        numeric_cols = [col for col in df.columns if col.startswith("numeric_")]
        integer_cols = [col for col in df.columns if col.startswith("integer_")]
        category_cols = [col for col in df.columns if col.startswith("category_")]

        assert len(numeric_cols) >= 1
        assert len(integer_cols) >= 1
        assert len(category_cols) >= 1

    def test_create_test_data_without_strings_or_dates(self):
        """Test creating test data without strings or dates."""
        benchmark = PerformanceBenchmark(verbose=False)

        df = benchmark.create_test_data(
            rows=50, cols=6, include_strings=False, include_dates=False
        )
        assert len(df) == 50
        assert len(df.columns) == 6

        # Should only have numeric and integer columns plus extras
        category_cols = [col for col in df.columns if col.startswith("category_")]
        assert len(category_cols) == 0  # No category columns
        assert "date" not in df.columns

    @patch("psutil.Process")
    def test_benchmark_operation(self, mock_process):
        """Test single operation benchmarking."""
        # Mock memory monitoring
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = (
            100 * 1024 * 1024
        )  # 100MB in bytes
        mock_process.return_value = mock_process_instance

        benchmark = PerformanceBenchmark(verbose=False)

        def test_operation():
            return "test_result"

        result = benchmark.benchmark_operation(
            "Test Operation", test_operation, "pandas", 5.0
        )

        assert result.operation == "Test Operation"
        assert result.backend == "pandas"
        assert result.file_size_mb == 5.0
        assert result.success is True
        assert result.error is None
        assert result.execution_time > 0

    @patch("psutil.Process")
    def test_benchmark_operation_with_error(self, mock_process):
        """Test benchmarking an operation that raises an error."""
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 100 * 1024 * 1024
        mock_process.return_value = mock_process_instance

        benchmark = PerformanceBenchmark(verbose=False)

        def failing_operation():
            raise ValueError("Test error")

        result = benchmark.benchmark_operation(
            "Failing Operation", failing_operation, "pandas", 5.0
        )

        assert result.operation == "Failing Operation"
        assert result.success is False
        assert result.error == "Test error"

    def test_benchmark_read_operations(self):
        """Test benchmarking read operations."""
        benchmark = PerformanceBenchmark(verbose=False)

        # Use small file sizes for testing
        file_sizes = [(100, "100 rows"), (200, "200 rows")]

        with patch.object(benchmark, "benchmark_operation") as mock_benchmark_op:
            # Mock the benchmark_operation calls
            mock_result = MagicMock()
            mock_benchmark_op.return_value = mock_result

            results = benchmark.benchmark_read_operations(file_sizes)

            # Should have 4 calls: 2 file sizes × 2 backends (pandas + Dask)
            assert mock_benchmark_op.call_count == 4
            assert len(results) == 4

    def test_benchmark_operations(self):
        """Test benchmarking various operations."""
        benchmark = PerformanceBenchmark(verbose=False)

        operations = ["groupby", "filter"]

        with patch.object(benchmark, "benchmark_operation") as mock_benchmark_op:
            mock_result = MagicMock()
            mock_benchmark_op.return_value = mock_result

            results = benchmark.benchmark_operations(operations, data_size=1000)

            # Should have 4 calls: 2 operations × 2 backends
            assert mock_benchmark_op.call_count == 4
            assert len(results) == 4

    def test_benchmark_threshold_sensitivity(self):
        """Test threshold sensitivity analysis."""
        benchmark = PerformanceBenchmark(verbose=False)

        thresholds = [1, 5]
        file_sizes_mb = [0.5, 2]

        with patch.object(benchmark, "benchmark_operation") as mock_benchmark_op:
            mock_result = MagicMock()
            mock_benchmark_op.return_value = mock_result

            results = benchmark.benchmark_threshold_sensitivity(
                thresholds=thresholds, file_sizes_mb=file_sizes_mb
            )

            # Should have 4 calls: 2 thresholds × 2 file sizes
            assert mock_benchmark_op.call_count == 4
            assert len(results) == 4

    def test_generate_report_empty_results(self):
        """Test report generation with no results."""
        benchmark = PerformanceBenchmark(verbose=True)

        # Should handle empty results gracefully
        benchmark.generate_report()  # Should not raise an error

    def test_generate_report_with_results(self):
        """Test report generation with mock results."""
        benchmark = PerformanceBenchmark(verbose=False)

        # Add some mock results
        benchmark.results = [
            BenchmarkResult(
                operation="Read 1K rows",
                backend="pandas",
                execution_time=0.1,
                memory_peak=10.0,
                memory_end=8.0,
                file_size_mb=1.0,
                success=True,
            ),
            BenchmarkResult(
                operation="Read 1K rows",
                backend="Dask",
                execution_time=0.2,
                memory_peak=5.0,
                memory_end=4.0,
                file_size_mb=1.0,
                success=True,
            ),
        ]

        # Mock console to avoid actual output during testing
        with patch.object(benchmark, "console", MagicMock()):
            benchmark.generate_report()

    def test_analyze_optimal_threshold(self):
        """Test optimal threshold analysis."""
        benchmark = PerformanceBenchmark(verbose=False)

        threshold_results = [
            BenchmarkResult(
                operation="Threshold 5MB",
                backend="pandas",
                execution_time=0.1,
                memory_peak=10.0,
                memory_end=8.0,
                file_size_mb=3.0,
                success=True,
            ),
            BenchmarkResult(
                operation="Threshold 10MB",
                backend="pandas",
                execution_time=0.2,
                memory_peak=15.0,
                memory_end=12.0,
                file_size_mb=3.0,
                success=True,
            ),
        ]

        optimal = benchmark._analyze_optimal_threshold(threshold_results)
        assert optimal in [5.0, 10.0]  # Should return one of the tested thresholds

    def test_analyze_optimal_threshold_empty(self):
        """Test optimal threshold analysis with no results."""
        benchmark = PerformanceBenchmark(verbose=False)

        optimal = benchmark._analyze_optimal_threshold([])
        assert optimal is None

    def test_compare_backends(self):
        """Test backend comparison."""
        benchmark = PerformanceBenchmark(verbose=False)

        benchmark.results = [
            BenchmarkResult(
                operation="Test",
                backend="pandas",
                execution_time=0.1,
                memory_peak=20.0,
                memory_end=15.0,
                file_size_mb=1.0,
                success=True,
            ),
            BenchmarkResult(
                operation="Test",
                backend="Dask",
                execution_time=0.2,
                memory_peak=10.0,
                memory_end=8.0,
                file_size_mb=1.0,
                success=True,
            ),
        ]

        recommendations = benchmark._compare_backends()
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 1  # Should have at least one recommendation


class TestComprehensiveBenchmark:
    @patch("parquetframe.benchmark.PerformanceBenchmark")
    def test_run_comprehensive_benchmark(self, mock_benchmark_class):
        """Test running comprehensive benchmark suite."""
        # Mock the benchmark instance
        mock_benchmark = MagicMock()
        mock_benchmark_class.return_value = mock_benchmark

        # Mock the benchmark methods
        mock_benchmark.benchmark_read_operations.return_value = []
        mock_benchmark.benchmark_operations.return_value = []
        mock_benchmark.benchmark_threshold_sensitivity.return_value = []
        mock_benchmark.results = []

        results = run_comprehensive_benchmark(verbose=False)

        assert isinstance(results, dict)
        assert "read_operations" in results
        assert "data_operations" in results
        assert "threshold_analysis" in results
        assert "summary" in results

        # Verify methods were called
        mock_benchmark.benchmark_read_operations.assert_called_once()
        mock_benchmark.benchmark_operations.assert_called_once()
        mock_benchmark.benchmark_threshold_sensitivity.assert_called_once()
        # generate_report should NOT be called when verbose=False
        mock_benchmark.generate_report.assert_not_called()

    @patch("parquetframe.benchmark.PerformanceBenchmark")
    def test_run_comprehensive_benchmark_with_output(self, mock_benchmark_class):
        """Test running comprehensive benchmark with output file."""
        mock_benchmark = MagicMock()
        mock_benchmark_class.return_value = mock_benchmark

        mock_benchmark.benchmark_read_operations.return_value = []
        mock_benchmark.benchmark_operations.return_value = []
        mock_benchmark.benchmark_threshold_sensitivity.return_value = []
        mock_benchmark.results = []

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            results = run_comprehensive_benchmark(output_file=temp_path, verbose=False)

            assert isinstance(results, dict)

            # Check that output file was created
            output_file = Path(temp_path)
            assert output_file.exists()

        finally:
            # Clean up
            if Path(temp_path).exists():
                Path(temp_path).unlink()


# Integration tests requiring actual file operations
class TestBenchmarkIntegration:
    """Integration tests that create actual files and run benchmarks."""

    @pytest.mark.slow
    def test_small_benchmark_with_real_files(self):
        """Test benchmarking with small real files."""
        benchmark = PerformanceBenchmark(verbose=False)

        # Use very small file sizes for fast tests
        file_sizes = [(100, "100 rows")]

        results = benchmark.benchmark_read_operations(file_sizes)

        # Should have results for both backends
        assert len(results) == 2  # pandas + Dask
        assert all(result.success for result in results)

        # Verify result structure
        for result in results:
            assert result.operation == "Read 100 rows"
            assert result.backend in ["pandas", "Dask"]
            assert result.execution_time > 0
            assert result.file_size_mb > 0

    @pytest.mark.slow
    def test_operations_benchmark_with_real_data(self):
        """Test operations benchmarking with real data."""
        benchmark = PerformanceBenchmark(verbose=False)

        # Test only basic operations for speed
        operations = ["filter"]

        results = benchmark.benchmark_operations(operations, data_size=1000)

        # Should have results for both backends
        assert len(results) == 2  # pandas + Dask

        for result in results:
            assert result.operation == "Filter"
            assert result.backend in ["pandas", "Dask"]
            assert result.execution_time > 0
