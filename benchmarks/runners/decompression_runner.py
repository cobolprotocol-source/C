"""
Decompression Performance and Integrity Runner for COBOL Benchmarks

Measures:
- Decompression throughput
- Round-trip data integrity
- Checksum validation
- Latency percentiles
"""

import time
import hashlib
import statistics
from pathlib import Path
from typing import Dict, Any, List
import logging

from .base_runner import BaseRunner, BenchmarkResult

logger = logging.getLogger(__name__)


class DecompressionRunner(BaseRunner):
    """Benchmark decompression performance and data integrity.
    
    Tests decompression of COBOL-compressed data and validates
    that round-trip compression/decompression preserves data integrity.
    """
    
    def __init__(self, output_dir: Path, compression_engine=None):
        """Initialize decompression benchmark.
        
        Args:
            output_dir: Directory for saving results
            compression_engine: COBOL compression provider instance
        """
        super().__init__("decompression", output_dir)
        self.compression_engine = compression_engine
        self.decompress_latencies: List[float] = []
        self.throughputs: List[float] = []
    
    def setup(self) -> bool:
        """Set up decompression benchmark.
        
        Returns:
            True if compression engine is available
        """
        try:
            if self.compression_engine is None:
                # Try to import dynamically
                from src.layers.pipelines.orchestration import AdaptiveCompressionPipeline
                self.compression_engine = AdaptiveCompressionPipeline()
                self.logger.info("Loaded compression engine: AdaptiveCompressionPipeline")
            
            return self.compression_engine is not None
        except Exception as e:
            self.logger.error(f"Failed to load compression engine: {e}")
            return False
    
    def run(self, dataset_path: Path, dataset_info: Dict) -> BenchmarkResult:
        """Decompress and verify integrity of a dataset.
        
        Args:
            dataset_path: Path to original (uncompressed) dataset
            dataset_info: Metadata about dataset
            
        Returns:
            BenchmarkResult with decompression metrics
        """
        test_name = f"decompress_{dataset_info.get('name', 'unknown')}"
        
        try:
            # Read original dataset
            with open(dataset_path, 'rb') as f:
                original_data = f.read()
            
            original_checksum = hashlib.sha256(original_data).hexdigest()
            original_size = len(original_data)
            
            # First compress the data
            compressed_data = self.compression_engine.compress(original_data)
            compressed_size = len(compressed_data)
            
            # Now perform decompression with latency tracking
            latencies: List[float] = []
            decompressed_data = None
            
            for run in range(3):  # 3 decompression runs
                start_time = time.perf_counter()
                
                # Decompress
                decompressed_data = self.compression_engine.decompress(compressed_data)
                
                elapsed = time.perf_counter() - start_time
                latencies.append(elapsed)
            
            # Verify round-trip integrity
            decompressed_checksum = hashlib.sha256(decompressed_data).hexdigest()
            integrity_ok = (original_checksum == decompressed_checksum)
            size_match = (original_size == len(decompressed_data))
            
            # Calculate throughput (MB/s) - use average latency
            avg_latency = statistics.mean(latencies)
            throughput = (compressed_size / (1024 * 1024)) / avg_latency if avg_latency > 0 else 0
            
            # Calculate latency percentiles
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[len(sorted_latencies) // 2] * 1000  # Convert to ms
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] * 1000
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] * 1000 if len(sorted_latencies) > 2 else p95
            
            # Store metrics for aggregation
            self.decompress_latencies.extend(latencies)
            self.throughputs.append(throughput)
            
            metrics = {
                "original_size_bytes": original_size,
                "compressed_size_bytes": compressed_size,
                "decompressed_size_bytes": len(decompressed_data),
                "throughput_mbps": round(throughput, 2),
                "latency_avg_ms": round(avg_latency * 1000, 4),
                "latency_p50_ms": round(p50, 4),
                "latency_p95_ms": round(p95, 4),
                "latency_p99_ms": round(p99, 4),
                "integrity_verified": integrity_ok,
                "size_match": size_match,
                "original_checksum": original_checksum,
                "decompressed_checksum": decompressed_checksum,
                "dataset_type": dataset_info.get('type', 'unknown')
            }
            
            success = integrity_ok and size_match
            
            if success:
                self.logger.info(
                    f"✓ {test_name}: size={original_size}, "
                    f"decompression_throughput={throughput:.1f} MB/s, "
                    f"integrity=✅"
                )
            else:
                self.logger.warning(
                    f"✗ {test_name}: integrity_ok={integrity_ok}, size_match={size_match}"
                )
            
            result = BenchmarkResult(
                test_name=test_name,
                dataset_type=dataset_info.get('type', 'unknown'),
                dataset_size=original_size,
                success=success,
                metrics=metrics
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Decompression test failed for {dataset_path}: {e}")
            return BenchmarkResult(
                test_name=test_name,
                dataset_type=dataset_info.get('type', 'unknown'),
                dataset_size=0,
                success=False,
                metrics={},
                error=str(e)
            )
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Aggregate decompression metrics across all runs.
        
        Returns:
            Dictionary of aggregated results
        """
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r.success]
        
        if not successful_results:
            return {"error": "No successful decompression tests"}
        
        # Extract metrics
        throughputs = [r.metrics.get('throughput_mbps', 0) for r in successful_results]
        latencies_ms = [r.metrics.get('latency_avg_ms', 0) for r in successful_results]
        
        integrity_results = [r.metrics.get('integrity_verified', False) for r in successful_results]
        integrity_rate = (sum(integrity_results) / len(integrity_results) * 100) if integrity_results else 0
        
        return {
            "tests_run": len(self.results),
            "tests_passed": len(successful_results),
            "success_rate": f"{(len(successful_results)/len(self.results)*100):.1f}%",
            "integrity_rate": f"{integrity_rate:.1f}%",
            "throughput_mbps": {
                "min": round(min(throughputs), 2) if throughputs else 0,
                "max": round(max(throughputs), 2) if throughputs else 0,
                "avg": round(statistics.mean(throughputs), 2) if throughputs else 0
            },
            "latency_ms": {
                "min": round(min(latencies_ms), 4) if latencies_ms else 0,
                "max": round(max(latencies_ms), 4) if latencies_ms else 0,
                "avg": round(statistics.mean(latencies_ms), 4) if latencies_ms else 0
            }
        }
    
    def cleanup(self) -> bool:
        """Clean up decompression benchmark resources.
        
        Returns:
            True (no resources to clean up)
        """
        return True
