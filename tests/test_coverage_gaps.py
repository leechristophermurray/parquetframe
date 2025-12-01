"""
Coverage analysis for new features.

Identifies gaps in test coverage and creates targeted tests.
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest


class TestGraphUtilsEdgeCases:
    """Edge case tests for graph algorithm utilities."""

    def test_validate_sources_empty_graph(self):
        """Test source validation with empty graph."""
        from parquetframe.graph.algo.utils import validate_sources

        graph = MagicMock()
        graph.vertices._df = pd.DataFrame({"id": []})

        with pytest.raises(ValueError, match="no vertices"):
            validate_sources(graph, None)

    def test_validate_sources_none_defaults_correctly(self):
        """Test that None sources defaults to first vertex."""
        from parquetframe.graph.algo.utils import validate_sources

        graph = MagicMock()
        graph.vertices._df = pd.DataFrame({"id": [42, 99, 100]})

        result = validate_sources(graph, None)
        assert result == [42]  # First vertex

    def test_create_result_dataframe_with_nullable_int(self):
        """Test DataFrame creation with nullable integers."""
        from parquetframe.graph.algo.utils import create_result_dataframe

        data = {"vertex": [0, 1, None, 3], "distance": [0, 1, 2, 3]}
        result = create_result_dataframe(
            data, ["vertex", "distance"], {"vertex": "Int64"}
        )

        assert "vertex" in result.columns
        assert pd.isna(result.iloc[2]["vertex"])

    def test_symmetrize_edges_already_undirected(self):
        """Test symmetrization of already undirected graph."""
        from parquetframe.graph.algo.utils import symmetrize_edges

        graph = MagicMock()
        graph.is_directed = False
        graph.edges = "original_edges"

        result = symmetrize_edges(graph, directed=False)
        assert result == "original_edges"  # Should return unchanged

    def test_check_convergence_empty_series(self):
        """Test convergence check with empty series."""
        from parquetframe.graph.algo.utils import check_convergence

        old = pd.Series([])
        new = pd.Series([])

        result = check_convergence(old, new, tol=0.01)
        assert not result  # Empty series should not converge

    def test_check_convergence_with_nan(self):
        """Test convergence check with NaN values."""
        from parquetframe.graph.algo.utils import check_convergence

        old = pd.Series([1.0, 2.0, None])
        new = pd.Series([1.01, 2.01, None])

        # Should handle NaN gracefully
        result = check_convergence(old, new, tol=0.1)
        assert isinstance(result, bool)

    def test_check_convergence_l2_metric(self):
        """Test convergence with L2 (Euclidean) metric."""
        from parquetframe.graph.algo.utils import check_convergence

        old = pd.Series([0.0, 0.0, 0.0])
        new = pd.Series([0.1, 0.1, 0.1])

        # L2 distance = sqrt(0.1^2 + 0.1^2 + 0.1^2) = sqrt(0.03) ≈ 0.173
        assert not check_convergence(old, new, tol=0.1, metric="l2")
        assert check_convergence(old, new, tol=0.2, metric="l2")

    def test_check_convergence_invalid_metric(self):
        """Test convergence with invalid metric."""
        from parquetframe.graph.algo.utils import check_convergence

        old = pd.Series([1.0, 2.0])
        new = pd.Series([1.0, 2.0])

        with pytest.raises(ValueError, match="Unknown metric"):
            check_convergence(old, new, tol=0.01, metric="invalid")


class TestEntityRelationshipEdgeCases:
    """Edge case tests for entity relationships."""

    def test_validate_foreign_key_empty_target(self):
        """Test foreign key validation with empty target entity."""
        from parquetframe.entity.relationship import RelationshipManager

        manager = RelationshipManager()

        entity_store = MagicMock()
        entity_store.get_entity.return_value = pd.DataFrame({"id": []})
        manager.set_entity_store(entity_store)

        result = manager.validate_foreign_key("Task", "User", 1)
        assert not result  # Empty target = invalid

    def test_validate_foreign_key_no_id_column(self):
        """Test foreign key validation without 'id' column."""
        from parquetframe.entity.relationship import RelationshipManager

        manager = RelationshipManager()

        entity_store = MagicMock()
        entity_store.get_entity.return_value = pd.DataFrame(
            {
                "user_id": [1, 2, 3],  # No 'id' column
                "name": ["Alice", "Bob", "Charlie"],
            }
        )
        manager.set_entity_store(entity_store)

        # Should fall back to checking all columns
        result = manager.validate_foreign_key("Task", "User", 2)
        assert result  # Found in user_id column

    def test_validate_foreign_key_store_error(self):
        """Test foreign key validation with store errors."""
        from parquetframe.entity.relationship import RelationshipManager

        manager = RelationshipManager()

        entity_store = MagicMock()
        entity_store.get_entity.side_effect = KeyError("Entity not found")
        manager.set_entity_store(entity_store)

        # Should fail open on errors
        result = manager.validate_foreign_key("Task", "User", 1)
        assert result


class TestInteractiveCLIEdgeCases:
    """Edge case tests for interactive CLI."""

    @pytest.mark.asyncio
    async def test_handle_permissions_without_args(self):
        """Test permissions command without arguments."""
        from unittest.mock import patch

        from parquetframe.datacontext import DataContext
        from parquetframe.interactive import InteractiveSession

        with patch("parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            data_context = MagicMock(spec=DataContext)
            data_context.source_location = "/tmp"
            # Use MagicMock for source_type to support .value attribute
            source_type_mock = MagicMock()
            source_type_mock.value = "test"
            data_context.source_type = source_type_mock

            session = InteractiveSession(data_context, enable_ai=False)
            session.console = MagicMock()

            # Should show usage message
            session._handle_permissions_command("")
            session.console.print.assert_called()

    @pytest.mark.asyncio
    async def test_handle_datafusion_not_available(self):
        """Test DataFusion command when not available."""
        from unittest.mock import patch

        from parquetframe.datacontext import DataContext
        from parquetframe.interactive import InteractiveSession

        with patch("parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            data_context = MagicMock(spec=DataContext)
            data_context.source_location = "/tmp"
            # Use MagicMock for source_type to support .value attribute
            source_type_mock = MagicMock()
            source_type_mock.value = "test"
            data_context.source_type = source_type_mock

            session = InteractiveSession(data_context, enable_ai=False)
            session.console = MagicMock()
            session.datafusion_enabled = False

            # Should show error message
            await session._handle_datafusion_query("SELECT 1")
            # Verify error message printed
            args, kwargs = session.console.print.call_args
            assert "not available" in str(args[0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
