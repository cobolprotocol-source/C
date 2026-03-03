/**
 * COBOL Protocol v1.6: GPU-Accelerated Entropy & Pattern Detection
 * 
 * High-performance CUDA kernels for:
 * 1. Shannon entropy calculation (vectorized)
 * 2. Byte frequency histograms (atomic operations)
 * 3. Pattern matching (rolling hash)
 * 4. Top-K pattern extraction (reduction)
 */

#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <cmath>
#include <cstring>

#define BLOCK_SIZE 256
#define HISTOGRAM_SIZE 256
#define MAX_PATTERNS 512
#define PATTERN_LENGTH 4

// ============================================================================
// HISTOGRAM KERNEL - Compute byte frequency distribution
// ============================================================================

__global__ void histogram_kernel(
    const unsigned char* data,
    unsigned int data_size,
    unsigned int* histogram
) {
    unsigned int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx < data_size) {
        unsigned char byte_val = data[idx];
        atomicAdd(&histogram[byte_val], 1);
    }
}

// ============================================================================
// ENTROPY KERNEL - Compute Shannon entropy from histogram
// ============================================================================

__global__ void entropy_kernel(
    const unsigned int* histogram,
    unsigned int data_size,
    double* entropy_out
) {
    unsigned int idx = threadIdx.x;
    if (idx >= HISTOGRAM_SIZE) return;
    
    double local_entropy = 0.0;
    unsigned int freq = histogram[idx];
    
    if (freq > 0 && data_size > 0) {
        double p = (double)freq / data_size;  // Probability
        local_entropy = -p * log2(p);          // Shanon entropy
    }
    
    // Parallel reduction
    __shared__ double shared_entropy[HISTOGRAM_SIZE];
    shared_entropy[idx] = local_entropy;
    __syncthreads();
    
    // Tree reduction
    for (unsigned int s = HISTOGRAM_SIZE / 2; s > 0; s >>= 1) {
        if (idx < s) {
            shared_entropy[idx] += shared_entropy[idx + s];
        }
        __syncthreads();
    }
    
    if (idx == 0) {
        *entropy_out = shared_entropy[0];
    }
}

// ============================================================================
// PATTERN FREQUENCY KERNEL - Count pattern occurrences (rolling hash)
// ============================================================================

__global__ void pattern_frequency_kernel(
    const unsigned char* data,
    unsigned int data_size,
    unsigned int* pattern_counts,
    unsigned int* pattern_keys,
    unsigned int max_patterns,
    unsigned int pattern_len
) {
    unsigned int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx + pattern_len <= data_size) {
        // Compute rolling hash for pattern
        unsigned int hash = 0;
        for (unsigned int i = 0; i < pattern_len; i++) {
            hash = hash * 31 + data[idx + i];
        }
        
        // Find or insert in pattern table (simple open addressing)
        unsigned int bucket = hash % max_patterns;
        unsigned int probes = 0;
        
        while (probes < max_patterns) {
            unsigned int expected = 0;
            
            // Atomic CAS to claim slot
            unsigned int old = atomicCAS(&pattern_keys[bucket], 0, hash);
            
            if (old == 0 || old == hash) {
                // Slot is ours or already ours, increment count
                atomicAdd(&pattern_counts[bucket], 1);
                break;
            }
            
            // Linear probing
            bucket = (bucket + 1) % max_patterns;
            probes++;
        }
    }
}

// ============================================================================
// TOP-K PATTERNS REDUCTION KERNEL
// ============================================================================

__global__ void extract_top_k_patterns(
    const unsigned int* pattern_counts,
    const unsigned int* pattern_keys,
    unsigned int num_buckets,
    unsigned int* top_k_counts,
    unsigned int* top_k_keys,
    unsigned int k
) {
    unsigned int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx < num_buckets && pattern_keys[idx] != 0) {
        unsigned int count = pattern_counts[idx];
        unsigned int key = pattern_keys[idx];
        
        // Find insertion position in top-k array
        unsigned int pos = k;
        
        for (unsigned int i = 0; i < k; i++) {
            if (count > top_k_counts[i]) {
                pos = i;
                break;
            }
        }
        
        // Shift and insert
        if (pos < k) {
            for (unsigned int i = k - 1; i > pos; i--) {
                top_k_counts[i] = top_k_counts[i - 1];
                top_k_keys[i] = top_k_keys[i - 1];
            }
            top_k_counts[pos] = count;
            top_k_keys[pos] = key;
        }
    }
}

// ============================================================================
// COMBINED ENTROPY & HISTOGRAM COMPUTATION
// ============================================================================

extern "C" {

double compute_entropy_gpu(
    const unsigned char* d_data,
    unsigned int data_size
) {
    // Allocate histogram on GPU
    unsigned int* d_histogram;
    double* d_entropy;
    
    cudaMalloc(&d_histogram, HISTOGRAM_SIZE * sizeof(unsigned int));
    cudaMalloc(&d_entropy, sizeof(double));
    
    // Initialize histogram
    cudaMemset(d_histogram, 0, HISTOGRAM_SIZE * sizeof(unsigned int));
    
    // Launch histogram kernel
    unsigned int blocks = (data_size + BLOCK_SIZE - 1) / BLOCK_SIZE;
    histogram_kernel<<<blocks, BLOCK_SIZE>>>(d_data, data_size, d_histogram);
    
    // Launch entropy reduction kernel
    entropy_kernel<<<1, HISTOGRAM_SIZE>>>(d_histogram, data_size, d_entropy);
    
    // Copy result back
    double entropy_value;
    cudaMemcpy(&entropy_value, d_entropy, sizeof(double), cudaMemcpyDeviceToHost);
    
    // Cleanup
    cudaFree(d_histogram);
    cudaFree(d_entropy);
    
    return entropy_value;
}

void compute_pattern_frequencies_gpu(
    const unsigned char* d_data,
    unsigned int data_size,
    unsigned int* d_pattern_counts,
    unsigned int* d_pattern_keys,
    unsigned int max_patterns
) {
    unsigned int blocks = (data_size + BLOCK_SIZE - 1) / BLOCK_SIZE;
    
    // Initialize pattern tables
    cudaMemset(d_pattern_counts, 0, max_patterns * sizeof(unsigned int));
    cudaMemset(d_pattern_keys, 0, max_patterns * sizeof(unsigned int));
    
    // Launch pattern frequency kernel
    pattern_frequency_kernel<<<blocks, BLOCK_SIZE>>>(
        d_data,
        data_size,
        d_pattern_counts,
        d_pattern_keys,
        max_patterns,
        PATTERN_LENGTH
    );
}

void extract_top_k_patterns_gpu(
    const unsigned int* d_pattern_counts,
    const unsigned int* d_pattern_keys,
    unsigned int num_buckets,
    unsigned int* d_top_k_counts,
    unsigned int* d_top_k_keys,
    unsigned int k
) {
    unsigned int blocks = (num_buckets + BLOCK_SIZE - 1) / BLOCK_SIZE;
    
    // Initialize top-k arrays
    cudaMemset(d_top_k_counts, 0, k * sizeof(unsigned int));
    cudaMemset(d_top_k_keys, 0, k * sizeof(unsigned int));
    
    // Launch top-k extraction
    extract_top_k_patterns<<<blocks, BLOCK_SIZE>>>(
        d_pattern_counts,
        d_pattern_keys,
        num_buckets,
        d_top_k_counts,
        d_top_k_keys,
        k
    );
}

} // extern "C"
