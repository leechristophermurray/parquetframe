import os
import tempfile

import pandas as pd
import pytest
import yaml

from parquetframe.dpac import run


def test_workflow_runner_simple():
    """Test a simple workflow with Parquet read/write (simulated via SQL for now as we don't have a simple 'create' step)."""
    # Actually, we can use SQL to generate data

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.parquet")
        yaml_path = os.path.join(tmpdir, "workflow.yml")

        workflow_def = {
            "name": "Test Workflow",
            "version": "1.0",
            "steps": [
                {
                    "name": "generate_data",
                    "type": "datafusion.sql",
                    "params": {"sql": "SELECT 1 as id, 'test' as name"},
                    "output": "data",
                },
                {
                    "name": "write_data",
                    "type": "parquet.write",
                    "inputs": ["data"],
                    "params": {"path": output_path},
                },
            ],
        }

        with open(yaml_path, "w") as f:
            yaml.dump(workflow_def, f)

        # Run workflow
        run(yaml_path)

        # Verify output
        assert os.path.exists(output_path)
        df = pd.read_parquet(output_path)
        assert len(df) == 1
        assert df.iloc[0]["id"] == 1
        assert df.iloc[0]["name"] == "test"


def test_workflow_runner_cycle_detection():
    """Test that a cycle in the workflow raises an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = os.path.join(tmpdir, "cycle.yml")

        workflow_def = {
            "name": "Cycle Workflow",
            "version": "1.0",
            "steps": [
                {
                    "name": "step_a",
                    "type": "test",
                    "depends_on": ["step_b"],
                    "params": {},
                },
                {
                    "name": "step_b",
                    "type": "test",
                    "depends_on": ["step_a"],
                    "params": {},
                },
            ],
        }

        with open(yaml_path, "w") as f:
            yaml.dump(workflow_def, f)

        # Expect failure
        with pytest.raises(RuntimeError) as excinfo:
            run(yaml_path)
        assert "Workflow execution failed" in str(excinfo.value)
        assert "Cycle detected" in str(excinfo.value) or "StepFailed" in str(
            excinfo.value
        )


def test_workflow_runner_missing_dependency():
    """Test that a missing dependency raises an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = os.path.join(tmpdir, "missing.yml")

        workflow_def = {
            "name": "Missing Dep Workflow",
            "version": "1.0",
            "steps": [
                {
                    "name": "step_a",
                    "type": "test",
                    "depends_on": ["non_existent"],
                    "params": {},
                }
            ],
        }

        with open(yaml_path, "w") as f:
            yaml.dump(workflow_def, f)

        # Expect failure
        with pytest.raises(RuntimeError) as excinfo:
            run(yaml_path)
        assert "Workflow execution failed" in str(excinfo.value)
        assert "Cycle detected or missing dependency" in str(
            excinfo.value
        ) or "StepFailed" in str(excinfo.value)
