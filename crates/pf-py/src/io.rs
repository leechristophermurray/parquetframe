//! PyO3 bindings for I/O operations.
//!
//! Provides Python-accessible functions for Parquet metadata reading and statistics.

use pf_io_core::parquet_meta;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Read Parquet file metadata without loading data.
///
/// # Arguments
/// * `path` - Path to the Parquet file (string)
///
/// # Returns
/// Dictionary with metadata:
///   - num_rows: Number of rows (int)
///   - num_row_groups: Number of row groups (int)
///   - num_columns: Number of columns (int)
///   - file_size_bytes: File size in bytes (int or None)
///   - version: Parquet version (int)
///   - column_names: List of column names (list of str)
///   - column_types: List of column types (list of str)
#[pyfunction]
fn read_parquet_metadata_rust(py: Python, path: String) -> PyResult<Py<PyDict>> {
    let metadata = parquet_meta::read_parquet_metadata(&path)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    let dict = PyDict::new(py);
    dict.set_item("num_rows", metadata.num_rows)?;
    dict.set_item("num_row_groups", metadata.num_row_groups)?;
    dict.set_item("num_columns", metadata.num_columns)?;
    dict.set_item("file_size_bytes", metadata.file_size_bytes)?;
    dict.set_item("version", metadata.version)?;
    dict.set_item("column_names", metadata.column_names)?;
    dict.set_item("column_types", metadata.column_types)?;

    Ok(dict.into())
}

/// Get row count from a Parquet file (very fast).
///
/// # Arguments
/// * `path` - Path to the Parquet file (string)
///
/// # Returns
/// Number of rows in the file (int)
#[pyfunction]
fn get_parquet_row_count_rust(path: String) -> PyResult<i64> {
    parquet_meta::get_row_count(&path).map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Get column names from a Parquet file.
///
/// # Arguments
/// * `path` - Path to the Parquet file (string)
///
/// # Returns
/// List of column names (list of str)
#[pyfunction]
fn get_parquet_column_names_rust(path: String) -> PyResult<Vec<String>> {
    parquet_meta::get_column_names(&path).map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Get column statistics from a Parquet file.
///
/// # Arguments
/// * `path` - Path to the Parquet file (string)
///
/// # Returns
/// List of dictionaries with statistics for each column:
///   - name: Column name (str)
///   - null_count: Number of nulls (int or None)
///   - distinct_count: Number of distinct values (int or None)
///   - min_value: Minimum value as string (str or None)
///   - max_value: Maximum value as string (str or None)
#[pyfunction]
fn get_parquet_column_stats_rust(py: Python, path: String) -> PyResult<Vec<Py<PyDict>>> {
    let stats = parquet_meta::get_column_statistics(&path)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    let mut result = Vec::new();
    for stat in stats {
        let dict = PyDict::new(py);
        dict.set_item("name", stat.name)?;
        dict.set_item("null_count", stat.null_count)?;
        dict.set_item("distinct_count", stat.distinct_count)?;
        dict.set_item("min_value", stat.min_value)?;
        dict.set_item("max_value", stat.max_value)?;
        result.push(dict.into());
    }

    Ok(result)
}

/// Register I/O functions with Python module.
pub fn register_io_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_parquet_metadata_rust, m)?)?;
    m.add_function(wrap_pyfunction!(get_parquet_row_count_rust, m)?)?;
    m.add_function(wrap_pyfunction!(get_parquet_column_names_rust, m)?)?;
    m.add_function(wrap_pyfunction!(get_parquet_column_stats_rust, m)?)?;
    Ok(())
}
