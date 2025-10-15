"""
Test fixtures and configuration for parquetframe tests.
"""

import os
import tempfile
import uuid
from collections.abc import Iterator
from pathlib import Path

# from typing import Dict - not needed, using dict directly
from unittest.mock import MagicMock

import pandas as pd
import pytest


def skip_orc_on_windows(format_name: str | None = None) -> None:
    """Skip ORC tests on Windows due to PyArrow timezone database issues.

    Args:
        format_name: The format name to check. If None, always skip on Windows.
                    If provided, only skip if format_name is 'orc'.
    """
    if os.name == "nt" and (format_name is None or format_name.lower() == "orc"):
        pytest.skip(
            "ORC tests skipped on Windows due to PyArrow timezone database issues"
        )


@pytest.fixture
def sample_small_df() -> pd.DataFrame:
    """Create a small sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": range(100),
            "name": [f"item_{i}" for i in range(100)],
            "value": range(100, 200),
            "category": ["A", "B", "C"] * 33 + ["A"],
        }
    )


@pytest.fixture
def sample_large_df() -> pd.DataFrame:
    """Create a large sample DataFrame for testing."""
    n_rows = 1_000_000  # 1M rows should be > 10MB when saved as parquet
    return pd.DataFrame(
        {
            "id": range(n_rows),
            "name": [f"item_{i}" for i in range(n_rows)],
            "value": range(n_rows),
            "category": ["A", "B", "C", "D"] * (n_rows // 4),
        }
    )


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def small_parquet_file(sample_small_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a small parquet file for testing."""
    file_path = temp_dir / "small_test.parquet"
    sample_small_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def small_pqt_file(sample_small_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a small .pqt file for testing."""
    file_path = temp_dir / "small_test.pqt"
    sample_small_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def large_parquet_file(sample_large_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a large parquet file for testing (>10MB)."""
    file_path = temp_dir / "large_test.parquet"
    sample_large_df.to_parquet(file_path)
    return file_path


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Create an empty DataFrame for testing."""
    return pd.DataFrame()


@pytest.fixture
def empty_parquet_file(empty_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create an empty parquet file for testing."""
    file_path = temp_dir / "empty_test.parquet"
    # pandas doesn't allow saving empty dataframes to parquet directly
    # so we create one with columns but no rows
    df_with_cols = pd.DataFrame(columns=["a", "b", "c"])
    df_with_cols.to_parquet(file_path)
    return file_path


@pytest.fixture
def nonexistent_file_path(temp_dir: Path) -> Path:
    """Return path to a file that doesn't exist."""
    return temp_dir / "nonexistent.parquet"


# Test data for various scenarios
@pytest.fixture
def mixed_types_df() -> pd.DataFrame:
    """DataFrame with mixed data types."""
    return pd.DataFrame(
        {
            "int_col": [1, 2, 3, 4, 5],
            "float_col": [1.1, 2.2, 3.3, 4.4, 5.5],
            "str_col": ["a", "b", "c", "d", "e"],
            "bool_col": [True, False, True, False, True],
            "datetime_col": pd.date_range("2023-01-01", periods=5),
        }
    )


@pytest.fixture
def compression_test_file(mixed_types_df: pd.DataFrame, temp_dir: Path) -> Path:
    """Create a parquet file with compression for testing."""
    file_path = temp_dir / "compressed_test.parquet"
    mixed_types_df.to_parquet(file_path, compression="snappy")
    return file_path


# AI and LLM Testing Fixtures


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for AI testing."""
    mock_client = MagicMock()

    # Mock successful chat response
    mock_client.chat.return_value = {
        "message": {"content": "SELECT COUNT(*) FROM users WHERE category = 'A';"}
    }

    # Mock model list response
    mock_client.list.return_value = {
        "models": [{"name": "llama3.2"}, {"name": "codellama"}]
    }

    return mock_client


@pytest.fixture
def mock_ollama_module(mock_ollama_client):
    """Mock the entire ollama module for comprehensive AI testing."""
    import sys

    # Create mock module
    mock_ollama = MagicMock()
    mock_ollama.Client.return_value = mock_ollama_client
    mock_ollama.chat = mock_ollama_client.chat
    mock_ollama.list = mock_ollama_client.list

    # Store original module if it exists
    original_ollama = sys.modules.get("ollama")

    # Mock the module import
    sys.modules["ollama"] = mock_ollama

    yield mock_ollama

    # Cleanup - restore original or remove
    if original_ollama is not None:
        sys.modules["ollama"] = original_ollama
    elif "ollama" in sys.modules:
        del sys.modules["ollama"]


@pytest.fixture
def sample_sql_queries() -> dict[str, str]:
    """Provide sample SQL queries for testing."""
    return {
        "simple_select": "SELECT * FROM users LIMIT 10;",
        "aggregate": "SELECT category, COUNT(*) FROM users GROUP BY category;",
        "filtered": "SELECT * FROM users WHERE value > 150;",
        "complex": """
            SELECT
                category,
                COUNT(*) as count,
                AVG(value) as avg_value,
                MAX(value) as max_value
            FROM users
            WHERE value > 100
            GROUP BY category
            HAVING COUNT(*) > 5
            ORDER BY count DESC;
        """,
        "invalid_syntax": "SELCT * FRM users;",  # Intentional syntax error
        "invalid_table": "SELECT * FROM non_existent_table;",
        "invalid_column": "SELECT non_existent_column FROM users;",
    }


@pytest.fixture
def sample_natural_language_queries() -> dict[str, str]:
    """Provide sample natural language queries for AI testing."""
    return {
        "simple": "Show me all users",
        "filtered": "Find users with value greater than 150",
        "aggregated": "How many users are in each category?",
        "complex": "Show me categories with more than 5 users and their average values",
        "ambiguous": "Show me some data",  # Intentionally vague
        "statistical": "What's the distribution of values by category?",
    }


@pytest.fixture
def mock_history_manager():
    """Mock HistoryManager for testing."""
    mock_manager = MagicMock()
    mock_manager.create_session.return_value = str(uuid.uuid4())
    mock_manager.log_query.return_value = str(uuid.uuid4())
    mock_manager.log_ai_message.return_value = str(uuid.uuid4())
    mock_manager.get_session_history.return_value = [
        {
            "query_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "query_text": "SELECT * FROM users;",
            "query_type": "sql",
            "timestamp": 1234567890.0,
            "success": True,
            "ai_generated": False,
        }
    ]
    mock_manager.get_statistics.return_value = {
        "total_sessions": 1,
        "total_queries": 5,
        "successful_queries": 4,
        "query_success_rate": 0.8,
        "total_ai_messages": 2,
        "successful_ai_messages": 2,
        "ai_success_rate": 1.0,
        "recent_sessions_7d": 1,
    }

    return mock_manager


@pytest.fixture
def mock_console():
    """Mock Rich Console for CLI testing."""
    console = MagicMock()
    console.print = MagicMock()
    return console


@pytest.fixture
def temp_parquet_dir() -> Iterator[Path]:
    """Create temporary directory with multiple parquet files for DataContext testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create sample data
        users_df = pd.DataFrame(
            {
                "id": range(1, 101),
                "name": [f"User_{i}" for i in range(1, 101)],
                "age": pd.Series([25, 30, 35, 40] * 25),
                "city": pd.Series(["New York", "London", "Tokyo", "Paris"] * 25),
                "active": pd.Series([True, False] * 50),
            }
        )

        sales_df = pd.DataFrame(
            {
                "order_id": [f"ORD-{i:06d}" for i in range(1, 51)],
                "user_id": pd.Series(range(1, 21)) * 2 + [21],  # 50 orders
                "amount": pd.Series([100.0, 250.0, 75.0] * 16 + [200.0, 300.0]),
                "product": pd.Series(
                    ["Widget", "Gadget", "Tool"] * 16 + ["Widget", "Gadget"]
                ),
            }
        )

        # Save as parquet files
        users_df.to_parquet(temp_path / "users.parquet")
        sales_df.to_parquet(temp_path / "sales.parquet")

        # Create subdirectory with archived data
        archive_dir = temp_path / "archive"
        archive_dir.mkdir()
        users_df.head(20).to_parquet(archive_dir / "users_archive.parquet")

        yield temp_path


# Database testing fixtures
@pytest.fixture
def sample_database_engine():
    """Create in-memory SQLite database with sample data."""
    from sqlalchemy import create_engine, text

    engine = create_engine("sqlite:///:memory:")

    # Create sample tables
    with engine.connect() as conn:
        # Users table
        conn.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                city TEXT,
                active BOOLEAN
            )
        """
            )
        )

        # Insert sample data
        conn.execute(
            text(
                """
            INSERT INTO users (name, age, city, active)
            VALUES
                ('Alice', 30, 'New York', 1),
                ('Bob', 25, 'London', 1),
                ('Charlie', 35, 'Tokyo', 0),
                ('Diana', 28, 'Paris', 1),
                ('Eve', 32, 'New York', 1)
        """
            )
        )

        # Sales table
        conn.execute(
            text(
                """
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                amount REAL,
                product TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
            )
        )

        conn.execute(
            text(
                """
            INSERT INTO sales (user_id, amount, product)
            VALUES
                (1, 100.50, 'Widget'),
                (2, 250.75, 'Gadget'),
                (1, 75.25, 'Tool'),
                (3, 300.00, 'Widget'),
                (4, 125.00, 'Gadget')
        """
            )
        )

        conn.commit()

    return engine


# Parametrized fixtures for comprehensive testing
@pytest.fixture(params=[True, False])
def ai_enabled(request) -> bool:
    """Parametrize tests with AI enabled/disabled."""
    return request.param


@pytest.fixture(params=["parquet", "database"])
def data_source_type(request) -> str:
    """Parametrize tests across different data source types."""
    return request.param
