//! Tetnus Neural Network Library
//!
//! Provides high-level neural network layers and modules built on tetnus-core.

pub mod error;
pub mod module;
pub mod linear;
pub mod activations;
pub mod sequential;
pub mod embedding;
pub mod norm;
pub mod preprocessing;

pub use error::{Result, TetnusNnError};
pub use module::Module;
pub use linear::Linear;
pub use activations::ReLU;
pub use sequential::Sequential;
pub use embedding::Embedding;
pub use norm::LayerNorm;
pub use preprocessing::{NumericalProcessor, CategoricalProcessor};
