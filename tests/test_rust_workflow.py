"""
Integration tests for Rust workflow engine bindings.

Tests the Python-Rust interface for the workflow engine.
"""

import pytest


def test_rust_module_available():
    """Test that the Rust backend module can be imported."""
    try:
        import _rustic

        assert _rustic.rust_available()
    except ImportError:
        pytest.skip("Rust backend not available")


def test_workflow_functions_exist():
    """Test that workflow functions are registered in the Rust module."""
    try:
        import _rustic

        # Check that workflow functions exist
        assert hasattr(_rustic, "execute_step")
        assert hasattr(_rustic, "create_dag")
        assert hasattr(_rustic, "execute_workflow")
        assert hasattr(_rustic, "workflow_rust_available")
        assert hasattr(_rustic, "workflow_metrics")
    except ImportError:
        pytest.skip("Rust backend not available")


def test_workflow_rust_not_yet_available():
    """Test that workflow engine reports not available (placeholder implementation)."""
    try:
        import _rustic

        # Should return False until full integration is complete
        assert not _rustic.workflow_rust_available()
    except ImportError:
        pytest.skip("Rust backend not available")


def test_execute_step_placeholder():
    """Test execute_step function with placeholder implementation."""
    try:
        import _rustic

        config = {"input": "data.parquet"}
        context = {"variables": {}}

        result = _rustic.execute_step("read", config, context)

        assert result is not None
        assert result["status"] == "executed"
        assert result["step_type"] == "read"
        assert "message" in result
    except ImportError:
        pytest.skip("Rust backend not available")


def test_create_dag_placeholder():
    """Test create_dag function with placeholder implementation."""
    try:
        import _rustic

        steps = [
            {"name": "step1", "type": "read"},
            {"name": "step2", "type": "filter", "depends_on": ["step1"]},
        ]

        result = _rustic.create_dag(steps)

        assert result is not None
        assert result["dag_created"] is True
        assert result["num_steps"] == 2
    except ImportError:
        pytest.skip("Rust backend not available")


def test_execute_workflow_placeholder():
    """Test execute_workflow function with placeholder implementation."""
    try:
        import _rustic

        workflow_config = {
            "name": "test_workflow",
            "steps": [
                {"name": "step1", "type": "read", "config": {"input": "data.parquet"}}
            ],
        }

        result = _rustic.execute_workflow(workflow_config, max_parallel=2)

        assert result is not None
        assert result["status"] == "completed"
        assert result["parallel_workers"] == 2
    except ImportError:
        pytest.skip("Rust backend not available")


def test_workflow_metrics():
    """Test workflow_metrics function."""
    try:
        import _rustic

        metrics = _rustic.workflow_metrics()

        assert metrics is not None
        assert "total_workflows" in metrics
        assert "total_steps" in metrics
        assert "avg_execution_ms" in metrics
        assert "parallel_speedup" in metrics
    except ImportError:
        pytest.skip("Rust backend not available")


class TestWorkflowIntegration:
    """Integration tests for workflow engine when fully implemented."""

    @pytest.mark.skipif(True, reason="Full workflow integration not yet complete")
    def test_real_workflow_execution(self):
        """Test real workflow execution once integration is complete."""
        import _rustic

        # This test will be enabled once workflow_rust_available() returns True
        assert _rustic.workflow_rust_available()

        workflow_config = {
            "name": "test_workflow",
            "steps": [
                {
                    "name": "read_data",
                    "type": "read",
                    "config": {"input": "test_data.parquet"},
                },
                {
                    "name": "filter_data",
                    "type": "filter",
                    "config": {"query": "value > 10"},
                    "depends_on": ["read_data"],
                },
            ],
        }

        result = _rustic.execute_workflow(workflow_config)

        assert result["status"] == "completed"
        assert result["steps_executed"] == 2
        assert result["execution_time_ms"] > 0
