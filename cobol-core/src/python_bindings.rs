/// PyO3 Python bindings for CobolCompressor
/// Exposes Rust compression library to Python

use pyo3::prelude::*;
use pyo3::exceptions;
use pyo3::types::PyDict;
use crate::{CobolCompressor, CobolError};

#[pyclass(name = "CobolCompressor")]
pub struct PyCobolCompressor {
    inner: CobolCompressor,
}

#[pymethods]
impl PyCobolCompressor {
    #[new]
    fn new(l1: Option<bool>, l2: Option<bool>, l3: Option<bool>) -> Self {
        let enable_l1 = l1.unwrap_or(true);
        let enable_l2 = l2.unwrap_or(true);
        let enable_l3 = l3.unwrap_or(true);
        
        PyCobolCompressor {
            inner: CobolCompressor::with_layers(enable_l1, enable_l2, enable_l3),
        }
    }

    fn compress(&self, data: &[u8]) -> PyResult<Vec<u8>> {
        self.inner
            .compress(data)
            .map_err(|err| exceptions::PyRuntimeError::new_err(err.to_string()))
    }

    fn decompress(&self, data: &[u8]) -> PyResult<Vec<u8>> {
        self.inner
            .decompress(data)
            .map_err(|err| exceptions::PyRuntimeError::new_err(err.to_string()))
    }
}

/// PyO3 module initialization
/// This doesn't work as a normal module - it will be handled by maturin
pub fn init_module(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyCobolCompressor>()?;
    m.add("__version__", "0.1.0")?;
    Ok(())
}
