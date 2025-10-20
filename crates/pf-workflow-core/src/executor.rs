//! Workflow executor for running steps.
//!
//! This module provides the main executor for running workflow steps
//! either sequentially or in parallel.

use crate::config::ExecutorConfig;
use crate::dag::DAG;
use crate::error::Result;
use crate::metrics::WorkflowMetrics;
use crate::step::Step;
use std::collections::HashMap;

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
    /// # Phase 3.4 Note
    /// This is a stub. Full implementation in Task 6.
    pub fn execute(&mut self) -> Result<WorkflowMetrics> {
        // Stub: return empty metrics
        Ok(WorkflowMetrics::new())
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
    use crate::step::SimpleStep;
    use serde_json::Value;

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
}
