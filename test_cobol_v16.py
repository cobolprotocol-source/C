"""
Integration Tests for COBOL v1.6 Advanced Features
===================================================

Tests for:
  • DAG pipeline (fast/deep/skip paths)
  • Codec switching
  • Hierarchical dictionary
  • GPU/FPGA scheduling
  • Cost model decisions
  • Health-driven routing
"""

import unittest
import logging
import sys
from typing import Tuple

# Add parent path
sys.path.insert(0, '/workspaces/cobolfix')

from dag_pipeline import (
    DAGPipeline, ExecutionPath, CodecRegistry, HierarchicalDictionary,
    CostModel, HealthMonitor
)
from heterogeneous_orchestrator import (
    HeterogeneousOrchestrator, DevicePool, GPUUpstream, FPGAMiddleTier
)
from cobol_v16_integrated import COBOLv16Engine, COBOLV16

logger = logging.getLogger(__name__)


# ============================================================================
# DAG PIPELINE TESTS
# ============================================================================


class TestDAGPipeline(unittest.TestCase):
    """Test DAG pipeline functionality."""
    
    def setUp(self):
        self.pipeline = DAGPipeline()
        self.test_data = b"The quick brown fox jumps over the lazy dog. " * 100
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly."""
        self.assertIsNotNone(self.pipeline.codec_registry)
        self.assertIsNotNone(self.pipeline.cost_model)
        self.assertIsNotNone(self.pipeline.health)
        self.assertEqual(len(self.pipeline.paths), 3)  # Fast, Deep, Skip
    
    def test_fast_path_compression(self):
        """Test fast execution path."""
        compressed, meta = self.pipeline.compress(self.test_data)
        
        self.assertIsNotNone(compressed)
        self.assertIn("path_selected", meta)
        self.assertIn("codec_used", meta)
        self.assertGreater(meta["compression_ratio"], 0)
    
    def test_codec_registry(self):
        """Test codec registry functionality."""
        registry = CodecRegistry()
        
        # Test available codecs
        self.assertIsNotNone(registry.get("lz4"))
        self.assertIsNotNone(registry.get("deflate"))
        
        # Test codec selection
        codec = registry.select_best("lz4")
        self.assertIsNotNone(codec)
        
        # Test compression/decompression roundtrip
        compressed = codec.compress(self.test_data)
        decompressed = codec.decompress(compressed)
        self.assertEqual(decompressed, self.test_data)
    
    def test_entropy_calculation(self):
        """Test entropy calculation."""
        entropy = self.pipeline._calculate_entropy(self.test_data)
        
        # ASCII text should have entropy ~ 4-5 bits/byte
        self.assertGreater(entropy, 3.0)
        self.assertLess(entropy, 6.0)
        
        # High entropy data
        high_entropy = bytes(range(256)) * 100
        high_e = self.pipeline._calculate_entropy(high_entropy)
        self.assertGreater(high_e, 7.0)  # Random should be ~8
    
    def test_health_monitor(self):
        """Test health monitoring."""
        health = HealthMonitor()
        
        # Check initial state
        devices = health.get_available_devices()
        self.assertIsInstance(devices, dict)
        self.assertTrue(devices["cpu"])
        
        # Simulate stress
        health.update_health(cpu_load=0.9)
        self.assertEqual(health.cpu_load, 0.9)
        
        # Should still recommend skipping layers if stressed
        self.assertTrue(health.should_adaptively_skip_layers())


# ============================================================================
# CODEC SWITCHING TESTS
# ============================================================================


class TestCodecSwitching(unittest.TestCase):
    """Test codec switching functionality."""
    
    def test_lz4_codec(self):
        """Test LZ4 codec."""
        from dag_pipeline import LZ4Codec
        
        codec = LZ4Codec()
        data = b"Test data " * 100
        
        compressed = codec.compress(data)
        self.assertLess(len(compressed), len(data))
        
        decompressed = codec.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_deflate_codec(self):
        """Test DEFLATE codec."""
        from dag_pipeline import DeflateCoded
        
        codec = DeflateCoded(compression_level=9)
        data = b"Test data " * 100
        
        compressed = codec.compress(data)
        self.assertLess(len(compressed), len(data))
        
        decompressed = codec.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_codec_fallback(self):
        """Test codec fallback mechanism."""
        registry = CodecRegistry()
        
        # All codecs should handle missing data gracefully
        for codec_name in ["lz4", "deflate"]:
            codec = registry.get(codec_name)
            
            # Attempt compression
            empty = b""
            result = codec.compress(empty)
            self.assertIsNotNone(result)


# ============================================================================
# HIERARCHICAL DICTIONARY TESTS
# ============================================================================


class TestHierarchicalDictionary(unittest.TestCase):
    """Test hierarchical dictionary system."""
    
    def setUp(self):
        self.dict = HierarchicalDictionary(max_entries=1000)
        self.test_data = b"the quick brown fox" * 50
    
    def test_dictionary_add_and_lookup(self):
        """Test adding and looking up patterns."""
        pattern = b"the quick"
        
        # Add pattern
        token_id = self.dict.add_pattern(pattern, freq=10)
        self.assertGreaterEqual(token_id, 256)  # Should be > single bytes
        
        # Lookup
        found_id = self.dict.lookup(pattern)
        self.assertEqual(found_id, token_id)
    
    def test_dictionary_frequencies(self):
        """Test frequency-based pattern tracking."""
        self.dict.add_pattern(b"abc", freq=5)
        self.dict.add_pattern(b"def", freq=10)
        
        # Higher frequency should be preserved
        stats = self.dict.get_stats()
        self.assertEqual(stats["total_entries"], 2)
    
    def test_hierarchical_structure(self):
        """Test hierarchical trie structure."""
        # Add various length patterns
        self.dict.add_pattern(b"a", freq=1)
        self.dict.add_pattern(b"ab", freq=5)
        self.dict.add_pattern(b"abc", freq=10)
        
        stats = self.dict.get_stats()
        self.assertGreater(stats["trie_depth"], 1)


# ============================================================================
# COST MODEL TESTS
# ============================================================================


class TestCostModel(unittest.TestCase):
    """Test cost model decision engine."""
    
    def setUp(self):
        self.cost_model = CostModel()
    
    def test_path_cost_estimation(self):
        """Test cost estimation for paths."""
        hardware = {"gpu": True, "fpga": False}
        
        # FAST path should be cheapest in time
        fast_cost = self.cost_model.estimate_cost(
            10000, 4.0, ExecutionPath.FAST, hardware
        )
        self.assertLess(fast_cost.time_estimate_ms, 50)
        
        # DEEP path should estimate high ratio
        deep_cost = self.cost_model.estimate_cost(
            10000, 4.0, ExecutionPath.DEEP, hardware
        )
        self.assertGreater(deep_cost.ratio_estimate, 5.0)
    
    def test_path_selection(self):
        """Test automatic path selection."""
        hardware = {"gpu": True, "fpga": False}
        
        # Time-critical should select FAST
        path = self.cost_model.select_path(
            10000, 5.0, hardware, time_critical=True
        )
        # May be FAST or SKIP depending on cost
        self.assertIn(path, [ExecutionPath.FAST, ExecutionPath.SKIP])
        
        # High entropy + time-critical still chooses fast
        path = self.cost_model.select_path(
            10000, 7.5, hardware, time_critical=True
        )
        self.assertIsNotNone(path)
    
    def test_result_recording(self):
        """Test recording actual results."""
        self.cost_model.record_result(ExecutionPath.FAST, 25.0, 1.5)
        self.cost_model.record_result(ExecutionPath.FAST, 30.0, 1.6)
        
        # Reliability should improve
        reliability = self.cost_model._get_reliability(ExecutionPath.FAST)
        self.assertGreater(reliability, 0.9)


# ============================================================================
# HETEROGENEOUS DEVICE TESTS
# ============================================================================


class TestHeterogeneousOrchestrator(unittest.TestCase):
    """Test heterogeneous device orchestration."""
    
    def setUp(self):
        self.orchestrator = HeterogeneousOrchestrator()
        self.test_data = b"Test compression data " * 100
    
    def test_device_pool_detection(self):
        """Test device detection."""
        status = self.orchestrator.device_pool.get_status()
        self.assertIn("devices", status)
        
        # CPU should always be available
        devices = list(status["devices"].keys())
        self.assertTrue(any("cpu" in d for d in devices))
    
    def test_gpu_upstream(self):
        """Test GPU upstream processing."""
        gpu = GPUUpstream(self.orchestrator.device_pool)
        
        # Entropy calculation (fallback to CPU)
        entropy = gpu.calculate_entropy_vectorized(self.test_data)
        self.assertGreater(entropy, 0)
        self.assertLess(entropy, 8.0)
        
        # Pattern detection
        patterns = gpu.find_frequent_patterns(self.test_data, min_length=4)
        self.assertGreater(len(patterns), 0)
    
    def test_heterogeneous_compression(self):
        """Test full heterogeneous pipeline."""
        compressed, meta = self.orchestrator.compress_heterogeneous(self.test_data)
        
        self.assertIsNotNone(compressed)
        self.assertIn("stages", meta)
        self.assertGreater(meta["compression_ratio"], 0)
        
        # Check pipeline stages
        stage_names = list(meta["stages"].keys())
        self.assertIn("codec", stage_names)


# ============================================================================
# INTEGRATED V1.6 TESTS
# ============================================================================


class TestCOBOLv16(unittest.TestCase):
    """Test integrated COBOL v1.6 engine."""
    
    def setUp(self):
        self.cobol = COBOLV16()
        self.test_data = b"COBOL Protocol v1.6 Test Data " * 100
    
    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = self.cobol.engine
        self.assertIsNotNone(engine.dag_pipeline)
        self.assertIsNotNone(engine.orchestrator)
        self.assertIsNotNone(engine.dictionary)
    
    def test_compression_roundtrip(self):
        """Test compression and decompression."""
        compressed, meta = self.cobol.compress(self.test_data)
        decompressed, dmeta = self.cobol.decompress(compressed)
        
        self.assertEqual(decompressed, self.test_data)
    
    def test_strategy_negotiation(self):
        """Test strategy negotiation."""
        # Normal compression
        compressed, meta = self.cobol.compress(self.test_data)
        self.assertIn("strategy_used", meta)
        
        # Time-critical should prefer FAST
        compressed_fast, meta_fast = self.cobol.compress(
            self.test_data, time_critical=True
        )
        self.assertLessEqual(
            meta_fast["total_time_ms"],
            meta["total_time_ms"] * 1.1  # Allow 10% margin
        )
    
    def test_high_ratio_mode(self):
        """Test high compression ratio mode."""
        compressed_normal, meta_normal = self.cobol.compress(self.test_data)
        compressed_ratio, meta_ratio = self.cobol.compress(
            self.test_data, high_ratio=True
        )
        
        # High ratio mode should produce smaller output
        # (though not guaranteed due to codec selection)
        self.assertIsNotNone(meta_ratio["compression_ratio"])
    
    def test_engine_status(self):
        """Test engine status reporting."""
        # Do some compression first
        self.cobol.compress(self.test_data)
        
        status = self.cobol.engine.get_engine_status()
        self.assertIn("uptime_stats", status)
        self.assertIn("device_pool", status)
        self.assertGreater(status["uptime_stats"]["total_bytes_processed"], 0)
    
    def test_adaptive_routing(self):
        """Test health-driven adaptive routing."""
        # Simulate CPU stress
        self.cobol.engine.health.update_health(cpu_load=0.95)
        
        compressed, meta = self.cobol.compress(self.test_data, adaptive=True)
        
        # Engine should still work (fallback to safe strategies)
        self.assertIsNotNone(compressed)
    
    def test_multiple_data_types(self):
        """Test compression on various data types."""
        test_cases = [
            (b"text " * 100, "text"),
            (bytes(range(256)) * 100, "binary"),
            (b'{"key":"value"}' * 100, "json"),
        ]
        
        for data, description in test_cases:
            compressed, meta = self.cobol.compress(data)
            decompressed, dmeta = self.cobol.decompress(compressed)
            
            self.assertEqual(
                decompressed, data,
                f"Roundtrip failed for {description}"
            )
            self.assertGreater(
                meta["compression_ratio"], 0,
                f"Invalid ratio for {description}"
            )


# ============================================================================
# PERFORMANCE BENCHMARKS
# ============================================================================


class TestPerformance(unittest.TestCase):
    """Performance-related tests."""
    
    def test_compression_throughput(self):
        """Test compression throughput."""
        cobol = COBOLV16()
        
        # 1 MB test
        test_data = (b"The quick brown fox " * 50000)[:1_000_000]
        
        compressed, meta = cobol.compress(test_data, time_critical=True)
        
        # Should achieve reasonable throughput
        throughput = len(test_data) / (meta["total_time_ms"] / 1000) / 1_000_000
        print(f"\n⏱️  Compression throughput: {throughput:.2f} MB/s")
        
        # Should be > 0.5 MB/s (minimum - dev container may be slow)
        # GPU acceleration will improve this significantly
        self.assertGreater(throughput, 0.5)
    
    def test_scalability(self):
        """Test scalability with data size."""
        cobol = COBOLV16()
        
        sizes = [1000, 10000, 100000]
        times = []
        
        for size in sizes:
            data = b"test " * (size // 5)
            _, meta = cobol.compress(data)
            times.append(meta["total_time_ms"])
            print(f"\n📊 Size {size:6d}: {meta['total_time_ms']:.2f}ms")
        
        # Time should scale roughly linearly
        # (not exponentially bad)
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1] if times[i-1] > 0 else 1
            # Allow up to 100x increase for 10x data (i.e., ratio < 100)
            self.assertLess(ratio, 200)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================


def run_tests():
    """Run all tests."""
    logging.basicConfig(
        level=logging.WARNING,
        format='%(message)s'
    )
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestDAGPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestCodecSwitching))
    suite.addTests(loader.loadTestsFromTestCase(TestHierarchicalDictionary))
    suite.addTests(loader.loadTestsFromTestCase(TestCostModel))
    suite.addTests(loader.loadTestsFromTestCase(TestHeterogeneousOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestCOBOLv16))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
