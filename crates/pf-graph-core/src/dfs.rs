//! Depth-First Search (DFS) algorithm.

use crate::{CsrGraph, GraphError, Result, VertexId};

/// Iterative DFS (stub)
pub fn dfs(
    _csr: &CsrGraph,
    _source: VertexId,
    _max_depth: Option<i32>,
) -> Result<Vec<VertexId>> {
    Err(GraphError::EmptyGraph)
}
