# Advanced Workflow Features

This page details advanced patterns for ParquetFrame YAML workflows, including variables, conditionals, retries/timeouts, resource hints, progress/cancellation, and Rust executor usage. Examples are self‑contained and runnable.

## Variables and Interpolation

You can pass variables on the CLI or define them in the YAML under `settings.variables`. Use `${var}` syntax in step params.

```yaml
settings:
  variables:
    input_path: data/users.parquet
    min_age: 30

pipeline:
  - name: load
    operation: read_parquet
    params:
      path: "${input_path}"

  - name: filter
    operation: query
    depends_on: [load]
    params:
      expr: "age >= ${min_age}"
```

CLI override:

```bash
pframe workflow pipeline.yml --variables "input_path=data/users.pqt,min_age=35"
```

## Conditional Execution and Branching

Use `when` expressions to gate steps based on variables or prior results (simple JSONPath-like selectors on prior step outputs).

```yaml
- name: maybe_aggregate
  operation: groupby_agg
  depends_on: [filter]
  when: "${min_age} >= 30"
  params:
    by: [city]
    agg: {amount: [sum, mean]}
```

## Retries and Timeouts

Configure per-step retry/timeout via `retry_policy` and `timeout_ms`.

```yaml
- name: fetch_remote
  operation: read_csv
  params:
    path: https://example.com/data.csv
  retry_policy:
    max_attempts: 3
    backoff_ms: [250, 1000, 3000]
  timeout_ms: 10000
```

## Resource Hints and Parallelism

Help the scheduler place work onto CPU or I/O pools and cap parallelism.

```yaml
settings:
  engine: rust
  max_parallel: 8

pipeline:
  - name: compute_stats
    operation: describe
    resource_hint: cpu_bound

  - name: write_out
    operation: to_parquet
    resource_hint: io_bound
```

## Progress and Cancellation

Register a progress callback and cancel long runs using a token (Python API shown here; CLI uses defaults).

```python
from parquetframe.workflows import CancellationToken
from parquetframe.workflow_rust import execute_workflow_rust

workflow = {
  "steps": [
    {"name": "load", "type": "read", "config": {"path": "data.parquet"}},
    {"name": "agg", "type": "groupby_agg", "depends_on": ["load"], "config": {"by": ["city"], "agg": {"amount": ["sum"]}}}
  ]
}

token = CancellationToken()
result = execute_workflow_rust(workflow, max_parallel=4)
```

## Rust Executor Usage

When available, the Rust workflow engine executes DAGs in parallel for 10–15× speedups. Set `settings.engine: rust` or rely on auto‑detection. Fallback remains Python.

## Best Practices

- Keep steps small and composable; prefer explicit dependencies.
- Use variables for file paths and tunables; keep YAML portable.
- Emit intermediate outputs to simplify debugging; leverage history/visualization.

## Python Step Handlers

For custom step logic (beyond built-in `read/filter/select/groupby/save/transform`), provide a Python step handler to the Rust engine. The handler receives `(step_type, name, config, ctx)` and returns JSON-serializable results.

```python
from parquetframe.workflow_rust import RustWorkflowEngine

def handler(step_type, name, config, ctx):
    # Access prior outputs: ctx['data']
    # Access variables: ctx.get('variables')
    # Execute your logic here and return JSON-serializable data
    return {"ok": True, "step": name}

wf = {
  "variables": {"threshold": 5},
  "steps": [
    {"name": "s1", "type": "read", "config": {"input": "file.parquet"}},
    {"name": "s2", "type": "compute", "depends_on": ["s1"], "config": {"k": "v"}},
  ],
}

engine = RustWorkflowEngine(max_parallel=2)
result = engine.execute_workflow(wf, step_handler=handler)
```

Guidelines:
- Keep handler return values small; store big artifacts externally and pass references.
- Use variables for tunables; interpolate as needed in config.
- Combine with progress/cancellation from above.

## Related Documentation

- [Workflow Overview](index.md)
- [Step Types](step-types.md)
- [Visualization](visualization.md)
- [Rust Workflow Engine](../rust-acceleration/workflow-engine.md)
