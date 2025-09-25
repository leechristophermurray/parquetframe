"""
Tests for workflow visualization functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from parquetframe.workflow_history import StepExecution, WorkflowExecution

# Import with fallback for optional dependencies
try:
    from parquetframe.workflow_visualization import WorkflowVisualizer

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


@pytest.mark.skipif(
    not VISUALIZATION_AVAILABLE, reason="Workflow visualization not available"
)
class TestWorkflowVisualizer:
    """Test WorkflowVisualizer functionality."""

    def test_visualizer_creation(self):
        """Test WorkflowVisualizer initialization."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            visualizer = WorkflowVisualizer()
            assert visualizer is not None

    def test_visualizer_creation_no_dependencies(self):
        """Test WorkflowVisualizer fails without dependencies."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", False):
            with patch("parquetframe.workflow_visualization.GRAPHVIZ_AVAILABLE", False):
                with pytest.raises(ImportError):
                    WorkflowVisualizer()

    def test_create_dag_from_workflow(self):
        """Test DAG creation from workflow definition."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            # Mock NetworkX
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {
                    "name": "Test Workflow",
                    "description": "A test workflow",
                    "steps": [
                        {
                            "name": "load_data",
                            "type": "read",
                            "input": "data.parquet",
                            "output": "raw_data",
                        },
                        {
                            "name": "filter_data",
                            "type": "filter",
                            "input": "raw_data",
                            "query": "age > 25",
                            "output": "filtered_data",
                        },
                        {
                            "name": "save_results",
                            "type": "save",
                            "input": "filtered_data",
                            "output": "results.parquet",
                        },
                    ],
                }

                result_graph = visualizer.create_dag_from_workflow(workflow)

                # Verify NetworkX DiGraph was created
                mock_nx.DiGraph.assert_called_once()
                assert result_graph == mock_graph

                # Verify nodes were added
                assert mock_graph.add_node.call_count == 3

                # Verify edges were added (should connect based on input/output)
                assert mock_graph.add_edge.call_count >= 2

    def test_create_dag_with_execution_data(self):
        """Test DAG creation with execution status data."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {
                    "name": "Test Workflow",
                    "steps": [
                        {"name": "step1", "type": "read"},
                        {"name": "step2", "type": "filter"},
                    ],
                }

                # Create execution data
                execution_data = WorkflowExecution(
                    workflow_name="Test Workflow",
                    workflow_file="test.yml",
                    execution_id="test_123",
                    start_time=MagicMock(),
                )

                step_exec = StepExecution(
                    name="step1",
                    step_type="read",
                    status="completed",
                    start_time=MagicMock(),
                    duration_seconds=1.5,
                )
                execution_data.add_step(step_exec)

                visualizer.create_dag_from_workflow(workflow, execution_data)

                # Verify nodes were added with execution status
                assert mock_graph.add_node.call_count == 2

    def test_visualize_with_graphviz(self):
        """Test Graphviz visualization."""
        with patch("parquetframe.workflow_visualization.GRAPHVIZ_AVAILABLE", True):
            # Mock graphviz
            mock_graphviz = MagicMock()
            mock_dot = MagicMock()
            mock_graphviz.Digraph.return_value = mock_dot

            with patch("parquetframe.workflow_visualization.graphviz", mock_graphviz):
                with patch(
                    "parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True
                ):
                    mock_nx = MagicMock()
                    mock_graph = MagicMock()
                    mock_nx.DiGraph.return_value = mock_graph
                    mock_graph.edges.return_value = [
                        ("step1", "step2", {"type": "data_dependency"})
                    ]

                    with patch("parquetframe.workflow_visualization.nx", mock_nx):
                        visualizer = WorkflowVisualizer()

                        workflow = {
                            "name": "Test Workflow",
                            "steps": [
                                {"name": "step1", "type": "read"},
                                {"name": "step2", "type": "save"},
                            ],
                        }

                        # Test without output path (returns source)
                        result = visualizer.visualize_with_graphviz(workflow)

                        # Verify Digraph was created
                        mock_graphviz.Digraph.assert_called_once()

                        # Verify nodes were added
                        assert mock_dot.node.call_count == 2

                        # Verify edges were added
                        assert mock_dot.edge.call_count >= 1

                        # Should return dot source when no output path
                        assert result == mock_dot.source

    def test_visualize_with_graphviz_output_file(self):
        """Test Graphviz visualization with output file."""
        with patch("parquetframe.workflow_visualization.GRAPHVIZ_AVAILABLE", True):
            mock_graphviz = MagicMock()
            mock_dot = MagicMock()
            mock_graphviz.Digraph.return_value = mock_dot
            mock_dot.render.return_value = None

            with patch("parquetframe.workflow_visualization.graphviz", mock_graphviz):
                with patch(
                    "parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True
                ):
                    mock_nx = MagicMock()
                    with patch("parquetframe.workflow_visualization.nx", mock_nx):
                        visualizer = WorkflowVisualizer()

                        workflow = {
                            "name": "Test",
                            "steps": [{"name": "step1", "type": "read"}],
                        }

                        with tempfile.TemporaryDirectory() as temp_dir:
                            output_path = Path(temp_dir) / "test_output"
                            result = visualizer.visualize_with_graphviz(
                                workflow, output_path=output_path, format="svg"
                            )

                            # Verify render was called
                            mock_dot.render.assert_called_once()

                            # Should return path with format extension
                            assert result == str(output_path.with_suffix(".svg"))

    def test_visualize_with_networkx_no_matplotlib(self):
        """Test NetworkX visualization without matplotlib."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            # Mock NetworkX but fail matplotlib import
            with patch("parquetframe.workflow_visualization.nx"):
                with patch.dict("sys.modules", {"matplotlib.pyplot": None}):
                    with patch("builtins.__import__", side_effect=ImportError):
                        visualizer = WorkflowVisualizer()

                        workflow = {"name": "Test", "steps": []}
                        result = visualizer.visualize_with_networkx(workflow)

                        # Should return None when matplotlib is not available
                        assert result is None

    def test_get_dag_statistics(self):
        """Test DAG statistics calculation."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph
            mock_graph.number_of_nodes.return_value = 3
            mock_graph.number_of_edges.return_value = 2
            mock_nx.is_directed_acyclic_graph.return_value = True
            mock_nx.dag_longest_path.return_value = ["step1", "step2", "step3"]
            mock_nx.isolates.return_value = []
            mock_graph.nodes.return_value = [
                ("step1", {"type": "read"}),
                ("step2", {"type": "filter"}),
                ("step3", {"type": "save"}),
            ]

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {
                    "steps": [
                        {"name": "step1", "type": "read"},
                        {"name": "step2", "type": "filter"},
                        {"name": "step3", "type": "save"},
                    ]
                }

                stats = visualizer.get_dag_statistics(workflow)

                assert stats["total_steps"] == 3
                assert stats["total_dependencies"] == 2
                assert stats["is_dag"]
                assert stats["longest_path"] == 3
                assert stats["complexity"] == 2 / 3
                assert "step_types" in stats
                assert stats["potential_issues"] == []

    def test_get_dag_statistics_with_cycles(self):
        """Test DAG statistics with cycle detection."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph
            mock_graph.number_of_nodes.return_value = 2
            mock_graph.number_of_edges.return_value = 2
            mock_nx.is_directed_acyclic_graph.return_value = False  # Has cycles
            mock_nx.isolates.return_value = []
            mock_graph.nodes.return_value = [
                ("step1", {"type": "read"}),
                ("step2", {"type": "save"}),
            ]

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {"steps": [{"name": "step1", "type": "read"}]}
                stats = visualizer.get_dag_statistics(workflow)

                assert "Workflow contains cycles" in stats["potential_issues"]

    def test_get_dag_statistics_no_networkx(self):
        """Test DAG statistics without NetworkX available."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", False):
            visualizer = WorkflowVisualizer.__new__(WorkflowVisualizer)  # Skip __init__

            workflow = {"steps": []}
            stats = visualizer.get_dag_statistics(workflow)

            assert "error" in stats
            assert stats["error"] == "NetworkX not available"

    def test_export_to_mermaid(self):
        """Test Mermaid diagram export."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph
            mock_graph.edges.return_value = [("step_1", "step_2")]

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {
                    "steps": [
                        {"name": "step 1", "type": "read"},
                        {"name": "step 2", "type": "save"},
                    ]
                }

                mermaid_code = visualizer.export_to_mermaid(workflow)

                # Should start with graph TD
                assert mermaid_code.startswith("graph TD")

                # Should contain node definitions
                assert "step_1" in mermaid_code
                assert "step_2" in mermaid_code

                # Should contain edges
                assert "step_1 --> step_2" in mermaid_code

    def test_export_to_mermaid_with_execution_data(self):
        """Test Mermaid export with execution status."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph
            mock_graph.edges.return_value = []

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {"steps": [{"name": "step1", "type": "read"}]}

                # Create execution data with completed step
                execution_data = WorkflowExecution(
                    workflow_name="Test",
                    workflow_file="test.yml",
                    execution_id="test_123",
                    start_time=MagicMock(),
                )

                step_exec = StepExecution(
                    name="step1",
                    step_type="read",
                    status="completed",
                    start_time=MagicMock(),
                )
                execution_data.add_step(step_exec)

                mermaid_code = visualizer.export_to_mermaid(workflow, execution_data)

                # Should include styling for completed step
                assert "fill:#90EE90" in mermaid_code

    def test_visualize_without_required_dependencies(self):
        """Test visualization methods fail gracefully without dependencies."""
        with patch("parquetframe.workflow_visualization.GRAPHVIZ_AVAILABLE", False):
            # Still allow NetworkX for initializer
            with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
                visualizer = WorkflowVisualizer()

                workflow = {"steps": []}

                # Should raise ImportError for graphviz
                with pytest.raises(ImportError, match="Graphviz is required"):
                    visualizer.visualize_with_graphviz(workflow)

        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", False):
            # Still allow graphviz for initializer
            with patch("parquetframe.workflow_visualization.GRAPHVIZ_AVAILABLE", True):
                visualizer = WorkflowVisualizer()

                workflow = {"steps": []}

                # Should raise ImportError for NetworkX
                with pytest.raises(ImportError, match="NetworkX is required"):
                    visualizer.visualize_with_networkx(workflow)

    def test_complex_workflow_dag_creation(self):
        """Test DAG creation with complex workflow dependencies."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {
                    "name": "Complex Workflow",
                    "steps": [
                        {
                            "name": "read_customers",
                            "type": "read",
                            "output": "customers",
                        },
                        {"name": "read_orders", "type": "read", "output": "orders"},
                        {
                            "name": "filter_customers",
                            "type": "filter",
                            "input": "customers",
                            "output": "active_customers",
                        },
                        {
                            "name": "join_data",
                            "type": "transform",
                            "input": "active_customers",
                            "output": "joined",
                        },
                        {
                            "name": "aggregate",
                            "type": "groupby",
                            "input": "joined",
                            "output": "summary",
                        },
                        {"name": "save_results", "type": "save", "input": "summary"},
                    ],
                }

                visualizer.create_dag_from_workflow(workflow)

                # Should create nodes for all steps
                assert mock_graph.add_node.call_count == 6

                # Should create edges based on dependencies
                # At minimum should have sequential dependencies
                assert mock_graph.add_edge.call_count > 0

    def test_workflow_with_no_steps(self):
        """Test handling of workflows with no steps."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph
            mock_graph.number_of_nodes.return_value = 0
            mock_graph.number_of_edges.return_value = 0
            mock_nx.is_directed_acyclic_graph.return_value = True
            mock_nx.dag_longest_path.return_value = []
            mock_nx.isolates.return_value = []
            mock_graph.nodes.return_value = []

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {"name": "Empty Workflow", "steps": []}

                # Should handle empty workflow gracefully
                stats = visualizer.get_dag_statistics(workflow)
                assert stats["total_steps"] == 0
                assert stats["total_dependencies"] == 0
                assert stats["complexity"] == 0

    def test_step_type_distribution(self):
        """Test step type distribution in statistics."""
        with patch("parquetframe.workflow_visualization.NETWORKX_AVAILABLE", True):
            mock_nx = MagicMock()
            mock_graph = MagicMock()
            mock_nx.DiGraph.return_value = mock_graph
            mock_graph.number_of_nodes.return_value = 4
            mock_graph.number_of_edges.return_value = 3
            mock_nx.is_directed_acyclic_graph.return_value = True
            mock_nx.dag_longest_path.return_value = ["step1", "step2", "step3", "step4"]
            mock_nx.isolates.return_value = []

            # Mock nodes with different types
            mock_graph.nodes.return_value = [
                ("step1", {"type": "read"}),
                ("step2", {"type": "filter"}),
                ("step3", {"type": "filter"}),
                ("step4", {"type": "save"}),
            ]

            with patch("parquetframe.workflow_visualization.nx", mock_nx):
                visualizer = WorkflowVisualizer()

                workflow = {
                    "steps": [
                        {"name": "step1", "type": "read"},
                        {"name": "step2", "type": "filter"},
                        {"name": "step3", "type": "filter"},
                        {"name": "step4", "type": "save"},
                    ]
                }

                stats = visualizer.get_dag_statistics(workflow)

                # Should count step types correctly
                assert stats["step_types"]["read"] == 1
                assert stats["step_types"]["filter"] == 2
                assert stats["step_types"]["save"] == 1
