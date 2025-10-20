//! Graph algorithms and data structures for ParquetFrame.
//!
//! This crate provides high-performance graph operations including:
//! - CSR/CSC adjacency structure building
//! - Graph traversal algorithms (BFS, DFS)
//! - Advanced algorithms (PageRank, Dijkstra, Connected Components)
//!
//! Phase 1: Core graph algorithms (CSR/CSC, BFS, DFS)

pub mod types;
pub mod error;
pub mod csr;
pub mod csc;
pub mod bfs;
pub mod dfs;

// Re-export commonly used types
pub use types::*;
pub use error::{GraphError, Result};
pub use csr::CsrGraph;
pub use csc::CscGraph;
pub use bfs::{bfs_parallel, bfs_sequential, BfsResult};
pub use dfs::dfs;
