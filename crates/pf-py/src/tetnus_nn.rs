//! Python bindings for TETNUS NN (Neural Network) module
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use tetnus_nn::{Linear, ReLU, Sequential, Module as _};
use crate::tetnus::{PyTensor, tetnus_err_to_py};

/// Linear layer (fully connected)
#[pyclass(name = "Linear")]
#[derive(Clone)]
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

/// ReLU Activation
#[pyclass(name = "ReLU")]
#[derive(Clone)]
pub struct PyReLU {
    inner: ReLU,
}

#[pymethods]
impl PyReLU {
    #[new]
    fn new() -> Self {
        PyReLU {
            inner: ReLU::new(),
        }
    }

    fn forward(&self, input: &PyTensor) -> PyResult<PyTensor> {
        self.inner.forward(&input.inner)
            .map(|t| PyTensor { inner: t })
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}

/// Sequential Container
#[pyclass(name = "Sequential")]
pub struct PySequential {
    inner: Sequential,
}

#[pymethods]
impl PySequential {
    #[new]
    fn new() -> Self {
        PySequential {
            inner: Sequential::new(),
        }
    }

    fn add(&mut self, module: Bound<'_, PyAny>) -> PyResult<()> {
        if let Ok(linear) = module.extract::<PyLinear>() {
            self.inner.add(Box::new(linear.inner));
        } else if let Ok(relu) = module.extract::<PyReLU>() {
            self.inner.add(Box::new(relu.inner));
        } else {
            return Err(PyValueError::new_err("Unsupported module type"));
        }
        Ok(())
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
    m.add_class::<PyReLU>()?;
    m.add_class::<PySequential>()?;

    parent.add_submodule(&m)?;
    Ok(())
}
