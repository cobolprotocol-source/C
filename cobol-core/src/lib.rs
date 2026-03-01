/// COBOL Core: Native multi-layer compression library
/// Implements L1-L3 compression with high performance
///
/// - L1: Adaptive byte-pair encoding
/// - L2: Structural XOR masking
/// - L3: Delta encoding with RLE

pub mod layer1;
pub mod layer2;
pub mod layer3;
pub mod error;
pub mod python_bindings;
// NAPI bindings disabled for now - requires special build system
// pub mod napi_bindings;

pub use error::{CobolError, CobolResult};

/// Main compression pipeline
pub struct CobolCompressor {
    enable_l1: bool,
    enable_l2: bool,
    enable_l3: bool,
}

impl CobolCompressor {
    pub fn new() -> Self {
        CobolCompressor {
            enable_l1: true,
            enable_l2: true,
            enable_l3: true,
        }
    }

    pub fn with_layers(l1: bool, l2: bool, l3: bool) -> Self {
        CobolCompressor {
            enable_l1: l1,
            enable_l2: l2,
            enable_l3: l3,
        }
    }

    /// Compress data through enabled layers
    pub fn compress(&self, data: &[u8]) -> CobolResult<Vec<u8>> {
        let mut current = data.to_vec();

        if self.enable_l1 {
            current = layer1::encode(&current)?;
        }
        if self.enable_l2 {
            current = layer2::encode(&current)?;
        }
        if self.enable_l3 {
            current = layer3::encode(&current)?;
        }

        Ok(current)
    }

    /// Decompress data through enabled layers in reverse order
    pub fn decompress(&self, data: &[u8]) -> CobolResult<Vec<u8>> {
        let mut current = data.to_vec();

        if self.enable_l3 {
            current = layer3::decode(&current)?;
        }
        if self.enable_l2 {
            current = layer2::decode(&current)?;
        }
        if self.enable_l1 {
            current = layer1::decode(&current)?;
        }

        Ok(current)
    }
}

impl Default for CobolCompressor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_roundtrip() {
        let data = b"Hello World! Hello World!";
        let compressor = CobolCompressor::new();
        let compressed = compressor.compress(data).unwrap();
        let decompressed = compressor.decompress(&compressed).unwrap();
        assert_eq!(data, &decompressed[..]);
    }

    #[test]
    fn test_selective_layers() {
        let data = b"test data test data test data";
        let compressor = CobolCompressor::with_layers(true, false, true);
        let compressed = compressor.compress(data).unwrap();
        let decompressed = compressor.decompress(&compressed).unwrap();
        assert_eq!(data, &decompressed[..]);
    }
}

// PyO3 Python module initialization
use pyo3::prelude::*;

#[pymodule]
fn cobol_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<python_bindings::PyCobolCompressor>()?;
    m.add("__version__", "0.1.0")?;
    
    // Add layer metadata
    m.add("LAYER_1_NAME", "Adaptive Byte-Pair Encoding")?;
    m.add("LAYER_2_NAME", "XOR Masking")?;
    m.add("LAYER_3_NAME", "Delta + RLE")?;

    Ok(())
}
