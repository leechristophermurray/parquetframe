#!/usr/bin/env python3
"""
Example: Using the Rust-accelerated workflow engine.

Demonstrates how to use the Rust workflow engine for high-performance
parallel execution of data processing workflows.

Phase 3.5-3.6: This example shows the API design.
Full functionality will be available once integration is complete.
"""

from parquetframe.workflow_rust import (
    RustWorkflowEngine,
    is_rust_workflow_available,
)


def example_basic_workflow():
    """Basic workflow execution example."""
    print("Example 1: Basic Workflow Execution")
    print("=" * 50)

    # Check if Rust workflow engine is available
    if not is_rust_workflow_available():
        print("⚠️  Rust workflow engine not yet available")
        print("   Using placeholder implementation")
        print()

    # Create workflow configuration
    workflow_config = {
        "name": "data_processing_pipeline",
        "version": "1.0",
        "steps": [
            {
                "name": "read_data",
                "type": "read",
                "config": {
                    "input": "data/input.parquet",
                    "columns": ["id", "value", "timestamp"],
                },
            },
            {
                "name": "filter_data",
                "type": "filter",
                "config": {"query": "value > 100"},
                "depends_on": ["read_data"],
            },
            {
                "name": "aggregate",
                "type": "aggregate",
                "config": {"groupby": ["id"], "agg": {"value": "sum"}},
                "depends_on": ["filter_data"],
            },
            {
                "name": "write_output",
                "type": "write",
                "config": {"output": "data/output.parquet"},
                "depends_on": ["aggregate"],
            },
        ],
    }

    # Execute workflow with Rust engine
    engine = RustWorkflowEngine(max_parallel=4)

    print(f"Executing workflow: {workflow_config['name']}")
    print("Parallel workers: 4")
    print()

    result = engine.execute_workflow(workflow_config)

    print("Workflow execution completed!")
    print(f"Status: {result['status']}")
    print(f"Execution time: {result['execution_time_ms']}ms")
    print(f"Steps executed: {result['steps_executed']}")
    print(f"Parallel workers: {result['parallel_workers']}")
    print()


def example_dag_analysis():
    """Example of DAG (dependency graph) creation."""
    print("Example 2: DAG Analysis")
    print("=" * 50)

    engine = RustWorkflowEngine()

    # Define steps with dependencies
    steps = [
        {"name": "step1", "type": "read"},
        {"name": "step2", "type": "filter", "depends_on": ["step1"]},
        {"name": "step3", "type": "transform", "depends_on": ["step1"]},
        {
            "name": "step4",
            "type": "merge",
            "depends_on": ["step2", "step3"],
        },
        {"name": "step5", "type": "write", "depends_on": ["step4"]},
    ]

    print("Analyzing workflow dependencies...")
    dag = engine.create_dag(steps)

    print(f"DAG created: {dag['dag_created']}")
    print(f"Number of steps: {dag['num_steps']}")
    print(f"Message: {dag['message']}")
    print()

    print("Execution plan:")
    print("  Level 1: step1 (can run immediately)")
    print("  Level 2: step2, step3 (can run in parallel)")
    print("  Level 3: step4 (waits for step2 and step3)")
    print("  Level 4: step5 (waits for step4)")
    print()


def example_step_execution():
    """Example of executing individual steps."""
    print("Example 3: Individual Step Execution")
    print("=" * 50)

    engine = RustWorkflowEngine()

    # Execute a single step
    config = {"input": "data.parquet", "columns": ["id", "value"]}
    context = {"variables": {"threshold": 100}}

    print("Executing single step...")
    result = engine.execute_step("read", config, context)

    print(f"Step status: {result['status']}")
    print(f"Step type: {result['step_type']}")
    print(f"Message: {result['message']}")
    print()


def example_performance_metrics():
    """Example of getting performance metrics."""
    print("Example 4: Performance Metrics")
    print("=" * 50)

    engine = RustWorkflowEngine()

    metrics = engine.get_metrics()

    print("Workflow Engine Metrics:")
    print(f"  Total workflows executed: {metrics['total_workflows']}")
    print(f"  Total steps executed: {metrics['total_steps']}")
    print(f"  Average execution time: {metrics['avg_execution_ms']:.2f}ms")
    print(f"  Average parallel speedup: {metrics['parallel_speedup']:.2f}x")
    print()


def example_parallel_execution():
    """Example showing parallel execution benefits."""
    print("Example 5: Parallel Execution")
    print("=" * 50)

    # Workflow with independent branches that can run in parallel
    workflow_config = {
        "name": "parallel_pipeline",
        "steps": [
            {"name": "read", "type": "read", "config": {"input": "data.parquet"}},
            # These three can run in parallel
            {
                "name": "process_a",
                "type": "filter",
                "config": {"query": "category == 'A'"},
                "depends_on": ["read"],
            },
            {
                "name": "process_b",
                "type": "filter",
                "config": {"query": "category == 'B'"},
                "depends_on": ["read"],
            },
            {
                "name": "process_c",
                "type": "filter",
                "config": {"query": "category == 'C'"},
                "depends_on": ["read"],
            },
            # Final merge waits for all three
            {
                "name": "merge",
                "type": "concat",
                "depends_on": ["process_a", "process_b", "process_c"],
            },
        ],
    }

    print("Workflow with parallel branches:")
    print("  read → [process_a, process_b, process_c] → merge")
    print()
    print("  process_a, process_b, and process_c can run in parallel!")
    print()

    engine = RustWorkflowEngine(max_parallel=3)
    result = engine.execute_workflow(workflow_config)

    print(f"Execution completed in {result['execution_time_ms']}ms")
    print(f"With {result['parallel_workers']} parallel workers")
    print()


def main():
    """Run all examples."""
    print("Rust Workflow Engine Examples")
    print("=" * 50)
    print()

    # Check availability
    if is_rust_workflow_available():
        print("✓ Rust workflow engine is available")
    else:
        print("⚠️  Rust workflow engine not yet fully integrated")
        print("   These examples show the API design")
    print()
    print()

    # Run examples
    example_basic_workflow()
    example_dag_analysis()
    example_step_execution()
    example_performance_metrics()
    example_parallel_execution()

    print("=" * 50)
    print("Examples completed!")
    print()
    print("Next steps:")
    print("1. Complete pf-workflow-core integration")
    print("2. Enable workflow_rust_available() to return True")
    print("3. Test with real workflows")
    print("4. Benchmark performance vs Python implementation")


if __name__ == "__main__":
    main()
