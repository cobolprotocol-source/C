/// Layer 1: Adaptive Byte-Pair Encoding
/// Detects common byte pairs and encodes efficiently

use crate::error::{CobolError, CobolResult};
use std::collections::HashMap;

const CHUNK_SIZE: usize = 256;
const MARKER_BYTE: u8 = 0xFF;

pub fn encode(data: &[u8]) -> CobolResult<Vec<u8>> {
    if data.is_empty() {
        return Ok(vec![]);
    }

    // Find most common byte pair in chunks
    let pairs = analyze_pairs(data);
    
    if pairs.is_empty() {
        return Ok(data.to_vec()); // No common pairs, pass-through
    }

    let (pair, count) = pairs.first().unwrap();
    
    // If pair count is too low, skip encoding
    if *count < 3 {
        return Ok(data.to_vec());
    }

    // Encode: replace most common pair with marker + value
    let mut result = Vec::with_capacity(data.len());
    result.push(MARKER_BYTE); // Header: marker byte follows
    result.push(pair[0]);
    result.push(pair[1]);

    let mut i = 0;
    while i < data.len() {
        if i + 1 < data.len() && data[i] == pair[0] && data[i + 1] == pair[1] {
            result.push(MARKER_BYTE);
            i += 2;
        } else {
            if data[i] == MARKER_BYTE {
                result.push(MARKER_BYTE);
                result.push(MARKER_BYTE); // Escape marker
            } else {
                result.push(data[i]);
            }
            i += 1;
        }
    }

    Ok(result)
}

pub fn decode(data: &[u8]) -> CobolResult<Vec<u8>> {
    if data.is_empty() {
        return Ok(vec![]);
    }

    if data.len() < 3 || data[0] != MARKER_BYTE {
        return Ok(data.to_vec()); // Not encoded, pass-through
    }

    let pair = [data[1], data[2]];
    let mut result = Vec::with_capacity(data.len() * 2);

    let mut i = 3;
    while i < data.len() {
        if data[i] == MARKER_BYTE {
            if i + 1 < data.len() && data[i + 1] == MARKER_BYTE {
                // Escaped marker
                result.push(MARKER_BYTE);
                i += 2;
            } else {
                // Restore pair
                result.extend_from_slice(&pair);
                i += 1;
            }
        } else {
            result.push(data[i]);
            i += 1;
        }
    }

    Ok(result)
}

fn analyze_pairs(data: &[u8]) -> Vec<([u8; 2], usize)> {
    let mut freq: HashMap<[u8; 2], usize> = HashMap::new();

    for pair in data.windows(2) {
        let p = [pair[0], pair[1]];
        *freq.entry(p).or_insert(0) += 1;
    }

    let mut pairs: Vec<_> = freq.into_iter().collect();
    pairs.sort_by(|a, b| b.1.cmp(&a.1)); // Sort by frequency descending
    pairs.truncate(10); // Keep top 10
    pairs
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encode_decode_roundtrip() {
        let data = b"hello world hello world";
        let encoded = encode(data).unwrap();
        let decoded = decode(&encoded).unwrap();
        assert_eq!(data, &decoded[..]);
    }

    #[test]
    fn test_empty_data() {
        assert_eq!(encode(&[]).unwrap(), vec![]);
        assert_eq!(decode(&[]).unwrap(), vec![]);
    }
}
