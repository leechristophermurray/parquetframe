"""
Tests for YAML workflow engine functionality.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from parquetframe.core import ParquetFrame

# Import workflow components with fallback
try:
    from parquetframe.workflows import (
        STEP_REGISTRY,
        FilterStep,
        GroupByStep,
        ReadStep,
        SaveStep,
        SelectStep,
        TransformStep,
        WorkflowContext,
        WorkflowEngine,
        WorkflowError,
        WorkflowExecutionError,
        WorkflowValidationError,
        create_example_workflow,
    )

    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False


@pytest.mark.skipif(
    not WORKFLOW_AVAILABLE, reason="Workflow functionality not available"
)
class TestWorkflowContext:
    def test_workflow_context_creation(self):
        """Test WorkflowContext initialization."""
        context = WorkflowContext()
        assert context.variables == {}
        assert context.datasets == {}
        assert context.outputs == {}
        assert isinstance(context.working_dir, Path)

    def test_variable_operations(self):
        """Test variable get/set operations."""
        context = WorkflowContext()

        # Test setting and getting variables
        context.set_variable("test_var", "test_value")
        assert context.get_variable("test_var") == "test_value"

        # Test default value for non-existent variable
        assert context.get_variable("non_existent", "default") == "default"

    def test_dataset_operations(self):
        """Test dataset get/set operations."""
        context = WorkflowContext()

        # Create a test ParquetFrame
        test_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        test_pf = ParquetFrame(test_df, islazy=False)

        context.set_dataset("test_data", test_pf)
        retrieved_pf = context.get_dataset("test_data")

        assert retrieved_pf is not None
        assert isinstance(retrieved_pf, ParquetFrame)

    def test_path_resolution(self):
        """Test path resolution functionality."""
        context = WorkflowContext(working_dir=Path("/tmp/test"))

        # Test absolute path
        abs_path = context.resolve_path("/absolute/path")
        assert abs_path == Path("/absolute/path")

        # Test relative path
        rel_path = context.resolve_path("relative/path")
        assert rel_path == Path("/tmp/test/relative/path")


@pytest.mark.skipif(
    not WORKFLOW_AVAILABLE, reason="Workflow functionality not available"
)
class TestWorkflowSteps:
    def test_read_step_validation(self):
        """Test ReadStep validation."""
        # Valid configuration
        step = ReadStep("test", {"input": "test.parquet"})
        errors = step.validate()
        assert errors == []

        # Invalid configuration - missing input
        step = ReadStep("test", {})
        errors = step.validate()
        assert len(errors) == 1
        assert "input" in errors[0]

    def test_filter_step_validation(self):
        """Test FilterStep validation."""
        # Valid configuration
        step = FilterStep("test", {"query": "age > 30"})
        errors = step.validate()
        assert errors == []

        # Invalid configuration - missing query
        step = FilterStep("test", {})
        errors = step.validate()
        assert len(errors) == 1
        assert "query" in errors[0]

    def test_select_step_validation(self):
        """Test SelectStep validation."""
        # Valid configuration
        step = SelectStep("test", {"columns": ["a", "b"]})
        errors = step.validate()
        assert errors == []

        # Invalid configuration - missing columns
        step = SelectStep("test", {})
        errors = step.validate()
        assert len(errors) == 1
        assert "columns" in errors[0]

    def test_groupby_step_validation(self):
        """Test GroupByStep validation."""
        # Valid configuration
        step = GroupByStep("test", {"by": ["category"]})
        errors = step.validate()
        assert errors == []

        # Invalid configuration - missing by
        step = GroupByStep("test", {})
        errors = step.validate()
        assert len(errors) == 1
        assert "by" in errors[0]

    def test_save_step_validation(self):
        """Test SaveStep validation."""
        # Valid configuration
        step = SaveStep("test", {"output": "output.parquet"})
        errors = step.validate()
        assert errors == []

        # Invalid configuration - missing output
        step = SaveStep("test", {})
        errors = step.validate()
        assert len(errors) == 1
        assert "output" in errors[0]

    def test_transform_step_validation(self):
        """Test TransformStep validation."""
        # Valid configuration
        step = TransformStep(
            "test", {"transforms": [{"column": "a", "operation": "rename", "to": "b"}]}
        )
        errors = step.validate()
        assert errors == []

        # Invalid configuration - missing transforms
        step = TransformStep("test", {})
        errors = step.validate()
        assert len(errors) == 1
        assert "transforms" in errors[0]

    def test_variable_interpolation(self):
        """Test variable interpolation in step execution."""
        context = WorkflowContext()
        context.set_variable("test_var", "test_value")
        context.set_variable("num_var", 42)

        step = ReadStep("test", {"input": "data_${test_var}.parquet"})

        # Test interpolation
        interpolated = step.interpolate_variables("${test_var}", context)
        assert interpolated == "test_value"

        interpolated = step.interpolate_variables("prefix_${test_var}_suffix", context)
        assert interpolated == "prefix_test_value_suffix"

        interpolated = step.interpolate_variables("number_${num_var}", context)
        assert interpolated == "number_42"

        # Test non-string values (should pass through unchanged)
        interpolated = step.interpolate_variables(123, context)
        assert interpolated == 123


@pytest.mark.skipif(
    not WORKFLOW_AVAILABLE, reason="Workflow functionality not available"
)
class TestWorkflowEngine:
    def test_workflow_engine_creation(self):
        """Test WorkflowEngine initialization."""
        engine = WorkflowEngine(verbose=False)
        assert engine.verbose is False

        engine = WorkflowEngine(verbose=True)
        assert engine.verbose is True

    def test_workflow_validation_valid(self):
        """Test validation of a valid workflow."""
        engine = WorkflowEngine(verbose=False)

        workflow = {
            "steps": [
                {"name": "read_data", "type": "read", "input": "test.parquet"},
                {"name": "filter_data", "type": "filter", "query": "age > 30"},
            ]
        }

        errors = engine.validate_workflow(workflow)
        assert errors == []

    def test_workflow_validation_missing_steps(self):
        """Test validation of workflow missing steps."""
        engine = WorkflowEngine(verbose=False)

        workflow = {"name": "test"}
        errors = engine.validate_workflow(workflow)
        assert len(errors) == 1
        assert "steps" in errors[0]

    def test_workflow_validation_invalid_step_type(self):
        """Test validation with invalid step type."""
        engine = WorkflowEngine(verbose=False)

        workflow = {"steps": [{"name": "invalid_step", "type": "invalid_type"}]}

        errors = engine.validate_workflow(workflow)
        assert len(errors) == 1
        assert "Unknown step type" in errors[0]

    def test_workflow_validation_missing_step_config(self):
        """Test validation with missing step configuration."""
        engine = WorkflowEngine(verbose=False)

        workflow = {
            "steps": [
                {
                    "name": "read_step",
                    "type": "read",
                    # Missing required 'input' field
                }
            ]
        }

        errors = engine.validate_workflow(workflow)
        assert len(errors) == 1
        assert "input" in errors[0]

    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
    def test_load_workflow_file(self):
        """Test loading workflow from YAML file."""
        engine = WorkflowEngine(verbose=False)

        workflow_content = """
        name: "Test Workflow"
        steps:
          - name: "read_data"
            type: "read"
            input: "test.parquet"
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(workflow_content)
            temp_path = f.name

        try:
            workflow = engine.load_workflow(temp_path)
            assert workflow["name"] == "Test Workflow"
            assert len(workflow["steps"]) == 1
            assert workflow["steps"][0]["type"] == "read"
        finally:
            os.unlink(temp_path)

    def test_load_workflow_file_not_found(self):
        """Test loading non-existent workflow file."""
        engine = WorkflowEngine(verbose=False)

        with pytest.raises(WorkflowError, match="Workflow file not found"):
            engine.load_workflow("non_existent_file.yml")


@pytest.mark.skipif(
    not WORKFLOW_AVAILABLE, reason="Workflow functionality not available"
)
class TestWorkflowStepExecution:
    def test_filter_step_execution(self):
        """Test FilterStep execution."""
        # Create test data
        test_df = pd.DataFrame(
            {"age": [25, 35, 45], "name": ["Alice", "Bob", "Charlie"]}
        )
        test_pf = ParquetFrame(test_df, islazy=False)

        # Create context with test data
        context = WorkflowContext()
        context.set_dataset("test_data", test_pf)

        # Create and execute filter step
        step = FilterStep(
            "test_filter",
            {"input": "test_data", "query": "age > 30", "output": "filtered_data"},
        )

        result = step.execute(context)

        # Verify results
        assert isinstance(result, ParquetFrame)
        filtered_data = context.get_dataset("filtered_data")
        assert filtered_data is not None

        # Check that filtering worked
        if hasattr(filtered_data._df, "compute"):
            df = filtered_data._df.compute()
        else:
            df = filtered_data._df

        assert len(df) == 2  # Should have Bob and Charlie
        assert all(df["age"] > 30)

    def test_select_step_execution(self):
        """Test SelectStep execution."""
        # Create test data
        test_df = pd.DataFrame(
            {
                "name": ["Alice", "Bob"],
                "age": [25, 35],
                "city": ["NYC", "LA"],
                "extra": ["x", "y"],
            }
        )
        test_pf = ParquetFrame(test_df, islazy=False)

        # Create context
        context = WorkflowContext()
        context.set_dataset("test_data", test_pf)

        # Create and execute select step
        step = SelectStep(
            "test_select",
            {
                "input": "test_data",
                "columns": ["name", "age"],
                "output": "selected_data",
            },
        )

        result = step.execute(context)

        # Verify results
        selected_data = context.get_dataset("selected_data")
        if hasattr(selected_data._df, "compute"):
            df = selected_data._df.compute()
        else:
            df = selected_data._df

        assert list(df.columns) == ["name", "age"]
        assert len(df) == 2

    def test_groupby_step_execution(self):
        """Test GroupByStep execution."""
        # Create test data
        test_df = pd.DataFrame(
            {
                "category": ["A", "B", "A", "B"],
                "value": [10, 20, 15, 25],
                "count": [1, 1, 1, 1],
            }
        )
        test_pf = ParquetFrame(test_df, islazy=False)

        # Create context
        context = WorkflowContext()
        context.set_dataset("test_data", test_pf)

        # Create and execute groupby step
        step = GroupByStep(
            "test_groupby",
            {
                "input": "test_data",
                "by": ["category"],
                "agg": {"value": ["sum", "mean"]},
                "output": "grouped_data",
            },
        )

        result = step.execute(context)

        # Verify results
        grouped_data = context.get_dataset("grouped_data")
        assert grouped_data is not None

        # Check that grouping worked
        if hasattr(grouped_data._df, "compute"):
            df = grouped_data._df.compute()
        else:
            df = grouped_data._df

        assert len(df) == 2  # Should have 2 groups (A and B)


@pytest.mark.skipif(
    not WORKFLOW_AVAILABLE, reason="Workflow functionality not available"
)
class TestWorkflowIntegration:
    def test_simple_workflow_execution(self):
        """Test execution of a simple workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test data file
            test_df = pd.DataFrame(
                {
                    "name": ["Alice", "Bob", "Charlie"],
                    "age": [25, 35, 45],
                    "city": ["NYC", "LA", "NYC"],
                }
            )
            test_file = temp_path / "test_data.parquet"
            test_df.to_parquet(test_file)

            # Create workflow
            workflow = {
                "name": "Test Workflow",
                "steps": [
                    {
                        "name": "load_data",
                        "type": "read",
                        "input": "test_data.parquet",
                        "output": "data",
                    },
                    {
                        "name": "filter_adults",
                        "type": "filter",
                        "input": "data",
                        "query": "age >= 30",
                        "output": "adults",
                    },
                    {
                        "name": "save_results",
                        "type": "save",
                        "input": "adults",
                        "output": "results.parquet",
                    },
                ],
            }

            # Execute workflow
            engine = WorkflowEngine(verbose=False)
            context = engine.execute_workflow(workflow, working_dir=temp_path)

            # Verify execution
            assert "data" in context.datasets
            assert "adults" in context.datasets

            # Verify output file was created
            output_file = temp_path / "results.parquet"
            assert output_file.exists()

            # Verify output data
            result_df = pd.read_parquet(output_file)
            assert len(result_df) == 2  # Bob and Charlie
            assert all(result_df["age"] >= 30)

    def test_workflow_with_variables(self):
        """Test workflow execution with variable interpolation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test data
            test_df = pd.DataFrame(
                {"value": [10, 20, 30, 40, 50], "category": ["A", "B", "A", "B", "A"]}
            )
            test_file = temp_path / "test_data.parquet"
            test_df.to_parquet(test_file)

            # Create workflow with variables
            workflow = {
                "name": "Variable Test Workflow",
                "variables": {"min_value": 25, "output_dir": "output"},
                "steps": [
                    {
                        "name": "load_data",
                        "type": "read",
                        "input": "test_data.parquet",
                        "output": "data",
                    },
                    {
                        "name": "filter_data",
                        "type": "filter",
                        "input": "data",
                        "query": "value >= ${min_value}",
                        "output": "filtered",
                    },
                    {
                        "name": "save_results",
                        "type": "save",
                        "input": "filtered",
                        "output": "${output_dir}/filtered_results.parquet",
                    },
                ],
            }

            # Execute workflow
            engine = WorkflowEngine(verbose=False)
            context = engine.execute_workflow(workflow, working_dir=temp_path)

            # Verify variable interpolation worked
            output_file = temp_path / "output" / "filtered_results.parquet"
            assert output_file.exists()

            # Verify filtering worked
            result_df = pd.read_parquet(output_file)
            assert all(result_df["value"] >= 25)


@pytest.mark.skipif(
    not WORKFLOW_AVAILABLE, reason="Workflow functionality not available"
)
class TestExampleWorkflow:
    def test_create_example_workflow(self):
        """Test creating example workflow."""
        example = create_example_workflow()

        assert isinstance(example, dict)
        assert "name" in example
        assert "steps" in example
        assert "variables" in example

        # Test that the example is valid
        engine = WorkflowEngine(verbose=False)
        errors = engine.validate_workflow(example)
        assert errors == []

    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
    def test_example_workflow_yaml_serialization(self):
        """Test that example workflow can be serialized to YAML."""
        example = create_example_workflow()

        # Should be able to serialize to YAML without errors
        yaml_str = yaml.dump(example, indent=2, default_flow_style=False)
        assert isinstance(yaml_str, str)
        assert len(yaml_str) > 0

        # Should be able to load it back
        loaded = yaml.safe_load(yaml_str)
        assert loaded == example


@pytest.mark.skipif(
    not WORKFLOW_AVAILABLE, reason="Workflow functionality not available"
)
class TestStepRegistry:
    def test_step_registry_completeness(self):
        """Test that step registry contains expected steps."""
        expected_steps = {"read", "filter", "select", "groupby", "save", "transform"}

        assert set(STEP_REGISTRY.keys()) == expected_steps

        # Verify all registered classes are proper step classes
        for step_name, step_class in STEP_REGISTRY.items():
            # Should be able to instantiate
            instance = step_class("test", {"dummy": "config"})

            # Should have required methods
            assert hasattr(instance, "execute")
            assert hasattr(instance, "validate")
            assert callable(instance.execute)
            assert callable(instance.validate)
