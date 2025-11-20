//! Tetnus Neural Network Library
//!
//! Provides high-level neural network layers and modules built on tetnus-core.

pub mod error;
pub mod module;
pub mod linear;
pub mod activations;
pub mod sequential;

pub use error::{Result, TetnusNnError};
pub use module::Module;
pub use linear::Linear;
pub use activations::ReLU;
pub use sequential::Sequential;
