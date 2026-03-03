"""
Compression Performance Runner for COBOL Benchmarks

Measures:
- Compression ratio
- Throughput (MB/s)
- Latency percentiles (p50, p95, p99)
- Memory usage
"""

import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple
import statistics
import logging

from .base_runner import BaseRunner, BenchmarkResult

logger = logging.getLogger(__name__)


class CompressionRunner(BaseRunner):
    """Benchmark compression performance of COBOL layers.
    
    Tests each enabled compression layer against standard datasets.
    Measures compression ratio, throughput, and latency distribution.
    """
    
    def __init__(self, output_dir: Path, compression_engine=None):
        """Initialize compression benchmark.
        
        Args:
            output_dir: Directory for saving results
            compression_engine: COBOL compression provider instance
        """
        super().__init__("compression", output_dir)
        self.compression_engine = compression_engine
        self.latencies: List[float] = []
        self.compression_ratios: List[float] = []
        self.throughputs: List[float] = []
    
    def setup(self) -> bool:
        """Set up compression benchmark.
        
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
        """Compress a dataset and collect metrics.
        
        Args:
            dataset_path: Path to input dataset
            dataset_info: Metadata about dataset
            
        Returns:
            BenchmarkResult with compression metrics
        """
        test_name = f"compress_{dataset_info.get('name', 'unknown')}"
        
        try:
            # Read dataset
            with open(dataset_path, 'rb') as f:
                original_data = f.read()
            
            original_size = len(original_data)
            
            # Perform compression with latency tracking
            latencies: List[float] = []
            compressed_data = None
            
            for run in range(3):  # 3 compression runs
                start_time = time.perf_counter()
                
                # Compress
                compressed_data = self.compression_engine.compress(original_data)
                
                elapsed = time.perf_counter() - start_time
                latencies.append(elapsed)
            
            compressed_size = len(compressed_data)
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
            
            # Calculate throughput (MB/s) - use average latency
            avg_latency = statistics.mean(latencies)
            throughput = (original_size / (1024 * 1024)) / avg_latency if avg_latency > 0 else 0
            
            # Calculate latency percentiles
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[len(sorted_latencies) // 2] * 1000  # Convert to ms
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] * 1000
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] * 1000 if len(sorted_latencies) > 2 else p95
            
            # Calculate checksum for verification
            compressed_checksum = hashlib.sha256(compressed_data).hexdigest()
            
            # Store metrics for aggregation
            self.latencies.extend(latencies)
            self.compression_ratios.append(compression_ratio)
            self.throughputs.append(throughput)
            
            metrics = {
                "original_size_bytes": original_size,
                "compressed_size_bytes": compressed_size,
                "compression_ratio": round(compression_ratio, 4),
                "throughput_mbps": round(throughput, 2),
                "latency_avg_ms": round(avg_latency * 1000, 4),
                "latency_p50_ms": round(p50, 4),
                "latency_p95_ms": round(p95, 4),
                "latency_p99_ms": round(p99, 4),
                "checksum": compressed_checksum,
                "dataset_type": dataset_info.get('type', 'unknown')
            }
            
            result = BenchmarkResult(
                test_name=test_name,
                dataset_type=dataset_info.get('type', 'unknown'),
                dataset_size=original_size,
                success=True,
                metrics=metrics
            )
            
            self.logger.info(
                f"✓ {test_name}: ratio={compression_ratio:.2f}x, "
                f"throughput={throughput:.1f} MB/s"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Compression test failed for {dataset_path}: {e}")
            return BenchmarkResult(
                test_name=test_name,
                dataset_type=dataset_info.get('type', 'unknown'),
                dataset_size=0,
                success=False,
                metrics={},
                error=str(e)
            )
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Aggregate compression metrics across all runs.
        
        Returns:
            Dictionary of aggregated results
        """
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r.success]
        
        if not successful_results:
            return {"error": "No successful compression tests"}
        
        # Extract metrics from successful results
        ratios = [r.metrics.get('compression_ratio', 0) for r in successful_results]
        throughputs = [r.metrics.get('throughput_mbps', 0) for r in successful_results]
        latencies_ms = [r.metrics.get('latency_avg_ms', 0) for r in successful_results]
        
        return {
            "tests_run": len(self.results),
            "tests_passed": len(successful_results),
            "success_rate": f"{(len(successful_results)/len(self.results)*100):.1f}%",
            "compression_ratio": {
                "min": round(min(ratios), 4) if ratios else 0,
                "max": round(max(ratios), 4) if ratios else 0,
                "avg": round(statistics.mean(ratios), 4) if ratios else 0,
                "median": round(statistics.median(ratios), 4) if ratios else 0
            },
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
        """Clean up compression benchmark resources.
        
        Returns:
            True (no resources to clean up)
        """
        return True
