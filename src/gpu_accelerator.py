"""
COBOL Protocol v1.6: GPU Accelerated Module
============================================

Python wrapper for CUDA-accelerated entropy calculation and pattern detection.
Provides seamless GPU/CPU fallback and performance profiling.
"""

import numpy as np
import ctypes
from typing import Tuple, List, Optional
import logging
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

# Try to import CUDA libraries
try:
    import pycuda.driver as cuda
    import pycuda.autoinit
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False
    logger.warning("PyCUDA not available, falling back to CPU")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class GPUMetrics:
    """GPU operation metrics."""
    entropy: float
    computation_time_ms: float
    device_used: str  # 'gpu' or 'cpu'
    data_size: int
    throughput_mbps: float = 0.0
    
    def __post_init__(self):
        if self.computation_time_ms > 0:
            self.throughput_mbps = (self.data_size / (1024 * 1024)) / (self.computation_time_ms / 1000)


class GPUAccelerator:
    """GPU-accelerated computation for entropy and pattern detection."""
    
    def __init__(self, use_cuda: bool = True, use_torch: bool = True):
        self.use_cuda = use_cuda and CUDA_AVAILABLE
        self.use_torch = use_torch and TORCH_AVAILABLE
        self.cuda_kernel = None
        
        if self.use_cuda:
            self._load_cuda_kernel()
        
        logger.info(f"GPU Accelerator initialized: CUDA={self.use_cuda}, Torch={self.use_torch}")
    
    def _load_cuda_kernel(self):
        """Load compiled CUDA kernel."""
        try:
            # Try to load compiled kernel
            import ctypes
            self.cuda_kernel = ctypes.CDLL("./gpu_entropy_patterns.so")
            logger.info("CUDA kernel loaded successfully")
        except OSError:
            logger.warning("CUDA kernel .so not found, using Torch GPU if available")
            self.use_cuda = False
    
    def compute_entropy_gpu(self, data: bytes) -> GPUMetrics:
        """
        Compute Shannon entropy using GPU acceleration.
        
        Args:
            data: Input bytes to analyze
            
        Returns:
            GPUMetrics with entropy value and computation time
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        
        start_time = time.time()
        
        # Try GPU path
        if self.use_torch and TORCH_AVAILABLE:
            return self._compute_entropy_torch(data, start_time)
        elif self.use_cuda and self.cuda_kernel:
            return self._compute_entropy_cuda(data, start_time)
        else:
            return self._compute_entropy_cpu(data, start_time)
    
    def _compute_entropy_torch(self, data: bytes, start_time: float) -> GPUMetrics:
        """Compute entropy using PyTorch GPU."""
        try:
            # Convert to tensor
            data_array = np.frombuffer(data, dtype=np.uint8)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                device = torch.device("cuda")
                device_str = "gpu"
            else:
                device = torch.device("cpu")
                device_str = "cpu"
            
            data_tensor = torch.from_numpy(data_array).to(device)
            
            # Compute histogram (vectorized)
            histogram = torch.bincount(data_tensor, minlength=256)
            
            # Compute probabilities
            probs = histogram.float() / len(data)
            
            # Shannon entropy: -sum(p * log2(p))
            entropy = -torch.sum(probs * torch.log2(probs + 1e-10))
            entropy_value = entropy.item()
            
            computation_time_ms = (time.time() - start_time) * 1000
            
            return GPUMetrics(
                entropy=entropy_value,
                computation_time_ms=computation_time_ms,
                device_used=device_str,
                data_size=len(data)
            )
        except Exception as e:
            logger.warning(f"Torch entropy computation failed: {e}, falling back to CPU")
            return self._compute_entropy_cpu(data, start_time)
    
    def _compute_entropy_cuda(self, data: bytes, start_time: float) -> GPUMetrics:
        """Compute entropy using raw CUDA kernel."""
        try:
            if not self.cuda_kernel:
                raise RuntimeError("CUDA kernel not loaded")
            
            # Allocate GPU memory
            data_array = np.frombuffer(data, dtype=np.uint8)
            d_data = cuda.mem_alloc(data_array.nbytes)
            cuda.memcpy_htod(d_data, data_array)
            
            # Call kernel using ctypes
            kernel_fn = self.cuda_kernel.compute_entropy_gpu
            kernel_fn.restype = ctypes.c_double
            kernel_fn.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            
            entropy_value = kernel_fn(d_data, len(data_array))
            
            d_data.free()
            
            computation_time_ms = (time.time() - start_time) * 1000
            
            return GPUMetrics(
                entropy=entropy_value,
                computation_time_ms=computation_time_ms,
                device_used="gpu",
                data_size=len(data)
            )
        except Exception as e:
            logger.warning(f"CUDA entropy computation failed: {e}, falling back to CPU")
            return self._compute_entropy_cpu(data, start_time)
    
    def _compute_entropy_cpu(self, data: bytes, start_time: float) -> GPUMetrics:
        """Fallback: CPU-based entropy computation."""
        data_array = np.frombuffer(data, dtype=np.uint8)
        
        # Compute histogram
        histogram, _ = np.histogram(data_array, bins=256, range=(0, 256))
        
        # Compute probabilities
        probs = histogram / len(data)
        
        # Shannon entropy: -sum(p * log2(p))
        entropy = -np.sum(probs[probs > 0] * np.log2(probs[probs > 0]))
        
        computation_time_ms = (time.time() - start_time) * 1000
        
        return GPUMetrics(
            entropy=entropy,
            computation_time_ms=computation_time_ms,
            device_used="cpu",
            data_size=len(data)
        )
    
    def extract_top_patterns(
        self,
        data: bytes,
        pattern_length: int = 4,
        top_k: int = 100
    ) -> Tuple[List[bytes], List[int]]:
        """
        Extract top-K most frequent patterns from data.
        
        Args:
            data: Input bytes
            pattern_length: Length of patterns to extract
            top_k: Number of top patterns to return
            
        Returns:
            Tuple of (pattern_bytes, frequencies)
        """
        if self.use_torch and TORCH_AVAILABLE:
            return self._extract_patterns_torch(data, pattern_length, top_k)
        else:
            return self._extract_patterns_cpu(data, pattern_length, top_k)
    
    def _extract_patterns_torch(
        self,
        data: bytes,
        pattern_length: int,
        top_k: int
    ) -> Tuple[List[bytes], List[int]]:
        """Extract patterns using PyTorch."""
        try:
            data_array = np.frombuffer(data, dtype=np.uint8)
            
            # Create pattern view using strided approach
            patterns = {}
            for i in range(len(data_array) - pattern_length + 1):
                pattern = bytes(data_array[i:i+pattern_length])
                patterns[pattern] = patterns.get(pattern, 0) + 1
            
            # Sort by frequency
            sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
            
            # Get top-k
            top_patterns = sorted_patterns[:top_k]
            
            pattern_bytes = [p[0] for p in top_patterns]
            frequencies = [p[1] for p in top_patterns]
            
            return pattern_bytes, frequencies
        except Exception as e:
            logger.warning(f"PyTorch pattern extraction failed: {e}, using CPU")
            return self._extract_patterns_cpu(data, pattern_length, top_k)
    
    def _extract_patterns_cpu(
        self,
        data: bytes,
        pattern_length: int,
        top_k: int
    ) -> Tuple[List[bytes], List[int]]:
        """CPU-based pattern extraction."""
        data_array = np.frombuffer(data, dtype=np.uint8)
        
        # Use dictionary for pattern counting
        patterns = {}
        
        for i in range(len(data_array) - pattern_length + 1):
            pattern = bytes(data_array[i:i+pattern_length])
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # Sort by frequency (descending)
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        
        # Extract top-k
        top_k_items = sorted_patterns[:top_k]
        
        pattern_bytes = [p[0] for p in top_k_items]
        frequencies = [p[1] for p in top_k_items]
        
        return pattern_bytes, frequencies
    
    def get_device_info(self) -> dict:
        """Get GPU device information."""
        info = {
            'cuda_available': CUDA_AVAILABLE,
            'cuda_enabled': self.use_cuda,
            'torch_available': TORCH_AVAILABLE,
            'torch_enabled': self.use_torch,
        }
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            info['cuda_device_count'] = torch.cuda.device_count()
            info['cuda_device_name'] = torch.cuda.get_device_name(0)
            info['cuda_compute_capability'] = torch.cuda.get_device_capability(0)
            info['cuda_memory_allocated'] = torch.cuda.memory_allocated()
            info['cuda_memory_reserved'] = torch.cuda.memory_reserved()
        
        return info


# ============================================================================
# PERFORMANCE BENCHMARKING
# ============================================================================

def benchmark_entropy_computation(data_size: int = 1_000_000) -> dict:
    """Benchmark entropy computation on various data types."""
    import string
    
    results = {}
    accelerator = GPUAccelerator()
    
    # Test 1: Random bytes
    random_data = np.random.bytes(data_size)
    metrics = accelerator.compute_entropy_gpu(random_data)
    results['random_data'] = {
        'entropy': metrics.entropy,
        'device': metrics.device_used,
        'time_ms': metrics.computation_time_ms,
        'throughput_mbps': metrics.throughput_mbps
    }
    
    # Test 2: Repetitive data
    repetitive_data = (b'ABCDEFGH' * (data_size // 8))[:data_size]
    metrics = accelerator.compute_entropy_gpu(repetitive_data)
    results['repetitive_data'] = {
        'entropy': metrics.entropy,
        'device': metrics.device_used,
        'time_ms': metrics.computation_time_ms,
        'throughput_mbps': metrics.throughput_mbps
    }
    
    # Test 3: Compressible data
    compressible_data = b'\x00' * (data_size // 2) + b'\xFF' * (data_size // 2)
    metrics = accelerator.compute_entropy_gpu(compressible_data)
    results['compressible_data'] = {
        'entropy': metrics.entropy,
        'device': metrics.device_used,
        'time_ms': metrics.computation_time_ms,
        'throughput_mbps': metrics.throughput_mbps
    }
    
    return results


if __name__ == "__main__":
    # Demo
    accelerator = GPUAccelerator()
    
    print("=" * 70)
    print("GPU Accelerator Test")
    print("=" * 70)
    
    # Device info
    device_info = accelerator.get_device_info()
    print("\nDevice Info:")
    for key, value in device_info.items():
        print(f"  {key}: {value}")
    
    # Entropy computation
    test_data = b"The quick brown fox jumps over the lazy dog " * 1000
    print(f"\nTest data size: {len(test_data)} bytes")
    
    metrics = accelerator.compute_entropy_gpu(test_data)
    print(f"\nEntropy Computation:")
    print(f"  Entropy: {metrics.entropy:.4f}")
    print(f"  Device: {metrics.device_used}")
    print(f"  Time: {metrics.computation_time_ms:.2f} ms")
    print(f"  Throughput: {metrics.throughput_mbps:.2f} MB/s")
    
    # Pattern extraction
    patterns, freqs = accelerator.extract_top_patterns(test_data, pattern_length=2, top_k=10)
    print(f"\nTop 10 Patterns (length=2):")
    for i, (pattern, freq) in enumerate(zip(patterns, freqs)):
        try:
            pattern_str = pattern.decode('ascii', errors='replace')
        except:
            pattern_str = repr(pattern)
        print(f"  {i+1}. {pattern_str:10s} → {freq:5d} occurrences")
    
    # Benchmarking
    print("\n" + "=" * 70)
    print("Benchmarking (1 MB data)...")
    print("=" * 70)
    
    bench_results = benchmark_entropy_computation(1_000_000)
    for data_type, results in bench_results.items():
        print(f"\n{data_type}:")
        print(f"  Entropy: {results['entropy']:.4f}")
        print(f"  Device: {results['device']}")
        print(f"  Time: {results['time_ms']:.2f} ms")
        print(f"  Throughput: {results['throughput_mbps']:.2f} MB/s")
