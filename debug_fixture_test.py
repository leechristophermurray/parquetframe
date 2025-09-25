#!/usr/bin/env python3
"""Debug fixture behavior within pytest."""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_mock_data_context_fixture_debug(mock_data_context):
    """Test that our mock_data_context fixture works correctly."""

    print(f"Context type: {type(mock_data_context)}")
    print(f"Context.execute type: {type(mock_data_context.execute)}")
    print(
        f"Context.execute is AsyncMock: {isinstance(mock_data_context.execute, AsyncMock)}"
    )
    print(f"Context.validate_query type: {type(mock_data_context.validate_query)}")
    print(
        f"Context.validate_query is AsyncMock: {isinstance(mock_data_context.validate_query, AsyncMock)}"
    )

    # Test if we can await the methods
    try:
        result = await mock_data_context.execute("SELECT 1")
        print(f"Execute result: {result}")
        print(f"Execute result type: {type(result)}")
    except Exception as e:
        print(f"Execute failed: {e}")

    try:
        valid = await mock_data_context.validate_query("SELECT 1")
        print(f"Validate result: {valid}")
    except Exception as e:
        print(f"Validate failed: {e}")

    # Check if our fixture actually returns the expected attributes
    print(f"Has is_initialized: {hasattr(mock_data_context, 'is_initialized')}")
    print(
        f"is_initialized value: {getattr(mock_data_context, 'is_initialized', 'MISSING')}"
    )
    print(f"Has get_table_names: {hasattr(mock_data_context, 'get_table_names')}")

    # This should pass
    assert isinstance(mock_data_context.execute, AsyncMock)
    assert isinstance(mock_data_context.validate_query, AsyncMock)
