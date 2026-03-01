/// Layer 2: Adaptive XOR Masking
/// Finds optimal XOR mask to reduce entropy

use crate::error::{CobolError, CobolResult};

const XOR_HEADER: u8 = 0xFE;

pub fn encode(data: &[u8]) -> CobolResult<Vec<u8>> {
    if data.is_empty() {
        return Ok(vec![]);
    }

    // Try multiple masks and choose the one with lowest entropy
    let masks = [0x00u8, 0xAA, 0x55, 0xFF];
    let best_mask = find_best_mask(data, &masks);

    // If no mask reduces entropy, return as-is
    if best_mask == 0x00 {
        return Ok(data.to_vec());
    }

    // Encode with header
    let mut result = vec![XOR_HEADER, best_mask];
    for byte in data {
        result.push(byte ^ best_mask);
    }

    Ok(result)
}

pub fn decode(data: &[u8]) -> CobolResult<Vec<u8>> {
    if data.len() < 2 || data[0] != XOR_HEADER {
        return Ok(data.to_vec()); // Not encoded
    }

    let mask = data[1];
    let mut result = Vec::with_capacity(data.len());

    for byte in &data[2..] {
        result.push(byte ^ mask);
    }

    Ok(result)
}

fn find_best_mask(data: &[u8], masks: &[u8]) -> u8 {
    let original_entropy = calculate_entropy(data);
    let mut best_mask = 0x00;
    let mut best_entropy = original_entropy;

    for &mask in masks {
        let masked: Vec<u8> = data.iter().map(|b| b ^ mask).collect();
        let masked_entropy = calculate_entropy(&masked);

        if masked_entropy < best_entropy {
            best_entropy = masked_entropy;
            best_mask = mask;
        }
    }

    best_mask
}

fn calculate_entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }

    let mut freq = [0usize; 256];
    for &byte in data {
        freq[byte as usize] += 1;
    }

    let len = data.len() as f64;
    let mut entropy = 0.0;

    for count in &freq {
        if *count > 0 {
            let p = *count as f64 / len;
            entropy -= p * p.log2();
        }
    }

    entropy
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
}
