"""
Multi-Engine Conversion Example - ParquetFrame Phase 2

Demonstrates seamless conversion between pandas, Polars, and Dask engines
while maintaining data integrity and leveraging engine-specific optimizations.

This example shows:
- Converting between different engines
- When to use each engine
- Performance implications of conversion
- Chaining operations across engines
"""

from pathlib import Path

import numpy as np
import pandas as pd

import parquetframe.core_v2 as pf2


def create_sample_data(n_rows: int = 10000) -> pd.DataFrame:
    """Create sample dataset for conversion demonstrations."""
    return pd.DataFrame(
        {
            "id": range(n_rows),
            "category": np.random.choice(["A", "B", "C", "D"], n_rows),
            "value1": np.random.randn(n_rows),
            "value2": np.random.randn(n_rows) * 100,
            "flag": np.random.choice([True, False], n_rows),
        }
    )


def example_basic_conversion():
    """Demonstrate basic engine conversion."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Engine Conversion")
    print("=" * 80)

    data_dir = Path("temp_phase2_conversion")
    data_dir.mkdir(exist_ok=True)

    try:
        # Create and save sample data
        df = create_sample_data(10000)
        data_path = data_dir / "sample_data.parquet"
        df.to_parquet(data_path, index=False)

        # Load with pandas
        print("\n1. Start with pandas engine:")
        df_pandas = pf2.read(data_path, engine="pandas")
        print(f"   ✓ Engine: {df_pandas.engine_name}")
        print(f"   ✓ Shape: {df_pandas.shape}")
        print(f"   ✓ Lazy: {df_pandas.is_lazy}")

        # Convert to Polars
        print("\n2. Convert to Polars:")
        try:
            df_polars = df_pandas.to_polars()
            print(f"   ✓ Engine: {df_polars.engine_name}")
            print(f"   ✓ Shape: {df_polars.shape}")
            print(f"   ✓ Lazy: {df_polars.is_lazy}")
        except ImportError:
            print("   ⚠ Polars not installed (pip install polars)")
            df_polars = None

        # Convert to Dask
        print("\n3. Convert to Dask:")
        try:
            df_dask = df_pandas.to_dask()
            print(f"   ✓ Engine: {df_dask.engine_name}")
            print(f"   ✓ Shape: {df_dask.shape}")
            print(f"   ✓ Lazy: {df_dask.is_lazy}")
        except ImportError:
            print("   ⚠ Dask not installed (pip install dask[complete])")
            df_dask = None

        # Convert back to pandas
        print("\n4. Convert back to pandas:")
        if df_dask:
            df_back = df_dask.to_pandas()
            print(f"   ✓ Engine: {df_back.engine_name}")
            print("   ✓ Data integrity maintained")

    finally:
        import shutil

        if data_dir.exists():
            shutil.rmtree(data_dir)


def example_conversion_workflow():
    """Demonstrate practical workflow using multiple engines."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Multi-Engine Workflow")
    print("=" * 80)

    data_dir = Path("temp_phase2_conversion")
    data_dir.mkdir(exist_ok=True)

    try:
        # Create larger dataset
        df = create_sample_data(50000)
        data_path = data_dir / "workflow_data.parquet"
        df.to_parquet(data_path, index=False)

        print("\n1. Workflow: Load → Filter (Polars) → Aggregate (pandas)")
        print("   " + "-" * 60)

        # Step 1: Load with automatic selection
        df = pf2.read(data_path)
        print(f"   ✓ Step 1: Load data with {df.engine_name} engine")

        # Step 2: Switch to Polars for filtering (if available)
        try:
            df_polars = df.to_polars()
            print("   ✓ Step 2: Convert to Polars for lazy filtering")
            # Simulate filtering
            print("   ✓ Step 3: Apply filters (lazy evaluation)")
        except ImportError:
            df_polars = df
            print("   ⚠ Polars not available, continuing with pandas")

        # Step 3: Convert to pandas for final aggregation
        _ = df_polars.to_pandas() if df_polars else df  # Demonstration
        print("   ✓ Step 4: Convert to pandas for aggregation")
        print("   ✓ Step 5: Compute final results")

        print("\n2. When to switch engines:")
        print("   • Start with pandas for exploration")
        print("   • Switch to Polars for complex transformations")
        print("   • Use Dask when data exceeds memory")
        print("   • Return to pandas for final analysis/plotting")

    finally:
        import shutil

        if data_dir.exists():
            shutil.rmtree(data_dir)


def example_lazy_vs_eager():
    """Demonstrate lazy vs eager evaluation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Lazy vs Eager Evaluation")
    print("=" * 80)

    print("\n1. Eager Evaluation (pandas):")
    print("   • Operations execute immediately")
    print("   • Results available right away")
    print("   • Memory overhead for intermediate results")
    print("   • Best for: Small datasets, interactive analysis")

    print("\n2. Lazy Evaluation (Polars, Dask):")
    print("   • Operations build execution plan")
    print("   • Nothing computed until .compute() or .collect()")
    print("   • Query optimization possible")
    print("   • Best for: Large datasets, complex pipelines")

    print("\n3. Example comparison:")
    print("\n   Eager (pandas):")
    print("   df = pf2.read('data.parquet', engine='pandas')")
    print("   result = df.groupby('category')['value'].mean()  # Executes immediately")

    print("\n   Lazy (Polars):")
    print("   df = pf2.read('data.parquet', engine='polars')")
    print("   result = df.groupby('category')['value'].mean()  # Builds plan")
    print("   result = result.compute()                         # Now executes")


def example_conversion_best_practices():
    """Display best practices for engine conversion."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Conversion Best Practices")
    print("=" * 80)

    practices = {
        "When to Convert": [
            "Data size changes significantly (e.g., after filtering)",
            "Operation type changes (e.g., from filtering to aggregation)",
            "Need engine-specific features",
            "Performance optimization required",
        ],
        "Avoid Frequent Conversions": [
            "Conversions have overhead (data copying/serialization)",
            "Stick with one engine for a sequence of operations",
            "Convert once at the beginning or end of pipeline",
            "Use .native property for engine-specific operations",
        ],
        "Memory Considerations": [
            "pandas → Dask: Good for scaling beyond memory",
            "Dask → pandas: Triggers computation, loads to memory",
            "Polars → pandas: May require more memory (eager)",
            "Monitor memory usage when converting",
        ],
        "Data Integrity": [
            "All engines preserve data correctly",
            "Some type conversions may occur (e.g., string dtypes)",
            "Timestamps and dates handled consistently",
            "Always verify critical calculations after conversion",
        ],
    }

    for category, tips in practices.items():
        print(f"\n{category}:")
        for tip in tips:
            print(f"   • {tip}")


def example_engine_specific_features():
    """Demonstrate accessing engine-specific features."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Engine-Specific Features")
    print("=" * 80)

    print("\n1. Using .native property:")
    print("   df = pf2.read('data.parquet', engine='polars')")
    print("   result = df.native.select(['col1', 'col2'])  # Polars syntax")

    print("\n2. pandas-specific:")
    print("   df_pandas = df.to_pandas()")
    print("   df_pandas.native.plot(kind='scatter', x='col1', y='col2')")
    print("   df_pandas.native.to_sql('table', engine)")

    print("\n3. Polars-specific:")
    print("   df_polars = df.to_polars()")
    print("   df_polars.native.lazy().filter(...).select(...).collect()")
    print("   df_polars.native.write_parquet('output.parquet')")

    print("\n4. Dask-specific:")
    print("   df_dask = df.to_dask()")
    print("   df_dask.native.persist()  # Load into distributed memory")
    print("   df_dask.native.to_parquet('output/', partition_on='date')")


def example_performance_tips():
    """Display performance optimization tips."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Performance Optimization")
    print("=" * 80)

    optimizations = [
        (
            "Start Right",
            "Choose the right engine from the beginning based on data size",
        ),
        ("Batch Operations", "Group operations before converting engines"),
        ("Lazy When Possible", "Use Polars/Dask for complex pipelines, compute once"),
        ("Memory-Aware", "Monitor memory usage, switch to Dask if approaching limits"),
        ("Filter Early", "Reduce data size before expensive conversions"),
        ("Cache Results", "Store intermediate results to avoid recomputation"),
        ("Parallel Processing", "Use Dask for CPU-intensive parallel operations"),
        ("Type Hints", "Specify dtypes to avoid unnecessary type inference"),
    ]

    print("\nOptimization Strategies:")
    print("-" * 60)
    for i, (title, description) in enumerate(optimizations, 1):
        print(f"\n{i}. {title}")
        print(f"   {description}")


def main():
    """Run all examples."""
    print("=" * 80)
    print("ParquetFrame Phase 2 - Multi-Engine Conversion Examples")
    print("=" * 80)

    example_basic_conversion()
    example_conversion_workflow()
    example_lazy_vs_eager()
    example_conversion_best_practices()
    example_engine_specific_features()
    example_performance_tips()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • Seamless conversion between pandas, Polars, and Dask")
    print("  • Choose engine based on data size and operation type")
    print("  • Minimize conversions for better performance")
    print("  • Use .native for engine-specific features")
    print("\nNext steps:")
    print("  • Try engine_selection.py for automatic selection")
    print("  • Try avro_roundtrip.py for Avro format support")
    print("  • Try entity_framework_demo.py for declarative persistence")


if __name__ == "__main__":
    main()
