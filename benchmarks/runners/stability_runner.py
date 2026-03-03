"""
Stability and Determinism Runners for COBOL Benchmarks

Phase 3 focuses on:
1. Memory growth tracking during prolonged compression
2. Determinism validation - same input produces same output
3. Resource cleanup verification
"""

import time
import hashlib
import statistics
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .base_runner import BaseRunner, BenchmarkResult

logger = logging.getLogger(__name__)


class StabilityRunner(BaseRunner):
    """Benchmark compression stability under sustained load.
    
    Measures:
    - Memory usage growth over time
    - CPU stability
    - No resource leaks during prolonged operation
    - Consistent performance (no degradation)
    """
    
    def __init__(self, output_dir: Path, compression_engine=None, duration_seconds: int = 60):
        """Initialize stability benchmark.
        
        Args:
            output_dir: Directory for saving results
            compression_engine: COBOL compression provider instance
            duration_seconds: How long to run the stability test
        """
        super().__init__("stability", output_dir)
        self.compression_engine = compression_engine
        self.duration_seconds = duration_seconds
        self.memory_samples: List[Tuple[float, float]] = []  # (timestamp, memory_mb)
        self.cpu_samples: List[Tuple[float, float]] = []     # (timestamp, cpu_percent)
        self.throughput_timeline: List[float] = []
    
    def setup(self) -> bool:
        """Set up stability benchmark.
        
        Returns:
            True if resources available
        """
        try:
            if self.compression_engine is None:
                from src.layers.pipelines.orchestration import AdaptiveCompressionPipeline
                self.compression_engine = AdaptiveCompressionPipeline()
                self.logger.info("Loaded compression engine for stability testing")
            
            if not PSUTIL_AVAILABLE:
                self.logger.warning("psutil not available - memory/CPU tracking disabled")
                return self.compression_engine is not None
            
            return self.compression_engine is not None
        except Exception as e:
            self.logger.error(f"Failed to set up stability benchmark: {e}")
            return False
    
    def run(self, dataset_path: Path, dataset_info: Dict) -> BenchmarkResult:
        """Run stability test on dataset.
        
        Compresses the same dataset repeatedly over specified duration.
        Tracks memory and CPU usage.
        
        Args:
            dataset_path: Path to test dataset
            dataset_info: Metadata about dataset
            
        Returns:
            BenchmarkResult with stability metrics
        """
        test_name = f"stability_{dataset_info.get('name', 'unknown')}"
        
        try:
            # Read dataset
            with open(dataset_path, 'rb') as f:
                original_data = f.read()
            
            original_size = len(original_data)
            start_time = time.time()
            end_time = start_time + self.duration_seconds
            
            iteration = 0
            throughputs: List[float] = []
            memory_baseline = None
            max_memory = None
            
            # Get baseline memory
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_baseline = process.memory_info().rss / (1024 * 1024)  # MB
                max_memory = memory_baseline
            
            self.logger.info(f"Starting {self.duration_seconds}s stability test...")
            
            # Run compression repeatedly until duration expires
            while time.time() < end_time:
                iteration += 1
                
                # Compress
                compress_start = time.perf_counter()
                compressed_data = self.compression_engine.compress(original_data)
                compress_elapsed = time.perf_counter() - compress_start
                
                # Calculate throughput
                throughput = (original_size / (1024 * 1024)) / compress_elapsed if compress_elapsed > 0 else 0
                throughputs.append(throughput)
                
                # Sample memory/CPU every 10th iteration
                if PSUTIL_AVAILABLE and iteration % 10 == 0:
                    current_time = time.time() - start_time
                    mem_info = process.memory_info().rss / (1024 * 1024)  # MB
                    cpu_percent = process.cpu_percent(interval=0.01)
                    
                    self.memory_samples.append((current_time, mem_info))
                    self.cpu_samples.append((current_time, cpu_percent))
                    
                    max_memory = max(max_memory, mem_info)
            
            # Calculate metrics
            memory_growth = (max_memory - memory_baseline) if (PSUTIL_AVAILABLE and memory_baseline) else None
            
            metrics = {
                "duration_seconds": self.duration_seconds,
                "iterations": iteration,
                "iterations_per_second": round(iteration / self.duration_seconds, 2),
                "throughput_avg_mbps": round(statistics.mean(throughputs), 2) if throughputs else 0,
                "throughput_min_mbps": round(min(throughputs), 2) if throughputs else 0,
                "throughput_max_mbps": round(max(throughputs), 2) if throughputs else 0,
                "throughput_stdev": round(statistics.stdev(throughputs), 2) if len(throughputs) > 1 else 0,
                "memory_baseline_mb": round(memory_baseline, 2) if memory_baseline else None,
                "memory_peak_mb": round(max_memory, 2) if max_memory else None,
                "memory_growth_mb": round(memory_growth, 2) if memory_growth is not None else None,
                "dataset_type": dataset_info.get('type', 'unknown')
            }
            
            # Stability OK if no significant memory growth (< 100MB) and consistent throughput
            throughput_variance = (metrics.get("throughput_stdev", 0) / metrics.get("throughput_avg_mbps", 1)) if metrics.get("throughput_avg_mbps") else 0
            memory_stable = (memory_growth is None) or (memory_growth < 100)
            performance_stable = throughput_variance < 0.2  # <20% CV
            
            success = memory_stable and performance_stable
            
            if success:
                self.logger.info(
                    f"✓ {test_name}: {iteration} iterations in {self.duration_seconds}s, "
                    f"avg {metrics['throughput_avg_mbps']} MB/s, "
                    f"memory stable (growth: {memory_growth:.1f}MB)"
                )
            else:
                self.logger.warning(
                    f"✗ {test_name}: stability issues detected "
                    f"(memory_stable={memory_stable}, perf_stable={performance_stable})"
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
            self.logger.error(f"Stability test failed for {dataset_path}: {e}")
            return BenchmarkResult(
                test_name=test_name,
                dataset_type=dataset_info.get('type', 'unknown'),
                dataset_size=0,
                success=False,
                metrics={},
                error=str(e)
            )
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Aggregate stability metrics.
        
        Returns:
            Dictionary of aggregated results
        """
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r.success]
        
        if not successful_results:
            return {"error": "No successful stability tests"}
        
        # Extract metrics
        iterations = [r.metrics.get('iterations', 0) for r in successful_results]
        throughputs = [r.metrics.get('throughput_avg_mbps', 0) for r in successful_results]
        memory_growths = [r.metrics.get('memory_growth_mb', 0) for r in successful_results if r.metrics.get('memory_growth_mb') is not None]
        
        return {
            "tests_run": len(self.results),
            "tests_passed": len(successful_results),
            "success_rate": f"{(len(successful_results)/len(self.results)*100):.1f}%",
            "total_iterations": sum(iterations),
            "iterations_per_second": {
                "avg": round(statistics.mean([r.metrics.get('iterations_per_second', 0) for r in successful_results]), 2)
            },
            "throughput_mbps": {
                "min": round(min(throughputs), 2) if throughputs else 0,
                "max": round(max(throughputs), 2) if throughputs else 0,
                "avg": round(statistics.mean(throughputs), 2) if throughputs else 0
            },
            "memory_growth_mb": {
                "avg": round(statistics.mean(memory_growths), 2) if memory_growths else 0,
                "max": round(max(memory_growths), 2) if memory_growths else 0
            }
        }
    
    def cleanup(self) -> bool:
        """Clean up resources.
        
        Returns:
            True
        """
        return True


class DeterminismRunner(BaseRunner):
    """Validate that compression is deterministic.
    
    Same input should always produce identical output:
    - Same byte-for-byte compressed data
    - Same checksums across multiple runs
    - No randomness or non-determinism
    """
    
    def __init__(self, output_dir: Path, compression_engine=None, num_runs: int = 5):
        """Initialize determinism benchmark.
        
        Args:
            output_dir: Directory for saving results
            compression_engine: COBOL compression provider instance
            num_runs: Number of compression runs to compare
        """
        super().__init__("determinism", output_dir)
        self.compression_engine = compression_engine
        self.num_runs = num_runs
    
    def setup(self) -> bool:
        """Set up determinism test.
        
        Returns:
            True if compression engine available
        """
        try:
            if self.compression_engine is None:
                from src.layers.pipelines.orchestration import AdaptiveCompressionPipeline
                self.compression_engine = AdaptiveCompressionPipeline()
                self.logger.info("Loaded compression engine for determinism testing")
            
            return self.compression_engine is not None
        except Exception as e:
            self.logger.error(f"Failed to set up determinism test: {e}")
            return False
    
    def run(self, dataset_path: Path, dataset_info: Dict) -> BenchmarkResult:
        """Test determinism on a dataset.
        
        Compresses the same data N times and verifies all outputs are identical.
        
        Args:
            dataset_path: Path to test dataset
            dataset_info: Metadata about dataset
            
        Returns:
            BenchmarkResult with determinism metrics
        """
        test_name = f"determinism_{dataset_info.get('name', 'unknown')}"
        
        try:
            # Read dataset
            with open(dataset_path, 'rb') as f:
                original_data = f.read()
            
            original_size = len(original_data)
            
            # Compress N times
            compressed_outputs = []
            checksums = []
            
            for run in range(self.num_runs):
                compressed = self.compression_engine.compress(original_data)
                compressed_outputs.append(compressed)
                checksum = hashlib.sha256(compressed).hexdigest()
                checksums.append(checksum)
            
            # Check if all outputs are identical
            all_identical = all(output == compressed_outputs[0] for output in compressed_outputs)
            all_checksums_match = all(cs == checksums[0] for cs in checksums)
            
            metrics = {
                "num_runs": self.num_runs,
                "original_size_bytes": original_size,
                "compressed_size_bytes": len(compressed_outputs[0]) if compressed_outputs else 0,
                "all_outputs_identical": all_identical,
                "all_checksums_match": all_checksums_match,
                "unique_checksums": len(set(checksums)),
                "reference_checksum": checksums[0] if checksums else None,
                "all_checksums": checksums,
                "dataset_type": dataset_info.get('type', 'unknown')
            }
            
            success = all_identical and all_checksums_match
            
            if success:
                self.logger.info(
                    f"✓ {test_name}: Deterministic across {self.num_runs} runs"
                )
            else:
                self.logger.warning(
                    f"✗ {test_name}: Non-deterministic output detected "
                    f"(unique_checksums: {len(set(checksums))})"
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
            self.logger.error(f"Determinism test failed for {dataset_path}: {e}")
            return BenchmarkResult(
                test_name=test_name,
                dataset_type=dataset_info.get('type', 'unknown'),
                dataset_size=0,
                success=False,
                metrics={},
                error=str(e)
            )
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Aggregate determinism metrics.
        
        Returns:
            Dictionary of aggregated results
        """
        if not self.results:
            return {}
        
        successful_results = [r for r in self.results if r.success]
        
        if not successful_results:
            return {"error": "No successful determinism tests"}
        
        return {
            "tests_run": len(self.results),
            "tests_passed": len(successful_results),
            "success_rate": f"{(len(successful_results)/len(self.results)*100):.1f}%",
            "deterministic_percentage": f"{(len(successful_results)/len(self.results)*100):.1f}%",
            "all_deterministic": all(r.success for r in self.results)
        }
    
    def cleanup(self) -> bool:
        """Clean up resources.
        
        Returns:
            True
        """
        return True
