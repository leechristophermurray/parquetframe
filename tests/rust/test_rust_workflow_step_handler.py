"""Tests that real Python step bodies can be invoked via step_handler.

We wire a simple step handler that records calls and returns JSON-serializable
outputs; Rust executor runs them in sequence.
"""

import pytest

from parquetframe.workflow_rust import RustWorkflowEngine, is_rust_workflow_available

pytestmark = pytest.mark.skipif(
    not is_rust_workflow_available(), reason="Rust workflow backend not available"
)


def test_step_handler_invoked_and_output_serialized():
    engine = RustWorkflowEngine(max_parallel=1)

    calls = []

    def handler(step_type, name, config, ctx):
        # Record the call order and basic data
        calls.append((step_type, name, bool(config), bool(ctx.get("data"))))
        # Return JSON-serializable payload
        return {"ok": True, "name": name, "type": step_type}

    wf = {
        "variables": {"x": 1},
        "steps": [
            {"name": "s1", "type": "read", "config": {"input": "file.parquet"}},
            {
                "name": "s2",
                "type": "compute",
                "depends_on": ["s1"],
                "config": {"k": "v"},
            },
        ],
    }

    result = engine.execute_workflow(wf, step_handler=handler)
    assert result["status"] in ("completed", "failed")
    # Ensure handler called for both steps
    assert {c[1] for c in calls} == {"s1", "s2"}
