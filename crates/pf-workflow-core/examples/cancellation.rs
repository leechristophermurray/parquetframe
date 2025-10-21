//! Workflow cancellation example.
//!
//! This example demonstrates how to gracefully cancel a running workflow
//! using cancellation tokens.

use pf_workflow_core::{
    CancellationToken, ConsoleProgressCallback, ExecutionContext, ExecutorConfig, Result, Step,
    StepMetrics, StepResult, WorkflowExecutor,
};
use serde_json::Value;
use std::sync::Arc;
use std::thread;
use std::time::Duration;

/// A long-running step that can be cancelled.
struct LongRunningStep {
    id: String,
    duration_ms: u64,
}

impl LongRunningStep {
    fn new(id: &str, duration_ms: u64) -> Self {
        Self {
            id: id.to_string(),
            duration_ms,
        }
    }
}

impl Step for LongRunningStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn dependencies(&self) -> &[String] {
        &[]
    }

    fn execute(&self, _ctx: &mut ExecutionContext) -> Result<StepResult> {
        println!("Executing {}... ({}ms)", self.id, self.duration_ms);
        thread::sleep(Duration::from_millis(self.duration_ms));

        let metrics = StepMetrics::new(self.id.clone());
        Ok(StepResult::new(Value::Null, metrics))
    }
}

fn example_timeout_cancellation() -> Result<()> {
    println!("=== Example 1: Timeout-based Cancellation ===\n");

    let config = ExecutorConfig::builder().max_parallel_steps(2).build();
    let mut executor = WorkflowExecutor::new(config);

    // Add many long-running steps
    for i in 1..=10 {
        executor.add_step(Box::new(LongRunningStep::new(&format!("step{}", i), 200)));
    }

    // Create cancellation token
    let token = CancellationToken::new();
    let token_clone = token.clone();

    // Spawn thread to cancel after timeout
    println!("Setting timeout: 500ms\n");
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(500));
        println!("\n⏰ Timeout reached - cancelling workflow...\n");
        token_clone.cancel();
    });

    // Execute with cancellation
    let result = executor.execute_parallel_with_cancellation(token);

    match result {
        Ok(metrics) => {
            println!(
                "Workflow completed {} steps before timeout",
                metrics.successful_steps
            );
        }
        Err(e) => {
            println!("✅ Workflow cancelled successfully: {}\n", e);
        }
    }

    Ok(())
}

fn example_user_cancellation() -> Result<()> {
    println!("=== Example 2: User-triggered Cancellation ===\n");

    let config = ExecutorConfig::default();
    let mut executor = WorkflowExecutor::new(config);

    // Add sequential long-running steps
    for i in 1..=5 {
        executor.add_step(Box::new(LongRunningStep::new(&format!("task{}", i), 300)));
    }

    let token = CancellationToken::new();
    let token_clone = token.clone();

    println!("Simulating user pressing Ctrl+C after 700ms...\n");

    // Simulate user cancellation
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(700));
        println!("\n🛑 User cancelled - stopping workflow...\n");
        token_clone.cancel();
    });

    let callback = ConsoleProgressCallback::new();
    let result = executor.execute_with_options(Some(token), Some(Box::new(callback)));

    match result {
        Ok(metrics) => {
            println!(
                "Completed {} steps before cancellation",
                metrics.successful_steps
            );
        }
        Err(e) => {
            println!("✅ Workflow stopped: {}\n", e);
        }
    }

    Ok(())
}

fn example_conditional_cancellation() -> Result<()> {
    println!("=== Example 3: Conditional Cancellation ===\n");

    let config = ExecutorConfig::builder().max_parallel_steps(3).build();
    let mut executor = WorkflowExecutor::new(config);

    // Add steps
    for i in 1..=12 {
        executor.add_step(Box::new(LongRunningStep::new(&format!("job{}", i), 150)));
    }

    let token = CancellationToken::new();
    let token_clone = token.clone();

    println!("Monitoring workflow - will cancel if takes > 800ms\n");

    // Monitor and conditionally cancel
    let start = std::time::Instant::now();
    thread::spawn(move || loop {
        thread::sleep(Duration::from_millis(100));
        if start.elapsed() > Duration::from_millis(800) {
            println!("\n⚠️  Workflow taking too long - cancelling...\n");
            token_clone.cancel();
            break;
        }
    });

    let result = executor.execute_parallel_with_cancellation(token);

    match result {
        Ok(metrics) => {
            println!(
                "Workflow completed: {} steps in {:?}",
                metrics.successful_steps, metrics.total_duration
            );
        }
        Err(e) => {
            println!("✅ Cancelled due to excessive runtime: {}\n", e);
        }
    }

    Ok(())
}

fn example_graceful_shutdown() -> Result<()> {
    println!("=== Example 4: Graceful Shutdown Pattern ===\n");

    let config = ExecutorConfig::builder().max_parallel_steps(4).build();
    let mut executor = WorkflowExecutor::new(config);

    // Create workflow with many steps
    for i in 1..=20 {
        executor.add_step(Box::new(LongRunningStep::new(&format!("batch{}", i), 100)));
    }

    // Shared cancellation token
    let token = Arc::new(CancellationToken::new());
    let token_for_signal = Arc::clone(&token);

    println!("Starting workflow (will demonstrate graceful shutdown)...\n");

    // Simulate shutdown signal handler
    let shutdown_thread = thread::spawn(move || {
        thread::sleep(Duration::from_millis(600));
        println!("\n📢 Received shutdown signal");
        println!("Initiating graceful shutdown...\n");
        token_for_signal.cancel();
    });

    let callback = ConsoleProgressCallback::new();
    let result =
        executor.execute_parallel_with_options(Some((*token).clone()), Some(Box::new(callback)));

    shutdown_thread.join().unwrap();

    match result {
        Ok(metrics) => {
            println!(
                "\n✅ Workflow finished: {}/{} steps completed",
                metrics.successful_steps, metrics.total_steps
            );
        }
        Err(e) => {
            println!("\n✅ Graceful shutdown completed: {}", e);
            println!("Partial results have been cleaned up.");
        }
    }

    println!();
    Ok(())
}

fn main() -> Result<()> {
    println!("===== Workflow Cancellation Examples =====\n");

    example_timeout_cancellation()?;
    thread::sleep(Duration::from_millis(200));

    example_user_cancellation()?;
    thread::sleep(Duration::from_millis(200));

    example_conditional_cancellation()?;
    thread::sleep(Duration::from_millis(200));

    example_graceful_shutdown()?;

    println!("===== All Examples Complete =====");
    Ok(())
}
