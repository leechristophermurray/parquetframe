//! Scheduler for parallel workflow execution.
//!
//! This module provides scheduling logic for executing workflow steps
//! in parallel while respecting dependencies and resource constraints.

use crate::dag::DAG;
use std::collections::{HashSet, VecDeque};

/// Scheduler for parallel step execution.
///
/// The scheduler determines which steps can run in parallel based on
/// the workflow DAG and resource constraints.
#[derive(Debug)]
pub struct ParallelScheduler {
    /// Maximum number of concurrent steps.
    max_concurrent: usize,

    /// Steps currently pending execution.
    pending: VecDeque<String>,

    /// Steps currently running.
    running: HashSet<String>,

    /// Steps that have completed.
    completed: HashSet<String>,
}

impl ParallelScheduler {
    /// Create a new parallel scheduler.
    ///
    /// # Arguments
    /// * `max_concurrent` - Maximum number of steps to run concurrently.
    ///   If 0, uses the number of CPU cores.
    pub fn new(max_concurrent: usize) -> Self {
        let max = if max_concurrent == 0 {
            num_cpus::get()
        } else {
            max_concurrent
        };

        Self {
            max_concurrent: max,
            pending: VecDeque::new(),
            running: HashSet::new(),
            completed: HashSet::new(),
        }
    }

    /// Get the maximum number of concurrent steps.
    pub fn max_concurrent(&self) -> usize {
        self.max_concurrent
    }

    /// Get the number of steps currently running.
    pub fn running_count(&self) -> usize {
        self.running.len()
    }

    /// Get the number of steps completed.
    pub fn completed_count(&self) -> usize {
        self.completed.len()
    }

    /// Check if the scheduler has capacity for more steps.
    pub fn has_capacity(&self) -> bool {
        self.running.len() < self.max_concurrent
    }

    /// Mark a step as completed.
    pub fn mark_completed(&mut self, step_id: String) {
        self.running.remove(&step_id);
        self.completed.insert(step_id);
    }

    /// Schedule steps based on DAG dependencies.
    ///
    /// Returns a list of step groups where each group can be executed in parallel.
    ///
    /// # Phase 3.4 Note
    /// This is a simplified implementation. Full implementation will be in Task 7.
    pub fn schedule_steps(&mut self, dag: &DAG) -> Vec<Vec<String>> {
        let mut groups = Vec::new();

        // Use DAG's built-in parallelizable groups
        if let Ok(dag_groups) = dag.get_parallelizable_groups() {
            for group in dag_groups {
                // Limit group size to max_concurrent
                let mut current_group = Vec::new();
                for step_id in group {
                    if current_group.len() < self.max_concurrent {
                        current_group.push(step_id);
                    } else {
                        // Start a new group if we exceed max_concurrent
                        if !current_group.is_empty() {
                            groups.push(current_group);
                            current_group = Vec::new();
                        }
                        current_group.push(step_id);
                    }
                }
                if !current_group.is_empty() {
                    groups.push(current_group);
                }
            }
        }

        groups
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scheduler_creation() {
        let scheduler = ParallelScheduler::new(4);
        assert_eq!(scheduler.max_concurrent(), 4);
        assert_eq!(scheduler.running_count(), 0);
        assert_eq!(scheduler.completed_count(), 0);
        assert!(scheduler.has_capacity());
    }

    #[test]
    fn test_scheduler_auto_cpu() {
        let scheduler = ParallelScheduler::new(0);
        assert!(scheduler.max_concurrent() > 0);
    }

    #[test]
    fn test_mark_completed() {
        let mut scheduler = ParallelScheduler::new(4);
        scheduler.running.insert("step1".to_string());
        assert_eq!(scheduler.running_count(), 1);

        scheduler.mark_completed("step1".to_string());
        assert_eq!(scheduler.running_count(), 0);
        assert_eq!(scheduler.completed_count(), 1);
    }

    #[test]
    fn test_schedule_linear_dag() {
        let mut scheduler = ParallelScheduler::new(4);
        let mut dag = DAG::new();

        // Linear: A -> B -> C
        dag.add_node("A".to_string());
        dag.add_node("B".to_string());
        dag.add_node("C".to_string());
        dag.add_edge("B".to_string(), "A".to_string()).unwrap();
        dag.add_edge("C".to_string(), "B".to_string()).unwrap();

        let groups = scheduler.schedule_steps(&dag);
        assert_eq!(groups.len(), 3);
        assert_eq!(groups[0], vec!["A"]);
        assert_eq!(groups[1], vec!["B"]);
        assert_eq!(groups[2], vec!["C"]);
    }
}
