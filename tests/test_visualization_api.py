"""
Tests for high-level visualization API.
"""

from unittest.mock import MagicMock, patch

import pytest

from parquetframe.visualization import visualize_store


class TestVisualizationAPI:
    """Test visualization API."""

    @patch("parquetframe.visualization.is_visualization_available")
    @patch("parquetframe.visualization.registry")
    @patch("parquetframe.visualization.EntityStore")
    @patch("parquetframe.visualization.entities_to_networkx")
    @patch("parquetframe.visualization.visualize_with_pyvis")
    def test_visualize_store(
        self, mock_pyvis, mock_nx_conv, mock_store_cls, mock_registry, mock_avail
    ):
        """Test visualize_store function."""
        # Mock availability
        mock_avail.return_value = {"networkx": True, "pyvis": True}

        # Mock registry and store
        mock_registry.list_entities.return_value = ["User"]
        mock_registry.get.return_value = MagicMock()

        mock_store = MagicMock()
        mock_store.find_all.return_value = [MagicMock()]
        mock_store_cls.return_value = mock_store

        # Mock graph conversion
        mock_nx_conv.return_value = MagicMock()

        # Mock pyvis output
        mock_pyvis.return_value = "graph.html"

        # Call function
        result = visualize_store(output_path="test.html")

        assert result == "graph.html"
        mock_registry.list_entities.assert_called_once()
        mock_store.find_all.assert_called_once()
        mock_nx_conv.assert_called_once()
        mock_pyvis.assert_called_once()

    @patch("parquetframe.visualization.is_visualization_available")
    def test_visualize_missing_deps(self, mock_avail):
        """Test error when dependencies missing."""
        mock_avail.return_value = {"networkx": False, "pyvis": True}

        with pytest.raises(ImportError):
            visualize_store()
