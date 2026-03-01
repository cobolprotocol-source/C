use std::fmt;

#[derive(Debug, Clone)]
pub enum CobolError {
    InvalidData(String),
    CompressionFailed(String),
    DecompressionFailed(String),
    IOError(String),
}

impl fmt::Display for CobolError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CobolError::InvalidData(msg) => write!(f, "Invalid data: {}", msg),
            CobolError::CompressionFailed(msg) => write!(f, "Compression failed: {}", msg),
            CobolError::DecompressionFailed(msg) => write!(f, "Decompression failed: {}", msg),
            CobolError::IOError(msg) => write!(f, "IO error: {}", msg),
        }
    }
}

impl std::error::Error for CobolError {}

pub type CobolResult<T> = Result<T, CobolError>;
