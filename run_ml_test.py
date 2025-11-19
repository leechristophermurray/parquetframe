import os

from parquetframe._rustic import run_workflow

workflow_path = os.path.abspath("examples/ml_pipeline.pf.yml")
print(f"Running workflow: {workflow_path}")
try:
    run_workflow(workflow_path)
    print("Workflow completed successfully.")
except Exception as e:
    print(f"Workflow failed: {e}")
