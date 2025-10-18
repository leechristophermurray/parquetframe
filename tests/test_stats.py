"""
Tests for statistical analysis functionality.

This module tests the StatsAccessor class and its various methods
including distribution analysis, correlation matrices, outlier detection, and statistical testing.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import from the package
from parquetframe.legacy import ParquetFrame
from parquetframe.stats import (
    StatsAccessor,
    detect_outliers_iqr,
    detect_outliers_zscore,
)


class TestStatisticalUtilities:
    """Test statistical utility functions."""

    def test_detect_outliers_iqr_pandas(self):
        """Test IQR outlier detection with pandas Series."""
        # Create data with known outliers
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])  # 100 is clear outlier
        outliers = detect_outliers_iqr(data)

        assert isinstance(outliers, pd.Series)
        assert outliers.dtype == bool
        assert outliers.iloc[-1]  # Last value (100) should be detected as outlier

    def test_detect_outliers_zscore_pandas(self):
        """Test Z-score outlier detection with pandas Series."""
        # Create data with known outliers
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
        outliers = detect_outliers_zscore(data, threshold=2.0)

        assert isinstance(outliers, pd.Series)
        assert outliers.dtype == bool
        assert outliers.iloc[-1]  # Last value (100) should be detected as outlier

    def test_outlier_detection_no_outliers(self):
        """Test outlier detection on normal data with no outliers."""
        # Create normal data without outliers
        np.random.seed(42)
        data = pd.Series(np.random.normal(0, 1, 100))

        outliers_iqr = detect_outliers_iqr(data)
        outliers_zscore = detect_outliers_zscore(data)

        # Should detect few or no outliers in normal data
        assert outliers_iqr.sum() <= 5  # At most 5% outliers expected
        assert outliers_zscore.sum() <= 3  # Very few with z-score > 3


class TestStatsAccessor:
    """Test StatsAccessor functionality."""

    def setup_method(self):
        """Set up test data."""
        np.random.seed(42)  # For reproducible results

        # Create comprehensive test dataset
        self.test_data = pd.DataFrame(
            {
                "normal_col": np.random.normal(50, 15, 1000),
                "uniform_col": np.random.uniform(0, 100, 1000),
                "skewed_col": np.random.exponential(2, 1000),
                "categorical": np.random.choice(["A", "B", "C"], 1000),
                "outlier_col": np.concatenate(
                    [
                        np.random.normal(50, 5, 990),  # Normal data
                        [
                            150,
                            200,
                            -50,
                            -100,
                            300,
                            400,
                            -200,
                            500,
                            600,
                            -300,
                        ],  # Clear outliers
                    ]
                ),
                "correlated_col": None,  # Will be set based on normal_col
            }
        )

        # Create correlated column
        self.test_data["correlated_col"] = self.test_data[
            "normal_col"
        ] * 2 + np.random.normal(0, 5, 1000)

        # Create ParquetFrame
        self.pf = ParquetFrame(self.test_data)

    def test_stats_accessor_exists(self):
        """Test that stats accessor is available."""
        assert hasattr(self.pf, "stats")
        assert isinstance(self.pf.stats, StatsAccessor)

    def test_describe_extended(self):
        """Test extended descriptive statistics."""
        extended_stats = self.pf.stats.describe_extended()

        assert isinstance(extended_stats, pd.DataFrame)

        # Check that we have all numeric columns
        numeric_cols = self.test_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            assert col in extended_stats.index

        # Check that extended statistics are present
        expected_stats = [
            "count",
            "mean",
            "std",
            "min",
            "max",
            "median",
            "skewness",
            "kurtosis",
        ]
        for stat in expected_stats:
            assert stat in extended_stats.columns

    def test_corr_matrix_pearson(self):
        """Test Pearson correlation matrix."""
        corr_matrix = self.pf.stats.corr_matrix(method="pearson")

        assert isinstance(corr_matrix, pd.DataFrame)

        # Should be square matrix
        assert corr_matrix.shape[0] == corr_matrix.shape[1]

        # Diagonal should be 1.0 (perfect self-correlation)
        np.testing.assert_array_almost_equal(np.diag(corr_matrix), 1.0)

        # Should have strong correlation between normal_col and correlated_col
        assert abs(corr_matrix.loc["normal_col", "correlated_col"]) > 0.8

    def test_corr_matrix_spearman(self):
        """Test Spearman correlation matrix."""
        corr_matrix = self.pf.stats.corr_matrix(method="spearman")

        assert isinstance(corr_matrix, pd.DataFrame)
        assert corr_matrix.shape[0] == corr_matrix.shape[1]

    def test_distribution_summary_single_column(self):
        """Test distribution summary for a single column."""
        dist_summary = self.pf.stats.distribution_summary("normal_col")

        assert isinstance(dist_summary, dict)

        # Check essential statistics are present
        essential_stats = [
            "count",
            "mean",
            "median",
            "std",
            "skewness",
            "kurtosis",
            "min",
            "max",
            "range",
            "distribution_shape",
        ]
        for stat in essential_stats:
            assert stat in dist_summary

        # Check percentiles are present
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            assert f"percentile_{p}" in dist_summary

    def test_distribution_summary_all_columns(self):
        """Test distribution summary for all numeric columns."""
        dist_summary = self.pf.stats.distribution_summary()

        assert isinstance(dist_summary, dict)

        numeric_cols = self.test_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            assert col in dist_summary
            assert isinstance(dist_summary[col], dict)

    def test_detect_outliers_iqr_method(self):
        """Test outlier detection using IQR method."""
        outliers_pf = self.pf.stats.detect_outliers("outlier_col", method="iqr")

        assert isinstance(outliers_pf, ParquetFrame)

        # Should have new column for outlier indicators
        outlier_col = "outlier_col_outlier_iqr"
        assert outlier_col in outliers_pf.pandas_df.columns

        # Should detect some outliers in our test data
        outlier_count = outliers_pf.pandas_df[outlier_col].sum()
        assert outlier_count > 0
        assert outlier_count >= 5  # We added 10 clear outliers

    def test_detect_outliers_zscore_method(self):
        """Test outlier detection using Z-score method."""
        outliers_pf = self.pf.stats.detect_outliers(
            "outlier_col", method="zscore", threshold=2.5
        )

        assert isinstance(outliers_pf, ParquetFrame)

        # Should have new column for outlier indicators
        outlier_col = "outlier_col_outlier_zscore"
        assert outlier_col in outliers_pf.pandas_df.columns

        # Should detect outliers
        outlier_count = outliers_pf.pandas_df[outlier_col].sum()
        assert outlier_count > 0

    def test_detect_outliers_all_columns(self):
        """Test outlier detection on all numeric columns."""
        outliers_pf = self.pf.stats.detect_outliers(method="iqr")

        assert isinstance(outliers_pf, ParquetFrame)

        # Should have outlier columns for all numeric columns
        numeric_cols = self.test_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            outlier_col = f"{col}_outlier_iqr"
            assert outlier_col in outliers_pf.pandas_df.columns

    def test_normality_test_without_scipy(self):
        """Test normality test when scipy is not available (fallback mode)."""
        # This test assumes scipy might not be available
        result = self.pf.stats.normality_test("normal_col")

        assert isinstance(result, dict)
        assert "sample_size" in result

        # Should have either scipy results or fallback results
        if "note" in result:
            # Fallback mode
            assert "skewness" in result
            assert "kurtosis" in result
            assert "is_approximately_normal" in result
        else:
            # Full scipy mode
            assert "kolmogorov_smirnov" in result

    def test_correlation_test_without_scipy(self):
        """Test correlation test when scipy might not be available."""
        result = self.pf.stats.correlation_test("normal_col", "correlated_col")

        assert isinstance(result, dict)
        assert "sample_size" in result

        # Should have either scipy results or fallback
        if "note" in result:
            # Fallback mode
            assert "pearson_correlation" in result
        else:
            # Full scipy mode
            assert "pearson" in result
            assert "spearman" in result

    def test_linear_regression_without_scipy(self):
        """Test linear regression when scipy might not be available."""
        result = self.pf.stats.linear_regression("normal_col", "correlated_col")

        assert isinstance(result, dict)
        assert "sample_size" in result

        # Should have either scipy results or fallback
        if "note" in result:
            # Fallback mode
            assert "correlation" in result
        else:
            # Full scipy mode with comprehensive results
            expected_keys = [
                "slope",
                "intercept",
                "r_value",
                "r_squared",
                "p_value",
                "standard_error",
                "mse",
                "rmse",
                "equation",
            ]
            for key in expected_keys:
                assert key in result

    def test_regression_summary(self):
        """Test regression summary functionality."""
        summary = self.pf.stats.regression_summary("normal_col", "correlated_col")

        assert isinstance(summary, pd.DataFrame)
        assert "Metric" in summary.columns
        assert "Value" in summary.columns
        assert len(summary) > 0


class TestStatsWithDask:
    """Test statistical functionality with Dask backend."""

    def setup_method(self):
        """Set up test data for Dask testing."""
        np.random.seed(42)

        # Create larger dataset for Dask testing
        large_data = pd.DataFrame(
            {
                "col1": np.random.normal(100, 20, 5000),
                "col2": np.random.uniform(0, 200, 5000),
                "col3": np.random.exponential(5, 5000),
            }
        )

        # Force Dask usage
        self.pf = ParquetFrame(large_data, islazy=True)

    def test_describe_extended_with_dask(self):
        """Test extended statistics with Dask backend."""
        extended_stats = self.pf.stats.describe_extended()

        assert isinstance(extended_stats, pd.DataFrame)
        assert self.pf.islazy  # Should still be using Dask

        # Should have computed statistics for all columns
        assert "col1" in extended_stats.index
        assert "col2" in extended_stats.index
        assert "col3" in extended_stats.index

    def test_correlation_matrix_with_dask(self):
        """Test correlation matrix with Dask backend."""
        corr_matrix = self.pf.stats.corr_matrix()

        assert isinstance(corr_matrix, pd.DataFrame)
        assert corr_matrix.shape == (3, 3)  # 3 columns = 3x3 matrix

    def test_outlier_detection_with_dask(self):
        """Test outlier detection with Dask backend."""
        outliers_pf = self.pf.stats.detect_outliers("col1", method="iqr")

        assert isinstance(outliers_pf, ParquetFrame)
        assert outliers_pf.islazy  # Should preserve Dask backend

        # Should have outlier column
        assert "col1_outlier_iqr" in outliers_pf.pandas_df.columns


class TestStatsEdgeCases:
    """Test edge cases and error conditions."""

    def test_accessor_with_no_data(self):
        """Test accessor behavior with no DataFrame loaded."""
        empty_pf = ParquetFrame()

        with pytest.raises(ValueError, match="No DataFrame loaded"):
            empty_pf.stats.describe_extended()

    def test_distribution_summary_nonexistent_column(self):
        """Test distribution summary with non-existent column."""
        data = pd.DataFrame({"col1": [1, 2, 3]})
        pf = ParquetFrame(data)

        with pytest.raises(KeyError):
            pf.stats.distribution_summary("nonexistent_column")

    def test_outlier_detection_invalid_method(self):
        """Test outlier detection with invalid method."""
        data = pd.DataFrame({"col1": [1, 2, 3, 4, 5]})
        pf = ParquetFrame(data)

        with pytest.raises(ValueError, match="Unsupported method"):
            pf.stats.detect_outliers("col1", method="invalid_method")

    def test_normality_test_nonexistent_column(self):
        """Test normality test with non-existent column."""
        data = pd.DataFrame({"col1": [1, 2, 3]})
        pf = ParquetFrame(data)

        with pytest.raises(KeyError):
            pf.stats.normality_test("nonexistent_column")

    def test_correlation_test_invalid_columns(self):
        """Test correlation test with invalid columns."""
        data = pd.DataFrame({"col1": [1, 2, 3]})
        pf = ParquetFrame(data)

        with pytest.raises(KeyError):
            pf.stats.correlation_test("col1", "nonexistent_column")

    def test_stats_with_missing_data(self):
        """Test statistical operations with missing data."""
        data = pd.DataFrame(
            {
                "col_with_na": [1, 2, np.nan, 4, 5, np.nan, 7, 8, 9, 10],
                "col_normal": range(10),
            }
        )
        pf = ParquetFrame(data)

        # Distribution summary should handle NaN values
        dist_summary = pf.stats.distribution_summary("col_with_na")
        assert "null_count" in dist_summary
        assert dist_summary["null_count"] == 2

        # Correlation should handle missing data by dropping rows
        corr_test = pf.stats.correlation_test("col_with_na", "col_normal")
        assert corr_test["sample_size"] == 8  # 10 - 2 NaN values


class TestStatsIntegration:
    """Test integration with other ParquetFrame features."""

    def test_stats_after_sql_operations(self):
        """Test statistical operations after SQL filtering."""
        data = pd.DataFrame(
            {
                "value": np.random.normal(50, 15, 1000),
                "category": np.random.choice(["A", "B", "C"], 1000),
                "score": np.random.uniform(0, 100, 1000),
            }
        )
        pf = ParquetFrame(data)

        # Apply SQL filter first
        filtered = pf.sql("SELECT * FROM df WHERE category = 'A'")

        # Then apply statistical operations
        stats = filtered.stats.distribution_summary("value")

        assert isinstance(stats, dict)
        assert "mean" in stats

    def test_chaining_stats_operations(self):
        """Test chaining multiple statistical operations."""
        data = pd.DataFrame(
            {
                "sales": np.random.normal(1000, 200, 500),
                "costs": np.random.normal(800, 150, 500),
                "region": np.random.choice(["North", "South", "East", "West"], 500),
            }
        )
        pf = ParquetFrame(data)

        # Chain: detect outliers, then analyze correlation of non-outliers
        with_outliers = pf.stats.detect_outliers("sales", method="iqr")

        # Filter out outliers using SQL
        no_outliers = with_outliers.sql(
            "SELECT * FROM df WHERE sales_outlier_iqr = false"
        )

        # Analyze correlation on clean data
        corr_test = no_outliers.stats.correlation_test("sales", "costs")

        assert isinstance(corr_test, dict)
        assert "sample_size" in corr_test

    def test_stats_with_save_restore(self):
        """Test that statistical operations work after save/restore cycle."""
        data = pd.DataFrame(
            {
                "metric1": np.random.normal(100, 25, 200),
                "metric2": np.random.exponential(10, 200),
            }
        )

        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "stats_test.parquet"

        # Save and reload
        pf = ParquetFrame(data)
        pf.save(str(temp_file))

        reloaded_pf = ParquetFrame.read(str(temp_file))

        # Test statistical operations on reloaded data
        corr_matrix = reloaded_pf.stats.corr_matrix()
        assert isinstance(corr_matrix, pd.DataFrame)

        dist_summary = reloaded_pf.stats.distribution_summary("metric1")
        assert isinstance(dist_summary, dict)
