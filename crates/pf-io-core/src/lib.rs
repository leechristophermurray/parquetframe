//! I/O operations for ParquetFrame.
//!
//! This crate provides high-performance I/O operations including:
//! - Parquet metadata parsing and fast-path filters
//! - Avro schema resolution and fast deserialization
//! - Columnar data operations on Arrow buffers
//!
//! Phase 2: I/O Fast-Paths Implementation

/// Error types for I/O operations
pub mod error;

/// Parquet metadata reading and statistics
pub mod parquet_meta;

// Re-export common types
pub use error::{IoError, Result};
pub use parquet_meta::{ColumnStatistics, ParquetMetadata};
