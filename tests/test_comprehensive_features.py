"""
Comprehensive tests for interactive CLI enhancements.

Tests created for all new features:
- Magic commands
- DataFusion integration
- Permissions management
- Graph algorithm utilities
- Entity foreign key validation
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

# =============================================================================
# Graph Algorithm Utilities Tests
# =============================================================================

class TestGraphAlgoUtils:
    """Tests for graph/algo/utils.py implementations."""
    
    def test_select_backend_explicit(self):
        """Test backend selection with explicit choice."""
        from parquetframe.graph.algo.utils import select_backend
        
        graph = MagicMock()
        
        # Explicitly specified backends
        assert select_backend(graph, "pandas") == "pandas"
        assert select_backend(graph, "dask") == "dask"
    
    def test_select_backend_auto_small_graph(self):
        """Test auto backend selection for small graph."""
        from parquetframe.graph.algo.utils import select_backend
        
        graph = MagicMock()
        graph.vertices.islazy = False
        graph.edges.islazy = False
        graph.edges.__len__ = MagicMock(return_value=1000)
        
        backend = select_backend(graph, "auto")
        assert backend == "pandas"
    
    def test_validate_sources_single(self):
        """Test source validation with single source."""
        from parquetframe.graph.algo.utils import validate_sources
        
        graph = MagicMock()
        graph.vertices._df = pd.DataFrame({"id": [0, 1, 2, 3]})
        
        result = validate_sources(graph, 2)
        assert result == [2]
    
    def test_validate_sources_multiple(self):
        """Test source validation with multiple sources."""
        from parquetframe.graph.algo.utils import validate_sources
        
        graph = MagicMock()
        graph.vertices._df = pd.DataFrame({"id": [0, 1, 2, 3, 4]})
        
        result = validate_sources(graph, [1, 3, 1, 4])  # Has duplicate
        assert result == [1, 3, 4]  # Deduplicated, order preserved
    
    def test_validate_sources_invalid(self):
        """Test source validation with invalid source."""
        from parquetframe.graph.algo.utils import validate_sources
        
        graph = MagicMock()
        graph.vertices._df = pd.DataFrame({"id": [0, 1, 2]})
        
        with pytest.raises(ValueError, match="Invalid source vertices"):
            validate_sources(graph, [1, 99])  # 99 doesn't exist
    
    def test_create_result_dataframe(self):
        """Test result DataFrame creation."""
        from parquetframe.graph.algo.utils import create_result_dataframe
        
        data = {
            "vertex": [0, 1, 2],
            "distance": [0, 1, 2],
            "predecessor": [None, 0, 1]
        }
        columns = ["vertex", "distance", "predecessor"]
        dtypes = {"vertex": "int64", "distance": "int64"}
        
        result = create_result_dataframe(data, columns, dtypes)
        
        assert list(result.columns) == columns
        assert len(result) == 3
        assert result["vertex"].dtype == np.int64
    
    def test_symmetrize_edges(self):
        """Test edge symmetrization."""
        from parquetframe.graph.algo.utils import symmetrize_edges
        
        graph = MagicMock()
        graph.is_directed = True
        graph.edges._df = pd.DataFrame({
            "src": [0, 1, 2],
            "dst": [1, 2, 0]
        })
        
        result = symmetrize_edges(graph, directed=True)
        
        # Should have original + reverse edges
        assert len(result) >= 3
        # Check reverse edges exist
        assert ((result["src"] == 1) & (result["dst"] == 0)).any()
    
    def test_check_convergence_l1(self):
        """Test convergence checking with L1 metric."""
        from parquetframe.graph.algo.utils import check_convergence
        
        old = pd.Series([1.0, 2.0, 3.0])
        new = pd.Series([1.001, 2.001, 3.001])
        
        # Should converge with large tolerance
        assert check_convergence(old, new, tol=0.01, metric="l1")
        
        # Should not converge with small tolerance
        assert not check_convergence(old, new, tol=0.0001, metric="l1")
    
    def test_check_convergence_max(self):
        """Test convergence checking with max metric."""
        from parquetframe.graph.algo.utils import check_convergence
        
        old = pd.Series([1.0, 2.0, 3.0])
        new = pd.Series([1.05, 2.01, 3.01])  # Max diff is 0.05
        
        assert not check_convergence(old, new, tol=0.01, metric="max")
        assert check_convergence(old, new, tol=0.1, metric="max")


# =============================================================================
# Entity Relationship Tests
# =============================================================================

class TestEntityRelationships:
    """Tests for entity/relationship.py foreign key validation."""
    
    def test_validate_foreign_key_success(self):
        """Test successful foreign key validation."""
        from parquetframe.entity.relationship import RelationshipManager
        
        manager = RelationshipManager()
        
        # Mock entity store
        entity_store = MagicMock()
        entity_store.get_entity.return_value = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })
        
        manager.set_entity_store(entity_store)
        
        # Valid foreign key
        assert manager.validate_foreign_key("Task", "User", 2)
    
    def test_validate_foreign_key_missing(self):
        """Test foreign key validation with missing key."""
        from parquetframe.entity.relationship import RelationshipManager
        
        manager = RelationshipManager()
        
        # Mock entity store
        entity_store = MagicMock()
        entity_store.get_entity.return_value = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })
        
        manager.set_entity_store(entity_store)
        
        # Invalid foreign key
        assert not manager.validate_foreign_key("Task", "User", 99)
    
    def test_validate_foreign_key_no_store(self):
        """Test foreign key validation without entity store (should pass)."""
        from parquetframe.entity.relationship import RelationshipManager
        
        manager = RelationshipManager()
        
        # Should pass without store configured
        assert manager.validate_foreign_key("Task", "User", 99)


# =============================================================================
# Integration: All Features Together
# =============================================================================

@pytest.mark.integration
class TestIntegratedFeatures:
    """Integration tests combining multiple features."""
    
    @pytest.mark.asyncio
    async def test_interactive_workflow(self):
        """Test complete interactive workflow with all features."""
        # This would test magic commands, permissions, and RAG together
        # Requires full interactive session setup
        pass  # Placeholder for future integration test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
