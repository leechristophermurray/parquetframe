//! Workflow execution engine for ParquetFrame.
//!
//! `pf-workflow-core` provides a high-performance, type-safe workflow orchestration engine
//! with support for both sequential and parallel execution, automatic retries, cancellation,
//! and comprehensive progress tracking.
//!
//! # Features
//!
//! - **DAG-based Workflow**: Define workflows as directed acyclic graphs with automatic
//!   dependency resolution and topological sorting
//! - **Parallel Execution**: Execute independent steps concurrently with configurable
//!   parallelism and resource-aware scheduling
//! - **Cancellation Support**: Gracefully cancel running workflows with cleanup
//! - **Progress Tracking**: Monitor workflow execution with customizable callbacks
//! - **Automatic Retries**: Configure retry behavior with exponential backoff
//! - **Error Handling**: Robust error propagation and dependency management
//! - **Metrics Collection**: Detailed timing, resource usage, and parallelism metrics
//!
//! # Quick Start
//!
//! ```
//! use pf_workflow_core::{ExecutorConfig, WorkflowExecutor, Step, StepResult, ExecutionContext};
//! use serde_json::Value;
//!
//! // Define a simple step
//! struct MyStep {
//!     id: String,
//! }
//!
//! impl Step for MyStep {
//!     fn id(&self) -> &str { &self.id }
//!     fn dependencies(&self) -> &[String] { &[] }
//!     fn execute(&self, _ctx: &mut ExecutionContext) -> pf_workflow_core::Result<StepResult> {
//!         let metrics = pf_workflow_core::StepMetrics::new(self.id.clone());
//!         Ok(StepResult::new(Value::from(42), metrics))
//!     }
//! }
//!
//! // Build and execute workflow
//! let mut executor = WorkflowExecutor::new(ExecutorConfig::default());
//! executor.add_step(Box::new(MyStep { id: "step1".to_string() }));
//! let metrics = executor.execute()?;
//! assert_eq!(metrics.successful_steps, 1);
//! # Ok::<(), pf_workflow_core::WorkflowError>(())
//! ```
//!
//! # Core Concepts
//!
//! ## Steps
//!
//! Steps are the basic unit of work in a workflow. Each step implements the [`Step`] trait:
//!
//! ```
//! # use pf_workflow_core::{Step, StepResult, ExecutionContext, Result, StepMetrics};
//! # use serde_json::Value;
//! struct DataLoadStep {
//!     id: String,
//! }
//!
//! impl Step for DataLoadStep {
//!     fn id(&self) -> &str {
//!         &self.id
//!     }
//!
//!     fn dependencies(&self) -> &[String] {
//!         &[] // No dependencies
//!     }
//!
//!     fn execute(&self, _ctx: &mut ExecutionContext) -> Result<StepResult> {
//!         // Do work here
//!         let metrics = StepMetrics::new(self.id.clone());
//!         Ok(StepResult::new(Value::from("data"), metrics))
//!     }
//! }
//! ```
//!
//! ## Dependencies
//!
//! Steps can depend on other steps. The engine ensures steps execute in the correct order:
//!
//! ```
//! # use pf_workflow_core::{ExecutorConfig, WorkflowExecutor, Step, StepResult, ExecutionContext, Result, StepMetrics};
//! # use serde_json::Value;
//! # struct Step1 { id: String }
//! # struct Step2 { id: String, deps: Vec<String> }
//! # impl Step for Step1 {
//! #     fn id(&self) -> &str { &self.id }
//! #     fn dependencies(&self) -> &[String] { &[] }
//! #     fn execute(&self, _: &mut ExecutionContext) -> Result<StepResult> {
//! #         Ok(StepResult::new(Value::Null, StepMetrics::new(self.id.clone())))
//! #     }
//! # }
//! # impl Step for Step2 {
//! #     fn id(&self) -> &str { &self.id }
//! #     fn dependencies(&self) -> &[String] { &self.deps }
//! #     fn execute(&self, _: &mut ExecutionContext) -> Result<StepResult> {
//! #         Ok(StepResult::new(Value::Null, StepMetrics::new(self.id.clone())))
//! #     }
//! # }
//! let mut executor = WorkflowExecutor::new(ExecutorConfig::default());
//!
//! executor.add_step(Box::new(Step1 { id: "load".to_string() }));
//! executor.add_step(Box::new(Step2 {
//!     id: "transform".to_string(),
//!     deps: vec!["load".to_string()],
//! }));
//!
//! // "load" executes before "transform"
//! executor.execute()?;
//! # Ok::<(), pf_workflow_core::WorkflowError>(())
//! ```
//!
//! ## Parallel Execution
//!
//! Execute independent steps concurrently:
//!
//! ```
//! # use pf_workflow_core::{ExecutorConfig, WorkflowExecutor};
//! let config = ExecutorConfig::builder()
//!     .max_parallel_steps(4)
//!     .build();
//!
//! let mut executor = WorkflowExecutor::new(config);
//! // Add steps...
//! # Ok::<(), pf_workflow_core::WorkflowError>(())
//! ```
//!
//! ## Progress Tracking
//!
//! Monitor workflow execution:
//!
//! ```no_run
//! use pf_workflow_core::{ConsoleProgressCallback, ExecutorConfig, WorkflowExecutor};
//!
//! let mut executor = WorkflowExecutor::new(ExecutorConfig::default());
//! // Add steps...
//!
//! let callback = ConsoleProgressCallback::new();
//! let metrics = executor.execute_with_progress(Box::new(callback))?;
//! # Ok::<(), pf_workflow_core::WorkflowError>(())
//! ```
//!
//! ## Cancellation
//!
//! Cancel running workflows gracefully:
//!
//! ```no_run
//! use pf_workflow_core::{CancellationToken, ExecutorConfig, WorkflowExecutor};
//! use std::thread;
//! use std::time::Duration;
//!
//! let token = CancellationToken::new();
//! let token_clone = token.clone();
//!
//! // Cancel after timeout
//! thread::spawn(move || {
//!     thread::sleep(Duration::from_secs(5));
//!     token_clone.cancel();
//! });
//!
//! let mut executor = WorkflowExecutor::new(ExecutorConfig::default());
//! // Add steps...
//!
//! let result = executor.execute_with_cancellation(token);
//! # Ok::<(), pf_workflow_core::WorkflowError>(())
//! ```
//!
//! # Examples
//!
//! See the `examples/` directory for comprehensive examples:
//!
//! - `basic_sequential.rs` - Simple ETL pipeline
//! - `parallel_execution.rs` - Parallel data processing with speedup comparison
//! - `progress_tracking.rs` - Various progress tracking methods
//! - `cancellation.rs` - Timeout and graceful shutdown patterns

pub mod cancellation;
pub mod config;
pub mod dag;
pub mod error;
pub mod executor;
pub mod metrics;
pub mod pools;
pub mod progress;
pub mod scheduler;
pub mod step;

// Re-export main types for convenience
pub use cancellation::CancellationToken;
pub use config::{ExecutorConfig, ExecutorConfigBuilder};
pub use dag::{Node, DAG};
pub use error::{DAGError, ExecutionError, ResourceError, Result, WorkflowError};
pub use executor::WorkflowExecutor;
pub use metrics::{StepMetrics, StepStatus, WorkflowMetrics};
pub use pools::ThreadPoolManager;
pub use progress::{
    CallbackProgressTracker, ConsoleProgressCallback, FileProgressTracker, NoOpCallback,
    ProgressCallback, ProgressEvent,
};
pub use scheduler::{ParallelScheduler, ResourceLimits};
pub use step::{ExecutionContext, ResourceHint, RetryConfig, Step, StepResult};
