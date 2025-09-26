"""
Tests for AI agent functionality.

This module provides comprehensive testing for the LLM agent, including:
- Query generation from natural language
- Self-correction capabilities
- Error handling and dependency management
- Prompt engineering and template building
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.parquetframe.ai.agent import LLMAgent, QueryResult
from src.parquetframe.ai.prompts import QueryPromptBuilder
from src.parquetframe.exceptions import DependencyError


class TestLLMAgentInitialization:
    """Test LLM agent initialization and dependency handling."""

    def test_initialization_with_ollama_available(self, mock_ollama_module):
        """Test successful initialization when ollama is available."""
        # Mock OLLAMA_AVAILABLE to be True
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            agent = LLMAgent(model_name="llama3.2")

            assert agent.model_name == "llama3.2"
            assert agent.max_retries == 2
            assert agent.temperature == 0.1
            assert not agent.use_multi_step

    def test_initialization_without_ollama(self):
        """Test initialization failure when ollama is not available."""
        with patch.dict("sys.modules", {"ollama": None}):
            with pytest.raises(DependencyError) as exc_info:
                LLMAgent()

            assert "ollama" in str(exc_info.value)
            assert "pip install ollama" in str(exc_info.value)

    def test_initialization_with_custom_parameters(self, mock_ollama_module):
        """Test initialization with custom parameters."""
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            agent = LLMAgent(
                model_name="codellama",
                max_retries=5,
                use_multi_step=True,
                temperature=0.3,
            )

            assert agent.model_name == "codellama"
            assert agent.max_retries == 5
            assert agent.use_multi_step
            assert agent.temperature == 0.3

    def test_model_verification_success(self, mock_ollama_module, mock_ollama_client):
        """Test successful model verification."""
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                mock_ollama_client.list.return_value = {
                    "models": [{"name": "llama3.2"}, {"name": "codellama"}]
                }

                # Should not raise an exception
                agent = LLMAgent(model_name="llama3.2")
                assert agent.model_name == "llama3.2"

    def test_model_verification_warning(
        self, mock_ollama_module, mock_ollama_client, caplog
    ):
        """Test warning when model is not available."""
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                mock_ollama_client.list.return_value = {
                    "models": [{"name": "codellama"}]
                }

                agent = LLMAgent(model_name="llama3.2")

                # Should log a warning but continue
                assert "Model 'llama3.2' not found" in caplog.text
                assert agent.model_name == "llama3.2"


class TestQueryGeneration:
    """Test query generation functionality."""

    @pytest.fixture
    def mock_data_context(self):
        """Mock DataContext for testing."""
        context = MagicMock()
        context.is_initialized = True

        # Properly mock async initialize method
        context.initialize = AsyncMock()

        context.get_table_names.return_value = ["users", "sales"]
        context.get_schema_as_text.return_value = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            city TEXT
        );
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            product TEXT
        );
        """

        # Mock successful query execution with proper async mock
        mock_result = MagicMock()
        mock_result.__len__ = MagicMock(return_value=5)
        context.execute = AsyncMock(return_value=mock_result)

        # Mock query validation method
        context.validate_query = AsyncMock(return_value=True)

        return context

    @pytest.mark.asyncio
    async def test_simple_query_generation(
        self, mock_ollama_module, mock_ollama_client, mock_data_context
    ):
        """Test simple query generation from natural language."""
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                # Setup mock response
                mock_ollama_client.chat.return_value = {
                    "message": {
                        "content": "```sql\nSELECT * FROM users WHERE age > 30;\n```"
                    }
                }

                agent = LLMAgent()
                result = await agent.generate_query(
                    "Show me users older than 30", mock_data_context
                )

                assert result.success
                assert "SELECT * FROM users WHERE age > 30;" in result.query
                assert result.result is not None
                assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_query_generation_with_context_initialization(
        self, mock_ollama_module, mock_ollama_client
    ):
        """Test query generation when DataContext needs initialization."""
        # Create mock context that needs initialization
        context = MagicMock()
        context.is_initialized = False
        context.initialize = AsyncMock()
        context.get_table_names.return_value = ["users"]
        context.get_schema_as_text.return_value = (
            "CREATE TABLE users (id INTEGER, name TEXT);"
        )

        mock_result = MagicMock()
        mock_result.__len__ = MagicMock(return_value=3)
        context.execute = AsyncMock(return_value=mock_result)
        context.validate_query = AsyncMock(return_value=True)

        mock_ollama_client.chat.return_value = {
            "message": {"content": "SELECT * FROM users;"}
        }

        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent()
                result = await agent.generate_query("Show all users", context)

                # Verify context was initialized
                context.initialize.assert_called_once()
                assert result.success

    @pytest.mark.asyncio
    async def test_multi_step_query_generation(
        self, mock_ollama_module, mock_ollama_client, mock_data_context
    ):
        """Test multi-step query generation for complex queries."""
        # Mock table selection response
        mock_ollama_client.chat.side_effect = [
            # First call: table selection
            {"message": {"content": "users, sales"}},
            # Second call: actual query generation
            {
                "message": {
                    "content": "SELECT u.name, SUM(s.amount) FROM users u JOIN sales s ON u.id = s.user_id GROUP BY u.name;"
                }
            },
        ]

        # Add table schema method to mock
        mock_data_context.get_table_schema.return_value = {
            "columns": [
                {"name": "id", "sql_type": "INTEGER"},
                {"name": "name", "sql_type": "TEXT"},
            ]
        }

        # Use multi-step approach
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent(use_multi_step=True)
                result = await agent.generate_query(
                    "Show me total sales by user name", mock_data_context
                )

                assert result.success
                assert "JOIN" in result.query
                assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_query_self_correction(
        self, mock_ollama_module, mock_ollama_client, mock_data_context
    ):
        """Test self-correction when initial query fails."""
        # Mock failed execution followed by successful retry
        mock_data_context.execute.side_effect = [
            Exception("Table 'user' doesn't exist"),  # First attempt fails
            MagicMock(),  # Second attempt succeeds
        ]

        # Mock LLM responses: initial query, then corrected query
        mock_ollama_client.chat.side_effect = [
            {"message": {"content": "SELECT * FROM user;"}},  # Wrong table name
            {"message": {"content": "SELECT * FROM users;"}},  # Corrected query
        ]

        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent()
                result = await agent.generate_query(
                    "Show me all users", mock_data_context
                )

                assert result.success
                assert result.attempts == 2
                assert "users" in result.query

    @pytest.mark.asyncio
    async def test_query_max_retries_exceeded(
        self, mock_ollama_module, mock_ollama_client, mock_data_context
    ):
        """Test behavior when max retries are exceeded."""
        # Mock continuous failures
        mock_data_context.execute.side_effect = Exception("Persistent error")

        mock_ollama_client.chat.return_value = {
            "message": {"content": "SELECT * FROM invalid_table;"}
        }

        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent(max_retries=2)
                result = await agent.generate_query("Show me data", mock_data_context)

                assert not result.success
                assert result.attempts > 1
                assert "Persistent error" in result.error

    @pytest.mark.asyncio
    async def test_query_generation_ollama_error(
        self, mock_ollama_module, mock_ollama_client, mock_data_context
    ):
        """Test handling of Ollama API errors."""
        mock_ollama_client.chat.side_effect = Exception("Ollama connection failed")

        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent()
                result = await agent.generate_query("Show me users", mock_data_context)

            assert not result.success
            assert "Ollama connection failed" in result.error


class TestQueryResultProcessing:
    """Test query result processing and extraction."""

    def test_query_result_creation(self):
        """Test QueryResult creation and properties."""
        result = QueryResult(
            success=True,
            query="SELECT * FROM users;",
            result=MagicMock(),
            error=None,
            attempts=1,
            execution_time_ms=123.45,
        )

        assert result.success
        assert not result.failed
        assert result.query == "SELECT * FROM users;"
        assert result.execution_time_ms == 123.45
        assert result.attempts == 1

    def test_failed_query_result(self):
        """Test failed QueryResult properties."""
        result = QueryResult(
            success=False, query=None, result=None, error="Query failed", attempts=3
        )

        assert not result.success
        assert result.failed
        assert result.error == "Query failed"
        assert result.attempts == 3


class TestPromptBuilding:
    """Test prompt template building functionality."""

    def test_query_prompt_builder(self):
        """Test basic query prompt building."""
        builder = QueryPromptBuilder()
        schema = "CREATE TABLE users (id INTEGER, name TEXT);"

        prompt = builder.build_for_context(schema, "users")

        assert "CREATE TABLE users" in prompt
        assert "SQL" in prompt
        assert "translate" in prompt.lower() and "question" in prompt.lower()

    def test_prompt_builder_with_no_main_table(self):
        """Test prompt building without a main table specified."""
        builder = QueryPromptBuilder()
        schema = "CREATE TABLE users (id INTEGER, name TEXT);"

        prompt = builder.build_for_context(schema, None)

        assert "CREATE TABLE users" in prompt
        assert isinstance(prompt, str)


class TestAIAgentIntegration:
    """Integration tests for AI agent with various scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.ai
    async def test_end_to_end_query_workflow(
        self, mock_ollama_module, mock_ollama_client, temp_parquet_dir
    ):
        """Test complete query workflow from natural language to results."""
        from src.parquetframe.datacontext import DataContextFactory

        # Create real DataContext with test data
        data_context = DataContextFactory.create_from_path(temp_parquet_dir)
        await data_context.initialize()

        # Mock successful SQL generation
        mock_ollama_client.chat.return_value = {
            "message": {"content": "SELECT COUNT(*) as user_count FROM users;"}
        }

        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            # Also patch the ollama module usage in the agent
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent()
                result = await agent.generate_query(
                    "How many users are there?", data_context
                )

                assert result.success
                assert "COUNT" in result.query.upper()
                assert result.result is not None

    @pytest.mark.asyncio
    @pytest.mark.ai
    async def test_natural_language_variations(
        self,
        mock_ollama_module,
        mock_ollama_client,
        sample_natural_language_queries,
    ):
        """Test various natural language query patterns."""
        # Create mock data context for this test
        mock_data_context = MagicMock()
        mock_data_context.is_initialized = True
        mock_data_context.execute = AsyncMock(return_value=MagicMock())

        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent()

                # Test different types of queries
                test_cases = [
                    ("simple", "SELECT * FROM users;"),
                    ("filtered", "SELECT * FROM users WHERE value > 150;"),
                    (
                        "aggregated",
                        "SELECT category, COUNT(*) FROM users GROUP BY category;",
                    ),
                ]

                for query_type, expected_sql in test_cases:
                    mock_ollama_client.chat.return_value = {
                        "message": {"content": expected_sql}
                    }

                    nl_query = sample_natural_language_queries[query_type]
                    result = await agent.generate_query(nl_query, mock_data_context)

                    assert result.success, f"Failed for query type: {query_type}"
                    assert result.query is not None


class TestErrorHandling:
    """Test comprehensive error handling in AI agent."""

    @pytest.mark.asyncio
    async def test_dependency_error_propagation(self):
        """Test that dependency errors are properly propagated."""
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", False):
            with pytest.raises(DependencyError) as exc_info:
                LLMAgent()

            error = exc_info.value
            assert error.missing_package == "ollama"
            assert "AI-powered query generation" in error.feature

    @pytest.mark.asyncio
    async def test_ai_error_on_model_verification_failure(self, mock_ollama_module):
        """Test AI error when model verification fails catastrophically."""
        # Mock a complete failure in model verification
        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            # Patch the module-level ollama to simulate the mock
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                mock_ollama_module.list.side_effect = Exception("API Error")
                # Should log warning but not fail initialization
                agent = LLMAgent()
                assert agent.model_name == "llama3.2"

    @pytest.mark.asyncio
    async def test_graceful_handling_of_empty_responses(
        self, mock_ollama_module, mock_ollama_client
    ):
        """Test handling of empty or malformed responses from LLM."""
        # Create mock data context for this test
        mock_data_context = MagicMock()
        mock_data_context.is_initialized = True

        mock_ollama_client.chat.return_value = {
            "message": {"content": ""}  # Empty response
        }

        with patch("src.parquetframe.ai.agent.OLLAMA_AVAILABLE", True):
            with patch("src.parquetframe.ai.agent.ollama", mock_ollama_module):
                agent = LLMAgent()
                result = await agent.generate_query("Show me users", mock_data_context)

                assert not result.success
                assert "Failed to generate query" in result.error
