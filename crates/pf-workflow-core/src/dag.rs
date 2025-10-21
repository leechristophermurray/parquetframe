//! Directed Acyclic Graph (DAG) for workflow dependencies.
//!
//! This module provides a DAG structure for representing workflow step
//! dependencies, with support for topological sorting and cycle detection.

use crate::error::{DAGError, Result};
use std::collections::{HashMap, HashSet, VecDeque};

/// A node in the workflow DAG.
#[derive(Debug, Clone)]
pub struct Node {
    /// Unique identifier for the node.
    pub id: String,

    /// List of node IDs this node depends on (incoming edges).
    pub dependencies: Vec<String>,

    /// List of node IDs that depend on this node (outgoing edges).
    pub dependents: Vec<String>,
}

impl Node {
    /// Create a new node with the given ID.
    pub fn new(id: String) -> Self {
        Self {
            id,
            dependencies: Vec::new(),
            dependents: Vec::new(),
        }
    }
}

/// Directed Acyclic Graph representing workflow dependencies.
#[derive(Debug, Clone)]
pub struct DAG {
    /// Map of node ID to node.
    nodes: HashMap<String, Node>,

    /// List of edges (from_id, to_id).
    edges: Vec<(String, String)>,
}

impl DAG {
    /// Create a new empty DAG.
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            edges: Vec::new(),
        }
    }

    /// Add a node to the DAG.
    pub fn add_node(&mut self, id: String) {
        self.nodes
            .entry(id.clone())
            .or_insert_with(|| Node::new(id));
    }

    /// Add an edge from one node to another (from depends on to).
    ///
    /// # Arguments
    /// * `from` - The node that depends on `to`
    /// * `to` - The node that `from` depends on
    pub fn add_edge(&mut self, from: String, to: String) -> Result<()> {
        // Ensure both nodes exist
        if !self.nodes.contains_key(&from) {
            return Err(DAGError::NodeNotFound(from).into());
        }
        if !self.nodes.contains_key(&to) {
            return Err(DAGError::NodeNotFound(to).into());
        }

        // Add edge
        self.edges.push((from.clone(), to.clone()));

        // Update node dependencies and dependents
        if let Some(from_node) = self.nodes.get_mut(&from) {
            if !from_node.dependencies.contains(&to) {
                from_node.dependencies.push(to.clone());
            }
        }

        if let Some(to_node) = self.nodes.get_mut(&to) {
            if !to_node.dependents.contains(&from) {
                to_node.dependents.push(from);
            }
        }

        Ok(())
    }

    /// Get a topological ordering of the nodes.
    ///
    /// Returns a vector of node IDs in an order such that all dependencies
    /// of a node appear before it in the list.
    pub fn topological_sort(&self) -> Result<Vec<String>> {
        if self.nodes.is_empty() {
            return Err(DAGError::EmptyDAG.into());
        }

        let mut in_degree: HashMap<String, usize> =
            self.nodes.keys().map(|id| (id.clone(), 0)).collect();

        // Calculate in-degrees
        for (from, _to) in &self.edges {
            *in_degree.get_mut(from).unwrap() += 1;
        }

        // Start with nodes that have no dependencies
        let mut queue: VecDeque<String> = in_degree
            .iter()
            .filter(|(_, &degree)| degree == 0)
            .map(|(id, _)| id.clone())
            .collect();

        let mut sorted = Vec::new();

        while let Some(node_id) = queue.pop_front() {
            sorted.push(node_id.clone());

            // Reduce in-degree for all dependents
            if let Some(node) = self.nodes.get(&node_id) {
                for dependent in &node.dependents {
                    if let Some(degree) = in_degree.get_mut(dependent) {
                        *degree = degree.saturating_sub(1);
                        if *degree == 0 {
                            queue.push_back(dependent.clone());
                        }
                    }
                }
            }
        }

        // If we didn't visit all nodes, there's a cycle
        if sorted.len() != self.nodes.len() {
            return Err(DAGError::CycleDetected.into());
        }

        Ok(sorted)
    }

    /// Get all nodes that have no pending dependencies.
    pub fn get_independent_nodes(&self) -> Vec<String> {
        self.nodes
            .values()
            .filter(|node| node.dependencies.is_empty())
            .map(|node| node.id.clone())
            .collect()
    }

    /// Get nodes that are ready to execute given a set of completed nodes.
    pub fn get_ready_nodes(&self, completed: &HashSet<String>) -> Vec<String> {
        self.nodes
            .values()
            .filter(|node| {
                // Node is ready if all its dependencies are completed
                !completed.contains(&node.id)
                    && node.dependencies.iter().all(|dep| completed.contains(dep))
            })
            .map(|node| node.id.clone())
            .collect()
    }

    /// Group nodes into levels that can run in parallel.
    ///
    /// Returns a vector of vectors, where each inner vector contains
    /// node IDs that can be executed in parallel.
    pub fn get_parallelizable_groups(&self) -> Result<Vec<Vec<String>>> {
        let sorted = self.topological_sort()?;
        let mut groups = Vec::new();
        let mut completed = HashSet::new();

        while completed.len() < sorted.len() {
            let ready = self.get_ready_nodes(&completed);
            if ready.is_empty() {
                break;
            }

            groups.push(ready.clone());
            completed.extend(ready);
        }

        Ok(groups)
    }

    /// Get the number of nodes in the DAG.
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Get the number of edges in the DAG.
    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }
}

impl Default for DAG {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_dag() {
        let dag = DAG::new();
        assert_eq!(dag.node_count(), 0);
        assert!(dag.topological_sort().is_err());
    }

    #[test]
    fn test_single_node() {
        let mut dag = DAG::new();
        dag.add_node("A".to_string());

        let sorted = dag.topological_sort().unwrap();
        assert_eq!(sorted, vec!["A"]);
    }

    #[test]
    fn test_linear_dag() {
        // A -> B -> C
        let mut dag = DAG::new();
        dag.add_node("A".to_string());
        dag.add_node("B".to_string());
        dag.add_node("C".to_string());

        dag.add_edge("B".to_string(), "A".to_string()).unwrap();
        dag.add_edge("C".to_string(), "B".to_string()).unwrap();

        let sorted = dag.topological_sort().unwrap();
        assert_eq!(sorted, vec!["A", "B", "C"]);
    }

    #[test]
    fn test_parallel_dag() {
        // A -> [B, C, D] -> E
        let mut dag = DAG::new();
        for id in &["A", "B", "C", "D", "E"] {
            dag.add_node(id.to_string());
        }

        dag.add_edge("B".to_string(), "A".to_string()).unwrap();
        dag.add_edge("C".to_string(), "A".to_string()).unwrap();
        dag.add_edge("D".to_string(), "A".to_string()).unwrap();
        dag.add_edge("E".to_string(), "B".to_string()).unwrap();
        dag.add_edge("E".to_string(), "C".to_string()).unwrap();
        dag.add_edge("E".to_string(), "D".to_string()).unwrap();

        let groups = dag.get_parallelizable_groups().unwrap();
        assert_eq!(groups.len(), 3);
        assert_eq!(groups[0], vec!["A"]);
        assert_eq!(groups[1].len(), 3); // B, C, D in any order
        assert_eq!(groups[2], vec!["E"]);
    }

    #[test]
    fn test_cycle_detection() {
        // A -> B -> A (cycle)
        let mut dag = DAG::new();
        dag.add_node("A".to_string());
        dag.add_node("B".to_string());

        dag.add_edge("B".to_string(), "A".to_string()).unwrap();
        dag.add_edge("A".to_string(), "B".to_string()).unwrap();

        let result = dag.topological_sort();
        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            crate::error::WorkflowError::DAG(DAGError::CycleDetected)
        ));
    }

    #[test]
    fn test_get_independent_nodes() {
        let mut dag = DAG::new();
        dag.add_node("A".to_string());
        dag.add_node("B".to_string());
        dag.add_node("C".to_string());

        dag.add_edge("B".to_string(), "A".to_string()).unwrap();

        let independent = dag.get_independent_nodes();
        assert!(independent.contains(&"A".to_string()));
        assert!(independent.contains(&"C".to_string()));
        assert!(!independent.contains(&"B".to_string()));
    }

    #[test]
    fn test_get_ready_nodes() {
        let mut dag = DAG::new();
        dag.add_node("A".to_string());
        dag.add_node("B".to_string());
        dag.add_node("C".to_string());

        dag.add_edge("B".to_string(), "A".to_string()).unwrap();
        dag.add_edge("C".to_string(), "B".to_string()).unwrap();

        let mut completed = HashSet::new();
        completed.insert("A".to_string());

        let ready = dag.get_ready_nodes(&completed);
        assert_eq!(ready, vec!["B"]);
    }
}
