//! Workflow executor for running steps.
//!
//! This module provides the main executor for running workflow steps
//! either sequentially or in parallel.

use crate::config::ExecutorConfig;
use crate::dag::DAG;
use crate::error::{ExecutionError, Result};
use crate::metrics::{StepMetrics, WorkflowMetrics};
use crate::step::{ExecutionContext, Step, StepResult};
use std::collections::HashMap;
use std::thread;
use std::time::{Duration, Instant};

/// Main workflow executor.
///
/// The executor coordinates the execution of workflow steps based on
/// the DAG and configuration.
///
/// # Phase 3.4 Note
/// This is a stub implementation. Full implementation will be in Tasks 6-8.
pub struct WorkflowExecutor {
    /// Configuration for execution.
    config: ExecutorConfig,

    /// The workflow DAG.
    dag: DAG,

    /// Map of step ID to step implementation.
    steps: HashMap<String, Box<dyn Step>>,
}

impl WorkflowExecutor {
    /// Create a new workflow executor.
    pub fn new(config: ExecutorConfig) -> Self {
        Self {
            config,
            dag: DAG::new(),
            steps: HashMap::new(),
        }
    }

    /// Add a step to the workflow.
    pub fn add_step(&mut self, step: Box<dyn Step>) {
        let step_id = step.id().to_string();

        // Add node to DAG
        self.dag.add_node(step_id.clone());

        // Add edges for dependencies
        for dep in step.dependencies() {
            // Ensure dependency node exists
            self.dag.add_node(dep.clone());
            // Add edge: this step depends on dep
            let _ = self.dag.add_edge(step_id.clone(), dep.clone());
        }

        // Store step
        self.steps.insert(step_id, step);
    }

    /// Get the number of steps in the workflow.
    pub fn step_count(&self) -> usize {
        self.steps.len()
    }

    /// Get the executor configuration.
    pub fn config(&self) -> &ExecutorConfig {
        &self.config
    }

    /// Get a reference to the DAG.
    pub fn dag(&self) -> &DAG {
        &self.dag
    }

    /// Execute the workflow sequentially.
    ///
    /// Steps are executed in topological order based on their dependencies.
    /// Each step is executed with retry logic according to its configuration.
    pub fn execute(&mut self) -> Result<WorkflowMetrics> {
        let workflow_start = Instant::now();

        // Get execution order from DAG
        let order = self.dag.topological_sort()?;

        // Create execution context
        let mut ctx = ExecutionContext::new();

        // Create workflow metrics
        let mut workflow_metrics = WorkflowMetrics::new();

        // Execute each step in order
        for step_id in order {
            let step = self.steps.get(&step_id)
                .ok_or_else(|| ExecutionError::StepFailed {
                    step_id: step_id.clone(),
                    reason: "Step not found".to_string(),
                })?;

            // Execute step with retry logic
            let result = self.execute_step_with_retry(step.as_ref(), &mut ctx)?;

            // Store step output in context for dependent steps
            ctx.set(step_id.clone(), result.output);

            // Add step metrics to workflow metrics
            workflow_metrics.add_step(result.metrics);
        }

        // Finalize workflow metrics
        let total_duration = workflow_start.elapsed();
        workflow_metrics.finalize(total_duration);

        Ok(workflow_metrics)
    }

    /// Execute a single step with retry logic and timeout handling.
    ///
    /// # Arguments
    /// * `step` - The step to execute
    /// * `ctx` - The execution context
    ///
    /// # Returns
    /// The step result with metrics, or an error if execution fails.
    fn execute_step_with_retry(
        &self,
        step: &dyn Step,
        ctx: &mut ExecutionContext,
    ) -> Result<StepResult> {
        let retry_config = step.retry_config();
        let step_timeout = step.timeout().or(self.config.step_timeout);
        let base_backoff = Duration::from_millis(self.config.retry_backoff_ms);

        let mut step_metrics = StepMetrics::new(step.id().to_string());
        step_metrics.start();

        let mut last_error = None;

        // Retry loop (attempt 0 is the first try)
        for attempt in 0..=retry_config.max_attempts {
            if attempt > 0 {
                step_metrics.increment_retry();

                // Calculate exponential backoff: base * 2^(attempt-1)
                let backoff = base_backoff * 2_u32.pow(attempt - 1);
                thread::sleep(backoff);
            }

            // Execute with timeout if specified
            let result = if let Some(timeout) = step_timeout {
                self.execute_step_with_timeout(step, ctx, timeout)
            } else {
                step.execute(ctx)
            };

            match result {
                Ok(mut step_result) => {
                    // Success - update metrics and return
                    step_metrics.complete();
                    step_result.metrics = step_metrics;
                    return Ok(step_result);
                }
                Err(e) => {
                    // Store error for potential retry or final failure
                    last_error = Some(e);

                    // If this was the last attempt, break
                    if attempt >= retry_config.max_attempts {
                        break;
                    }
                    // Otherwise, loop will retry
                }
            }
        }

        // All retries exhausted - mark as failed
        let error_msg = last_error
            .map(|e| e.to_string())
            .unwrap_or_else(|| "Unknown error".to_string());

        step_metrics.fail(error_msg.clone());

        Err(ExecutionError::RetryExhausted(
            format!("Step '{}' failed after {} attempts: {}",
                step.id(),
                retry_config.max_attempts + 1,
                error_msg
            )
        ).into())
    }

    /// Execute a step with a timeout.
    ///
    /// Note: This is a simplified timeout implementation.
    /// In production, you'd use more sophisticated timeout mechanisms.
    fn execute_step_with_timeout(
        &self,
        step: &dyn Step,
        ctx: &mut ExecutionContext,
        timeout: Duration,
    ) -> Result<StepResult> {
        let start = Instant::now();

        // Execute the step
        let result = step.execute(ctx)?;

        // Check if we exceeded timeout
        if start.elapsed() > timeout {
            return Err(ExecutionError::Timeout(
                format!("Step '{}' exceeded timeout of {:?}", step.id(), timeout)
            ).into());
        }

        Ok(result)
    }

    /// Execute the workflow in parallel.
    ///
    /// # Phase 3.4 Note
    /// This is a stub. Full implementation in Task 7.
    pub fn execute_parallel(&mut self) -> Result<WorkflowMetrics> {
        // Stub: return empty metrics
        Ok(WorkflowMetrics::new())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::error::{ExecutionError, WorkflowError};
    use crate::step::{RetryConfig, SimpleStep, Step, StepResult};
    use serde_json::Value;
    use std::sync::{Arc, Mutex};
    use std::thread;
    use std::time::Duration;

    #[test]
    fn test_executor_creation() {
        let config = ExecutorConfig::default();
        let executor = WorkflowExecutor::new(config);
        assert_eq!(executor.step_count(), 0);
    }

    #[test]
    fn test_add_step() {
        let config = ExecutorConfig::default();
        let mut executor = WorkflowExecutor::new(config);

        let step = Box::new(SimpleStep::new("step1".to_string(), Value::from(42)));
        executor.add_step(step);

        assert_eq!(executor.step_count(), 1);
        assert_eq!(executor.dag().node_count(), 1);
    }

    #[test]
    fn test_add_step_with_dependencies() {
        let config = ExecutorConfig::default();
        let mut executor = WorkflowExecutor::new(config);

        let step1 = Box::new(SimpleStep::new("step1".to_string(), Value::from(1)));
        let step2 = Box::new(
            SimpleStep::new("step2".to_string(), Value::from(2))
                .with_dependencies(vec!["step1".to_string()])
        );

        executor.add_step(step1);
        executor.add_step(step2);

        assert_eq!(executor.step_count(), 2);
        assert_eq!(executor.dag().node_count(), 2);
        assert_eq!(executor.dag().edge_count(), 1);
    }

    #[test]
    fn test_execute_simple_workflow() {
        let config = ExecutorConfig::default();
        let mut executor = WorkflowExecutor::new(config);

        // Add simple linear workflow: A -> B -> C
        let step_a = Box::new(SimpleStep::new("A".to_string(), Value::from(1)));
        let step_b = Box::new(
            SimpleStep::new("B".to_string(), Value::from(2))
                .with_dependencies(vec!["A".to_string()])
        );
        let step_c = Box::new(
            SimpleStep::new("C".to_string(), Value::from(3))
                .with_dependencies(vec!["B".to_string()])
        );

        executor.add_step(step_a);
        executor.add_step(step_b);
        executor.add_step(step_c);

        // Execute workflow
        let result = executor.execute();
        assert!(result.is_ok());

        let metrics = result.unwrap();
        assert_eq!(metrics.total_steps, 3);
        assert_eq!(metrics.successful_steps, 3);
        assert_eq!(metrics.failed_steps, 0);
    }

    #[test]
    fn test_execute_with_dependencies() {
        let config = ExecutorConfig::default();
        let mut executor = WorkflowExecutor::new(config);

        // Create workflow with dependencies
        let step1 = Box::new(SimpleStep::new("step1".to_string(), Value::from(10)));
        let step2 = Box::new(SimpleStep::new("step2".to_string(), Value::from(20)));
        let step3 = Box::new(
            SimpleStep::new("step3".to_string(), Value::from(30))
                .with_dependencies(vec!["step1".to_string(), "step2".to_string()])
        );

        executor.add_step(step1);
        executor.add_step(step2);
        executor.add_step(step3);

        let result = executor.execute();
        assert!(result.is_ok());

        let metrics = result.unwrap();
        assert_eq!(metrics.total_steps, 3);
        assert_eq!(metrics.successful_steps, 3);

        // Verify execution completed (even if very fast, duration should be non-zero in nanos)
        assert!(metrics.total_duration.as_nanos() > 0);
    }

    #[test]
    fn test_metrics_collection() {
        let config = ExecutorConfig::default();
        let mut executor = WorkflowExecutor::new(config);

        let step = Box::new(SimpleStep::new("test_step".to_string(), Value::from(42)));
        executor.add_step(step);

        let result = executor.execute().unwrap();

        assert_eq!(result.total_steps, 1);
        assert_eq!(result.successful_steps, 1);
        assert_eq!(result.step_metrics.len(), 1);

        let step_metric = &result.step_metrics[0];
        assert_eq!(step_metric.step_id, "test_step");
        assert!(matches!(step_metric.status, crate::metrics::StepStatus::Completed));
        assert!(step_metric.duration.is_some());
    }

    #[test]
    fn test_parallelism_factor_sequential() {
        let config = ExecutorConfig::default();
        let mut executor = WorkflowExecutor::new(config);

        // Add multiple steps
        for i in 0..3 {
            let step = Box::new(SimpleStep::new(format!("step{}", i), Value::from(i)));
            executor.add_step(step);
        }

        let result = executor.execute().unwrap();

        // For sequential execution, parallelism factor should be close to 1.0
        // (allowing small variations due to overhead)
        assert!(result.parallelism_factor >= 0.8);
        assert!(result.parallelism_factor <= 1.2);
    }

    // Test helpers for retry/timeout behavior
    struct FlakyStep {
        id: String,
        deps: Vec<String>,
        output: Value,
        fail_times: u32,
        attempts: Arc<Mutex<u32>>,
        retry: RetryConfig,
    }

    impl FlakyStep {
        fn new(id: &str, output: Value, fail_times: u32, max_attempts: u32) -> Self {
            Self {
                id: id.to_string(),
                deps: vec![],
                output,
                fail_times,
                attempts: Arc::new(Mutex::new(0)),
                retry: RetryConfig { max_attempts, backoff: Duration::from_millis(1) },
            }
        }

        #[allow(dead_code)]
        fn with_dependencies(mut self, deps: Vec<String>) -> Self {
            self.deps = deps;
            self
        }
    }

    impl Step for FlakyStep {
        fn id(&self) -> &str { &self.id }
        fn execute(&self, _ctx: &mut ExecutionContext) -> crate::error::Result<StepResult> {
            let mut guard = self.attempts.lock().unwrap();
            *guard += 1;
            if *guard <= self.fail_times {
                return Err(ExecutionError::StepFailed { step_id: self.id.clone(), reason: "flaky failure".to_string() }.into());
            }
            Ok(StepResult::new(self.output.clone(), StepMetrics::new(self.id.clone())))
        }
        fn dependencies(&self) -> &[String] { &self.deps }
        fn retry_config(&self) -> RetryConfig { self.retry.clone() }
    }

    struct TimeoutStep {
        id: String,
        deps: Vec<String>,
        sleep: Duration,
        timeout: Duration,
    }

    impl TimeoutStep {
        fn new(id: &str, sleep: Duration, timeout: Duration) -> Self {
            Self { id: id.to_string(), deps: vec![], sleep, timeout }
        }
        #[allow(dead_code)]
        fn with_dependencies(mut self, deps: Vec<String>) -> Self {
            self.deps = deps;
            self
        }
    }

    impl Step for TimeoutStep {
        fn id(&self) -> &str { &self.id }
        fn execute(&self, _ctx: &mut ExecutionContext) -> crate::error::Result<StepResult> {
            thread::sleep(self.sleep);
            Ok(StepResult::new(Value::from("done"), StepMetrics::new(self.id.clone())))
        }
        fn dependencies(&self) -> &[String] { &self.deps }
        fn timeout(&self) -> Option<Duration> { Some(self.timeout) }
    }

    #[test]
    fn test_retry_logic_success_after_failures() {
        let config = ExecutorConfig::builder().retry_backoff_ms(1).build();
        let mut executor = WorkflowExecutor::new(config);

        // Flaky step fails once, then succeeds; allow 1 retry
        let step = Box::new(FlakyStep::new("flaky_success", Value::from(123), 1, 1));
        executor.add_step(step);

        let metrics = executor.execute().unwrap();
        assert_eq!(metrics.total_steps, 1);
        assert_eq!(metrics.successful_steps, 1);
        assert_eq!(metrics.failed_steps, 0);
        assert_eq!(metrics.step_metrics[0].retry_count, 1);
        assert!(matches!(metrics.step_metrics[0].status, crate::metrics::StepStatus::Completed));
    }

    #[test]
    fn test_retry_exhausted_failure() {
        let config = ExecutorConfig::builder().retry_backoff_ms(1).build();
        let mut executor = WorkflowExecutor::new(config);

        // Flaky step fails 3 times but only 2 retries allowed => overall failure
        let step = Box::new(FlakyStep::new("flaky_fail", Value::from(0), 3, 2));
        executor.add_step(step);

        let err = executor.execute().unwrap_err();
        match err {
            WorkflowError::Execution(ExecutionError::RetryExhausted(msg)) => {
                assert!(msg.contains("flaky_fail"));
                assert!(msg.to_lowercase().contains("exceeded") || msg.to_lowercase().contains("failed after"));
            }
            other => panic!("unexpected error: {:?}", other),
        }
    }

    #[test]
    fn test_timeout_enforced() {
        let config = ExecutorConfig::builder().retry_backoff_ms(1).build();
        let mut executor = WorkflowExecutor::new(config);

        // Step sleeps longer than its timeout => should trigger timeout and fail
        let step = Box::new(TimeoutStep::new("sleepy", Duration::from_millis(30), Duration::from_millis(5)));
        executor.add_step(step);

        let err = executor.execute().unwrap_err();
        match err {
            WorkflowError::Execution(ExecutionError::RetryExhausted(msg)) => {
                assert!(msg.contains("sleepy"));
                assert!(msg.contains("exceeded timeout"));
            }
            other => panic!("unexpected error: {:?}", other),
        }
    }
}
