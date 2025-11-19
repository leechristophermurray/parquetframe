/// Financial analytics core library for ParquetFrame.
///
/// Provides high-performance technical indicators, risk metrics,
/// and financial calculations built on top of pf-time-core.

pub mod error;
pub mod indicators;
pub mod utils;

pub use error::FinError;
pub type Result<T> = std::result::Result<T, FinError>;
