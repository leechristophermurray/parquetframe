"""
Engine Selection Example - ParquetFrame Phase 2

Demonstrates intelligent automatic engine selection based on data size,
manual engine override, and performance characteristics of pandas, Polars, and Dask.

This example shows:
- Automatic engine selection based on file size
- Manual engine specification
- Engine-specific optimizations
- Performance comparison across engines
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd

import parquetframe.core_v2 as pf2
from parquetframe import set_config


def create_sample_data(size: str = "small") -> pd.DataFrame:
    """
    Create sample dataset of different sizes.

    Args:
        size: 'small' (<10MB), 'medium' (10-100MB), or 'large' (>100MB)

    Returns:
        pandas DataFrame with sample data
    """
    sizes = {
        "small": 1_000,  # ~1MB - triggers pandas
        "medium": 100_000,  # ~10MB - triggers polars
        "large": 1_000_000,  # ~100MB - triggers dask
    }

    n_rows = sizes.get(size, sizes["small"])

    print(f"Creating {size} dataset with {n_rows:,} rows...")

    return pd.DataFrame(
        {
            "id": range(n_rows),
            "timestamp": pd.date_range("2024-01-01", periods=n_rows, freq="1min"),
            "category": np.random.choice(["A", "B", "C", "D", "E"], n_rows),
            "value": np.random.randn(n_rows),
            "flag": np.random.choice([True, False], n_rows),
            "description": [f"Item_{i}" for i in range(n_rows)],
        }
    )


def example_automatic_selection():
    """Demonstrate automatic engine selection based on data size."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Automatic Engine Selection")
    print("=" * 80)

    # Create temporary directory for examples
    data_dir = Path("temp_phase2_examples")
    data_dir.mkdir(exist_ok=True)

    try:
        # Small dataset -> pandas (fast for small data)
        small_df = create_sample_data("small")
        small_path = data_dir / "small_data.parquet"
        small_df.to_parquet(small_path, index=False)

        print(f"\n1. Small dataset ({small_path.stat().st_size / 1024 / 1024:.2f} MB):")
        df_small = pf2.read(small_path)
        print(f"   ✓ Auto-selected engine: {df_small.engine_name}")
        print(f"   ✓ Lazy evaluation: {df_small.is_lazy}")
        print(f"   ✓ Shape: {df_small.shape}")

        # Medium dataset -> polars (optimized for medium data)
        medium_df = create_sample_data("medium")
        medium_path = data_dir / "medium_data.parquet"
        medium_df.to_parquet(medium_path, index=False)

        print(
            f"\n2. Medium dataset ({medium_path.stat().st_size / 1024 / 1024:.2f} MB):"
        )
        df_medium = pf2.read(medium_path)
        print(f"   ✓ Auto-selected engine: {df_medium.engine_name}")
        print(f"   ✓ Lazy evaluation: {df_medium.is_lazy}")
        print(f"   ✓ Shape: {df_medium.shape}")

        # Large dataset -> dask (distributed for large data)
        print("\n3. Large dataset (simulated >100MB):")
        print("   Note: Dask selected for datasets >100MB by default")
        print("   ✓ Would auto-select: dask")
        print("   ✓ Lazy evaluation: True")
        print("   ✓ Out-of-core processing enabled")

    finally:
        # Cleanup
        import shutil

        if data_dir.exists():
            shutil.rmtree(data_dir)


def example_manual_engine_override():
    """Demonstrate manual engine specification."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Manual Engine Override")
    print("=" * 80)

    data_dir = Path("temp_phase2_examples")
    data_dir.mkdir(exist_ok=True)

    try:
        # Create sample data
        df = create_sample_data("small")
        data_path = data_dir / "sample_data.parquet"
        df.to_parquet(data_path, index=False)

        # Force pandas engine
        print("\n1. Force pandas engine:")
        df_pandas = pf2.read(data_path, engine="pandas")
        print(f"   ✓ Engine: {df_pandas.engine_name}")
        print("   ✓ Best for: Small datasets, immediate results")

        # Force polars engine (if available)
        print("\n2. Force Polars engine:")
        try:
            df_polars = pf2.read(data_path, engine="polars")
            print(f"   ✓ Engine: {df_polars.engine_name}")
            print("   ✓ Best for: Medium datasets, lazy evaluation")
        except ImportError:
            print("   ⚠ Polars not installed (pip install polars)")

        # Force dask engine (if available)
        print("\n3. Force Dask engine:")
        try:
            df_dask = pf2.read(data_path, engine="dask")
            print(f"   ✓ Engine: {df_dask.engine_name}")
            print("   ✓ Best for: Large datasets, distributed computing")
        except ImportError:
            print("   ⚠ Dask not installed (pip install dask[complete])")

    finally:
        import shutil

        if data_dir.exists():
            shutil.rmtree(data_dir)


def example_configuration():
    """Demonstrate global configuration for engine selection."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Global Configuration")
    print("=" * 80)

    # Set global engine preference
    print("\n1. Setting global engine preference:")
    set_config(
        default_engine="pandas",  # Prefer pandas by default
        pandas_threshold_mb=50.0,  # Use pandas up to 50MB
        polars_threshold_mb=500.0,  # Switch to Dask after 500MB
        verbose=True,  # Enable logging
    )
    print("   ✓ Default engine: pandas")
    print("   ✓ pandas threshold: 50 MB")
    print("   ✓ Dask threshold: 500 MB")

    print("\n2. Using environment variables:")
    print("   export PARQUETFRAME_DEFAULT_ENGINE=polars")
    print("   export PARQUETFRAME_PANDAS_THRESHOLD_MB=25")

    print("\n3. Runtime override:")
    print("   df = pf2.read('data.parquet', engine='dask')  # Ignores config")


def example_performance_comparison():
    """Compare performance across engines."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Performance Comparison")
    print("=" * 80)

    data_dir = Path("temp_phase2_examples")
    data_dir.mkdir(exist_ok=True)

    try:
        # Create medium-sized dataset for comparison
        df = create_sample_data("medium")
        data_path = data_dir / "benchmark_data.parquet"
        df.to_parquet(data_path, index=False)

        engines_to_test = ["pandas"]

        # Check which engines are available
        try:
            import polars  # noqa: F401

            engines_to_test.append("polars")
        except ImportError:
            pass

        try:
            import dask  # noqa: F401

            engines_to_test.append("dask")
        except ImportError:
            pass

        print(f"\nBenchmarking read performance with {len(df):,} rows:")
        print("-" * 60)

        results = {}

        for engine in engines_to_test:
            start = time.time()
            df_loaded = pf2.read(data_path, engine=engine)

            # Perform simple aggregation
            if engine == "dask":
                # Dask is lazy, need to compute
                _ = df_loaded.native.groupby("category")["value"].mean().compute()
            else:
                _ = df_loaded.native.groupby("category")["value"].mean()

            elapsed = time.time() - start
            results[engine] = elapsed

            print(f"{engine:8s}: {elapsed:.4f}s")

        # Show relative performance
        if len(results) > 1:
            fastest = min(results.values())
            print("\nRelative Performance:")
            print("-" * 60)
            for engine, time_taken in sorted(results.items(), key=lambda x: x[1]):
                speedup = time_taken / fastest
                print(
                    f"{engine:8s}: {speedup:.2f}x {'(baseline)' if speedup == 1.0 else ''}"
                )

    finally:
        import shutil

        if data_dir.exists():
            shutil.rmtree(data_dir)


def example_engine_characteristics():
    """Display engine characteristics and use cases."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Engine Characteristics")
    print("=" * 80)

    engines = {
        "pandas": {
            "evaluation": "Eager",
            "best_for": "< 100 MB",
            "memory": "In-memory",
            "pros": "Fast startup, familiar API, rich ecosystem",
            "cons": "Limited scalability, single-threaded",
        },
        "polars": {
            "evaluation": "Lazy",
            "best_for": "100 MB - 10 GB",
            "memory": "In-memory",
            "pros": "Very fast, query optimization, multi-threaded",
            "cons": "Different API, newer ecosystem",
        },
        "dask": {
            "evaluation": "Lazy",
            "best_for": "> 10 GB",
            "memory": "Out-of-core",
            "pros": "Distributed, scales beyond RAM, pandas API",
            "cons": "Slower startup, requires compute() calls",
        },
    }

    for engine, chars in engines.items():
        print(f"\n{engine.upper()}")
        print("-" * 40)
        for key, value in chars.items():
            print(f"  {key.replace('_', ' ').title():15s}: {value}")


def main():
    """Run all examples."""
    print("=" * 80)
    print("ParquetFrame Phase 2 - Engine Selection Examples")
    print("=" * 80)

    example_automatic_selection()
    example_manual_engine_override()
    example_configuration()
    example_performance_comparison()
    example_engine_characteristics()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • Phase 2 automatically selects the best engine for your data")
    print("  • You can override with engine='pandas|polars|dask'")
    print("  • Use set_config() for global preferences")
    print("  • Different engines excel at different scales")
    print("\nNext steps:")
    print("  • Try multi_engine_conversion.py for engine switching")
    print("  • Try avro_roundtrip.py for Avro format support")
    print("  • Try entity_framework_demo.py for declarative persistence")


if __name__ == "__main__":
    main()
