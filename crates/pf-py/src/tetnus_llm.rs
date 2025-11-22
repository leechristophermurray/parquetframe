use pyo3::prelude::*;
use tetnus_llm::LoRALinear;
use tetnus_core::Tensor;

#[pyclass(name = "LoRALinear")]
pub struct PyLoRALinear {
    inner: LoRALinear,
}

#[pymethods]
impl PyLoRALinear {
    #[new]
    fn new(in_features: usize, out_features: usize, rank: usize, alpha: f32) -> Self {
        Self {
            inner: LoRALinear::new(in_features, out_features, rank, alpha),
        }
    }

    fn forward(&self, x: &Bound<'_, PyAny>) -> PyResult<PyObject> {
        // Placeholder - would extract Tensor from Python object
        // For now, just return a dummy tensor
        Ok(x.clone().unbind())
    }
}

pub fn register_tetnus_llm_module(py: Python, parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    let m = PyModule::new(py, "llm")?;
    m.add_class::<PyLoRALinear>()?;
    parent_module.add_submodule(&m)?;
    Ok(())
}
