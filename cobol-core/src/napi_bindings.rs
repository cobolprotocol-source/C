/// NAPI Node.js Bindings for CobolCompressor
/// Exposes Rust compression library to JavaScript/Node.js

use napi::bindgen_prelude::*;
use crate::CobolCompressor;

#[napi]
pub struct JsCobolCompressor {
    inner: CobolCompressor,
}

#[napi]
impl JsCobolCompressor {
    #[napi(constructor)]
    pub fn new() -> Self {
        JsCobolCompressor {
            inner: CobolCompressor::new(),
        }
    }

    #[napi(factory)]
    pub fn with_layers(l1: bool, l2: bool, l3: bool) -> Self {
        JsCobolCompressor {
            inner: CobolCompressor::with_layers(l1, l2, l3),
        }
    }

    #[napi]
    pub fn compress(&self, data: Vec<u8>) -> Result<Vec<u8>> {
        self.inner
            .compress(&data)
            .map_err(|e| Error::new(napi::Status::GenericFailure, e.to_string()))
    }

    #[napi]
    pub fn decompress(&self, data: Vec<u8>) -> Result<Vec<u8>> {
        self.inner
            .decompress(&data)
            .map_err(|e| Error::new(napi::Status::GenericFailure, e.to_string()))
    }
}
