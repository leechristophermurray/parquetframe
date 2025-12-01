"""
Tests for Knowlogy library management.
"""

from unittest.mock import MagicMock, patch

import pytest

from parquetframe.knowlogy import list_libraries
from parquetframe.knowlogy.library import LibraryManager


class TestLibraryManager:
    """Test library management."""

    def test_list_libraries(self):
        """Test listing available libraries."""
        libs = list_libraries()
        assert "statistics" in libs
        assert isinstance(libs["statistics"], str)

    @patch("parquetframe.knowlogy.library.Path.exists")
    @patch("parquetframe.knowlogy.library.subprocess.run")
    def test_load_library_success(self, mock_run, mock_exists):
        """Test successful library load."""
        mock_exists.return_value = True  # Pretend script exists
        mock_run.return_value = MagicMock(returncode=0, stdout="Loaded!")

        result = LibraryManager.load_library("statistics")
        assert result is True
        mock_run.assert_called_once()

    def test_load_unknown_library(self):
        """Test loading unknown library raises error."""
        with pytest.raises(ValueError):
            LibraryManager.load_library("nonexistent")
