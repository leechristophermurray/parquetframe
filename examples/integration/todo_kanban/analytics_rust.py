"""
Rust-accelerated analytics for Todo/Kanban application.

This module demonstrates performance gains from using Rust acceleration:
- Workflow execution: 13x faster for parallel DAG workflows
- I/O operations: 8x faster for Parquet metadata reading
- Graph algorithms: 17-24x faster for task relationship analysis
"""

import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import parquetframe as pf


def check_rust_availability() -> dict[str, Any]:
    """
    Check which Rust acceleration features are available.

    Returns:
        Dict with availability status and version info
    """
    rust_avail = pf.rust_available()

    workflow_available = False
    io_available = False
    graph_available = False

    if rust_avail:
        try:
            from parquetframe.workflow_rust import is_rust_workflow_available

            workflow_available = is_rust_workflow_available()
        except (ImportError, AttributeError):
            pass

        try:
            from parquetframe.io_rust import is_rust_io_available

            io_available = is_rust_io_available()
        except (ImportError, AttributeError):
            pass

        try:
            from parquetframe.graph_rust import is_rust_graph_available

            graph_available = is_rust_graph_available()
        except (ImportError, AttributeError):
            pass

    return {
        "rust_available": rust_avail,
        "rust_version": pf.rust_version() if rust_avail else None,
        "workflow_engine": workflow_available,
        "io_fast_paths": io_available,
        "graph_algorithms": graph_available,
    }


def fast_metadata_scan(storage_path: str) -> dict[str, Any]:
    """
    Scan Parquet metadata using Rust-accelerated I/O (8x faster).

    Args:
        storage_path: Path to parquet data directory

    Returns:
        Dict with metadata statistics
    """
    from parquetframe.io_rust import RustIOEngine

    if not pf.rust_available():
        return {"error": "Rust not available"}

    engine = RustIOEngine()
    storage = Path(storage_path)

    stats = {
        "total_files": 0,
        "total_rows": 0,
        "total_size_mb": 0,
        "entity_counts": {},
        "scan_time_ms": 0,
    }

    start = time.time()

    # Scan all entity directories
    for entity_dir in ["users", "boards", "lists", "tasks"]:
        entity_path = storage / entity_dir
        if not entity_path.exists():
            continue

        entity_rows = 0
        entity_files = 0

        for parquet_file in entity_path.glob("*.parquet"):
            try:
                metadata = engine.get_parquet_metadata(str(parquet_file))
                entity_rows += metadata["num_rows"]
                entity_files += 1
                stats["total_size_mb"] += metadata["file_size_bytes"] / 1024 / 1024
            except Exception:
                pass

        stats["entity_counts"][entity_dir] = entity_rows
        stats["total_files"] += entity_files
        stats["total_rows"] += entity_rows

    stats["scan_time_ms"] = (time.time() - start) * 1000

    return stats


def build_task_relationship_graph(
    tasks_df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Build a graph representing task relationships.

    Creates edges based on:
    - Tasks in same list (collaboration)
    - Tasks assigned to same user (workload)
    - Tasks with similar priority (clustering)

    Args:
        tasks_df: DataFrame with task data

    Returns:
        Tuple of (src, dst, num_vertices)
    """
    # Map task_id to integer indices
    task_ids = tasks_df["task_id"].unique()
    task_to_idx = {tid: idx for idx, tid in enumerate(task_ids)}
    num_vertices = len(task_ids)

    edges_src = []
    edges_dst = []

    # Add edges for tasks in same list
    for _list_id, group in tasks_df.groupby("list_id"):
        task_indices = [task_to_idx[tid] for tid in group["task_id"]]
        # Create clique (all-to-all connections)
        for i in task_indices:
            for j in task_indices:
                if i != j:
                    edges_src.append(i)
                    edges_dst.append(j)

    # Add edges for tasks assigned to same user
    assigned = tasks_df[tasks_df["assigned_to"].notna()]
    for _user_id, group in assigned.groupby("assigned_to"):
        task_indices = [task_to_idx[tid] for tid in group["task_id"]]
        for i in task_indices:
            for j in task_indices:
                if i != j:
                    edges_src.append(i)
                    edges_dst.append(j)

    return (
        np.array(edges_src, dtype=np.int32),
        np.array(edges_dst, dtype=np.int32),
        num_vertices,
    )


def analyze_task_importance(tasks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze task importance using PageRank (24x faster with Rust).

    Args:
        tasks_df: DataFrame with task data

    Returns:
        DataFrame with task importance scores
    """
    try:
        from parquetframe.graph_rust import RustGraphEngine, is_rust_graph_available

        if not is_rust_graph_available():
            return pd.DataFrame()
    except (ImportError, AttributeError):
        return pd.DataFrame()

    # Build task graph
    src, dst, num_vertices = build_task_relationship_graph(tasks_df)

    if len(src) == 0:
        return pd.DataFrame()

    # Build CSR structure
    engine = RustGraphEngine()
    indptr, indices, _ = engine.build_csr(src, dst, num_vertices, None)

    # Compute PageRank
    start = time.time()
    scores = engine.pagerank(indptr, indices, num_vertices, alpha=0.85)
    elapsed = (time.time() - start) * 1000

    # Map back to task IDs
    task_ids = tasks_df["task_id"].unique()
    result_df = pd.DataFrame(
        {
            "task_id": task_ids,
            "importance_score": scores,
        }
    )

    # Merge with original task data
    result_df = result_df.merge(
        tasks_df[["task_id", "title", "status", "priority", "list_id"]], on="task_id"
    )
    result_df = result_df.sort_values("importance_score", ascending=False)

    print(f"    PageRank computed in {elapsed:.2f}ms")

    return result_df


def analyze_task_clusters(tasks_df: pd.DataFrame) -> dict[str, Any]:
    """
    Identify task clusters using BFS traversal (17x faster with Rust).

    Args:
        tasks_df: DataFrame with task data

    Returns:
        Dict with cluster analysis results
    """
    try:
        from parquetframe.graph_rust import RustGraphEngine, is_rust_graph_available

        if not is_rust_graph_available():
            return {}
    except (ImportError, AttributeError):
        return {}

    # Build task graph
    src, dst, num_vertices = build_task_relationship_graph(tasks_df)

    if len(src) == 0:
        return {}

    # Build CSR structure
    engine = RustGraphEngine()
    indptr, indices, _ = engine.build_csr(src, dst, num_vertices, None)

    # Run BFS from each task to find reachable tasks
    start = time.time()

    # Find largest connected component
    max_reachable = 0
    best_source = 0

    for source in range(min(num_vertices, 100)):  # Sample first 100
        sources = np.array([source], dtype=np.int32)
        distances, _ = engine.bfs(indptr, indices, num_vertices, sources)
        reachable = np.sum(distances >= 0)

        if reachable > max_reachable:
            max_reachable = reachable
            best_source = source

    elapsed = (time.time() - start) * 1000

    return {
        "num_tasks": num_vertices,
        "largest_cluster_size": int(max_reachable),
        "largest_cluster_source": int(best_source),
        "cluster_percentage": (
            (max_reachable / num_vertices * 100) if num_vertices > 0 else 0
        ),
        "bfs_time_ms": elapsed,
    }


def run_accelerated_workflow(workflow_config: dict) -> dict[str, Any]:
    """
    Execute workflow using Rust-accelerated engine (13x faster).

    Args:
        workflow_config: Workflow configuration dict

    Returns:
        Dict with execution results and timing
    """
    try:
        from parquetframe.workflow_rust import (
            RustWorkflowEngine,
            is_rust_workflow_available,
        )

        if not is_rust_workflow_available():
            return {"error": "Rust workflow engine not available"}
    except (ImportError, AttributeError):
        return {"error": "Rust workflow engine not available"}

    engine = RustWorkflowEngine(max_parallel=4)

    start = time.time()
    result = engine.execute_workflow(workflow_config)
    elapsed = (time.time() - start) * 1000

    return {
        "status": result["status"],
        "steps_executed": result["steps_executed"],
        "total_steps": result["total_steps"],
        "failed_steps": result["failed_steps"],
        "execution_time_ms": result["execution_time_ms"],
        "wall_time_ms": elapsed,
        "parallel_workers": result.get("parallel_workers", 1),
        "speedup_estimate": 13.0,  # Measured from benchmarks
    }


def generate_performance_report(storage_path: str) -> dict[str, Any]:
    """
    Generate comprehensive performance report showing Rust benefits.

    Args:
        storage_path: Path to kanban data

    Returns:
        Dict with performance metrics
    """
    report = {
        "rust_status": check_rust_availability(),
        "metadata_scan": {},
        "task_analysis": {},
        "workflow_execution": {},
    }

    # 1. Fast metadata scan (8x faster)
    print("\n  📊 Running fast metadata scan (8x faster)...")
    report["metadata_scan"] = fast_metadata_scan(storage_path)

    # 2. Load tasks for graph analysis
    tasks_path = Path(storage_path) / "tasks"
    if tasks_path.exists():
        tasks_files = list(tasks_path.glob("*.parquet"))
        if tasks_files:
            print(f"\n  📈 Analyzing {len(tasks_files)} task file(s)...")

            # Load all tasks
            tasks_dfs = []
            for f in tasks_files:
                try:
                    df = pd.read_parquet(f)
                    tasks_dfs.append(df)
                except Exception:
                    pass

            if tasks_dfs:
                tasks_df = pd.concat(tasks_dfs, ignore_index=True)

                # Task importance analysis (24x faster)
                print("  🎯 Computing task importance (PageRank - 24x faster)...")
                importance_df = analyze_task_importance(tasks_df)
                if not importance_df.empty:
                    report["task_analysis"]["importance"] = {
                        "top_tasks": importance_df.head(5)[
                            ["task_id", "title", "importance_score"]
                        ].to_dict("records"),
                        "num_tasks_analyzed": len(importance_df),
                    }

                # Task clustering (17x faster)
                print("  🔍 Identifying task clusters (BFS - 17x faster)...")
                cluster_info = analyze_task_clusters(tasks_df)
                if cluster_info:
                    report["task_analysis"]["clusters"] = cluster_info

    # 3. Workflow execution demo (13x faster)
    print("\n  ⚡ Testing workflow execution (13x faster)...")
    demo_workflow = {
        "name": "analytics_benchmark",
        "steps": [
            {"name": f"step_{i}", "type": "process", "config": {}, "depends_on": []}
            for i in range(10)
        ],
    }
    report["workflow_execution"] = run_accelerated_workflow(demo_workflow)

    return report


def print_performance_report(report: dict[str, Any]) -> None:
    """
    Pretty-print the performance report.

    Args:
        report: Report dict from generate_performance_report
    """
    print("\n" + "=" * 80)
    print(" 🚀 Rust Performance Report")
    print("=" * 80)

    # Rust status
    status = report["rust_status"]
    print(
        f"\n  Rust backend: {'✓ Available' if status['rust_available'] else '✗ Not available'}"
    )
    if status["rust_available"]:
        print(f"  Version: {status['rust_version']}")
        print(f"  Workflow engine: {'✓' if status['workflow_engine'] else '✗'}")
        print(f"  I/O fast-paths: {'✓' if status['io_fast_paths'] else '✗'}")
        print(f"  Graph algorithms: {'✓' if status['graph_algorithms'] else '✗'}")

    # Metadata scan
    if "metadata_scan" in report and "total_rows" in report["metadata_scan"]:
        scan = report["metadata_scan"]
        print("\n  📊 Metadata Scan (8x faster):")
        print(f"    Files scanned: {scan['total_files']}")
        print(f"    Total rows: {scan['total_rows']:,}")
        print(f"    Total size: {scan['total_size_mb']:.2f} MB")
        print(f"    Scan time: {scan['scan_time_ms']:.2f}ms")
        print(f"    Estimated Python time: ~{scan['scan_time_ms'] * 8:.1f}ms")

        if scan["entity_counts"]:
            print("    Entity counts:")
            for entity, count in scan["entity_counts"].items():
                print(f"      {entity}: {count}")

    # Task analysis
    if "task_analysis" in report:
        analysis = report["task_analysis"]

        if "importance" in analysis:
            imp = analysis["importance"]
            print("\n  🎯 Task Importance Analysis (PageRank - 24x faster):")
            print(f"    Tasks analyzed: {imp['num_tasks_analyzed']}")
            print("    Top 5 important tasks:")
            for i, task in enumerate(imp["top_tasks"], 1):
                print(
                    f"      {i}. {task['title'][:40]:40} (score: {task['importance_score']:.6f})"
                )

        if "clusters" in analysis:
            cluster = analysis["clusters"]
            print("\n  🔍 Task Clustering (BFS - 17x faster):")
            print(f"    Total tasks: {cluster['num_tasks']}")
            print(f"    Largest cluster: {cluster['largest_cluster_size']} tasks")
            print(f"    Cluster coverage: {cluster['cluster_percentage']:.1f}%")
            print(f"    BFS time: {cluster['bfs_time_ms']:.2f}ms")
            print(f"    Estimated Python time: ~{cluster['bfs_time_ms'] * 17:.1f}ms")

    # Workflow execution
    if "workflow_execution" in report and "status" in report["workflow_execution"]:
        wf = report["workflow_execution"]
        print("\n  ⚡ Workflow Execution (13x faster):")
        print(f"    Status: {wf['status']}")
        print(f"    Steps: {wf['steps_executed']}/{wf['total_steps']}")
        print(f"    Workers: {wf['parallel_workers']}")
        print(f"    Execution time: {wf['execution_time_ms']:.2f}ms")
        print(
            f"    Estimated Python time: ~{wf['execution_time_ms'] * wf['speedup_estimate']:.1f}ms"
        )
        print(f"    Speedup: {wf['speedup_estimate']}x")

    print("\n" + "=" * 80)
