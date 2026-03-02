"""
Test Suite for GPU Accelerated Components (v1.6+)
===================================================

Tests for:
  1. GPU entropy computation (vs CPU baseline)
  2. Pattern extraction on GPU
  3. Device detection & fallback
  4. Performance benchmarks
  5. Integration with heterogeneous orchestrator
"""

import unittest
import time
import numpy as np
from typing import Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing GPU modules
try:
    from gpu_accelerator import GPUAccelerator, GPUMetrics, benchmark_entropy_computation
    GPU_ACCEL_AVAILABLE = True
except ImportError:
    GPU_ACCEL_AVAILABLE = False
    logger.warning("gpu_accelerator not available, GPU tests may be skipped")

try:
    from heterogeneous_orchestrator import DevicePool, GPUUpstream
    HETERO_AVAILABLE = True
except ImportError:
    HETERO_AVAILABLE = False
    logger.warning("heterogeneous_orchestrator not available")


# ============================================================================
# TEST: GPU ACCELERATOR
# ============================================================================

@unittest.skipIf(not GPU_ACCEL_AVAILABLE, "GPU accelerator not available")
class TestGPUAccelerator(unittest.TestCase):
    """Test GPU accelerator module."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize GPU accelerator."""
        cls.accelerator = GPUAccelerator()
    
    def test_entropy_computation_basic(self):
        """Test entropy computation on simple data."""
        # Test data with known entropy
        data = b"AAAABBBBCCCCDDDD"  # 4 bytes, 4 each
        
        metrics = self.accelerator.compute_entropy_gpu(data)
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.data_size, len(data))
        self.assertGreater(metrics.entropy, 0)
        self.assertLess(metrics.entropy, 8)  # Max 8 bits
        
        logger.info(f"Basic entropy test: entropy={metrics.entropy:.4f}, "
                   f"device={metrics.device_used}, time={metrics.computation_time_ms:.2f}ms")
    
    def test_entropy_random_data(self):
        """Test entropy on random data (max entropy)."""
        random_data = np.random.bytes(10000)
        
        metrics = self.accelerator.compute_entropy_gpu(random_data)
        
        # Random data should have high entropy (close to 8)
        self.assertGreater(metrics.entropy, 7.0)
        self.assertLess(metrics.entropy, 8.0)
        
        logger.info(f"Random data entropy: {metrics.entropy:.4f}")
    
    def test_entropy_repetitive_data(self):
        """Test entropy on repetitive data (low entropy)."""
        repetitive_data = b"ABCDEFGH" * 1000
        
        metrics = self.accelerator.compute_entropy_gpu(repetitive_data)
        
        # Repetitive data should have lower entropy
        self.assertGreater(metrics.entropy, 0)
        self.assertLess(metrics.entropy, 5.0)
        
        logger.info(f"Repetitive data entropy: {metrics.entropy:.4f}")
    
    def test_entropy_incompressible(self):
        """Test entropy on incompressible data."""
        # Mix of two values (minimal pattern)
        incompressible = b'\x00' * 5000 + b'\xFF' * 5000
        
        metrics = self.accelerator.compute_entropy_gpu(incompressible)
        
        # Should have entropy of 1.0 (binary)
        self.assertAlmostEqual(metrics.entropy, 1.0, places=1)
        
        logger.info(f"Incompressible data entropy: {metrics.entropy:.4f}")
    
    def test_pattern_extraction(self):
        """Test pattern extraction from data."""
        # Create data with obvious patterns
        pattern_data = (b"ABCD" * 100) + (b"XYZ" * 50)
        
        patterns, freqs = self.accelerator.extract_top_patterns(
            pattern_data,
            pattern_length=4,
            top_k=10
        )
        
        self.assertGreater(len(patterns), 0)
        self.assertEqual(len(patterns), len(freqs))
        
        # First pattern should be most frequent
        self.assertGreaterEqual(freqs[0], freqs[-1])
        
        logger.info(f"Extracted {len(patterns)} patterns")
        logger.info(f"Top pattern: {patterns[0]}, frequency: {freqs[0]}")
    
    def test_throughput_metric(self):
        """Test throughput calculation in metrics."""
        large_data = np.random.bytes(1_000_000)
        
        metrics = self.accelerator.compute_entropy_gpu(large_data)
        
        self.assertGreater(metrics.throughput_mbps, 0)
        logger.info(f"Throughput: {metrics.throughput_mbps:.2f} MB/s")
    
    def test_device_info(self):
        """Test device information retrieval."""
        info = self.accelerator.get_device_info()
        
        self.assertIsNotNone(info)
        self.assertIn('cuda_available', info)
        self.assertIn('torch_available', info)
        
        logger.info(f"Device info: {info}")


# ============================================================================
# TEST: GPU UPSTREAM INTEGRATION
# ============================================================================

@unittest.skipIf(not (GPU_ACCEL_AVAILABLE and HETERO_AVAILABLE),
                 "GPU upstream not available")
class TestGPUUpstream(unittest.TestCase):
    """Test GPU upstream in heterogeneous orchestrator."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize GPU upstream."""
        cls.device_pool = DevicePool()
        cls.gpu_upstream = GPUUpstream(cls.device_pool)
    
    def test_upstream_entropy_calculation(self):
        """Test GPU upstream entropy."""
        test_data = b"The quick brown fox jumps over the lazy dog" * 100
        
        entropy = self.gpu_upstream.calculate_entropy_vectorized(test_data)
        
        self.assertGreater(entropy, 0)
        self.assertLess(entropy, 8)
        
        logger.info(f"GPU upstream entropy: {entropy:.4f}")
    
    def test_upstream_pattern_finding(self):
        """Test GPU upstream pattern finding."""
        test_data = (b"Hello World! " * 50) + (b"Test Data " * 30)
        
        patterns = self.gpu_upstream.find_frequent_patterns(
            test_data,
            min_length=2,
            top_k=20
        )
        
        self.assertGreater(len(patterns), 0)
        self.assertLessEqual(len(patterns), 20)
        
        # Verify format (bytes, int)
        for pattern, freq in patterns:
            self.assertIsInstance(pattern, bytes)
            self.assertIsInstance(freq, int)
            self.assertGreater(freq, 0)
        
        logger.info(f"Found {len(patterns)} patterns")
    
    def test_gpu_metrics_retrieval(self):
        """Test GPU metrics retrieval."""
        metrics = self.gpu_upstream.get_gpu_metrics()
        
        if metrics:
            self.assertIsInstance(metrics, dict)
            logger.info(f"GPU metrics available: {list(metrics.keys())}")
        else:
            logger.info("No GPU metrics available (expected if no GPU)")
    
    def test_fallback_mechanism(self):
        """Test fallback when GPU unavailable."""
        # Create upstream that forces CPU
        gpu_upstream = GPUUpstream(self.device_pool)
        gpu_upstream.gpu_accel = None  # Disable GPU
        
        test_data = b"Test data for CPU fallback"
        
        # Should still work via CPU
        entropy = gpu_upstream.calculate_entropy_vectorized(test_data)
        self.assertGreater(entropy, 0)
        
        patterns = gpu_upstream.find_frequent_patterns(test_data)
        self.assertIsInstance(patterns, list)
        
        logger.info("Fallback mechanism working correctly")


# ============================================================================
# TEST: PERFORMANCE & BENCHMARKING
# ============================================================================

@unittest.skipIf(not GPU_ACCEL_AVAILABLE, "GPU accelerator not available")
class TestGPUPerformance(unittest.TestCase):
    """Performance benchmarks for GPU acceleration."""
    
    def test_cpu_vs_gpu_small_data(self):
        """Compare CPU vs GPU on small data (10KB)."""
        accelerator = GPUAccelerator()
        test_data = np.random.bytes(10_000)
        
        # CPU computation
        cpu_accel = GPUAccelerator(use_cuda=False, use_torch=False)
        cpu_metrics = cpu_accel.compute_entropy_gpu(test_data)
        
        # GPU computation
        gpu_metrics = accelerator.compute_entropy_gpu(test_data)
        
        logger.info(f"\nCPU vs GPU (10KB):")
        logger.info(f"  CPU: {cpu_metrics.computation_time_ms:.2f}ms")
        logger.info(f"  GPU: {gpu_metrics.computation_time_ms:.2f}ms")
        logger.info(f"  Entropy match: {abs(cpu_metrics.entropy - gpu_metrics.entropy) < 0.01}")
    
    def test_throughput_large_data(self):
        """Measure throughput on large data (10MB)."""
        accelerator = GPUAccelerator()
        large_data = np.random.bytes(10_000_000)
        
        start = time.time()
        metrics = accelerator.compute_entropy_gpu(large_data)
        elapsed = time.time() - start
        
        logger.info(f"\nThroughput (10MB):")
        logger.info(f"  Time: {elapsed*1000:.2f}ms")
        logger.info(f"  Throughput: {metrics.throughput_mbps:.2f} MB/s")
    
    def test_pattern_extraction_speed(self):
        """Measure pattern extraction speed."""
        accelerator = GPUAccelerator()
        test_data = np.random.bytes(1_000_000)
        
        start = time.time()
        patterns, freqs = accelerator.extract_top_patterns(
            test_data,
            pattern_length=4,
            top_k=100
        )
        elapsed = time.time() - start
        
        throughput = (len(test_data) / (1024*1024)) / elapsed
        logger.info(f"\nPattern Extraction (1MB):")
        logger.info(f"  Time: {elapsed*1000:.2f}ms")
        logger.info(f"  Patterns found: {len(patterns)}")
        logger.info(f"  Throughput: {throughput:.2f} MB/s")
    
    def test_benchmark_suite(self):
        """Run full benchmark suite."""
        logger.info("\n" + "="*70)
        logger.info("Running Benchmark Suite (1MB data)")
        logger.info("="*70)
        
        results = benchmark_entropy_computation(1_000_000)
        
        for data_type, metrics in results.items():
            logger.info(f"\n{data_type}:")
            logger.info(f"  Entropy: {metrics['entropy']:.4f}")
            logger.info(f"  Device: {metrics['device']}")
            logger.info(f"  Time: {metrics['time_ms']:.2f}ms")
            logger.info(f"  Throughput: {metrics['throughput_mbps']:.2f} MB/s")


# ============================================================================
# TEST: DEVICE POOL INTEGRATION
# ============================================================================

@unittest.skipIf(not HETERO_AVAILABLE, "heterogeneous_orchestrator not available")
class TestDevicePoolGPU(unittest.TestCase):
    """Test device pool with GPU support."""
    
    def test_device_detection(self):
        """Test that device pool detects GPUs."""
        pool = DevicePool()
        status = pool.get_status()
        
        self.assertIn("devices", status)
        self.assertIsInstance(status["devices"], dict)
        
        # Log detected devices
        for device_id, info in status["devices"].items():
            logger.info(f"Detected device: {device_id} (type={info['type']}, "
                       f"available={info['available']})")
    
    def test_device_metrics_update(self):
        """Test updating device metrics."""
        pool = DevicePool()
        
        # Get a device
        devices = list(pool.devices.keys())
        if devices:
            device_id = devices[0]
            
            # Update metrics
            pool.update_metrics(device_id, utilization=50.0, memory_mb=2048)
            
            # Check update
            status = pool.get_status()
            device_info = status["devices"][device_id]
            self.assertAlmostEqual(device_info["utilization"], 50.0)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_tests():
    """Run all GPU acceleration tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    if GPU_ACCEL_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestGPUAccelerator))
        suite.addTests(loader.loadTestsFromTestCase(TestGPUPerformance))
    
    if GPU_ACCEL_AVAILABLE and HETERO_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestGPUUpstream))
    
    if HETERO_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestDevicePoolGPU))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("GPU Acceleration Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All GPU acceleration tests PASSED")
    else:
        print(f"\n❌ Some tests FAILED")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
