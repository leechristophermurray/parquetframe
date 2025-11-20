//! Python bindings for TETNUS NN (Neural Network) module
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use tetnus_nn::{Linear, Module as _};
use crate::tetnus::{PyTensor, tetnus_err_to_py};

/// Linear layer (fully connected)
#[pyclass(name = "Linear")]
pub struct PyLinear {
    inner: Linear,
}

#[pymethods]
impl PyLinear {
    #[new]
    #[pyo3(signature = (in_features, out_features, bias=true))]
    fn new(in_features: usize, out_features: usize, bias: bool) -> PyResult<Self> {
        Linear::new(in_features, out_features, bias)
            .map(|inner| PyLinear { inner })
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    fn forward(&self, input: &PyTensor) -> PyResult<PyTensor> {
        self.inner.forward(&input.inner)
            .map(|t| PyTensor { inner: t })
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    fn parameters(&self) -> Vec<PyTensor> {
        self.inner.parameters()
            .into_iter()
            .map(|t| PyTensor { inner: t })
            .collect()
    }
}

/// Register NN functions and classes
pub fn register_nn_module(parent: &Bound<'_, PyModule>) -> PyResult<()> {
    let m = PyModule::new(parent.py(), "nn")?;

    m.add_class::<PyLinear>()?;

    parent.add_submodule(&m)?;
    Ok(())
}
