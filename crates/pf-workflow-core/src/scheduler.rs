//! Scheduler for parallel workflow execution.
//!
//! This module provides scheduling logic for executing workflow steps
//! in parallel while respecting dependencies and resource constraints.

use crate::dag::DAG;
use crate::step::{ResourceHint, Step};
use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

/// Configuration for resource limits.
#[derive(Debug, Clone)]
pub struct ResourceLimits {
    /// Maximum number of concurrent CPU-bound tasks.
    pub max_cpu_tasks: usize,

    /// Maximum number of concurrent IO-bound tasks.
    pub max_io_tasks: usize,

    /// Maximum total memory usage in bytes.
    pub max_memory_bytes: usize,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            max_cpu_tasks: num_cpus::get(),
            max_io_tasks: num_cpus::get() * 2, // IO can handle more concurrency
            max_memory_bytes: usize::MAX, // No limit by default
        }
    }
}

/// Scheduler for parallel step execution.
///
/// The scheduler determines which steps can run in parallel based on
/// the workflow DAG and resource constraints. It implements wave-based
/// execution where each wave contains steps that can run in parallel.
///
/// # Resource Awareness
///
/// The scheduler tracks CPU-bound vs IO-bound tasks separately and enforces
/// different concurrency limits for each type. This prevents CPU-bound tasks
/// from overwhelming the system while allowing higher concurrency for IO-bound work.
///
/// # Examples
///
/// ```
/// use pf_workflow_core::{ParallelScheduler, ResourceLimits};
///
/// let limits = ResourceLimits {
///     max_cpu_tasks: 4,
///     max_io_tasks: 8,
///     max_memory_bytes: 2 * 1024 * 1024 * 1024, // 2GB
/// };
/// let scheduler = ParallelScheduler::with_limits(limits);
/// ```
#[derive(Debug)]
pub struct ParallelScheduler {
    /// Maximum number of concurrent steps.
    max_concurrent: usize,

    /// Resource limits for scheduling.
    resource_limits: ResourceLimits,

    /// Number of CPU-bound tasks currently in-flight.
    cpu_tasks_inflight: Arc<AtomicUsize>,

    /// Number of IO-bound tasks currently in-flight.
    io_tasks_inflight: Arc<AtomicUsize>,

    /// Total memory currently in use (estimated).
    memory_in_use: Arc<AtomicUsize>,

    /// Steps currently pending execution.
    #[allow(dead_code)]
    pending: VecDeque<String>,

    /// Steps currently running.
    running: HashSet<String>,

    /// Steps that have completed.
    completed: HashSet<String>,
}

impl ParallelScheduler {
    /// Create a new parallel scheduler with default resource limits.
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
            resource_limits: ResourceLimits::default(),
            cpu_tasks_inflight: Arc::new(AtomicUsize::new(0)),
            io_tasks_inflight: Arc::new(AtomicUsize::new(0)),
            memory_in_use: Arc::new(AtomicUsize::new(0)),
            pending: VecDeque::new(),
            running: HashSet::new(),
            completed: HashSet::new(),
        }
    }

    /// Create a new parallel scheduler with custom resource limits.
    ///
    /// # Arguments
    /// * `limits` - Resource limits for CPU, IO, and memory.
    pub fn with_limits(limits: ResourceLimits) -> Self {
        let max = limits.max_cpu_tasks.max(limits.max_io_tasks);

        Self {
            max_concurrent: max,
            resource_limits: limits,
            cpu_tasks_inflight: Arc::new(AtomicUsize::new(0)),
            io_tasks_inflight: Arc::new(AtomicUsize::new(0)),
            memory_in_use: Arc::new(AtomicUsize::new(0)),
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

    /// Mark a step as running and update resource counters.
    pub fn mark_running(&mut self, step_id: String, hint: ResourceHint) {
        self.running.insert(step_id);

        // Update resource counters
        match hint {
            ResourceHint::LightCPU | ResourceHint::HeavyCPU | ResourceHint::Default => {
                self.cpu_tasks_inflight.fetch_add(1, Ordering::Relaxed);
            }
            ResourceHint::LightIO | ResourceHint::HeavyIO => {
                self.io_tasks_inflight.fetch_add(1, Ordering::Relaxed);
            }
            ResourceHint::Memory(bytes) => {
                self.memory_in_use.fetch_add(bytes, Ordering::Relaxed);
            }
        }
    }

    /// Mark a step as completed and release resources.
    pub fn mark_completed(&mut self, step_id: String, hint: ResourceHint) {
        self.running.remove(&step_id);
        self.completed.insert(step_id);

        // Release resource counters
        match hint {
            ResourceHint::LightCPU | ResourceHint::HeavyCPU | ResourceHint::Default => {
                self.cpu_tasks_inflight.fetch_sub(1, Ordering::Relaxed);
            }
            ResourceHint::LightIO | ResourceHint::HeavyIO => {
                self.io_tasks_inflight.fetch_sub(1, Ordering::Relaxed);
            }
            ResourceHint::Memory(bytes) => {
                self.memory_in_use.fetch_sub(bytes, Ordering::Relaxed);
            }
        }
    }

    /// Check if a step with the given resource hint can execute now.
    ///
    /// Returns true if there is sufficient capacity for the step's resource requirements.
    pub fn can_execute(&self, hint: ResourceHint) -> bool {
        match hint {
            ResourceHint::LightCPU | ResourceHint::HeavyCPU | ResourceHint::Default => {
                let current = self.cpu_tasks_inflight.load(Ordering::Relaxed);
                current < self.resource_limits.max_cpu_tasks
            }
            ResourceHint::LightIO | ResourceHint::HeavyIO => {
                let current = self.io_tasks_inflight.load(Ordering::Relaxed);
                current < self.resource_limits.max_io_tasks
            }
            ResourceHint::Memory(bytes) => {
                let current = self.memory_in_use.load(Ordering::Relaxed);
                current.saturating_add(bytes) <= self.resource_limits.max_memory_bytes
            }
        }
    }

    /// Wait for capacity to become available for the given resource hint.
    ///
    /// This method blocks until the step can be executed based on resource availability.
    /// It uses a simple polling approach with exponential backoff.
    ///
    /// # Arguments
    /// * `hint` - The resource hint for the step waiting to execute
    /// * `timeout` - Maximum time to wait before giving up
    ///
    /// # Returns
    /// `true` if capacity became available, `false` if timeout occurred
    pub fn wait_for_capacity(&self, hint: ResourceHint, timeout: Duration) -> bool {
        let start = std::time::Instant::now();
        let mut backoff_ms = 1u64;

        while start.elapsed() < timeout {
            if self.can_execute(hint) {
                return true;
            }

            // Exponential backoff with max 100ms
            thread::sleep(Duration::from_millis(backoff_ms));
            backoff_ms = (backoff_ms * 2).min(100);
        }

        false
    }

    /// Schedule steps for parallel execution with resource awareness.
    ///
    /// Returns a list of execution waves where each wave contains steps that can
    /// run in parallel. Steps within a wave have no dependencies on each other,
    /// and resource limits are respected.
    ///
    /// # Arguments
    /// * `dag` - The workflow DAG
    /// * `steps` - Map of step IDs to step implementations (for accessing resource hints)
    ///
    /// # Returns
    /// A vector of waves, where each wave is a vector of step IDs to execute in parallel.
    pub fn schedule_parallel(
        &self,
        dag: &DAG,
        steps: &HashMap<String, Box<dyn Step>>,
    ) -> Vec<Vec<String>> {
        let mut waves = Vec::new();
        let mut completed = HashSet::new();
        let mut in_progress = HashSet::new();

        // Get all steps in topological order
        let all_steps = match dag.topological_sort() {
            Ok(steps) => steps,
            Err(_) => return waves, // Return empty on error (cycle detected)
        };

        let total_steps = all_steps.len();

        // Build dependency map for quick lookups
        let mut dep_map: HashMap<String, Vec<String>> = HashMap::new();
        for step_id in &all_steps {
            if let Some(step) = steps.get(step_id) {
                dep_map.insert(step_id.clone(), step.dependencies().to_vec());
            }
        }

        // Wave-based scheduling
        while completed.len() < total_steps {
            let mut current_wave = Vec::new();
            let mut wave_cpu_tasks = 0;
            let mut wave_io_tasks = 0;
            let mut wave_memory: usize = 0;

            // Find steps ready to execute (all dependencies completed)
            for step_id in &all_steps {
                // Skip if already completed or in progress
                if completed.contains(step_id) || in_progress.contains(step_id) {
                    continue;
                }

                // Check if all dependencies are completed
                let deps = dep_map.get(step_id).map(|v| v.as_slice()).unwrap_or(&[]);
                let deps_ready = deps.iter().all(|dep| completed.contains(dep));

                if !deps_ready {
                    continue;
                }

                // Check resource constraints for this wave
                if let Some(step) = steps.get(step_id) {
                    let hint = step.resource_hint();

                    let can_add = match hint {
                        ResourceHint::LightCPU | ResourceHint::HeavyCPU | ResourceHint::Default => {
                            wave_cpu_tasks < self.resource_limits.max_cpu_tasks
                        }
                        ResourceHint::LightIO | ResourceHint::HeavyIO => {
                            wave_io_tasks < self.resource_limits.max_io_tasks
                        }
                        ResourceHint::Memory(bytes) => {
                            wave_memory.saturating_add(bytes) <= self.resource_limits.max_memory_bytes
                        }
                    };

                    if can_add {
                        current_wave.push(step_id.clone());
                        in_progress.insert(step_id.clone());

                        // Update wave resource counters
                        match hint {
                            ResourceHint::LightCPU | ResourceHint::HeavyCPU | ResourceHint::Default => {
                                wave_cpu_tasks += 1;
                            }
                            ResourceHint::LightIO | ResourceHint::HeavyIO => {
                                wave_io_tasks += 1;
                            }
                            ResourceHint::Memory(bytes) => {
                                wave_memory += bytes;
                            }
                        }
                    }
                }
            }

            // If no steps can be added to the current wave, we're done or deadlocked
            if current_wave.is_empty() {
                break;
            }

            // Mark all steps in this wave as completed for dependency resolution
            for step_id in &current_wave {
                completed.insert(step_id.clone());
                in_progress.remove(step_id);
            }

            waves.push(current_wave);
        }

        waves
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
        scheduler.mark_running("step1".to_string(), ResourceHint::Default);
        assert_eq!(scheduler.running_count(), 1);
        assert_eq!(scheduler.cpu_tasks_inflight.load(Ordering::Relaxed), 1);

        scheduler.mark_completed("step1".to_string(), ResourceHint::Default);
        assert_eq!(scheduler.running_count(), 0);
        assert_eq!(scheduler.completed_count(), 1);
        assert_eq!(scheduler.cpu_tasks_inflight.load(Ordering::Relaxed), 0);
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
