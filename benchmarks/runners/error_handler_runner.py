"""
Error Handling and Edge Case Runner for COBOL Benchmarks

Phase 4 tests robustness:
1. Corrupted/truncated data handling
2. Invalid metadata handling
3. Empty data edge cases
4. Maximum size limits
5. Graceful error recovery
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .base_runner import BaseRunner, BenchmarkResult

logger = logging.getLogger(__name__)


class ErrorHandlingRunner(BaseRunner):
    """Test compression engine error handling and robustness.
    
    Tests:
    - Truncated/corrupted compressed data
    - Empty input handling
    - Very small data (<1KB)
    - Maximum size limits
    - Invalid parameters
    - Graceful failure recovery
    """
    
    def __init__(self, output_dir: Path, compression_engine=None):
        """Initialize error handling tests.
        
        Args:
            output_dir: Directory for saving results
            compression_engine: COBOL compression provider instance
        """
        super().__init__("error_handling", output_dir)
        self.compression_engine = compression_engine
        self.test_results: Dict[str, bool] = {}
    
    def setup(self) -> bool:
        """Set up error handling tests.
        
        Returns:
            True if compression engine available
        """
        try:
            if self.compression_engine is None:
                from src.layers.pipelines.orchestration import AdaptiveCompressionPipeline
                self.compression_engine = AdaptiveCompressionPipeline()
                self.logger.info("Loaded compression engine for error handling testing")
            
            return self.compression_engine is not None
        except Exception as e:
            self.logger.error(f"Failed to set up error handling tests: {e}")
            return False
    
    def test_empty_data(self) -> tuple[bool, str]:
        """Test compression of empty data.
        
        Returns:
            (success, message)
        """
        try:
            result = self.compression_engine.compress(b"")
            if result is not None:
                self.logger.debug("Empty data compression handled gracefully")
                return True, "Empty data handled"
            else:
                return False, "Returned None for empty data"
        except Exception as e:
            self.logger.debug(f"Empty data raised exception (acceptable): {e}")
            return True, f"Exception raised: {type(e).__name__}"
    
    def test_small_data(self) -> tuple[bool, str]:
        """Test compression of very small data (<1KB).
        
        Returns:
            (success, message)
        """
        try:
            small_data = b"Hello, World!" * 10  # 130 bytes
            result = self.compression_engine.compress(small_data)
            decompressed = self.compression_engine.decompress(result)
            
            if decompressed == small_data:
                self.logger.debug(f"Small data ({len(small_data)} bytes) handled correctly")
                return True, "Small data handled correctly"
            else:
                return False, "Decompression mismatch for small data"
        except Exception as e:
            self.logger.error(f"Small data test failed: {e}")
            return False, str(e)
    
    def test_single_byte(self) -> tuple[bool, str]:
        """Test compression of single byte.
        
        Returns:
            (success, message)
        """
        try:
            single_byte = b"\x42"
            result = self.compression_engine.compress(single_byte)
            decompressed = self.compression_engine.decompress(result)
            
            if decompressed == single_byte:
                return True, "Single byte handled"
            else:
                return False, "Single byte decompression failed"
        except Exception as e:
            self.logger.debug(f"Single byte raised: {type(e).__name__}")
            return True, f"Exception: {type(e).__name__}"
    
    def test_repetitive_data(self) -> tuple[bool, str]:
        """Test compression of highly repetitive data.
        
        Returns:
            (success, message)
        """
        try:
            repetitive = b"A" * 1000000  # 1MB of same byte
            result = self.compression_engine.compress(repetitive)
            decompressed = self.compression_engine.decompress(result)
            
            if decompressed == repetitive:
                ratio = len(repetitive) / len(result) if result else 0
                self.logger.debug(f"Repetitive data compressed {ratio:.0f}x")
                return True, f"Compressed {ratio:.0f}x"
            else:
                return False, "Repetitive data decompression failed"
        except Exception as e:
            self.logger.error(f"Repetitive data test failed: {e}")
            return False, str(e)
    
    def test_random_data(self) -> tuple[bool, str]:
        """Test compression of random (incompressible) data.
        
        Returns:
            (success, message)
        """
        try:
            random_data = os.urandom(10000)  # 10KB random
            result = self.compression_engine.compress(random_data)
            decompressed = self.compression_engine.decompress(result)
            
            if decompressed == random_data:
                ratio = len(random_data) / len(result) if result else 0
                self.logger.debug(f"Random data: {ratio:.2f}x")
                return True, f"Ratio {ratio:.2f}x (random data)"
            else:
                return False, "Random data decompression failed"
        except Exception as e:
            self.logger.error(f"Random data test failed: {e}")
            return False, str(e)
    
    def test_truncated_data(self) -> tuple[bool, str]:
        """Test decompression of truncated compressed data.
        
        Should fail gracefully, not crash.
        
        Returns:
            (success, message)
        """
        try:
            original = b"Test data" * 1000
            compressed = self.compression_engine.compress(original)
            
            # Truncate the compressed data by 50%
            truncated = compressed[:len(compressed) // 2]
            
            try:
                decompressed = self.compression_engine.decompress(truncated)
                # If it doesn't crash, that's a pass (might be incomplete data)
                self.logger.debug("Truncated data handled without crash")
                return True, "Handled gracefully"
            except Exception as e:
                # Exception is acceptable for corrupted data
                self.logger.debug(f"Truncated data raised: {type(e).__name__}")
                return True, f"Exception raised: {type(e).__name__}"
        except Exception as e:
            self.logger.error(f"Truncated data test failed: {e}")
            return False, str(e)
    
    def test_corrupted_header(self) -> tuple[bool, str]:
        """Test decompression of data with corrupted header.
        
        Returns:
            (success, message)
        """
        try:
            original = b"Test data" * 1000
            compressed = self.compression_engine.compress(original)
            
            # Corrupt first few bytes
            corrupted = b"X" * 10 + compressed[10:]
            
            try:
                decompressed = self.compression_engine.decompress(corrupted)
                return False, "Should have failed on corrupted header"
            except Exception as e:
                # Exception is expected
                self.logger.debug(f"Corrupted header rejected: {type(e).__name__}")
                return True, f"Rejected: {type(e).__name__}"
        except Exception as e:
            self.logger.error(f"Corrupted header test failed: {e}")
            return False, str(e)
    
    def run(self, dataset_path: Path, dataset_info: Dict) -> BenchmarkResult:
        """Run all error handling tests on a dataset.
        
        Args:
            dataset_path: Path to test dataset (optional)
            dataset_info: Metadata
            
        Returns:
            BenchmarkResult with error handling metrics
        """
        test_name = "error_handling_suite"
        
        try:
            tests = {
                "empty_data": self.test_empty_data,
                "single_byte": self.test_single_byte,
                "small_data": self.test_small_data,
                "repetitive_data": self.test_repetitive_data,
                "random_data": self.test_random_data,
                "truncated_data": self.test_truncated_data,
                "corrupted_header": self.test_corrupted_header,
            }
            
            results = {}
            passed = 0
            failed = 0
            
            for test_name_key, test_func in tests.items():
                try:
                    success, message = test_func()
                    results[test_name_key] = {
                        "passed": success,
                        "message": message
                    }
                    if success:
                        passed += 1
                    else:
                        failed += 1
                except Exception as e:
                    results[test_name_key] = {
                        "passed": False,
                        "message": f"Test exception: {e}"
                    }
                    failed += 1
            
            success = (failed == 0)
            
            metrics = {
                "test_suite": "error_handling",
                "total_tests": len(tests),
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/len(tests)*100):.1f}%",
                "results": results
            }
            
            status = "✓" if success else "⚠"
            self.logger.info(
                f"{status} Error handling suite: {passed}/{len(tests)} tests passed"
            )
            
            result = BenchmarkResult(
                test_name="error_handling",
                dataset_type="synthetic",
                dataset_size=0,
                success=success,
                metrics=metrics
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error handling test suite failed: {e}")
            return BenchmarkResult(
                test_name="error_handling",
                dataset_type="synthetic",
                dataset_size=0,
                success=False,
                metrics={},
                error=str(e)
            )
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Aggregate error handling metrics.
        
        Returns:
            Dictionary of aggregated results
        """
        if not self.results:
            return {}
        
        # Should only have one result (the full suite)
        if self.results:
            return self.results[0].metrics
        
        return {}
    
    def cleanup(self) -> bool:
        """Clean up resources.
        
        Returns:
            True
        """
        return True
