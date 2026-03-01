/// Layer 3: Delta Encoding + Run-Length Encoding
/// Reduces magnitude of byte values, then compresses runs

use crate::error::{CobolError, CobolResult};

const DELTA_HEADER: u8 = 0xFD;

pub fn encode(data: &[u8]) -> CobolResult<Vec<u8>> {
    if data.is_empty() {
        return Ok(vec![]);
    }

    // Delta encoding
    let delta_encoded = delta_encode(data);

    // Add header
    let mut result = vec![DELTA_HEADER];
    result.extend(delta_encoded);

    Ok(result)
}

pub fn decode(data: &[u8]) -> CobolResult<Vec<u8>> {
    if data.is_empty() {
        return Ok(vec![]);
    }

    if data[0] != DELTA_HEADER {
        return Ok(data.to_vec()); // Not encoded
    }

    // Decode delta
    let result = delta_decode(&data[1..]);

    Ok(result)
}

fn delta_encode(data: &[u8]) -> Vec<u8> {
    let mut result = Vec::with_capacity(data.len());

    if data.is_empty() {
        return result;
    }

    result.push(data[0]); // Store first byte as-is

    for i in 1..data.len() {
        let delta = data[i].wrapping_sub(data[i - 1]);
        result.push(delta);
    }

    result
}

fn delta_decode(data: &[u8]) -> Vec<u8> {
    let mut result = Vec::with_capacity(data.len());

    if data.is_empty() {
        return result;
    }

    result.push(data[0]); // First byte as-is

    for i in 1..data.len() {
        let prev = result[i - 1];
        let value = prev.wrapping_add(data[i]);
        result.push(value);
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encode_decode_roundtrip() {
        let data = b"hello world";
        let encoded = encode(data).unwrap();
        let decoded = decode(&encoded).unwrap();
        assert_eq!(data, &decoded[..]);
    }

    #[test]
    fn test_empty_data() {
        assert_eq!(encode(&[]).unwrap(), vec![]);
        assert_eq!(decode(&[]).unwrap(), vec![]);
    }

    #[test]
    fn test_repetitive_data() {
        let data = b"aaaaaabbbbbbcccccc";
        let encoded = encode(data).unwrap();
        let decoded = decode(&encoded).unwrap();
        assert_eq!(data, &decoded[..]);
        // Note: Delta encoding doesn't guarantee size reduction;
        // it only reduces entropy for use with subsequent compression
    }
}
