#!/usr/bin/env python3
"""Debug test to check mock_data_context fixture behavior."""

import asyncio
import sys
from unittest.mock import AsyncMock

# Add source paths
sys.path.insert(0, "src")
sys.path.insert(0, "tests")

from conftest import mock_data_context


async def test_mock_data_context_debug():
    """Debug test to see what our mock_data_context fixture produces."""

    # Create fixture like pytest would
    context = mock_data_context()

    print(f"Context type: {type(context)}")
    print(f"Context.execute type: {type(context.execute)}")
    print(f"Context.execute is AsyncMock: {isinstance(context.execute, AsyncMock)}")
    print(f"Context.validate_query type: {type(context.validate_query)}")
    print(
        f"Context.validate_query is AsyncMock: {isinstance(context.validate_query, AsyncMock)}"
    )

    # Test if we can await it
    try:
        result = await context.execute("SELECT 1")
        print(f"Execute result: {result}")
    except Exception as e:
        print(f"Execute failed: {e}")

    try:
        valid = await context.validate_query("SELECT 1")
        print(f"Validate result: {valid}")
    except Exception as e:
        print(f"Validate failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_mock_data_context_debug())
