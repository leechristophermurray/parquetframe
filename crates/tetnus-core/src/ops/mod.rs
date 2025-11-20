/// Computation graph operations

use crate::{Tensor, Result};

/// Trait for differentiable operations
pub trait Op: Send + Sync {
    /// Forward pass: compute the output
    fn forward(&self, inputs: &[&Tensor]) -> Result<Tensor>;

    /// Backward pass: compute gradients for inputs given output gradient
    fn backward(&self, grad_output: &Tensor) -> Result<Vec<Tensor>>;

    /// Name of the operation (for debugging)
    fn name(&self) -> &str;
}

// Stub implementations - will be filled in next
pub mod matmul;
pub mod elementwise;
pub mod view;
pub mod reduce;
