//! Tetnus Neural Network Library
//!
//! Provides high-level neural network layers and modules built on tetnus-core.

pub mod error;
pub mod module;
pub mod linear;

pub use error::{Result, TetnusNnError};
pub use module::Module;
pub use linear::Linear;
