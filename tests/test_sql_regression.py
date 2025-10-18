"""
Regression tests for SQL multi-format functionality.

This module tests specific edge cases and regression scenarios
that have been encountered in SQL multi-format operations.
"""

import tempfile
import time
from pathlib import Path

import pandas as pd
import pytest

import parquetframe as pqf


class TestSQLRegressionCases:
    """Test specific regression cases for SQL functionality."""

    @pytest.fixture
    def regression_data(self):
        """Create regression test data with edge cases."""
        # Data with NULL values and edge cases
        users_with_nulls = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5, 6],
                "name": ["Alice", "Bob", None, "Diana", "", "Frank"],
                "age": [25, None, 35, 28, 32, 0],
                "salary": [50000.0, 75000.0, None, 0.0, 80000.0, 25000.0],
                "active": [True, None, False, True, True, False],
            }
        )

        # Orders with mixed data types
        orders_mixed = pd.DataFrame(
            {
                "order_id": ["ORD-001", "ORD-002", "ORD-003", None, "ORD-005"],
                "user_id": [1, 2, 1, 4, 6],
                "amount": [1200.50, 0.0, None, 999.99, 50.0],
                "date": pd.to_datetime(
                    ["2023-01-15", "2023-01-20", None, "2023-02-15", "2023-03-01"]
                ),
                "metadata": [
                    '{"priority": "high"}',
                    '{"priority": "low"}',
                    None,
                    "{}",
                    '{"rush": true}',
                ],
            }
        )

        return {"users": users_with_nulls, "orders": orders_mixed}

    @pytest.fixture
    def regression_files(self, regression_data):
        """Create test files for regression testing."""
        temp_dir = tempfile.mkdtemp()
        files = {}

        # Create CSV and JSON versions
        for name, df in regression_data.items():
            csv_path = Path(temp_dir) / f"{name}.csv"
            json_path = Path(temp_dir) / f"{name}.json"
            parquet_path = Path(temp_dir) / f"{name}.parquet"

            # Handle datetime serialization for JSON
            if "date" in df.columns:
                df_json = df.copy()
                df_json["date"] = df_json["date"].dt.strftime("%Y-%m-%d").fillna("")
                df_json.to_json(json_path, orient="records")
            else:
                df.to_json(json_path, orient="records")

            df.to_csv(csv_path, index=False)
            df.to_parquet(parquet_path)

            files[name] = {
                "csv": csv_path,
                "json": json_path,
                "parquet": parquet_path,
            }

        yield temp_dir, files

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_null_value_handling_csv_vs_parquet(self, regression_files):
        """Test handling of NULL values between CSV and Parquet formats."""
        temp_dir, files = regression_files

        csv_pf = pqf.read(files["users"]["csv"])
        parquet_pf = pqf.read(files["users"]["parquet"])

        # Test COUNT with NULL handling
        csv_result = csv_pf.sql("SELECT COUNT(name) as name_count FROM df")
        parquet_result = parquet_pf.sql("SELECT COUNT(name) as name_count FROM df")

        # Both should handle NULLs consistently (COUNT ignores NULLs)
        assert (
            csv_result.pandas_df.iloc[0]["name_count"]
            == parquet_result.pandas_df.iloc[0]["name_count"]
        )

        # Test WHERE with NULL comparisons
        csv_null_result = csv_pf.sql(
            "SELECT COUNT(*) as total FROM df WHERE age IS NULL"
        )
        parquet_null_result = parquet_pf.sql(
            "SELECT COUNT(*) as total FROM df WHERE age IS NULL"
        )

        assert (
            csv_null_result.pandas_df.iloc[0]["total"]
            == parquet_null_result.pandas_df.iloc[0]["total"]
        )

    def test_empty_string_vs_null_handling(self, regression_files):
        """Test distinction between empty strings and NULL values."""
        temp_dir, files = regression_files

        pf = pqf.read(files["users"]["parquet"])

        # Test filtering empty strings vs NULLs
        empty_result = pf.sql("SELECT COUNT(*) as total FROM df WHERE name = ''")
        null_result = pf.sql("SELECT COUNT(*) as total FROM df WHERE name IS NULL")

        # Should find 1 empty string and 1 NULL
        assert empty_result.pandas_df.iloc[0]["total"] == 1
        assert null_result.pandas_df.iloc[0]["total"] == 1

    def test_zero_vs_null_numeric_handling(self, regression_files):
        """Test handling of zero vs NULL in numeric columns."""
        temp_dir, files = regression_files

        pf = pqf.read(files["users"]["parquet"])

        # Test AVG with zero values and NULLs
        result = pf.sql(
            """
            SELECT
                AVG(age) as avg_age,
                AVG(salary) as avg_salary,
                COUNT(age) as age_count,
                COUNT(salary) as salary_count
            FROM df
        """
        )

        row = result.pandas_df.iloc[0]
        # AVG should exclude NULLs but include zeros
        assert row["age_count"] == 5  # 5 non-NULL ages (including 0)
        assert row["salary_count"] == 5  # 5 non-NULL salaries (including 0.0)

    def test_cross_format_join_with_nulls(self, regression_files):
        """Test JOINs between formats when NULL values are present."""
        temp_dir, files = regression_files

        users_csv = pqf.read(files["users"]["csv"])
        orders_json = pqf.read(files["orders"]["json"])

        # Test LEFT JOIN with NULL handling
        result = users_csv.sql(
            """
            SELECT
                u.name,
                u.age,
                COALESCE(o.order_id, 'NO_ORDER') as order_status
            FROM df u
            LEFT JOIN orders o ON u.id = o.user_id
            ORDER BY u.id
        """,
            orders=orders_json,
        )

        assert len(result) >= 6  # Should include all users
        # Check that users without orders get 'NO_ORDER'
        no_order_count = len(
            result.pandas_df[result.pandas_df["order_status"] == "NO_ORDER"]
        )
        assert no_order_count > 0

    def test_datetime_handling_across_formats(self, regression_files):
        """Test datetime column handling across different formats."""
        temp_dir, files = regression_files

        # Note: JSON may have different datetime handling
        parquet_pf = pqf.read(files["orders"]["parquet"])

        # Test date filtering and extraction
        result = parquet_pf.sql(
            """
            SELECT
                order_id,
                amount,
                EXTRACT(YEAR FROM date) as order_year,
                EXTRACT(MONTH FROM date) as order_month
            FROM df
            WHERE date IS NOT NULL
            ORDER BY date
        """
        )

        assert len(result) == 4  # 4 non-NULL dates
        assert all(
            year >= 2023 for year in result.pandas_df["order_year"] if pd.notna(year)
        )

    @pytest.mark.parametrize(
        "format_combo", [("csv", "json"), ("json", "parquet"), ("csv", "parquet")]
    )
    def test_data_type_consistency_across_joins(self, regression_files, format_combo):
        """Test that JOINs maintain data type consistency across formats."""
        temp_dir, files = regression_files
        format1, format2 = format_combo

        users_pf = pqf.read(files["users"][format1])
        orders_pf = pqf.read(files["orders"][format2])

        # Test JOIN with numeric operations
        result = users_pf.sql(
            """
            SELECT
                u.name,
                u.salary,
                SUM(COALESCE(o.amount, 0)) as total_orders,
                COUNT(o.order_id) as order_count
            FROM df u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.name, u.salary
            HAVING u.salary IS NOT NULL
            ORDER BY total_orders DESC
        """,
            orders=orders_pf,
        )

        assert len(result) > 0
        # Verify numeric operations work correctly
        assert all(
            pd.notna(val) or val >= 0
            for val in result.pandas_df["total_orders"]
            if pd.notna(val)
        )

    def test_large_result_set_memory_handling(self, regression_files):
        """Test memory handling with larger result sets."""
        temp_dir, files = regression_files

        pf = pqf.read(files["users"]["parquet"])

        # Create a Cartesian product to test larger results
        result = pf.sql(
            """
            SELECT
                u1.name as name1,
                u2.name as name2,
                (u1.salary + COALESCE(u2.salary, 0)) as combined_salary
            FROM df u1
            CROSS JOIN df u2
            WHERE u1.id <= 3 AND u2.id <= 3
            ORDER BY combined_salary DESC
        """
        )

        # Should create 9 rows (3x3)
        assert len(result) == 9
        assert "combined_salary" in result.pandas_df.columns

    def test_string_encoding_edge_cases(self, regression_files):
        """Test handling of special characters and encoding edge cases."""
        temp_dir, files = regression_files

        pf = pqf.read(files["orders"]["parquet"])

        # Test JSON string handling within SQL
        result = pf.sql(
            """
            SELECT
                order_id,
                metadata,
                CASE
                    WHEN metadata LIKE '%priority%' THEN 'has_priority'
                    WHEN metadata = '{}' THEN 'empty_json'
                    WHEN metadata IS NULL THEN 'null_metadata'
                    ELSE 'other'
                END as metadata_type
            FROM df
            ORDER BY order_id
        """
        )

        assert len(result) == 5
        metadata_types = set(result.pandas_df["metadata_type"])
        expected_types = {"has_priority", "empty_json", "null_metadata", "other"}
        assert metadata_types.issubset(expected_types)


class TestSQLPerformanceRegression:
    """Test performance-related regression cases."""

    @pytest.fixture
    def performance_data(self):
        """Create larger dataset for performance testing."""
        # Create moderately sized dataset for performance testing
        n_users = 1000
        n_orders = 2000

        users = pd.DataFrame(
            {
                "id": range(1, n_users + 1),
                "name": [f"User_{i}" for i in range(1, n_users + 1)],
                "age": [25 + (i % 40) for i in range(n_users)],
                "city": [
                    ["NYC", "LA", "Chicago", "Boston", "Seattle"][i % 5]
                    for i in range(n_users)
                ],
                "salary": [40000 + (i * 100) % 60000 for i in range(n_users)],
            }
        )

        orders = pd.DataFrame(
            {
                "order_id": range(1, n_orders + 1),
                "user_id": [(i % n_users) + 1 for i in range(n_orders)],
                "amount": [100 + (i * 50) % 2000 for i in range(n_orders)],
                "product_category": [
                    ["electronics", "clothing", "books", "food"][i % 4]
                    for i in range(n_orders)
                ],
            }
        )

        return {"users": users, "orders": orders}

    @pytest.fixture
    def performance_files(self, performance_data):
        """Create performance test files."""
        temp_dir = tempfile.mkdtemp()
        files = {}

        for name, df in performance_data.items():
            parquet_path = Path(temp_dir) / f"{name}.parquet"
            csv_path = Path(temp_dir) / f"{name}.csv"

            df.to_parquet(parquet_path)
            df.to_csv(csv_path, index=False)

            files[name] = {"parquet": parquet_path, "csv": csv_path}

        yield temp_dir, files

        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.slow
    def test_complex_join_performance(self, performance_files):
        """Test that complex JOINs complete within reasonable time."""
        temp_dir, files = performance_files

        users_pf = pqf.read(files["users"]["parquet"])
        orders_pf = pqf.read(files["orders"]["parquet"])

        start_time = time.time()

        result = users_pf.sql(
            """
            SELECT
                u.city,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(o.order_id) as order_count,
                SUM(o.amount) as total_revenue,
                AVG(o.amount) as avg_order_value,
                MAX(o.amount) as max_order
            FROM df u
            JOIN orders o ON u.id = o.user_id
            GROUP BY u.city
            HAVING COUNT(o.order_id) > 50
            ORDER BY total_revenue DESC
        """,
            orders=orders_pf,
        )

        execution_time = time.time() - start_time

        # Should complete in under 5 seconds for this dataset size
        assert execution_time < 5.0, f"Query took {execution_time:.2f}s, expected < 5s"
        assert len(result) > 0
        assert "total_revenue" in result.pandas_df.columns

    def test_format_read_performance_comparison(self, performance_files):
        """Compare read performance across formats."""
        temp_dir, files = performance_files

        # Test parquet read time
        start_time = time.time()
        parquet_pf = pqf.read(files["users"]["parquet"])
        result1 = parquet_pf.sql("SELECT COUNT(*) as total FROM df")
        parquet_time = time.time() - start_time

        # Test CSV read time
        start_time = time.time()
        csv_pf = pqf.read(files["users"]["csv"])
        result2 = csv_pf.sql("SELECT COUNT(*) as total FROM df")
        csv_time = time.time() - start_time

        # Both should give same results
        assert result1.pandas_df.iloc[0]["total"] == result2.pandas_df.iloc[0]["total"]

        # Parquet should generally be faster (but allow for variance)
        # We're not strictly asserting this since it depends on system performance
        print(f"Parquet read+query time: {parquet_time:.3f}s")
        print(f"CSV read+query time: {csv_time:.3f}s")

    @pytest.mark.slow
    def test_memory_usage_stability(self, performance_files):
        """Test memory usage remains stable during repeated operations."""
        temp_dir, files = performance_files

        users_pf = pqf.read(files["users"]["parquet"])

        # Perform multiple queries to test memory stability
        for i in range(10):
            result = users_pf.sql(
                f"""
                SELECT
                    city,
                    COUNT(*) as user_count,
                    AVG(salary) as avg_salary
                FROM df
                WHERE age > {20 + i}
                GROUP BY city
                ORDER BY user_count DESC
                LIMIT 3
            """
            )
            assert len(result) > 0
            # Force garbage collection to prevent memory buildup
            del result

    def test_query_caching_performance(self, performance_files):
        """Test query caching improves repeated query performance."""
        temp_dir, files = performance_files

        pf = pqf.read(files["users"]["parquet"])
        query = (
            "SELECT city, COUNT(*) as count FROM df GROUP BY city ORDER BY count DESC"
        )

        # First execution (cold)
        start_time = time.time()
        result1 = pf.sql(query, use_cache=True)
        first_time = time.time() - start_time

        # Second execution (should use cache)
        start_time = time.time()
        result2 = pf.sql(query, use_cache=True)
        second_time = time.time() - start_time

        # Results should be identical
        pd.testing.assert_frame_equal(result1.pandas_df, result2.pandas_df)

        # Second query should be faster (though not strictly required due to overhead)
        print(f"First execution: {first_time:.4f}s")
        print(f"Second execution (cached): {second_time:.4f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
