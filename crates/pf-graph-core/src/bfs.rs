//! Breadth-First Search (BFS) algorithms.

use crate::{CsrGraph, GraphError, Result, VertexId};

/// BFS traversal result
#[derive(Debug, Clone)]
pub struct BfsResult {
    pub distances: Vec<i32>,
    pub predecessors: Vec<i32>,
}

/// Sequential BFS (stub)
pub fn bfs_sequential(
    _csr: &CsrGraph,
    _source: VertexId,
    _max_depth: Option<i32>,
) -> Result<BfsResult> {
    Err(GraphError::EmptyGraph)
}

/// Parallel BFS (stub)
pub fn bfs_parallel(
    _csr: &CsrGraph,
    _sources: &[VertexId],
    _max_depth: Option<i32>,
) -> Result<BfsResult> {
    Err(GraphError::EmptyGraph)
}
