from unittest.mock import MagicMock, patch

import pytest

from parquetframe.datacontext import DataContext
from parquetframe.interactive import InteractiveSession
from parquetframe.permissions.core import RelationTuple


@pytest.fixture
def mock_data_context():
    dc = MagicMock(spec=DataContext)
    dc.source_location = "/tmp/test"
    # Mock the source_type enum
    mock_enum = MagicMock()
    mock_enum.value = "parquet"
    dc.source_type = mock_enum
    dc.get_table_names.return_value = ["table1"]
    return dc


@pytest.fixture
def session(mock_data_context):
    with patch("parquetframe.interactive.INTERACTIVE_AVAILABLE", True):
        session = InteractiveSession(mock_data_context, enable_ai=False)
        # Mock console to capture output
        session.console = MagicMock()
        return session


@pytest.mark.asyncio
async def test_magic_permissions(session):
    # Test grant
    session._handle_permissions_command("grant user:alice viewer doc:doc1")
    assert not session.permission_store.is_empty()
    tuple_obj = RelationTuple("doc", "doc1", "viewer", "user", "alice")
    assert session.permission_store.has_tuple(tuple_obj)

    # Test check
    session._handle_permissions_command("check user:alice viewer doc:doc1")
    # Verify console output contains success message
    args, _ = session.console.print.call_args
    assert "GRANTED" in str(args[0])

    # Test revoke
    session._handle_permissions_command("revoke user:alice viewer doc:doc1")
    assert session.permission_store.is_empty()

    # Test check after revoke
    session._handle_permissions_command("check user:alice viewer doc:doc1")
    args, _ = session.console.print.call_args
    assert "DENIED" in str(args[0])


@pytest.mark.asyncio
async def test_magic_datafusion(session):
    # Mock DataFusion context
    session.datafusion_enabled = True
    session.datafusion_ctx = MagicMock()
    mock_df = MagicMock()
    mock_df.to_pandas.return_value = "pandas_df"
    session.datafusion_ctx.sql.return_value = mock_df

    # Test %df magic
    await session._handle_datafusion_query("SELECT * FROM table1")

    session.datafusion_ctx.sql.assert_called_with("SELECT * FROM table1")
    mock_df.to_pandas.assert_called_once()


@pytest.mark.asyncio
async def test_magic_rag(session):
    # Test %rag magic
    await session._handle_rag_command("test query")
    # Verify placeholder message
    args, _ = session.console.print.call_args
    assert "placeholder" in str(args[0])
