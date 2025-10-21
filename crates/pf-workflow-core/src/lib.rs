//! Workflow execution engine for ParquetFrame.
//!
//! This crate provides high-performance workflow orchestration including:
//! - DAG execution with topological ordering
//! - Concurrency management and resource scheduling
//! - Backpressure, retries, and timeouts
//!
//! # Phase 3.4: Workflow Engine Core
//!
//! This implementation provides:
//! - DAG-based workflow representation with cycle detection
//! - Topological sorting for execution ordering
//! - Parallel execution scheduling
//! - Comprehensive metrics collection
//! - Configurable retry and timeout behavior

pub mod cancellation;
pub mod config;
pub mod dag;
pub mod error;
pub mod executor;
pub mod metrics;
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
pub use progress::{ConsoleProgressCallback, NoOpCallback, ProgressCallback, ProgressEvent};
pub use scheduler::ParallelScheduler;
pub use step::{ExecutionContext, ResourceHint, RetryConfig, Step, StepResult};
