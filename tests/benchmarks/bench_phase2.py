"""
Simple benchmarks for Phase 2 components.

Run with: pytest tests/benchmarks/bench_phase2.py --benchmark-only
"""

import pandas as pd
import pytest

from parquetframe.config import config_context, reset_config
from parquetframe.core import read_csv, read_parquet


@pytest.fixture
def small_csv(tmp_path):
    """Create a small CSV file (1k rows)."""
    file_path = tmp_path / "small.csv"
    df = pd.DataFrame(
        {"a": range(1000), "b": range(1000, 2000), "c": range(2000, 3000)}
    )
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def medium_csv(tmp_path):
    """Create a medium CSV file (100k rows)."""
    file_path = tmp_path / "medium.csv"
    df = pd.DataFrame(
        {"a": range(100000), "b": range(100000, 200000), "c": range(200000, 300000)}
    )
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def small_parquet(tmp_path):
    """Create a small Parquet file (1k rows)."""
    file_path = tmp_path / "small.parquet"
    df = pd.DataFrame(
        {"a": range(1000), "b": range(1000, 2000), "c": range(2000, 3000)}
    )
    df.to_parquet(file_path)
    return file_path


@pytest.fixture
def medium_parquet(tmp_path):
    """Create a medium Parquet file (100k rows)."""
    file_path = tmp_path / "medium.parquet"
    df = pd.DataFrame(
        {"a": range(100000), "b": range(100000, 200000), "c": range(200000, 300000)}
    )
    df.to_parquet(file_path)
    return file_path


@pytest.fixture(autouse=True)
def setup():
    """Setup before each benchmark."""
    reset_config()
    yield
    reset_config()


class TestReadBenchmarks:
    """Benchmarks for reading data."""

    def test_bench_read_small_csv_pandas(self, benchmark, small_csv):
        """Benchmark reading small CSV with pandas."""
        with config_context(default_engine="pandas"):
            result = benchmark(read_csv, small_csv)
            assert len(result) == 1000

    def test_bench_read_small_csv_polars(self, benchmark, small_csv):
        """Benchmark reading small CSV with polars."""
        with config_context(default_engine="polars"):
            result = benchmark(read_csv, small_csv)
            assert len(result) == 1000

    def test_bench_read_medium_csv_pandas(self, benchmark, medium_csv):
        """Benchmark reading medium CSV with pandas."""
        with config_context(default_engine="pandas"):
            result = benchmark(read_csv, medium_csv)
            assert len(result) == 100000

    def test_bench_read_medium_csv_polars(self, benchmark, medium_csv):
        """Benchmark reading medium CSV with polars."""
        with config_context(default_engine="polars"):
            result = benchmark(read_csv, medium_csv)
            assert len(result) == 100000

    def test_bench_read_parquet_pandas(self, benchmark, small_parquet):
        """Benchmark reading Parquet with pandas."""
        with config_context(default_engine="pandas"):
            result = benchmark(read_parquet, small_parquet)
            assert len(result) == 1000

    def test_bench_read_parquet_polars(self, benchmark, small_parquet):
        """Benchmark reading Parquet with polars."""
        with config_context(default_engine="polars"):
            result = benchmark(read_parquet, small_parquet)
            assert len(result) == 1000


class TestOperationBenchmarks:
    """Benchmarks for DataFrame operations."""

    def test_bench_groupby_pandas(self, benchmark, medium_parquet):
        """Benchmark groupby operation with pandas."""
        with config_context(default_engine="pandas"):
            df = read_parquet(medium_parquet)

            def operation():
                return df.groupby("a")["b"].sum()

            result = benchmark(operation)

    def test_bench_groupby_polars(self, benchmark, medium_parquet):
        """Benchmark groupby operation with polars."""
        with config_context(default_engine="polars"):
            df = read_parquet(medium_parquet)

            def operation():
                result = df.group_by("a").agg({"b": "sum"})
                return result.collect() if hasattr(result, "collect") else result

            benchmark(operation)

    def test_bench_filter_pandas(self, benchmark, medium_parquet):
        """Benchmark filter operation with pandas."""
        with config_context(default_engine="pandas"):
            df = read_parquet(medium_parquet)

            def operation():
                return df[df["a"] > 50000]

            result = benchmark(operation)

    def test_bench_filter_polars(self, benchmark, medium_parquet):
        """Benchmark filter operation with polars."""
        with config_context(default_engine="polars"):
            df = read_parquet(medium_parquet)

            def operation():
                import polars as pl

                result = df.filter(pl.col("a") > 50000)
                return result.collect() if hasattr(result, "collect") else result

            benchmark(operation)


class TestEntityBenchmarks:
    """Benchmarks for entity operations."""

    def test_bench_entity_save(self, benchmark, tmp_path):
        """Benchmark entity save operation."""
        from dataclasses import dataclass

        from parquetframe.entity import entity
        from parquetframe.entity.metadata import registry

        registry.clear()

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str
            email: str

        def save_user():
            user = User(1, "Alice", "alice@example.com")
            user.save()

        benchmark(save_user)
        registry.clear()

    def test_bench_entity_find_all(self, benchmark, tmp_path):
        """Benchmark entity find_all operation."""
        from dataclasses import dataclass

        from parquetframe.entity import entity
        from parquetframe.entity.metadata import registry

        registry.clear()

        @entity(storage_path=tmp_path / "users", primary_key="user_id")
        @dataclass
        class User:
            user_id: int
            name: str

        # Prepopulate with data
        for i in range(100):
            User(i, f"User{i}").save()

        def find_all():
            return User.find_all()

        result = benchmark(find_all)
        assert len(result) == 100

        registry.clear()
