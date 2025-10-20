//! PyO3 bindings for graph algorithms.
//!
//! Provides Python-accessible functions for CSR/CSC construction and graph traversal.

use numpy::{PyArray1, PyReadonlyArray1, PyArrayMethods};
use pf_graph_core::{bfs_parallel, bfs_sequential, dfs, CscGraph, CsrGraph};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Build CSR adjacency structure from edge lists.
///
/// # Arguments
/// * `src` - Source vertex IDs (numpy array)
/// * `dst` - Destination vertex IDs (numpy array)
/// * `num_vertices` - Total number of vertices
/// * `weights` - Optional edge weights (numpy array)
///
/// # Returns
/// Tuple of (indptr, indices, weights) as numpy arrays
#[pyfunction]
fn build_csr_rust<'py>(
    py: Python<'py>,
    src: PyReadonlyArray1<i32>,
    dst: PyReadonlyArray1<i32>,
    num_vertices: usize,
    weights: Option<PyReadonlyArray1<f64>>,
) -> PyResult<(
    Py<PyArray1<i64>>,
    Py<PyArray1<i32>>,
    Option<Py<PyArray1<f64>>>,
)> {
    let src_slice = src.as_slice()?;
    let dst_slice = dst.as_slice()?;
    let weights_slice = weights.as_ref().map(|w| w.as_slice()).transpose()?;

    let csr = CsrGraph::from_edges(src_slice, dst_slice, num_vertices, weights_slice)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    let indptr = PyArray1::from_vec(py, csr.indptr).to_owned().into();
    let indices = PyArray1::from_vec(py, csr.indices).to_owned().into();
    let w = csr
        .weights
        .map(|ws| PyArray1::from_vec(py, ws).to_owned().into());

    Ok((indptr, indices, w))
}

/// Build CSC adjacency structure from edge lists.
///
/// # Arguments
/// * `src` - Source vertex IDs (numpy array)
/// * `dst` - Destination vertex IDs (numpy array)
/// * `num_vertices` - Total number of vertices
/// * `weights` - Optional edge weights (numpy array)
///
/// # Returns
/// Tuple of (indptr, indices, weights) as numpy arrays
#[pyfunction]
fn build_csc_rust<'py>(
    py: Python<'py>,
    src: PyReadonlyArray1<i32>,
    dst: PyReadonlyArray1<i32>,
    num_vertices: usize,
    weights: Option<PyReadonlyArray1<f64>>,
) -> PyResult<(
    Py<PyArray1<i64>>,
    Py<PyArray1<i32>>,
    Option<Py<PyArray1<f64>>>,
)> {
    let src_slice = src.as_slice()?;
    let dst_slice = dst.as_slice()?;
    let weights_slice = weights.as_ref().map(|w| w.as_slice()).transpose()?;

    let csc = CscGraph::from_edges(src_slice, dst_slice, num_vertices, weights_slice)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    let indptr = PyArray1::from_vec(py, csc.indptr).to_owned().into();
    let indices = PyArray1::from_vec(py, csc.indices).to_owned().into();
    let w = csc
        .weights
        .map(|ws| PyArray1::from_vec(py, ws).to_owned().into());

    Ok((indptr, indices, w))
}

/// Perform BFS traversal on a graph.
///
/// # Arguments
/// * `indptr` - CSR indptr array
/// * `indices` - CSR indices array
/// * `num_vertices` - Total number of vertices
/// * `sources` - Source vertex IDs (numpy array)
/// * `max_depth` - Optional maximum traversal depth
///
/// # Returns
/// Tuple of (distances, predecessors) as numpy arrays
#[pyfunction]
fn bfs_rust<'py>(
    py: Python<'py>,
    indptr: PyReadonlyArray1<i64>,
    indices: PyReadonlyArray1<i32>,
    num_vertices: usize,
    sources: PyReadonlyArray1<i32>,
    max_depth: Option<i32>,
) -> PyResult<(Py<PyArray1<i32>>, Py<PyArray1<i32>>)> {
    let csr = CsrGraph {
        indptr: indptr.to_vec()?,
        indices: indices.to_vec()?,
        weights: None,
        num_vertices,
    };

    let sources_slice = sources.as_slice()?;
    let result = if sources_slice.len() == 1 {
        bfs_sequential(&csr, sources_slice[0], max_depth)
    } else {
        bfs_parallel(&csr, sources_slice, max_depth)
    }
    .map_err(|e| PyValueError::new_err(e.to_string()))?;

    let distances: Py<PyArray1<i32>> = PyArray1::from_vec(py, result.distances).to_owned().into();
    let predecessors: Py<PyArray1<i32>> = PyArray1::from_vec(py, result.predecessors).to_owned().into();

    Ok((distances, predecessors))
}

/// Perform DFS traversal on a graph.
///
/// # Arguments
/// * `indptr` - CSR indptr array
/// * `indices` - CSR indices array
/// * `num_vertices` - Total number of vertices
/// * `source` - Source vertex ID
/// * `max_depth` - Optional maximum traversal depth
///
/// # Returns
/// Array of visited vertex IDs in DFS order
#[pyfunction]
fn dfs_rust<'py>(
    py: Python<'py>,
    indptr: PyReadonlyArray1<i64>,
    indices: PyReadonlyArray1<i32>,
    num_vertices: usize,
    source: i32,
    max_depth: Option<i32>,
) -> PyResult<Py<PyArray1<i32>>> {
    let csr = CsrGraph {
        indptr: indptr.to_vec()?,
        indices: indices.to_vec()?,
        weights: None,
        num_vertices,
    };

    let result = dfs(&csr, source, max_depth).map_err(|e| PyValueError::new_err(e.to_string()))?;

    Ok(PyArray1::from_vec(py, result).to_owned().into())
}

/// Simple test function to verify module loading.
#[pyfunction]
fn graph_test() -> String {
    "Graph module loaded successfully".to_string()
}

/// Register graph functions with Python module.
pub fn register_graph_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(graph_test, m)?)?;
    m.add_function(wrap_pyfunction!(build_csr_rust, m)?)?;
    m.add_function(wrap_pyfunction!(build_csc_rust, m)?)?;
    m.add_function(wrap_pyfunction!(bfs_rust, m)?)?;
    m.add_function(wrap_pyfunction!(dfs_rust, m)?)?;
    Ok(())
}
