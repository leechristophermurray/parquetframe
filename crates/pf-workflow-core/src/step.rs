//! Step trait and execution context for workflow steps.
//!
//! This module defines the trait that all workflow steps must implement,
//! as well as the execution context that steps receive.

use crate::error::Result;
use crate::metrics::StepMetrics;
use serde_json::Value;
use std::collections::HashMap;
use std::time::Duration;

/// Trait for workflow steps.
pub trait Step: Send + Sync {
    /// Get the step's unique identifier.
    fn id(&self) -> &str;

    /// Execute the step.
    fn execute(&self, ctx: &mut ExecutionContext) -> Result<StepResult>;

    /// Get the IDs of steps this step depends on.
    fn dependencies(&self) -> &[String];

    /// Get the timeout for this step, if any.
    fn timeout(&self) -> Option<Duration> {
        None
    }

    /// Get the retry configuration for this step.
    fn retry_config(&self) -> RetryConfig {
        RetryConfig::default()
    }
}

/// Configuration for retry behavior.
#[derive(Debug, Clone)]
pub struct RetryConfig {
    /// Maximum number of retry attempts.
    pub max_attempts: u32,

    /// Backoff duration between retries.
    pub backoff: Duration,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_attempts: 0,
            backoff: Duration::from_millis(100),
        }
    }
}

/// Execution context shared across workflow steps.
#[derive(Debug)]
pub struct ExecutionContext {
    /// Data storage for step outputs.
    /// Maps step ID to its output value.
    pub data: HashMap<String, Value>,

    /// Accumulated metrics (for internal use).
    pub(crate) metrics: Vec<StepMetrics>,
}

impl ExecutionContext {
    /// Create a new execution context.
    pub fn new() -> Self {
        Self {
            data: HashMap::new(),
            metrics: Vec::new(),
        }
    }

    /// Store a value with the given key.
    pub fn set(&mut self, key: String, value: Value) {
        self.data.insert(key, value);
    }

    /// Get a value by key.
    pub fn get(&self, key: &str) -> Option<&Value> {
        self.data.get(key)
    }

    /// Check if a key exists.
    pub fn contains_key(&self, key: &str) -> bool {
        self.data.contains_key(key)
    }
}

impl Default for ExecutionContext {
    fn default() -> Self {
        Self::new()
    }
}

/// Result of a step execution.
#[derive(Debug)]
pub struct StepResult {
    /// Output value from the step.
    pub output: Value,

    /// Metrics collected during step execution.
    pub metrics: StepMetrics,
}

impl StepResult {
    /// Create a new step result.
    pub fn new(output: Value, metrics: StepMetrics) -> Self {
        Self { output, metrics }
    }
}

/// A simple step implementation for testing.
#[cfg(test)]
pub struct SimpleStep {
    id: String,
    dependencies: Vec<String>,
    output: Value,
}

#[cfg(test)]
impl SimpleStep {
    pub fn new(id: String, output: Value) -> Self {
        Self {
            id,
            dependencies: Vec::new(),
            output,
        }
    }

    pub fn with_dependencies(mut self, deps: Vec<String>) -> Self {
        self.dependencies = deps;
        self
    }
}

#[cfg(test)]
impl Step for SimpleStep {
    fn id(&self) -> &str {
        &self.id
    }

    fn execute(&self, _ctx: &mut ExecutionContext) -> Result<StepResult> {
        let metrics = StepMetrics::new(self.id.clone());
        Ok(StepResult::new(self.output.clone(), metrics))
    }

    fn dependencies(&self) -> &[String] {
        &self.dependencies
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_execution_context() {
        let mut ctx = ExecutionContext::new();

        ctx.set("key1".to_string(), Value::from("value1"));
        assert!(ctx.contains_key("key1"));
        assert_eq!(ctx.get("key1").unwrap(), &Value::from("value1"));

        assert!(!ctx.contains_key("nonexistent"));
    }

    #[test]
    fn test_simple_step() {
        let step = SimpleStep::new("test".to_string(), Value::from(42));
        assert_eq!(step.id(), "test");
        assert_eq!(step.dependencies().len(), 0);

        let mut ctx = ExecutionContext::new();
        let result = step.execute(&mut ctx).unwrap();
        assert_eq!(result.output, Value::from(42));
    }

    #[test]
    fn test_step_with_dependencies() {
        let step = SimpleStep::new("test".to_string(), Value::from(42))
            .with_dependencies(vec!["dep1".to_string(), "dep2".to_string()]);

        assert_eq!(step.dependencies().len(), 2);
        assert_eq!(step.dependencies()[0], "dep1");
    }
}
