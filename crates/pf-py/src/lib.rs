//! Python bindings for ParquetFrame Rust backend.
//!
//! This module provides PyO3 bindings that expose Rust functionality to Python.
//! It serves as the bridge between Python and Rust components.
//!
//! Phase 0: Foundation - Basic detection functionality
//! Phase 1+: Actual graph, I/O, and workflow bindings

use pyo3::prelude::*;

/// Check if Rust backend is available.
///
/// This function is called by Python to detect if the Rust backend
/// was successfully compiled and loaded.
///
/// # Returns
/// Always returns `true` when the Rust module is loaded.
#[pyfunction]
fn rust_available() -> bool {
    true
}

/// Get the version of the Rust backend.
///
/// # Returns
/// Version string matching the workspace version (1.1.0 for Phase 0)
#[pyfunction]
fn rust_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// ParquetFrame Rust backend module.
///
/// This module is imported by Python as `parquetframe._rustic`.
/// It provides high-performance implementations of performance-critical operations.
#[pymodule]
fn _rustic(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_available, m)?)?;
    m.add_function(wrap_pyfunction!(rust_version, m)?)?;
    Ok(())
}
