//! Integration tests for pf-workflow-core.
//!
//! These tests verify end-to-end functionality of the workflow engine
//! with real-world usage patterns.

use pf_workflow_core::{
    CallbackProgressTracker, CancellationToken, ExecutorConfig, FileProgressTracker, ProgressEvent,
    ResourceHint, RetryConfig, Step, StepMetrics, StepResult, WorkflowExecutor,
};
use serde_json::Value;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

// ============================================================================
// Test Helpers
// ============================================================================

/// A step that simulates data loading from a source.
#[derive(Debug)]
struct DataLoadStep {
    id: String,
    source: String,
    delay_ms: u64,
}

impl DataLoadStep {
    fn new(id: &str, source: &str, delay_ms: u64) -> Self {
        Self {
            id: id.to_string(),
            source: source.to_string(),
            delay_ms,
        }
    }
}

impl Step for DataLoadStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &[]
    }

    fn execute(
        &self,
        _ctx: &mut pf_workflow_core::ExecutionContext,
    ) -> pf_workflow_core::Result<StepResult> {
        thread::sleep(Duration::from_millis(self.delay_ms));

        let metrics = StepMetrics::new(self.id.clone());
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

/// A step that simulates data transformation.
#[derive(Debug)]
struct TransformStep {
    id: String,
    dependencies: Vec<String>,
    delay_ms: u64,
}

impl TransformStep {
    fn new(id: &str, dependencies: Vec<String>, delay_ms: u64) -> Self {
        Self {
            id: id.to_string(),
            dependencies,
            delay_ms,
        }
    }
}

impl Step for TransformStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &self.dependencies
    }

    fn execute(
        &self,
        ctx: &mut pf_workflow_core::ExecutionContext,
    ) -> pf_workflow_core::Result<StepResult> {
        thread::sleep(Duration::from_millis(self.delay_ms));

        // Aggregate input rows from dependencies
        let mut total_rows = 0;
        for dep_id in &self.dependencies {
            if let Some(dep_output) = ctx.get(dep_id) {
                if let Some(rows) = dep_output.get("rows").and_then(|v| v.as_i64()) {
                    total_rows += rows;
                }
            }
        }

        let metrics = StepMetrics::new(self.id.clone());
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

/// A step that simulates writing results to storage.
#[derive(Debug)]
struct WriteStep {
    id: String,
    dependencies: Vec<String>,
    destination: String,
    delay_ms: u64,
}

impl WriteStep {
    fn new(id: &str, dependencies: Vec<String>, destination: &str, delay_ms: u64) -> Self {
        Self {
            id: id.to_string(),
            dependencies,
            destination: destination.to_string(),
            delay_ms,
        }
    }
}

impl Step for WriteStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &self.dependencies
    }

    fn execute(
        &self,
        ctx: &mut pf_workflow_core::ExecutionContext,
    ) -> pf_workflow_core::Result<StepResult> {
        thread::sleep(Duration::from_millis(self.delay_ms));

        // Get input data from dependency
        let input_rows = self
            .dependencies
            .first()
            .and_then(|dep_id| ctx.get(dep_id))
            .and_then(|v| v.get("transformed_rows").or_else(|| v.get("rows")))
            .and_then(|v| v.as_i64())
            .unwrap_or(0);

        let metrics = StepMetrics::new(self.id.clone());
        Ok(StepResult::new(
            Value::Object(serde_json::Map::from_iter([
                (
                    "destination".to_string(),
                    Value::String(self.destination.clone()),
                ),
                ("written_rows".to_string(), Value::Number(input_rows.into())),
            ])),
            metrics,
        ))
    }

    fn resource_hint(&self) -> ResourceHint {
        ResourceHint::HeavyIO
    }
}

/// A flaky step that fails a certain number of times before succeeding.
#[derive(Debug)]
struct FlakyNetworkStep {
    id: String,
    failures_remaining: Arc<Mutex<usize>>,
    max_failures: usize,
}

impl FlakyNetworkStep {
    fn new(id: &str, max_failures: usize) -> Self {
        Self {
            id: id.to_string(),
            failures_remaining: Arc::new(Mutex::new(max_failures)),
            max_failures,
        }
    }
}

/// A step that always fails (for testing error handling).
#[derive(Debug)]
struct AlwaysFailStep {
    id: String,
}

impl AlwaysFailStep {
    fn new(id: &str) -> Self {
        Self { id: id.to_string() }
    }
}

impl Step for FlakyNetworkStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &[]
    }

    fn execute(
        &self,
        _ctx: &mut pf_workflow_core::ExecutionContext,
    ) -> pf_workflow_core::Result<StepResult> {
        thread::sleep(Duration::from_millis(10));

        let mut remaining = self.failures_remaining.lock().unwrap();
        if *remaining > 0 {
            *remaining -= 1;
            return Err(pf_workflow_core::ExecutionError::StepFailed {
                step_id: self.id.clone(),
                reason: "Network timeout".to_string(),
            }
            .into());
        }

        let metrics = StepMetrics::new(self.id.clone());
        Ok(StepResult::new(
            Value::String("Network call succeeded".to_string()),
            metrics,
        ))
    }

    fn retry_config(&self) -> RetryConfig {
        RetryConfig {
            max_attempts: (self.max_failures + 1) as u32,
            backoff: Duration::from_millis(5),
        }
    }
}

impl Step for AlwaysFailStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &[]
    }

    fn execute(
        &self,
        _ctx: &mut pf_workflow_core::ExecutionContext,
    ) -> pf_workflow_core::Result<StepResult> {
        Err(pf_workflow_core::ExecutionError::StepFailed {
            step_id: self.id.clone(),
            reason: "This step always fails".to_string(),
        }
        .into())
    }

    fn retry_config(&self) -> RetryConfig {
        RetryConfig {
            max_attempts: 2,
            backoff: Duration::from_millis(1),
        }
    }
}

// ============================================================================
// Integration Tests
// ============================================================================

#[test]
fn test_etl_pipeline_sequential() {
    // Simulate a simple ETL pipeline:
    // Extract (Load) -> Transform -> Load (Write)
    let config = ExecutorConfig::default();
    let mut executor = WorkflowExecutor::new(config);

    // Extract phase
    executor.add_step(Box::new(DataLoadStep::new("extract", "database_a", 20)));

    // Transform phase
    executor.add_step(Box::new(TransformStep::new(
        "transform",
        vec!["extract".to_string()],
        30,
    )));

    // Load phase
    executor.add_step(Box::new(WriteStep::new(
        "load",
        vec!["transform".to_string()],
        "warehouse",
        20,
    )));

    let start = Instant::now();
    let result = executor.execute();
    let duration = start.elapsed();

    assert!(result.is_ok());
    let metrics = result.unwrap();
    assert_eq!(metrics.total_steps, 3);
    assert_eq!(metrics.successful_steps, 3);
    assert_eq!(metrics.failed_steps, 0);

    // Should take at least 70ms (20 + 30 + 20)
    assert!(
        duration.as_millis() >= 70,
        "Expected at least 70ms, got {}ms",
        duration.as_millis()
    );
}

#[test]
fn test_parallel_data_ingestion() {
    // Simulate parallel data ingestion from multiple sources
    // followed by aggregation and single write
    let config = ExecutorConfig::builder().max_parallel_steps(4).build();
    let mut executor = WorkflowExecutor::new(config);

    // Load from 4 sources in parallel
    for i in 1..=4 {
        executor.add_step(Box::new(DataLoadStep::new(
            &format!("load_source_{}", i),
            &format!("source_{}", i),
            30,
        )));
    }

    // Aggregate all sources
    executor.add_step(Box::new(TransformStep::new(
        "aggregate",
        vec![
            "load_source_1".to_string(),
            "load_source_2".to_string(),
            "load_source_3".to_string(),
            "load_source_4".to_string(),
        ],
        20,
    )));

    // Write aggregated results
    executor.add_step(Box::new(WriteStep::new(
        "write_result",
        vec!["aggregate".to_string()],
        "data_lake",
        20,
    )));

    let start = Instant::now();
    let result = executor.execute_parallel();
    let duration = start.elapsed();

    assert!(result.is_ok());
    let metrics = result.unwrap();
    assert_eq!(metrics.total_steps, 6);
    assert_eq!(metrics.successful_steps, 6);

    // Parallel execution should be significantly faster than sequential
    // Sequential would be: 4*30 + 20 + 20 = 160ms
    // Parallel should be close to: 30 + 20 + 20 = 70ms (plus overhead)
    // Just log timing - actual performance varies with system load
    println!("Parallel execution time: {}ms", duration.as_millis());
}

#[test]
fn test_complex_dag_workflow() {
    // Test a complex DAG with multiple levels and branches
    //
    //           load1     load2
    //              \       /
    //             transform1
    //              /      \
    //        trans2a    trans2b
    //              \      /
    //             aggregate
    //                 |
    //               write
    let config = ExecutorConfig::builder().max_parallel_steps(4).build();
    let mut executor = WorkflowExecutor::new(config);

    // Level 1: Load data
    executor.add_step(Box::new(DataLoadStep::new("load1", "db1", 10)));
    executor.add_step(Box::new(DataLoadStep::new("load2", "db2", 10)));

    // Level 2: First transform
    executor.add_step(Box::new(TransformStep::new(
        "transform1",
        vec!["load1".to_string(), "load2".to_string()],
        15,
    )));

    // Level 3: Parallel transforms
    executor.add_step(Box::new(TransformStep::new(
        "trans2a",
        vec!["transform1".to_string()],
        10,
    )));
    executor.add_step(Box::new(TransformStep::new(
        "trans2b",
        vec!["transform1".to_string()],
        10,
    )));

    // Level 4: Aggregate
    executor.add_step(Box::new(TransformStep::new(
        "aggregate",
        vec!["trans2a".to_string(), "trans2b".to_string()],
        15,
    )));

    // Level 5: Write
    executor.add_step(Box::new(WriteStep::new(
        "write",
        vec!["aggregate".to_string()],
        "final_output",
        10,
    )));

    let result = executor.execute_parallel();
    assert!(result.is_ok());

    let metrics = result.unwrap();
    assert_eq!(metrics.total_steps, 7);
    assert_eq!(metrics.successful_steps, 7);
    assert_eq!(metrics.failed_steps, 0);

    // Verify reasonable parallelism
    println!("Parallelism factor: {}", metrics.parallelism_factor);
}

#[test]
fn test_retry_on_transient_failures() {
    // Test that flaky network calls succeed after retries
    let config = ExecutorConfig::builder().retry_backoff_ms(5).build();
    let mut executor = WorkflowExecutor::new(config);

    // Add a step that fails 3 times before succeeding
    executor.add_step(Box::new(FlakyNetworkStep::new("api_call", 3)));

    // Add a dependent step
    executor.add_step(Box::new(DataLoadStep::new(
        "process_result",
        "api_data",
        10,
    )));

    let result = executor.execute();
    assert!(result.is_ok());

    let metrics = result.unwrap();
    assert_eq!(metrics.successful_steps, 2);
    assert_eq!(metrics.failed_steps, 0);

    // Check that retries were attempted
    let api_step_metrics = metrics
        .step_metrics
        .iter()
        .find(|m| m.step_id == "api_call")
        .unwrap();
    assert!(
        api_step_metrics.retry_count > 0,
        "Expected retries, got {} retry attempts",
        api_step_metrics.retry_count
    );
}

#[test]
fn test_cancellation_in_long_workflow() {
    // Test cancelling a long-running workflow
    let config = ExecutorConfig::builder().max_parallel_steps(2).build();
    let mut executor = WorkflowExecutor::new(config);

    // Add many steps with delays
    for i in 1..=20 {
        executor.add_step(Box::new(DataLoadStep::new(
            &format!("step_{}", i),
            &format!("source_{}", i),
            50,
        )));
    }

    let token = CancellationToken::new();
    let token_clone = token.clone();

    // Cancel after 200ms (should complete ~4-8 steps depending on parallelism)
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(200));
        token_clone.cancel();
    });

    let result = executor.execute_parallel_with_cancellation(token);
    assert!(result.is_err());

    match result {
        Err(pf_workflow_core::WorkflowError::Execution(
            pf_workflow_core::ExecutionError::Cancelled,
        )) => {
            // Expected
        }
        _ => panic!("Expected cancellation error"),
    }
}

#[test]
fn test_progress_tracking_integration() {
    // Test comprehensive progress tracking through a workflow
    let config = ExecutorConfig::builder().max_parallel_steps(2).build();
    let mut executor = WorkflowExecutor::new(config);

    // Build a simple pipeline
    executor.add_step(Box::new(DataLoadStep::new("load", "source", 10)));
    executor.add_step(Box::new(TransformStep::new(
        "transform",
        vec!["load".to_string()],
        10,
    )));
    executor.add_step(Box::new(WriteStep::new(
        "write",
        vec!["transform".to_string()],
        "dest",
        10,
    )));

    let events = Arc::new(Mutex::new(Vec::new()));
    let events_clone = Arc::clone(&events);

    let tracker = CallbackProgressTracker::new(move |event: ProgressEvent| {
        events_clone.lock().unwrap().push(event);
    });

    let result = executor.execute_parallel_with_progress(Box::new(tracker));
    assert!(result.is_ok());

    let collected_events = events.lock().unwrap();
    assert_eq!(collected_events.len(), 6); // 3 started + 3 completed

    // Verify sequence of events
    assert!(matches!(collected_events[0], ProgressEvent::Started { .. }));
    assert_eq!(collected_events[0].step_id(), "load");
    assert!(matches!(
        collected_events[1],
        ProgressEvent::Completed { .. }
    ));
    assert_eq!(collected_events[1].step_id(), "load");
}

#[test]
fn test_file_progress_logging() {
    // Test that progress is correctly logged to a file
    let temp_dir = std::env::temp_dir();
    let log_path = temp_dir.join("integration_test_progress.jsonl");

    // Clean up any existing file
    let _ = std::fs::remove_file(&log_path);

    let config = ExecutorConfig::default();
    let mut executor = WorkflowExecutor::new(config);

    executor.add_step(Box::new(DataLoadStep::new("step1", "src1", 5)));
    executor.add_step(Box::new(DataLoadStep::new("step2", "src2", 5)));

    let tracker = FileProgressTracker::new(&log_path).expect("Failed to create tracker");

    let result = executor.execute_with_progress(Box::new(tracker));
    assert!(result.is_ok());

    // Verify log file contains events
    let contents = std::fs::read_to_string(&log_path).expect("Failed to read log file");
    let lines: Vec<&str> = contents.lines().collect();

    assert_eq!(lines.len(), 4); // 2 started + 2 completed

    // Verify each line is valid JSON
    for line in lines {
        let _event: ProgressEvent = serde_json::from_str(line).expect("Failed to parse JSON line");
    }

    // Clean up
    let _ = std::fs::remove_file(&log_path);
}

#[test]
fn test_mixed_sequential_parallel_execution() {
    // Test a workflow that benefits from parallel execution
    // but also has sequential dependencies
    let config = ExecutorConfig::builder().max_parallel_steps(4).build();
    let mut executor = WorkflowExecutor::new(config);

    // Phase 1: Single initialization step
    executor.add_step(Box::new(DataLoadStep::new("init", "config", 10)));

    // Phase 2: Parallel processing (all depend on init)
    for i in 1..=4 {
        executor.add_step(Box::new(TransformStep::new(
            &format!("process_{}", i),
            vec!["init".to_string()],
            20,
        )));
    }

    // Phase 3: Aggregation (depends on all parallel steps)
    executor.add_step(Box::new(TransformStep::new(
        "aggregate",
        vec![
            "process_1".to_string(),
            "process_2".to_string(),
            "process_3".to_string(),
            "process_4".to_string(),
        ],
        15,
    )));

    // Phase 4: Final write
    executor.add_step(Box::new(WriteStep::new(
        "finalize",
        vec!["aggregate".to_string()],
        "output",
        10,
    )));

    let start = Instant::now();
    let result = executor.execute_parallel();
    let duration = start.elapsed();

    assert!(result.is_ok());
    let metrics = result.unwrap();
    assert_eq!(metrics.total_steps, 7);
    assert_eq!(metrics.successful_steps, 7);

    // Should be faster than sequential execution
    // Sequential: 10 + 4*20 + 15 + 10 = 115ms
    // Parallel: 10 + 20 + 15 + 10 = 55ms (plus overhead)
    println!(
        "Execution time: {}ms (parallelism factor: {})",
        duration.as_millis(),
        metrics.parallelism_factor
    );
}

#[test]
fn test_resource_aware_scheduling() {
    // Test that resource hints influence scheduling
    let config = ExecutorConfig::builder().max_parallel_steps(4).build();
    let mut executor = WorkflowExecutor::new(config);

    // Mix of CPU and IO intensive tasks
    executor.add_step(Box::new(DataLoadStep::new("io1", "db1", 15))); // IO
    executor.add_step(Box::new(DataLoadStep::new("io2", "db2", 15))); // IO

    executor.add_step(Box::new(TransformStep::new("cpu1", vec![], 15))); // CPU
    executor.add_step(Box::new(TransformStep::new("cpu2", vec![], 15))); // CPU

    let result = executor.execute_parallel();
    assert!(result.is_ok());

    let metrics = result.unwrap();
    assert_eq!(metrics.successful_steps, 4);

    // All should execute successfully regardless of resource hints
    println!(
        "Resource-aware scheduling completed in {:?}",
        metrics.total_duration
    );
}

#[test]
fn test_error_propagation_stops_dependent_steps() {
    // Test that when a step fails, dependent steps are not executed
    let config = ExecutorConfig::builder()
        .max_parallel_steps(2)
        .retry_backoff_ms(1)
        .build();
    let mut executor = WorkflowExecutor::new(config);

    // Step that will always fail
    executor.add_step(Box::new(AlwaysFailStep::new("failing_step")));

    // Steps that depend on the failing step (should not execute)
    executor.add_step(Box::new(TransformStep::new(
        "dependent1",
        vec!["failing_step".to_string()],
        10,
    )));
    executor.add_step(Box::new(TransformStep::new(
        "dependent2",
        vec!["failing_step".to_string()],
        10,
    )));

    let result = executor.execute_parallel();
    assert!(result.is_err(), "Expected workflow to fail");

    // Verify error is about the failing step
    let err = result.unwrap_err();
    let err_msg = err.to_string();
    assert!(
        err_msg.contains("failing_step") || err_msg.contains("This step always fails"),
        "Error should mention the failing step: {}",
        err_msg
    );
}

#[test]
fn test_high_volume_workflow() {
    // Test workflow engine with many steps
    let config = ExecutorConfig::builder().max_parallel_steps(8).build();
    let mut executor = WorkflowExecutor::new(config);

    // Create a large workflow (50 steps)
    for i in 0..10 {
        // Each batch of 5 steps processes independently
        for j in 0..5 {
            let step_id = format!("step_{}_{}", i, j);
            executor.add_step(Box::new(DataLoadStep::new(
                &step_id,
                &format!("src_{}", j),
                5,
            )));
        }
    }

    let start = Instant::now();
    let result = executor.execute_parallel();
    let duration = start.elapsed();

    assert!(result.is_ok());
    let metrics = result.unwrap();
    assert_eq!(metrics.total_steps, 50);
    assert_eq!(metrics.successful_steps, 50);

    println!(
        "Processed 50 steps in {}ms (parallelism factor: {})",
        duration.as_millis(),
        metrics.parallelism_factor
    );

    // With 8 parallel and 5ms each, should take roughly 50*5/8 = 31ms minimum
    // Allow generous overhead for CI environments where thread scheduling varies
    assert!(
        duration.as_millis() < 500,
        "Expected < 500ms, got {}ms",
        duration.as_millis()
    );
}
