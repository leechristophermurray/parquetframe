//! Basic sequential workflow example.
//!
//! This example demonstrates how to create and execute a simple
//! sequential workflow with dependent steps.

use pf_workflow_core::{
    ExecutionContext, ExecutorConfig, ResourceHint, Result, Step, StepResult, WorkflowExecutor,
};
use serde_json::Value;

/// A simple data loading step.
struct LoadDataStep {
    id: String,
    source: String,
}

impl LoadDataStep {
    fn new(id: &str, source: &str) -> Self {
        Self {
            id: id.to_string(),
            source: source.to_string(),
        }
    }
}

impl Step for LoadDataStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &[]
    }

    fn execute(&self, _ctx: &mut ExecutionContext) -> Result<StepResult> {
        println!("Loading data from: {}", self.source);

        // Simulate loading data
        std::thread::sleep(std::time::Duration::from_millis(100));

        let metrics = pf_workflow_core::StepMetrics::new(self.id.clone());
        Ok(StepResult::new(
            Value::Object(serde_json::Map::from_iter([
                ("source".to_string(), Value::String(self.source.clone())),
                ("rows".to_string(), Value::Number(1000.into())),
            ])),
            metrics,
        ))
    }

    fn resource_hint(&self) -> ResourceHint {
        ResourceHint::HeavyIO
    }
}

/// A data transformation step.
struct TransformDataStep {
    id: String,
    dependencies: Vec<String>,
}

impl TransformDataStep {
    fn new(id: &str, dependencies: Vec<String>) -> Self {
        Self {
            id: id.to_string(),
            dependencies,
        }
    }
}

impl Step for TransformDataStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &self.dependencies
    }

    fn execute(&self, ctx: &mut ExecutionContext) -> Result<StepResult> {
        println!("Transforming data from dependencies");

        // Get input data from dependencies
        let mut total_rows = 0;
        for dep_id in &self.dependencies {
            if let Some(dep_output) = ctx.get(dep_id) {
                if let Some(rows) = dep_output.get("rows").and_then(|v| v.as_i64()) {
                    total_rows += rows;
                    println!("  - Processing {} rows from {}", rows, dep_id);
                }
            }
        }

        // Simulate transformation
        std::thread::sleep(std::time::Duration::from_millis(150));

        let metrics = pf_workflow_core::StepMetrics::new(self.id.clone());
        Ok(StepResult::new(
            Value::Object(serde_json::Map::from_iter([(
                "transformed_rows".to_string(),
                Value::Number(total_rows.into()),
            )])),
            metrics,
        ))
    }

    fn resource_hint(&self) -> ResourceHint {
        ResourceHint::HeavyCPU
    }
}

/// A data writing step.
struct WriteDataStep {
    id: String,
    dependencies: Vec<String>,
    destination: String,
}

impl WriteDataStep {
    fn new(id: &str, dependencies: Vec<String>, destination: &str) -> Self {
        Self {
            id: id.to_string(),
            dependencies,
            destination: destination.to_string(),
        }
    }
}

impl Step for WriteDataStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &self.dependencies
    }

    fn execute(&self, ctx: &mut ExecutionContext) -> Result<StepResult> {
        // Get transformed data
        let rows = self
            .dependencies
            .first()
            .and_then(|dep_id| ctx.get(dep_id))
            .and_then(|v| v.get("transformed_rows").and_then(|r| r.as_i64()))
            .unwrap_or(0);

        println!("Writing {} rows to: {}", rows, self.destination);

        // Simulate writing
        std::thread::sleep(std::time::Duration::from_millis(100));

        let metrics = pf_workflow_core::StepMetrics::new(self.id.clone());
        Ok(StepResult::new(
            Value::Object(serde_json::Map::from_iter([
                (
                    "destination".to_string(),
                    Value::String(self.destination.clone()),
                ),
                ("written_rows".to_string(), Value::Number(rows.into())),
            ])),
            metrics,
        ))
    }

    fn resource_hint(&self) -> ResourceHint {
        ResourceHint::HeavyIO
    }
}

fn main() -> Result<()> {
    println!("=== Basic Sequential Workflow Example ===\n");

    // Create executor with default configuration
    let config = ExecutorConfig::default();
    let mut executor = WorkflowExecutor::new(config);

    // Build a simple ETL pipeline: Extract -> Transform -> Load
    println!("Building workflow...");

    // Step 1: Load data from source
    executor.add_step(Box::new(LoadDataStep::new("extract", "database.csv")));

    // Step 2: Transform the loaded data
    executor.add_step(Box::new(TransformDataStep::new(
        "transform",
        vec!["extract".to_string()],
    )));

    // Step 3: Write transformed data
    executor.add_step(Box::new(WriteDataStep::new(
        "load",
        vec!["transform".to_string()],
        "output.parquet",
    )));

    // Execute workflow
    println!("\nExecuting workflow...\n");
    let start = std::time::Instant::now();

    let metrics = executor.execute()?;

    let duration = start.elapsed();

    // Print results
    println!("\n=== Workflow Complete ===");
    println!("Total duration: {:?}", duration);
    println!("Total steps: {}", metrics.total_steps);
    println!("Successful steps: {}", metrics.successful_steps);
    println!("Failed steps: {}", metrics.failed_steps);
    println!("\nStep details:");
    for step_metric in &metrics.step_metrics {
        println!(
            "  - {}: {:?} ({:?})",
            step_metric.step_id,
            step_metric.status,
            step_metric.duration.unwrap_or_default()
        );
    }

    Ok(())
}
