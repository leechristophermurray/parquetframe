"""
Integration tests for Interactive CLI with all features.

Tests the complete workflow:
- Magic commands + DataFusion
- Permissions + SQL queries
- RAG integration
- Graph algorithms with utilities
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.integration
@pytest.mark.asyncio
class TestInteractiveCLIIntegration:
    """Integration tests for complete Interactive CLI workflows."""

    async def test_magic_sql_with_permissions(self):
        """Test SQL magic command with permission checks."""
        from parquetframe.interactive import InteractiveSession
        from parquetframe.datacontext import DataContext

        # Create temp data
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame(
                {
                    "id": [1, 2, 3],
                    "name": ["Alice", "Bob", "Charlie"],
                    "department": ["Engineering", "Sales", "Engineering"],
                }
            )
            parquet_path = Path(tmpdir) / "users.parquet"
            df.to_parquet(parquet_path)

            # Create session
            with patch("parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
                data_context = MagicMock(spec=DataContext)
                data_context.source_location = tmpdir
                data_context.source_type.value = "parquet"
                data_context.get_table_names.return_value = ["users"]
                data_context.execute = AsyncMock(return_value=df)

                session = InteractiveSession(data_context, enable_ai=False)

                # Grant permission
                session._handle_permissions_command(
                    "grant user:alice viewer table:users"
                )

                # Check permission
                session._handle_permissions_command(
                    "check user:alice viewer table:users"
                )

                # Execute SQL query
                await session._handle_query(
                    "SELECT * FROM users WHERE department = 'Engineering'"
                )

                # Verify permission was granted
                assert not session.permission_store.is_empty()

    async def test_datafusion_with_python_variables(self):
        """Test DataFusion integration with Python variable inspection."""
        from parquetframe.interactive import InteractiveSession
        from parquetframe.datacontext import DataContext

        with patch("parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            data_context = MagicMock(spec=DataContext)
            data_context.source_location = "/tmp/test"
            data_context.source_type.value = "parquet"

            session = InteractiveSession(data_context, enable_ai=False)

            # Mock DataFusion context
            session.datafusion_enabled = True
            session.datafusion_ctx = MagicMock()
            mock_df = MagicMock()
            result_df = pd.DataFrame({"count": [42]})
            mock_df.to_pandas.return_value = result_df
            session.datafusion_ctx.sql.return_value = mock_df

            # Execute %df query
            await session._handle_datafusion_query("SELECT COUNT(*) as count FROM data")

            # Verify execution
            session.datafusion_ctx.sql.assert_called_once()


@pytest.mark.integration
class TestGraphAlgorithmIntegration:
    """Integration tests for graph algorithms with utilities."""

    def test_graph_backend_selection_workflow(self):
        """Test complete graph algorithm workflow with backend selection."""
        from parquetframe.graph.algo.utils import (
            select_backend,
            validate_sources,
            create_result_dataframe,
        )

        # Create mock graph
        graph = MagicMock()
        graph.vertices._df = pd.DataFrame({"id": range(10)})
        graph.vertices.islazy = False
        graph.edges._df = pd.DataFrame({"src": [0, 1, 2], "dst": [1, 2, 3]})
        graph.edges.islazy = False
        graph.edges.__len__ = MagicMock(return_value=3)

        # Select backend
        backend = select_backend(graph, "auto", "bfs")
        assert backend in ["pandas", "dask"]

        # Validate sources
        sources = validate_sources(graph, [0, 1])
        assert sources == [0, 1]

        # Create result
        data = {"vertex": [0, 1, 2], "distance": [0, 1, 2]}
        result = create_result_dataframe(data, ["vertex", "distance"])
        assert len(result) == 3
        assert list(result.columns) == ["vertex", "distance"]

    def test_graph_edge_symmetrization_workflow(self):
        """Test edge symmetrization for undirected algorithms."""
        from parquetframe.graph.algo.utils import symmetrize_edges

        graph = MagicMock()
        graph.is_directed = True
        graph.edges._df = pd.DataFrame(
            {"src": [0, 1, 2, 3], "dst": [1, 2, 3, 0], "weight": [1.0, 2.0, 3.0, 4.0]}
        )

        # Symmetrize
        sym_edges = symmetrize_edges(graph, directed=True)

        # Should have forward and backward edges
        assert len(sym_edges) >= 4

        # Check specific reverse edge exists
        assert ((sym_edges["src"] == 1) & (sym_edges["dst"] == 0)).any()


@pytest.mark.integration
class TestEntityForeignKeyIntegration:
    """Integration tests for entity foreign key validation."""

    def test_entity_relationship_validation_workflow(self):
        """Test complete entity relationship workflow."""
        from parquetframe.entity.relationship import RelationshipManager, Relationship

        manager = RelationshipManager()

        # Define relationship
        rel = Relationship(
            name="task_assignee",
            source_entity="Task",
            target_entity="User",
            foreign_key="assignee_id",
            relationship_type="many_to_one",
        )
        manager.register(rel)

        # Mock entity store
        entity_store = MagicMock()
        users_df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
        tasks_df = pd.DataFrame(
            {
                "id": [101, 102, 103],
                "title": ["Task A", "Task B", "Task C"],
                "assignee_id": [1, 2, 99],  # 99 is invalid
            }
        )

        entity_store.get_entity.side_effect = lambda name: (
            users_df if name == "User" else tasks_df
        )
        manager.set_entity_store(entity_store)

        # Validate foreign keys
        assert manager.validate_foreign_key("Task", "User", 1)  # Valid
        assert manager.validate_foreign_key("Task", "User", 2)  # Valid
        assert not manager.validate_foreign_key("Task", "User", 99)  # Invalid

        # Get relationships
        rels = manager.get_relationships("Task")
        assert len(rels) == 1
        assert rels[0].foreign_key == "assignee_id"


@pytest.mark.integration
@pytest.mark.asyncio
class TestRAGPermissionsIntegration:
    """Integration tests for RAG with permissions."""

    async def test_rag_query_with_permission_filtering(self):
        """Test RAG query with permission-based filtering."""
        from parquetframe.ai.config import AIConfig
        from parquetframe.ai.rag_pipeline import SimpleRagPipeline

        # Create config
        config = AIConfig()
        config.rag_enabled_entities = {"Task", "Project"}
        config.retrieval_k = 5

        # Mock entity store
        entity_store = MagicMock()
        entity_store.get_entities.return_value = [
            {"id": 1, "title": "Task 1", "priority": "high"},
            {"id": 2, "title": "Task 2", "priority": "low"},
        ]

        # Mock LLM
        with patch.object(config, "get_model") as mock_model:
            mock_llm = MagicMock()
            mock_llm.generate.return_value = "Found 2 high priority tasks"
            mock_model.return_value = mock_llm

            # Create RAG pipeline
            rag = SimpleRagPipeline(config, entity_store)

            # Run query
            result = rag.run_query("Show me high priority tasks", "user:alice")

            # Verify
            assert "response_text" in result
            assert "context_used" in result
            assert result["user_context"] == "user:alice"


@pytest.mark.integration
class TestPerformanceBenchmarks:
    """Performance benchmarks for new features."""

    def test_graph_utils_performance(self):
        """Benchmark graph utilities with larger datasets."""
        from parquetframe.graph.algo.utils import (
            validate_sources,
            create_result_dataframe,
        )
        import time

        # Large graph
        graph = MagicMock()
        graph.vertices._df = pd.DataFrame({"id": range(10000)})

        start = time.time()
        sources = validate_sources(graph, list(range(100)))
        elapsed = time.time() - start

        assert len(sources) == 100
        assert elapsed < 1.0  # Should be fast

    def test_foreign_key_validation_performance(self):
        """Benchmark foreign key validation with large datasets."""
        from parquetframe.entity.relationship import RelationshipManager
        import time

        manager = RelationshipManager()

        # Large entity table
        entity_store = MagicMock()
        entity_store.get_entity.return_value = pd.DataFrame(
            {"id": range(10000), "name": [f"Entity_{i}" for i in range(10000)]}
        )
        manager.set_entity_store(entity_store)

        start = time.time()
        for i in range(100):
            manager.validate_foreign_key("Task", "User", i * 10)
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should handle 100 validations quickly


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
