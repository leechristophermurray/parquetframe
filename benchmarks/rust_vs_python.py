"""Benchmark Rust vs Python implementations."""

import time
from collections.abc import Callable

import pandas as pd

from parquetframe.backends.rust_backend import get_rust_version, is_rust_available


def benchmark(func: Callable, name: str, iterations: int = 100) -> dict:
    """Benchmark a function."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append(time.perf_counter() - start)
    return {"name": name, "mean": sum(times) / len(times), "iterations": iterations}


def run_benchmarks() -> pd.DataFrame:
    """Run benchmarks."""
    print("🚀 ParquetFrame Benchmarks")
    print(f"Rust available: {is_rust_available()}")
    if is_rust_available():
        print(f"Version: {get_rust_version()}")
    print("\n📊 Phase 0: Framework ready, benchmarks coming in Phase 1+")
    return pd.DataFrame()


if __name__ == "__main__":
    run_benchmarks()
