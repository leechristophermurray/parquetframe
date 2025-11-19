"""
Benchmarks for TIME (time-series) operations.

Compares ParquetFrame's Rust-accelerated time-series operations
against pure pandas implementations.
"""

import time

import numpy as np
import pandas as pd

from parquetframe.time import asof_join as pf_asof_join
from parquetframe.time import resample as pf_resample
from parquetframe.time import rolling_window as pf_rolling


def benchmark_resample(n_rows: int = 100_000) -> dict[str, float]:
    """Benchmark resampling operations."""
    # Create sample data
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n_rows, freq="1s"),
            "value": np.random.randn(n_rows),
        }
    )

    # Pandas implementation
    start = time.time()
    _ = df.set_index("timestamp").resample("1min").mean()
    pandas_time = time.time() - start

    # ParquetFrame implementation
    start = time.time()
    _ = pf_resample(df, time_column="timestamp", freq="1min", agg="mean")
    pf_time = time.time() - start

    return {
        "operation": "resample",
        "rows": n_rows,
        "pandas_ms": pandas_time * 1000,
        "parquetframe_ms": pf_time * 1000,
        "speedup": pandas_time / pf_time,
    }


def benchmark_rolling(n_rows: int = 100_000, window: int = 100) -> dict[str, float]:
    """Benchmark rolling window operations."""
    # Create sample data
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n_rows, freq="1s"),
            "value": np.random.randn(n_rows),
        }
    )

    # Pandas implementation
    start = time.time()
    _ = df.set_index("timestamp")["value"].rolling(window).mean()
    pandas_time = time.time() - start

    # ParquetFrame implementation
    start = time.time()
    _ = pf_rolling(df, time_column="timestamp", window_size=window, agg="mean")
    pf_time = time.time() - start

    return {
        "operation": "rolling_mean",
        "rows": n_rows,
        "window": window,
        "pandas_ms": pandas_time * 1000,
        "parquetframe_ms": pf_time * 1000,
        "speedup": pandas_time / pf_time,
    }


def benchmark_asof_join(
    left_rows: int = 10_000, right_rows: int = 100_000
) -> dict[str, float]:
    """Benchmark as-of join operations."""
    # Create sample data
    left_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=left_rows, freq="10s"),
            "order_id": range(left_rows),
        }
    )

    right_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=right_rows, freq="1s"),
            "price": np.random.uniform(100, 200, right_rows),
        }
    )

    # Pandas implementation
    start = time.time()
    _ = pd.merge_asof(left_df, right_df, on="timestamp", direction="backward")
    pandas_time = time.time() - start

    # ParquetFrame implementation
    start = time.time()
    _ = pf_asof_join(left_df, right_df, on="timestamp", strategy="backward")
    pf_time = time.time() - start

    return {
        "operation": "asof_join",
        "left_rows": left_rows,
        "right_rows": right_rows,
        "pandas_ms": pandas_time * 1000,
        "parquetframe_ms": pf_time * 1000,
        "speedup": pandas_time / pf_time,
    }


def run_all_benchmarks() -> list[dict[str, float]]:
    """Run all TIME benchmarks and return results."""
    results = []

    print("Running TIME benchmarks...")
    print("=" * 80)

    # Resample benchmarks
    for n_rows in [10_000, 100_000, 1_000_000]:
        print(f"\nResampling {n_rows:,} rows...")
        result = benchmark_resample(n_rows)
        results.append(result)
        print(f"  pandas: {result['pandas_ms']:.2f}ms")
        print(f"  parquetframe: {result['parquetframe_ms']:.2f}ms")
        print(f"  speedup: {result['speedup']:.2f}x")

    # Rolling window benchmarks
    for n_rows, window in [(100_000, 50), (100_000, 100), (1_000_000, 100)]:
        print(f"\nRolling mean {n_rows:,} rows, window={window}...")
        result = benchmark_rolling(n_rows, window)
        results.append(result)
        print(f"  pandas: {result['pandas_ms']:.2f}ms")
        print(f"  parquetframe: {result['parquetframe_ms']:.2f}ms")
        print(f"  speedup: {result['speedup']:.2f}x")

    # As-of join benchmarks
    for left, right in [(1_000, 10_000), (10_000, 100_000)]:
        print(f"\nAs-of join {left:,} x {right:,} rows...")
        result = benchmark_asof_join(left, right)
        results.append(result)
        print(f"  pandas: {result['pandas_ms']:.2f}ms")
        print(f"  parquetframe: {result['parquetframe_ms']:.2f}ms")
        print(f"  speedup: {result['speedup']:.2f}x")

    print("\n" + "=" * 80)
    print(
        f"Benchmarks complete! Average speedup: {np.mean([r['speedup'] for r in results]):.2f}x"
    )

    return results


if __name__ == "__main__":
    results = run_all_benchmarks()

    # Save results to CSV
    import pandas as pd

    results_df = pd.DataFrame(results)
    results_df.to_csv("time_benchmark_results.csv", index=False)
    print("\nResults saved to time_benchmark_results.csv")
