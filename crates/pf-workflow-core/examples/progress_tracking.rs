//! Progress tracking example.
//!
//! This example demonstrates different ways to track workflow progress
//! using callbacks and file-based logging.

use pf_workflow_core::{
    CallbackProgressTracker, ConsoleProgressCallback, ExecutionContext, ExecutorConfig,
    FileProgressTracker, ProgressEvent, Result, Step, StepMetrics, StepResult, WorkflowExecutor,
};
use serde_json::Value;
use std::sync::{Arc, Mutex};
use std::time::Duration;

/// A simple processing step with configurable delay.
struct ProcessStep {
    id: String,
    dependencies: Vec<String>,
    delay_ms: u64,
}

impl ProcessStep {
    fn new(id: &str, dependencies: Vec<String>, delay_ms: u64) -> Self {
        Self {
            id: id.to_string(),
            dependencies,
            delay_ms,
        }
    }
}

impl Step for ProcessStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &self.dependencies
    }

    fn execute(&self, _ctx: &mut ExecutionContext) -> Result<StepResult> {
        std::thread::sleep(Duration::from_millis(self.delay_ms));

        let metrics = StepMetrics::new(self.id.clone());
        Ok(StepResult::new(Value::Null, metrics))
    }
}

/// Custom progress tracker that collects statistics.
struct StatsTracker {
    started: Arc<Mutex<usize>>,
    completed: Arc<Mutex<usize>>,
    failed: Arc<Mutex<usize>>,
}

impl StatsTracker {
    fn new() -> Self {
        Self {
            started: Arc::new(Mutex::new(0)),
            completed: Arc::new(Mutex::new(0)),
            failed: Arc::new(Mutex::new(0)),
        }
    }

    fn get_stats(&self) -> (usize, usize, usize) {
        (
            *self.started.lock().unwrap(),
            *self.completed.lock().unwrap(),
            *self.failed.lock().unwrap(),
        )
    }

    fn into_callback(self) -> CallbackProgressTracker<impl Fn(ProgressEvent) + Send + Sync> {
        let started = Arc::clone(&self.started);
        let completed = Arc::clone(&self.completed);
        let failed = Arc::clone(&self.failed);

        CallbackProgressTracker::new(move |event: ProgressEvent| {
            match event {
                ProgressEvent::Started { .. } => {
                    *started.lock().unwrap() += 1;
                }
                ProgressEvent::Completed { .. } => {
                    *completed.lock().unwrap() += 1;
                }
                ProgressEvent::Failed { .. } => {
                    *failed.lock().unwrap() += 1;
                }
                ProgressEvent::Cancelled { .. } => {
                    // Count as neither completed nor failed
                }
            }
        })
    }
}

fn example_console_progress() -> Result<()> {
    println!("=== Example 1: Console Progress Tracking ===\n");

    let config = ExecutorConfig::builder().max_parallel_steps(2).build();
    let mut executor = WorkflowExecutor::new(config);

    // Build a simple workflow
    executor.add_step(Box::new(ProcessStep::new("step1", vec![], 100)));
    executor.add_step(Box::new(ProcessStep::new(
        "step2",
        vec!["step1".to_string()],
        100,
    )));
    executor.add_step(Box::new(ProcessStep::new(
        "step3",
        vec!["step1".to_string()],
        100,
    )));
    executor.add_step(Box::new(ProcessStep::new(
        "step4",
        vec!["step2".to_string(), "step3".to_string()],
        100,
    )));

    // Execute with console progress
    let callback = ConsoleProgressCallback::new();
    let metrics = executor.execute_parallel_with_progress(Box::new(callback))?;

    println!(
        "\nWorkflow completed: {} successful steps\n",
        metrics.successful_steps
    );
    Ok(())
}

fn example_file_logging() -> Result<()> {
    println!("=== Example 2: File-based Progress Logging ===\n");

    let log_path = std::env::temp_dir().join("workflow_progress.jsonl");
    println!("Logging to: {:?}\n", log_path);

    // Clean up any existing log
    let _ = std::fs::remove_file(&log_path);

    let config = ExecutorConfig::default();
    let mut executor = WorkflowExecutor::new(config);

    // Build workflow
    executor.add_step(Box::new(ProcessStep::new("load", vec![], 50)));
    executor.add_step(Box::new(ProcessStep::new(
        "transform",
        vec!["load".to_string()],
        75,
    )));
    executor.add_step(Box::new(ProcessStep::new(
        "write",
        vec!["transform".to_string()],
        50,
    )));

    // Execute with file logging
    let tracker = FileProgressTracker::new(&log_path).map_err(|e| {
        pf_workflow_core::ExecutionError::StepFailed {
            step_id: "file_tracker".to_string(),
            reason: e.to_string(),
        }
    })?;
    let metrics = executor.execute_with_progress(Box::new(tracker))?;

    println!("Workflow completed: {} steps", metrics.successful_steps);

    // Read and display log
    let contents = std::fs::read_to_string(&log_path).map_err(|e| {
        pf_workflow_core::ExecutionError::StepFailed {
            step_id: "read_log".to_string(),
            reason: e.to_string(),
        }
    })?;
    println!(
        "\nProgress log contents ({} lines):",
        contents.lines().count()
    );
    for (i, line) in contents.lines().enumerate() {
        if let Ok(event) = serde_json::from_str::<ProgressEvent>(line) {
            println!("  {}: {}", i + 1, event);
        }
    }

    // Clean up
    let _ = std::fs::remove_file(&log_path);
    println!();
    Ok(())
}

fn example_custom_callback() -> Result<()> {
    println!("=== Example 3: Custom Callback with Statistics ===\n");

    let config = ExecutorConfig::builder().max_parallel_steps(3).build();
    let mut executor = WorkflowExecutor::new(config);

    // Build a larger workflow
    for i in 1..=6 {
        let deps = if i > 1 {
            vec![format!("step{}", i - 1)]
        } else {
            vec![]
        };
        executor.add_step(Box::new(ProcessStep::new(&format!("step{}", i), deps, 30)));
    }

    // Create stats tracker
    let tracker = StatsTracker::new();
    let stats_clone = StatsTracker {
        started: Arc::clone(&tracker.started),
        completed: Arc::clone(&tracker.completed),
        failed: Arc::clone(&tracker.failed),
    };

    // Execute with custom callback
    let callback = tracker.into_callback();
    let _metrics = executor.execute_parallel_with_progress(Box::new(callback))?;

    // Display statistics
    let (started, completed, failed) = stats_clone.get_stats();
    println!("Statistics:");
    println!("  Started:   {}", started);
    println!("  Completed: {}", completed);
    println!("  Failed:    {}", failed);
    println!();

    Ok(())
}

fn example_inline_closure() -> Result<()> {
    println!("=== Example 4: Inline Closure Callback ===\n");

    let config = ExecutorConfig::default();
    let mut executor = WorkflowExecutor::new(config);

    executor.add_step(Box::new(ProcessStep::new("analyze", vec![], 50)));
    executor.add_step(Box::new(ProcessStep::new(
        "report",
        vec!["analyze".to_string()],
        50,
    )));

    // Use closure to collect step names
    let step_names = Arc::new(Mutex::new(Vec::new()));
    let names_clone = Arc::clone(&step_names);

    let callback = CallbackProgressTracker::new(move |event: ProgressEvent| {
        if matches!(event, ProgressEvent::Completed { .. }) {
            names_clone
                .lock()
                .unwrap()
                .push(event.step_id().to_string());
        }
    });

    let _metrics = executor.execute_with_progress(Box::new(callback))?;

    println!(
        "Steps completed in order: {:?}\n",
        step_names.lock().unwrap()
    );
    Ok(())
}

fn main() -> Result<()> {
    println!("===== Workflow Progress Tracking Examples =====\n");

    example_console_progress()?;
    example_file_logging()?;
    example_custom_callback()?;
    example_inline_closure()?;

    println!("===== All Examples Complete =====");
    Ok(())
}
