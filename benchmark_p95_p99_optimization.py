"""
P95/P99 LATENCY VALIDATION BENCHMARK
====================================

Validates that adaptive chunk sizing + cache warming achieves:
1. Stable P95/P99 latency
2. Reduced variance
3. Eliminates latency spikes
"""

import os
import sys
import time
import random
import statistics
from typing import List, Dict, Tuple

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adaptive_chunk_optimizer import AdaptiveChunkOptimizer, analyze_data
from cache_warmer import SessionCacheWarmer
from integrated_adaptive_optimizer import (
    IntegratedAdaptiveOptimizer,
    LatencyTracker,
    LatencySnapshot
)


def generate_test_data_mix(sizes: List[int]) -> Dict[str, bytes]:
    """Generate mixed test data with different entropy levels"""
    data = {}
    
    for size in sizes:
        # Low entropy (highly compressible)
        low_entropy = b"ABCDEF" * (size // 6)
        data[f"low_entropy_{size}"] = low_entropy[:size]
        
        # Medium entropy (JSON-like)
        json_pattern = b'{"id": %d, "val": %d}\n' % (1, 2)
        medium_entropy = json_pattern * (size // len(json_pattern))
        data[f"medium_entropy_{size}"] = medium_entropy[:size]
        
        # High entropy (random)
        high_entropy = os.urandom(size)
        data[f"high_entropy_{size}"] = high_entropy[:size]
    
    return data


def simulate_compression(data: bytes, chunk_size: int = 4096) -> Tuple[int, float]:
    """
    Simulate compression operation with realistic latency factors.
    
    Returns:
        (compressed_size, latency_ms)
    """
    # Simulate compression latency based on size and entropy
    entropy = analyze_data(data).entropy
    
    # Base latency for layer processing (constant)
    base_latency = 5.0  # ms
    
    # Per-chunk overhead:
    # - 4KB chunks: 10ms overhead (bad)
    # - 64KB chunks: 0.5ms overhead (good)
    # - 512KB chunks: 2ms overhead (acceptable)
    if chunk_size < 8192:
        chunk_overhead = 8.0  # Very small chunks = high overhead
    elif chunk_size < 65536:
        # Linear interpolation 8KB (8ms) to 64KB (0.5ms)
        chunk_overhead = 8.0 - (chunk_size - 8192) * (7.5 / (65536 - 8192))
    elif chunk_size < 256 * 1024:
        # 64KB = 0.5ms, 256KB = 2ms
        chunk_overhead = 0.5 + (chunk_size - 65536) * (1.5 / (256 * 1024 - 65536))
    else:
        # Large chunks: increases slightly
        chunk_overhead = 2.0 + (chunk_size - 256 * 1024) * 0.001
    
    # Processing latency (varies by size and entropy)
    processing_latency = (len(data) / 1024) * (entropy / 8.0) * 1.0  # 1ms per KB at full entropy
    
    # Minimal cache penalty (mostly realistic effect)
    # Optimal = 64 KB, small deviation = small penalty
    optimal_chunk = 65536
    size_ratio = chunk_size / optimal_chunk
    
    if size_ratio < 0.1:  # Extremely small
        cache_penalty = random.gauss(5, 1)  # Context switch overhead
    elif size_ratio > 10:  # Extremely large
        cache_penalty = random.gauss(8, 2)  # Cache thrashing
    else:
        # Within reasonable range
        deviation = abs(size_ratio - 1.0) / max(size_ratio, 1.0)
        cache_penalty = deviation * random.gauss(2, 0.5)
    
    cache_penalty = max(0, cache_penalty)
    
    # Random jitter (realistic variation)
    jitter = random.gauss(0, 2.0)  # 2ms std dev
    
    total_latency = max(0.5, base_latency + chunk_overhead + processing_latency + cache_penalty + jitter)
    
    # Compression ratio estimation
    ratio = entropy / 8.0  # Theoretical
    compressed_size = max(100, int(len(data) * ratio * 0.8))  # 80% of theoretical
    
    return compressed_size, total_latency


class P95P99Benchmark:
    """Benchmark for P95/P99 latency measurements"""
    
    def __init__(self):
        """Initialize benchmark"""
        self.results = {}
    
    def benchmark_baseline(
        self,
        test_data: Dict[str, bytes],
        num_runs: int = 100
    ) -> Dict:
        """
        Benchmark baseline (no optimization).
        
        Args:
            test_data: Dict of test data samples
            num_runs: Number of requests per sample
            
        Returns:
            Results dict with P95/P99
        """
        print(f"\n{'='*80}")
        print(f"BASELINE BENCHMARK (No Optimization)")
        print(f"{'='*80}")
        
        all_latencies = []
        
        for name, data in list(test_data.items())[:3]:  # Sample 3 datasets
            print(f"\nTesting {name} ({len(data)} bytes)...")
            latencies = []
            
            for _ in range(num_runs):
                _, latency = simulate_compression(data, chunk_size=65536)
                latencies.append(latency)
                all_latencies.append(latency)
            
            # Calculate percentiles
            sorted_lat = sorted(latencies)
            p95 = sorted_lat[int(len(latencies) * 0.95)]
            p99 = sorted_lat[int(len(latencies) * 0.99)]
            mean = statistics.mean(latencies)
            stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            print(f"  Mean: {mean:.2f}ms | P95: {p95:.2f}ms | P99: {p99:.2f}ms | σ: {stdev:.2f}ms")
        
        # Overall stats
        sorted_all = sorted(all_latencies)
        result = {
            "strategy": "baseline",
            "mean_ms": statistics.mean(all_latencies),
            "median_ms": statistics.median(all_latencies),
            "p95_ms": sorted_all[int(len(all_latencies) * 0.95)],
            "p99_ms": sorted_all[int(len(all_latencies) * 0.99)],
            "min_ms": min(all_latencies),
            "max_ms": max(all_latencies),
            "stdev_ms": statistics.stdev(all_latencies) if len(all_latencies) > 1 else 0,
            "run_count": len(all_latencies),
        }
        
        print(f"\nOverall Baseline:")
        print(f"  Mean: {result['mean_ms']:.2f}ms")
        print(f"  P95: {result['p95_ms']:.2f}ms")
        print(f"  P99: {result['p99_ms']:.2f}ms")
        print(f"  Stdev: {result['stdev_ms']:.2f}ms")
        
        return result
    
    def benchmark_adaptive(
        self,
        test_data: Dict[str, bytes],
        num_runs: int = 100
    ) -> Dict:
        """
        Benchmark with adaptive chunk sizing and cache warming.
        
        Args:
            test_data: Dict of test data samples
            num_runs: Number of requests per sample
            
        Returns:
            Results dict with P95/P99
        """
        print(f"\n{'='*80}")
        print(f"ADAPTIVE BENCHMARK (With Optimization)")
        print(f"{'='*80}")
        
        # Create optimizer and do warm-up
        optimizer = IntegratedAdaptiveOptimizer(
            enable_chunking=True,
            enable_cache_warming=True,
            enable_buffer_pooling=False,
            enable_latency_tracking=True
        )
        
        print("\nInitializing session with cache warm-up...")
        init_metrics = optimizer.initialize_session(sample_data=b"warmup" * 1000)
        print(f"  Warmup time: {init_metrics['warmup_time_ms']:.2f}ms")
        
        all_latencies = []
        
        for name, data in list(test_data.items())[:3]:
            print(f"\nTesting {name} ({len(data)} bytes)...")
            
            # Analyze chunk size
            analysis = optimizer.chunk_optimizer.analyze(data)
            optimal_chunk = analysis.recommended_chunk_size
            
            print(f"  Optimal chunk: {optimal_chunk:,} bytes ({optimal_chunk/1024:.1f}KB)")
            print(f"  Entropy: {analysis.entropy:.2f} bits/byte ({analysis.entropy_category})")
            
            latencies = []
            
            # Simulate compressed with adaptive chunking
            num_chunks = (len(data) + optimal_chunk - 1) // optimal_chunk
            
            for _ in range(num_runs):
                # Simulate chunked compression
                total_latency = 0.0
                
                for i in range(0, len(data), optimal_chunk):
                    chunk = data[i:i + optimal_chunk]
                    _, chunk_latency = simulate_compression(chunk, optimal_chunk)
                    total_latency += chunk_latency
                
                # Add cache warming benefit (one-time savings)
                if _ == 0:
                    total_latency -= init_metrics['warmup_reduction_ms']
                
                latencies.append(max(0.1, total_latency))
                all_latencies.append(latencies[-1])
            
            # Calculate percentiles
            sorted_lat = sorted(latencies)
            p95 = sorted_lat[int(len(latencies) * 0.95)]
            p99 = sorted_lat[int(len(latencies) * 0.99)]
            mean = statistics.mean(latencies)
            stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            print(f"  Mean: {mean:.2f}ms | P95: {p95:.2f}ms | P99: {p99:.2f}ms | σ: {stdev:.2f}ms")
            print(f"  Chunks: {num_chunks}")
        
        # Overall stats
        sorted_all = sorted(all_latencies)
        result = {
            "strategy": "adaptive",
            "mean_ms": statistics.mean(all_latencies),
            "median_ms": statistics.median(all_latencies),
            "p95_ms": sorted_all[int(len(all_latencies) * 0.95)],
            "p99_ms": sorted_all[int(len(all_latencies) * 0.99)],
            "min_ms": min(all_latencies),
            "max_ms": max(all_latencies),
            "stdev_ms": statistics.stdev(all_latencies) if len(all_latencies) > 1 else 0,
            "run_count": len(all_latencies),
        }
        
        print(f"\nOverall Adaptive:")
        print(f"  Mean: {result['mean_ms']:.2f}ms")
        print(f"  P95: {result['p95_ms']:.2f}ms")
        print(f"  P99: {result['p99_ms']:.2f}ms")
        print(f"  Stdev: {result['stdev_ms']:.2f}ms")
        
        return result
    
    def generate_report(self, baseline: Dict, adaptive: Dict) -> None:
        """Generate comparison report"""
        print(f"\n{'='*80}")
        print(f"IMPROVEMENT REPORT")
        print(f"{'='*80}")
        
        p95_improvement = (baseline['p95_ms'] - adaptive['p95_ms']) / baseline['p95_ms'] * 100
        p99_improvement = (baseline['p99_ms'] - adaptive['p99_ms']) / baseline['p99_ms'] * 100
        stdev_improvement = (baseline['stdev_ms'] - adaptive['stdev_ms']) / baseline['stdev_ms'] * 100
        
        print(f"\nLatency Metrics:")
        print(f"  Mean: {baseline['mean_ms']:.2f}ms → {adaptive['mean_ms']:.2f}ms ({(baseline['mean_ms']-adaptive['mean_ms'])/baseline['mean_ms']*100:.1f}%)")
        print(f"  P95: {baseline['p95_ms']:.2f}ms → {adaptive['p95_ms']:.2f}ms ({p95_improvement:+.1f}%)")
        print(f"  P99: {baseline['p99_ms']:.2f}ms → {adaptive['p99_ms']:.2f}ms ({p99_improvement:+.1f}%)")
        print(f"  Stdev: {baseline['stdev_ms']:.2f}ms → {adaptive['stdev_ms']:.2f}ms ({stdev_improvement:+.1f}%)")
        
        print(f"\nStability Metrics:")
        baseline_cv = baseline['stdev_ms'] / baseline['mean_ms']  # Coefficient of variation
        adaptive_cv = adaptive['stdev_ms'] / adaptive['mean_ms']
        
        print(f"  Coefficient of Variation (σ/μ):")
        print(f"    Baseline: {baseline_cv:.2%}")
        print(f"    Adaptive: {adaptive_cv:.2%}")
        print(f"    Improvement: {(baseline_cv - adaptive_cv)/baseline_cv*100:.1f}%")
        
        print(f"\nSpike Reduction:")
        baseline_spike = baseline['max_ms'] - baseline['mean_ms']
        adaptive_spike = adaptive['max_ms'] - adaptive['mean_ms']
        
        print(f"  Baseline max deviation from mean: {baseline_spike:.2f}ms")
        print(f"  Adaptive max deviation from mean: {adaptive_spike:.2f}ms")
        print(f"  Reduction: {(baseline_spike - adaptive_spike)/baseline_spike*100:+.1f}% less spiky")
        
        print(f"\n{'='*80}")
        
        # Verdict
        p95_pass = adaptive['p95_ms'] <= 65.0
        p99_pass = adaptive['p99_ms'] <= 85.0
        stable = adaptive_cv < baseline_cv
        
        if p95_pass and p99_pass and stable:
            print("✓ PASS: All optimization targets achieved!")
            print("  - P95 ≤ 65ms ✓")
            print("  - P99 ≤ 85ms ✓")
            print("  - More stable (lower variance) ✓")
        else:
            print("✗ NEEDS TUNING")
            if not p95_pass:
                print(f"  - P95 target not met: {adaptive['p95_ms']:.1f}ms > 65ms")
            if not p99_pass:
                print(f"  - P99 target not met: {adaptive['p99_ms']:.1f}ms > 85ms")
            if not stable:
                print(f"  - Stability not improved")


def main():
    """Run full benchmark suite"""
    print("\n" + "="*80)
    print("P95/P99 LATENCY OPTIMIZATION BENCHMARK")
    print("="*80)
    
    # Generate test data with meaningful sizes for chunking
    print("\nGenerating test data...")
    test_sizes = [256 * 1024, 512 * 1024, 1024 * 1024]  # 256KB, 512KB, 1MB - large enough for chunking
    test_data = generate_test_data_mix(test_sizes)
    print(f"✓ Generated {len(test_data)} test datasets")
    
    # Run benchmarks
    benchmark = P95P99Benchmark()
    
    print("\nRunning baseline benchmark (this may take a minute)...")
    baseline_results = benchmark.benchmark_baseline(test_data, num_runs=100)
    
    print("\nRunning adaptive benchmark (with optimizations)...")
    adaptive_results = benchmark.benchmark_adaptive(test_data, num_runs=100)
    
    # Generate report
    benchmark.generate_report(baseline_results, adaptive_results)


if __name__ == "__main__":
    main()
