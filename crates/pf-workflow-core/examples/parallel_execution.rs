//! Parallel workflow execution example.
//!
//! This example demonstrates parallel execution of independent steps
//! and shows the performance benefits of parallelism.

use pf_workflow_core::{
    ExecutionContext, ExecutorConfig, ResourceHint, Result, Step, StepMetrics, StepResult,
    WorkflowExecutor,
};
use serde_json::Value;
use std::time::{Duration, Instant};

/// A step that simulates processing a data partition.
struct ProcessPartitionStep {
    id: String,
    partition_id: usize,
    processing_time_ms: u64,
}

impl ProcessPartitionStep {
    fn new(partition_id: usize, processing_time_ms: u64) -> Self {
        Self {
            id: format!("partition_{}", partition_id),
            partition_id,
            processing_time_ms,
        }
    }
}

impl Step for ProcessPartitionStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &[]
    }

    fn execute(&self, _ctx: &mut ExecutionContext) -> Result<StepResult> {
        println!("Processing partition {}...", self.partition_id);
        std::thread::sleep(Duration::from_millis(self.processing_time_ms));

        let metrics = StepMetrics::new(self.id.clone());
        Ok(StepResult::new(
            Value::Object(serde_json::Map::from_iter([
                (
                    "partition_id".to_string(),
                    Value::Number(self.partition_id.into()),
                ),
                ("rows_processed".to_string(), Value::Number(10000.into())),
            ])),
            metrics,
        ))
    }

    fn resource_hint(&self) -> ResourceHint {
        ResourceHint::HeavyCPU
    }
}

/// A step that aggregates results from multiple partitions.
struct AggregateStep {
    id: String,
    dependencies: Vec<String>,
}

impl AggregateStep {
    fn new(dependencies: Vec<String>) -> Self {
        Self {
            id: "aggregate".to_string(),
            dependencies,
        }
    }
}

impl Step for AggregateStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &self.dependencies
    }

    fn execute(&self, ctx: &mut ExecutionContext) -> Result<StepResult> {
        println!(
            "Aggregating results from {} partitions...",
            self.dependencies.len()
        );

        let mut total_rows = 0;
        for dep_id in &self.dependencies {
            if let Some(output) = ctx.get(dep_id) {
                if let Some(rows) = output.get("rows_processed").and_then(|v| v.as_i64()) {
                    total_rows += rows;
                }
            }
        }

        std::thread::sleep(Duration::from_millis(50));

        let metrics = StepMetrics::new(self.id.clone());
        Ok(StepResult::new(
            Value::Object(serde_json::Map::from_iter([(
                "total_rows".to_string(),
                Value::Number(total_rows.into()),
            )])),
            metrics,
        ))
    }

    fn resource_hint(&self) -> ResourceHint {
        ResourceHint::LightCPU
    }
}

fn main() -> Result<()> {
    println!("=== Parallel Workflow Execution Example ===\n");

    let num_partitions = 8;
    let processing_time_per_partition = 100; // ms
    let max_parallel = 4;

    // Create executor with parallel configuration
    let config = ExecutorConfig::builder()
        .max_parallel_steps(max_parallel)
        .build();
    let mut executor = WorkflowExecutor::new(config);

    println!("Building workflow with {} partitions...", num_partitions);
    println!("Max parallel steps: {}\n", max_parallel);

    // Add partition processing steps (all independent)
    let mut partition_ids = Vec::new();
    for i in 0..num_partitions {
        let step = ProcessPartitionStep::new(i, processing_time_per_partition);
        partition_ids.push(step.id.clone());
        executor.add_step(Box::new(step));
    }

    // Add aggregation step that depends on all partitions
    executor.add_step(Box::new(AggregateStep::new(partition_ids)));

    // Execute sequentially for comparison
    println!("--- Sequential Execution ---");
    let mut seq_executor = WorkflowExecutor::new(ExecutorConfig::default());
    for i in 0..num_partitions {
        seq_executor.add_step(Box::new(ProcessPartitionStep::new(
            i,
            processing_time_per_partition,
        )));
    }

    let seq_start = Instant::now();
    let seq_metrics = seq_executor.execute()?;
    let seq_duration = seq_start.elapsed();

    println!(
        "Sequential completed in {:?} ({} steps)\n",
        seq_duration, seq_metrics.successful_steps
    );

    // Execute in parallel
    println!("--- Parallel Execution ---");
    let par_start = Instant::now();
    let par_metrics = executor.execute_parallel()?;
    let par_duration = par_start.elapsed();

    println!(
        "Parallel completed in {:?} ({} steps + 1 aggregate)",
        par_duration, num_partitions
    );

    // Calculate speedup
    let speedup = seq_duration.as_secs_f64() / par_duration.as_secs_f64();

    println!("\n=== Performance Comparison ===");
    println!("Sequential duration: {:?}", seq_duration);
    println!("Parallel duration: {:?}", par_duration);
    println!("Speedup: {:.2}x", speedup);
    println!("Parallelism factor: {:.2}", par_metrics.parallelism_factor);
    println!(
        "Efficiency: {:.1}%",
        (speedup / max_parallel as f64) * 100.0
    );

    println!("\nExpected vs Actual:");
    println!(
        "  Expected time (ideal): ~{}ms",
        (num_partitions as u64 * processing_time_per_partition) / max_parallel as u64 + 50
    );
    println!("  Actual time: {}ms", par_duration.as_millis());

    Ok(())
}
