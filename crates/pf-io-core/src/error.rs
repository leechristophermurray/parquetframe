//! Error types for I/O operations.

use std::io;
use thiserror::Error;

/// Result type for I/O operations.
pub type Result<T> = std::result::Result<T, IoError>;

/// Error types for I/O operations.
#[derive(Error, Debug)]
pub enum IoError {
    /// File not found or inaccessible
    #[error("File not found: {0}")]
    FileNotFound(String),

    /// Failed to read file
    #[error("Failed to read file: {0}")]
    ReadError(String),

    /// Invalid Parquet file format
    #[error("Invalid Parquet file: {0}")]
    InvalidParquet(String),

    /// Invalid Avro file format
    #[error("Invalid Avro file: {0}")]
    InvalidAvro(String),

    /// Schema parsing error
    #[error("Schema error: {0}")]
    SchemaError(String),

    /// I/O error from std::io
    #[error("I/O error: {0}")]
    Io(#[from] io::Error),

    /// Parquet error
    #[error("Parquet error: {0}")]
    Parquet(String),

    /// Generic error
    #[error("{0}")]
    Other(String),
}

impl From<parquet::errors::ParquetError> for IoError {
    fn from(err: parquet::errors::ParquetError) -> Self {
        IoError::Parquet(err.to_string())
    }
}
