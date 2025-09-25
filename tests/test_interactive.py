"""
Tests for interactive CLI functionality.

This module provides basic testing for the interactive CLI, focusing on:
- Session initialization
- Dependency handling
- Basic functionality validation
"""

import os
import platform
from unittest.mock import patch

import pytest

from src.parquetframe.exceptions import DependencyError
from src.parquetframe.interactive import InteractiveSession


# Helper to detect CI environment on Windows
def is_windows_ci():
    """Detect if running in Windows CI environment."""
    return platform.system() == "Windows" and (
        "GITHUB_ACTIONS" in os.environ
        or "CI" in os.environ
        or "RUNNER_OS" in os.environ
    )


class TestInteractiveSessionInitialization:
    """Test interactive session initialization."""

    @pytest.mark.skipif(is_windows_ci(), reason="Windows CI lacks console buffer")
    def test_initialization_with_valid_data_context(self, temp_parquet_dir):
        """Test successful initialization with valid DataContext."""
        from src.parquetframe.datacontext import DataContextFactory

        # Skip if interactive dependencies not available
        with patch("src.parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            with patch("src.parquetframe.interactive.LLMAgent") as mock_agent:
                mock_agent.side_effect = DependencyError("ollama", "AI")

                data_context = DataContextFactory.create_from_path(temp_parquet_dir)
                session = InteractiveSession(data_context, enable_ai=False)

                assert session.data_context == data_context
                assert session.console is not None
                assert not session.ai_enabled

    @pytest.mark.skipif(is_windows_ci(), reason="Windows CI lacks console buffer")
    def test_initialization_with_ai_enabled(self, temp_parquet_dir, mock_ollama_module):
        """Test initialization with AI features enabled."""
        from src.parquetframe.datacontext import DataContextFactory

        with patch("src.parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
                data_context = DataContextFactory.create_from_path(temp_parquet_dir)
                session = InteractiveSession(data_context, enable_ai=True)

                assert session.data_context == data_context
                assert session.ai_enabled is True

    def test_initialization_without_interactive_deps(self, temp_parquet_dir):
        """Test initialization failure when interactive deps are missing."""
        from src.parquetframe.datacontext import DataContextFactory

        with patch("src.parquetframe.interactive.INTERACTIVE_AVAILABLE", False):
            data_context = DataContextFactory.create_from_path(temp_parquet_dir)

            with pytest.raises(DependencyError) as exc_info:
                InteractiveSession(data_context)

            assert "prompt_toolkit or rich" in str(exc_info.value)


class TestInteractiveSessionUtilities:
    """Test utility methods in interactive session."""

    def test_interactive_available_import(self):
        """Test that we can import the interactive module."""
        from src.parquetframe.interactive import INTERACTIVE_AVAILABLE

        # Should be a boolean
        assert isinstance(INTERACTIVE_AVAILABLE, bool)

    @pytest.mark.skipif(is_windows_ci(), reason="Windows CI lacks console buffer")
    def test_session_id_generation(self, temp_parquet_dir):
        """Test session ID generation."""
        from src.parquetframe.datacontext import DataContextFactory

        with patch("src.parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            with patch("src.parquetframe.interactive.LLMAgent") as mock_agent:
                mock_agent.side_effect = DependencyError("ollama", "AI")

                data_context = DataContextFactory.create_from_path(temp_parquet_dir)
                session = InteractiveSession(data_context, enable_ai=False)

                # Should have a session ID
                assert hasattr(session, "session_id")
                assert isinstance(session.session_id, str)

    def test_ai_agent_initialization_failure(self, temp_parquet_dir):
        """Test that AI agent failures are handled gracefully."""
        from src.parquetframe.datacontext import DataContextFactory

        with patch("src.parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            with patch("src.parquetframe.interactive.LLMAgent") as mock_agent:
                mock_agent.side_effect = Exception("AI initialization failed")

                data_context = DataContextFactory.create_from_path(temp_parquet_dir)
                # Should not raise an exception
                session = InteractiveSession(data_context, enable_ai=True)

                # AI should be disabled due to failure
                assert not session.ai_enabled


class TestBasicFunctionality:
    """Test basic interactive session functionality."""

    @pytest.mark.skipif(is_windows_ci(), reason="Windows CI lacks console buffer")
    def test_console_creation(self, temp_parquet_dir):
        """Test that console is properly created."""
        from src.parquetframe.datacontext import DataContextFactory

        with patch("src.parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            with patch("src.parquetframe.interactive.LLMAgent") as mock_agent:
                mock_agent.side_effect = DependencyError("ollama", "AI")

                data_context = DataContextFactory.create_from_path(temp_parquet_dir)
                session = InteractiveSession(data_context, enable_ai=False)

                # Should have rich Console
                assert hasattr(session, "console")
                assert session.console is not None

    @pytest.mark.skipif(is_windows_ci(), reason="Windows CI lacks console buffer")
    def test_history_manager_creation(self, temp_parquet_dir):
        """Test that history manager is created."""
        from src.parquetframe.datacontext import DataContextFactory

        with patch("src.parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
            with patch("src.parquetframe.interactive.LLMAgent") as mock_agent:
                mock_agent.side_effect = DependencyError("ollama", "AI")

                data_context = DataContextFactory.create_from_path(temp_parquet_dir)
                session = InteractiveSession(data_context, enable_ai=False)

                # Should have history manager
                assert hasattr(session, "history_manager")
                assert session.history_manager is not None
