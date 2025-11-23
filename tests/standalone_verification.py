import sys
from unittest.mock import MagicMock, patch

# Mock modules before importing interactive
sys.modules["pandas"] = MagicMock()
sys.modules["datafusion"] = MagicMock()
sys.modules["prompt_toolkit"] = MagicMock()
sys.modules["rich"] = MagicMock()
sys.modules["rich.console"] = MagicMock()
sys.modules["rich.panel"] = MagicMock()
sys.modules["rich.table"] = MagicMock()

# Now import the module under test
# We need to mock the imports inside interactive.py as well if they are not already mocked by sys.modules
with patch.dict(
    sys.modules,
    {
        "parquetframe.datacontext": MagicMock(),
        "parquetframe.exceptions": MagicMock(),
        "parquetframe.history": MagicMock(),
        "parquetframe.ai": MagicMock(),
        "parquetframe.permissions.core": MagicMock(),
    },
):
    # We need to manually load the file content and exec it because of the imports
    # or just rely on the fact that we mocked the dependencies.
    # However, interactive.py imports from .datacontext which is relative.
    # So we need to be in the package or set up the path.
    pass

# Actually, let's just create a test that mocks the class directly if we can import it.
# Since we can't import it easily without dependencies, we will rely on the fact that I modified the code correctly.
# But I really want to verify it.

# Let's try to run a script that defines the mocks and then execs the file content.
file_path = "src/parquetframe/interactive.py"
with open(file_path) as f:
    code = f.read()

# Remove relative imports for standalone execution or mock them
code = code.replace("from .ai", "from ai_mock")
code = code.replace("from .datacontext", "from datacontext_mock")
code = code.replace("from .exceptions", "from exceptions_mock")
code = code.replace("from .history", "from history_mock")
code = code.replace("from .permissions.core", "from permissions_mock")
code = code.replace("from .cli.context", "from context_mock")


# Define mocks
class MockObject:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return MagicMock()

    def __getattr__(self, name):
        return MagicMock()


class DependencyError(Exception):
    def __init__(self, **kwargs):
        pass


sys.modules["ai_mock"] = MagicMock()
sys.modules["datacontext_mock"] = MagicMock()
sys.modules["exceptions_mock"] = MagicMock()
sys.modules["exceptions_mock"].DependencyError = DependencyError
sys.modules["history_mock"] = MagicMock()
sys.modules["permissions_mock"] = MagicMock()
sys.modules["context_mock"] = MagicMock()

# Execute the modified code
# We need to capture the globals from exec to access the class
g = globals().copy()
exec(code, g)
InteractiveSession = g["InteractiveSession"]
# Force INTERACTIVE_AVAILABLE to True
g["INTERACTIVE_AVAILABLE"] = True


# Now we can test the class InteractiveSession
async def run_tests():
    print("Running standalone tests...")

    # Setup
    data_context = MagicMock()
    # We need to pass the globals where InteractiveSession was defined so it sees INTERACTIVE_AVAILABLE
    # But InteractiveSession looks up INTERACTIVE_AVAILABLE in its module globals.
    # Since we used exec(code, g), the module globals are g.
    # So we need to instantiate it using the class from g.

    # However, methods inside InteractiveSession will use globals from g.
    # So we need to make sure g is consistent.

    # Let's patch the class's __init__ to skip the check or ensure the global is seen.
    # Actually, since we set g["INTERACTIVE_AVAILABLE"] = True, it should be fine.

    session = InteractiveSession(data_context, enable_ai=False)
    session.console = MagicMock()
    session.permission_store = MagicMock()
    session.datafusion_ctx = MagicMock()
    session.datafusion_enabled = True

    # Test %permissions
    print("Testing %permissions...")
    session._handle_permissions_command("grant user:alice viewer doc:doc1")
    session.permission_store.add_tuple.assert_called()
    print("  %permissions grant passed")

    session._handle_permissions_command("check user:alice viewer doc:doc1")
    session.permission_store.has_tuple.assert_called()
    print("  %permissions check passed")

    # Test %df
    print("Testing %df...")
    await session._handle_datafusion_query("SELECT 1")
    session.datafusion_ctx.sql.assert_called_with("SELECT 1")
    print("  %df passed")

    # Test %rag
    print("Testing %rag...")
    await session._handle_rag_command("query")
    # Just check it didn't crash and printed something
    session.console.print.assert_called()
    print("  %rag passed")

    print("All standalone tests passed!")


import asyncio

asyncio.run(run_tests())
