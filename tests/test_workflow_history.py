"""
Tests for workflow execution history tracking functionality.
"""

import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from parquetframe.workflow_history import (
    StepExecution,
    WorkflowExecution,
    WorkflowHistoryManager,
)


class TestStepExecution:
    """Test StepExecution class functionality."""

    def test_step_execution_creation(self):
        """Test StepExecution initialization."""
        step = StepExecution(
            name="test_step",
            step_type="read",
            status="pending",
            start_time=datetime.now(),
        )

        assert step.name == "test_step"
        assert step.step_type == "read"
        assert step.status == "pending"
        assert isinstance(step.start_time, datetime)
        assert step.end_time is None
        assert step.duration_seconds is None
        assert step.error_message is None

    def test_step_execution_start(self):
        """Test step execution start functionality."""
        step = StepExecution(
            name="test_step",
            step_type="read",
            status="pending",
            start_time=datetime.now(),
        )

        step.start()
        assert step.status == "running"
        assert isinstance(step.start_time, datetime)

    def test_step_execution_complete(self):
        """Test step execution completion."""
        start_time = datetime.now()
        step = StepExecution(
            name="test_step",
            step_type="read",
            status="running",
            start_time=start_time,
        )

        # Simulate some execution time
        time.sleep(0.01)

        output_datasets = ["output_data"]
        step.complete(output_datasets)

        assert step.status == "completed"
        assert step.end_time is not None
        assert step.duration_seconds is not None
        assert step.duration_seconds > 0
        assert step.output_datasets == output_datasets

    def test_step_execution_fail(self):
        """Test step execution failure."""
        start_time = datetime.now()
        step = StepExecution(
            name="test_step",
            step_type="read",
            status="running",
            start_time=start_time,
        )

        # Simulate some execution time
        time.sleep(0.01)

        error_message = "Test error message"
        step.fail(error_message)

        assert step.status == "failed"
        assert step.end_time is not None
        assert step.duration_seconds is not None
        assert step.duration_seconds > 0
        assert step.error_message == error_message

    def test_step_execution_skip(self):
        """Test step execution skip."""
        step = StepExecution(
            name="test_step",
            step_type="read",
            status="pending",
            start_time=datetime.now(),
        )

        skip_reason = "Conditional skip"
        step.skip(skip_reason)

        assert step.status == "skipped"
        assert step.end_time is not None
        assert step.error_message == skip_reason

    def test_step_execution_with_config(self):
        """Test step execution with configuration data."""
        config = {
            "input": "test.parquet",
            "threshold_mb": 50,
            "columns": ["a", "b", "c"],
        }

        step = StepExecution(
            name="test_step",
            step_type="read",
            status="pending",
            start_time=datetime.now(),
            input_datasets=["input_data"],
            config=config,
        )

        assert step.config == config
        assert step.input_datasets == ["input_data"]


class TestWorkflowExecution:
    """Test WorkflowExecution class functionality."""

    def test_workflow_execution_creation(self):
        """Test WorkflowExecution initialization."""
        workflow = WorkflowExecution(
            workflow_name="test_workflow",
            workflow_file="test.yml",
            execution_id="test_123",
            start_time=datetime.now(),
        )

        assert workflow.workflow_name == "test_workflow"
        assert workflow.workflow_file == "test.yml"
        assert workflow.execution_id == "test_123"
        assert isinstance(workflow.start_time, datetime)
        assert workflow.status == "running"
        assert len(workflow.steps) == 0
        assert workflow.success_count == 0
        assert workflow.failure_count == 0
        assert workflow.skip_count == 0

    def test_workflow_execution_add_step(self):
        """Test adding steps to workflow execution."""
        workflow = WorkflowExecution(
            workflow_name="test_workflow",
            workflow_file="test.yml",
            execution_id="test_123",
            start_time=datetime.now(),
        )

        # Add completed step
        completed_step = StepExecution(
            name="step1",
            step_type="read",
            status="completed",
            start_time=datetime.now(),
            memory_usage_mb=100.5,
        )
        workflow.add_step(completed_step)

        assert len(workflow.steps) == 1
        assert workflow.success_count == 1
        assert workflow.failure_count == 0
        assert workflow.peak_memory_usage_mb == 100.5

        # Add failed step
        failed_step = StepExecution(
            name="step2",
            step_type="filter",
            status="failed",
            start_time=datetime.now(),
            memory_usage_mb=150.0,
        )
        workflow.add_step(failed_step)

        assert len(workflow.steps) == 2
        assert workflow.success_count == 1
        assert workflow.failure_count == 1
        assert workflow.peak_memory_usage_mb == 150.0

        # Add skipped step
        skipped_step = StepExecution(
            name="step3",
            step_type="save",
            status="skipped",
            start_time=datetime.now(),
        )
        workflow.add_step(skipped_step)

        assert len(workflow.steps) == 3
        assert workflow.success_count == 1
        assert workflow.failure_count == 1
        assert workflow.skip_count == 1

    def test_workflow_execution_complete(self):
        """Test workflow execution completion."""
        workflow = WorkflowExecution(
            workflow_name="test_workflow",
            workflow_file="test.yml",
            execution_id="test_123",
            start_time=datetime.now(),
        )

        # Simulate some execution time
        time.sleep(0.01)

        workflow.complete()

        assert workflow.status == "completed"
        assert workflow.end_time is not None
        assert workflow.duration_seconds is not None
        assert workflow.duration_seconds > 0

    def test_workflow_execution_fail(self):
        """Test workflow execution failure."""
        workflow = WorkflowExecution(
            workflow_name="test_workflow",
            workflow_file="test.yml",
            execution_id="test_123",
            start_time=datetime.now(),
        )

        # Simulate some execution time
        time.sleep(0.01)

        error_message = "Workflow failed"
        workflow.fail(error_message)

        assert workflow.status == "failed"
        assert workflow.end_time is not None
        assert workflow.duration_seconds is not None
        assert workflow.duration_seconds > 0

    def test_workflow_execution_summary_stats(self):
        """Test workflow execution summary statistics."""
        workflow = WorkflowExecution(
            workflow_name="test_workflow",
            workflow_file="test.yml",
            execution_id="test_123",
            start_time=datetime.now(),
        )

        # Add some steps
        step1 = StepExecution(
            name="step1",
            step_type="read",
            status="completed",
            start_time=datetime.now(),
            duration_seconds=1.5,
            memory_usage_mb=100.0,
        )
        step2 = StepExecution(
            name="step2",
            step_type="filter",
            status="failed",
            start_time=datetime.now(),
            duration_seconds=0.5,
            memory_usage_mb=150.0,
        )

        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.complete()

        stats = workflow.get_summary_stats()

        assert stats["total_steps"] == 2
        assert stats["successful_steps"] == 1
        assert stats["failed_steps"] == 1
        assert stats["skipped_steps"] == 0
        assert stats["success_rate"] == 0.5
        assert stats["average_step_duration"] == 1.0
        assert stats["peak_memory_mb"] == 150.0

    def test_workflow_execution_with_variables(self):
        """Test workflow execution with variables."""
        variables = {
            "input_dir": "data",
            "output_dir": "results",
            "threshold": 50,
        }

        workflow = WorkflowExecution(
            workflow_name="test_workflow",
            workflow_file="test.yml",
            execution_id="test_123",
            start_time=datetime.now(),
            variables=variables,
        )

        assert workflow.variables == variables


class TestWorkflowHistoryManager:
    """Test WorkflowHistoryManager functionality."""

    def test_history_manager_creation(self):
        """Test WorkflowHistoryManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)
            assert manager.history_dir == Path(temp_dir)
            assert manager.history_dir.exists()

    def test_history_manager_default_location(self):
        """Test WorkflowHistoryManager with default history directory."""
        manager = WorkflowHistoryManager()
        assert manager.history_dir == Path.home() / ".parquetframe" / "history"

    def test_create_execution_record(self):
        """Test creating workflow execution records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            variables = {"test_var": "test_value"}
            execution = manager.create_execution_record(
                workflow_name="test_workflow",
                workflow_file="test.yml",
                variables=variables,
            )

            assert execution.workflow_name == "test_workflow"
            assert execution.workflow_file == "test.yml"
            assert execution.variables == variables
            assert execution.execution_id.startswith("test_workflow_")
            assert isinstance(execution.start_time, datetime)

    def test_save_and_load_execution_record(self):
        """Test saving and loading execution records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            # Create test execution
            execution = manager.create_execution_record(
                workflow_name="test_workflow",
                workflow_file="test.yml",
                variables={"test": "value"},
            )

            # Add some steps
            step = StepExecution(
                name="test_step",
                step_type="read",
                status="completed",
                start_time=datetime.now(),
                duration_seconds=1.0,
            )
            execution.add_step(step)
            execution.complete()

            # Save the execution
            hist_file = manager.save_execution_record(execution)
            assert hist_file.exists()
            assert hist_file.suffix == ".hist"

            # Load the execution
            loaded_execution = manager.load_execution_record(hist_file)

            assert loaded_execution.workflow_name == execution.workflow_name
            assert loaded_execution.workflow_file == execution.workflow_file
            assert loaded_execution.execution_id == execution.execution_id
            assert loaded_execution.variables == execution.variables
            assert loaded_execution.status == execution.status
            assert len(loaded_execution.steps) == len(execution.steps)
            assert loaded_execution.steps[0].name == execution.steps[0].name
            assert loaded_execution.steps[0].status == execution.steps[0].status

    def test_list_execution_records(self):
        """Test listing execution records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            # Create and save multiple executions
            executions = []
            for i in range(3):
                execution = manager.create_execution_record(
                    workflow_name=f"workflow_{i}",
                    workflow_file=f"test_{i}.yml",
                )
                execution.complete()
                manager.save_execution_record(execution)
                executions.append(execution)
                time.sleep(0.01)  # Ensure different timestamps

            # Test listing all records
            hist_files = manager.list_execution_records()
            assert len(hist_files) == 3

            # Test filtering by workflow name
            workflow_0_files = manager.list_execution_records("workflow_0")
            assert len(workflow_0_files) == 1

            # Test that files are sorted by modification time (newest first)
            all_files = manager.list_execution_records()
            assert all_files[0].stat().st_mtime >= all_files[1].stat().st_mtime

    def test_get_execution_summary(self):
        """Test getting execution summaries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            # Create test execution with steps
            execution = manager.create_execution_record(
                workflow_name="test_workflow",
                workflow_file="test.yml",
            )

            step = StepExecution(
                name="test_step",
                step_type="read",
                status="completed",
                start_time=datetime.now(),
                duration_seconds=2.5,
            )
            execution.add_step(step)
            execution.complete()

            hist_file = manager.save_execution_record(execution)
            summary = manager.get_execution_summary(hist_file)

            assert summary["execution_id"] == execution.execution_id
            assert summary["workflow_name"] == execution.workflow_name
            assert summary["status"] == execution.status
            assert summary["stats"]["total_steps"] == 1
            assert summary["stats"]["successful_steps"] == 1

    def test_cleanup_old_records(self):
        """Test cleaning up old execution records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            # Create test execution
            execution = manager.create_execution_record(
                workflow_name="test_workflow",
                workflow_file="test.yml",
            )
            hist_file = manager.save_execution_record(execution)

            # Verify file exists
            assert hist_file.exists()

            # On some platforms (especially Windows), we need to ensure the file timestamp
            # is definitely older than the cutoff. Let's manually set the file's mtime to the past
            old_time = time.time() - (2 * 24 * 60 * 60)  # 2 days ago
            os.utime(hist_file, (old_time, old_time))

            # Cleanup with 1 day (should remove files older than 1 day)
            removed_count = manager.cleanup_old_records(keep_days=1)
            assert removed_count == 1
            assert not hist_file.exists()

            # Test that recent files are not removed
            execution2 = manager.create_execution_record(
                workflow_name="test_workflow_2",
                workflow_file="test2.yml",
            )
            hist_file2 = manager.save_execution_record(execution2)
            assert hist_file2.exists()

            # This should not remove the recent file
            removed_count = manager.cleanup_old_records(keep_days=1)
            assert removed_count == 0
            assert hist_file2.exists()

    def test_get_workflow_statistics(self):
        """Test getting workflow statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            # Create multiple executions with different outcomes
            # Successful execution
            successful_execution = manager.create_execution_record(
                workflow_name="test_workflow",
                workflow_file="test.yml",
            )
            successful_execution.complete()
            manager.save_execution_record(successful_execution)

            # Failed execution
            failed_execution = manager.create_execution_record(
                workflow_name="test_workflow",
                workflow_file="test.yml",
            )
            failed_execution.fail("Test failure")
            manager.save_execution_record(failed_execution)

            # Get statistics
            stats = manager.get_workflow_statistics("test_workflow")

            assert stats["total_executions"] == 2
            assert stats["successful_executions"] == 1
            assert stats["failed_executions"] == 1
            assert stats["success_rate"] == 0.5

            # Test with no records
            no_records_stats = manager.get_workflow_statistics("nonexistent")
            assert "message" in no_records_stats

    def test_json_serialization_with_datetime(self):
        """Test JSON serialization handles datetime objects correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            # Create execution with datetime fields
            execution = manager.create_execution_record(
                workflow_name="test_workflow",
                workflow_file="test.yml",
            )

            step = StepExecution(
                name="test_step",
                step_type="read",
                status="running",
                start_time=datetime.now(),
            )
            step.complete()
            execution.add_step(step)
            execution.complete()

            # Save and verify JSON structure
            hist_file = manager.save_execution_record(execution)

            with open(hist_file) as f:
                data = json.load(f)

            # Check that datetime fields are strings in JSON
            assert isinstance(data["start_time"], str)
            assert isinstance(data["end_time"], str)
            assert isinstance(data["steps"][0]["start_time"], str)
            assert isinstance(data["steps"][0]["end_time"], str)

            # Verify loading works correctly
            loaded_execution = manager.load_execution_record(hist_file)
            assert isinstance(loaded_execution.start_time, datetime)
            assert isinstance(loaded_execution.end_time, datetime)
            assert isinstance(loaded_execution.steps[0].start_time, datetime)
            assert isinstance(loaded_execution.steps[0].end_time, datetime)

    def test_error_handling_corrupted_file(self):
        """Test error handling for corrupted history files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = WorkflowHistoryManager(history_dir=temp_dir)

            # Create a corrupted JSON file
            corrupted_file = Path(temp_dir) / "corrupted.hist"
            with open(corrupted_file, "w") as f:
                f.write("{ invalid json ")

            # Should raise an exception when trying to load
            with pytest.raises(json.JSONDecodeError):
                manager.load_execution_record(corrupted_file)

    def test_metrics_tracking(self):
        """Test that metrics are properly tracked."""
        step = StepExecution(
            name="test_step",
            step_type="read",
            status="running",
            start_time=datetime.now(),
        )

        # Complete step with custom metrics
        step.complete()

        # Check that metrics dict exists and can store custom data
        step.metrics["custom_metric"] = "test_value"
        assert step.metrics["custom_metric"] == "test_value"
