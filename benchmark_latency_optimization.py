"""
LATENCY OPTIMIZATION BENCHMARK
==============================

Validates that optimizations achieve 20-45% latency reduction
without changing compression correctness.

Usage:
    python benchmark_latency_optimization.py
"""

import os
import sys
import time
import logging
import statistics
import numpy as np
from typing import List, Tuple, Dict, Any

logging.basicConfig(
    level=logging.WARNING,  # Quiet for benchmarking
    format='%(levelname)s: %(message)s'
)

# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def generate_test_data(size_bytes: int) -> bytes:
    """Generate realistic test data"""
    # Mix of structured data (JSON-like) and numeric sequences
    json_pattern = b'{"id": %d, "value": %d, "name": "test_%d"}\n'
    numeric_pattern = np.random.randint(0, 256, size_bytes // 100, dtype=np.uint8)
    
    result = b''
    numeric_idx = 0
    for i in range(size_bytes // 100):
        result += json_pattern % (i, i * 10, i)
        if numeric_idx < len(numeric_pattern):
            result += bytes([numeric_pattern[numeric_idx]])
            numeric_idx += 1
    
    return result[:size_bytes]


def generate_repeated_data(size_bytes: int) -> bytes:
    """Generate highly repetitive data (best case for compression)"""
    pattern = b"COBOL_DATA_PATTERN_REPXXXXXXXX" * 100
    return (pattern * (size_bytes // len(pattern) + 1))[:size_bytes]


def generate_random_data(size_bytes: int) -> bytes:
    """Generate random data (worst case for compression)"""
    return os.urandom(size_bytes)


# ============================================================================
# MICROBENCHMARK: Original vs Optimized
# ============================================================================

def benchmark_original_vs_optimized(
    engine,
    test_data: bytes,
    num_runs: int = 10
) -> Dict[str, Any]:
    """
    Compare latency: original compress_chained vs optimized wrapper
    
    Returns:
        Dictionary with timing results and speedup metrics
    """
    print(f"\n{'='*80}")
    print(f"LATENCY BENCHMARK: {len(test_data):,} bytes, {num_runs} runs")
    print(f"{'='*80}")
    
    # ===== ORIGINAL (engine.compress_chained) =====
    print(f"\n[1/2] Measuring original pipeline...")
    original_times = []
    
    # Warm up
    for _ in range(2):
        try:
            engine.compress_chained(test_data)
        except Exception as e:
            print(f"  Warning: Engine error: {e}")
            return {}
    
    # Benchmark
    for run in range(num_runs):
        start = time.perf_counter()
        try:
            result_original = engine.compress_chained(test_data)
        except:
            continue
        elapsed = (time.perf_counter() - start) * 1000
        original_times.append(elapsed)
    
    original_avg = statistics.mean(original_times)
    original_stdev = statistics.stdev(original_times) if len(original_times) > 1 else 0
    original_min = min(original_times)
    original_max = max(original_times)
    
    print(f"  Original: {original_avg:.2f} ms ± {original_stdev:.2f} ms " +
          f"[{original_min:.2f} - {original_max:.2f}]")
    
    # ===== OPTIMIZED (fusion optimizer) =====
    print(f"\n[2/2] Measuring optimized pipeline...")
    
    try:
        from fusion_pipeline_optimizer import FusionPipelineOptimizer
        optimizer = FusionPipelineOptimizer(engine, enable_batch_logging=True)
    except ImportError:
        print("  ERROR: fusion_pipeline_optimizer not available")
        return {'error': 'Missing fusion_pipeline_optimizer module'}
    
    optimized_times = []
    
    for run in range(num_runs):
        start = time.perf_counter()
        result_optimized = optimizer.compress_fused(test_data)
        elapsed = (time.perf_counter() - start) * 1000
        optimized_times.append(elapsed)
    
    optimized_avg = statistics.mean(optimized_times)
    optimized_stdev = statistics.stdev(optimized_times) if len(optimized_times) > 1 else 0
    optimized_min = min(optimized_times)
    optimized_max = max(optimized_times)
    
    print(f"  Optimized: {optimized_avg:.2f} ms ± {optimized_stdev:.2f} ms " +
          f"[{optimized_min:.2f} - {optimized_max:.2f}]")
    
    # ===== COMPARISON =====
    speedup = original_avg / optimized_avg
    improvement_pct = (1 - optimized_avg / original_avg) * 100
    reduction_ms = original_avg - optimized_avg
    
    print(f"\n{'='*80}")
    print(f"RESULTS:")
    print(f"{'='*80}")
    print(f"  Speedup: {speedup:.2f}x faster")
    print(f"  Improvement: {improvement_pct:.1f}%")
    print(f"  Latency reduction: {reduction_ms:.2f} ms")
    print(f"  Target: 20-45% (20-50 ms reduction)")
    
    if improvement_pct >= 20:
        print(f"  ✓ TARGET ACHIEVED")
    else:
        print(f"  ✗ Below target (need {20 - improvement_pct:.1f}% more)")
    
    return {
        'test_data_size': len(test_data),
        'num_runs': num_runs,
        'original_avg_ms': original_avg,
        'original_stdev_ms': original_stdev,
        'original_min_ms': original_min,
        'original_max_ms': original_max,
        'optimized_avg_ms': optimized_avg,
        'optimized_stdev_ms': optimized_stdev,
        'optimized_min_ms': optimized_min,
        'optimized_max_ms': optimized_max,
        'speedup': speedup,
        'improvement_pct': improvement_pct,
        'reduction_ms': reduction_ms,
        'target_met': improvement_pct >= 20,
    }


# ============================================================================
# MACROBENCHMARK: Scale Test (1000+ Requests)
# ============================================================================

def benchmark_scale_test(
    engine,
    request_count: int = 1000,
    chunk_size_bytes: int = 65536
) -> Dict[str, Any]:
    """
    Measure performance at scale: thousands of concurrent requests
    
    Tests:
    1. Small chunks (64 KB) - typical compression unit
    2. Latency distribution (min/max/percentiles)
    3. Consistency (stdev)
    """
    print(f"\n{'='*80}")
    print(f"SCALE BENCHMARK: {request_count:,} requests × {chunk_size_bytes:,} bytes")
    print(f"{'='*80}")
    
    try:
        from buffer_pool_optimizer import ContextFreePipelineWrapper
        wrapper = ContextFreePipelineWrapper(engine)
    except ImportError:
        print("  ERROR: buffer_pool_optimizer not available")
        return {'error': 'Missing buffer_pool_optimizer module'}
    
    latencies = []
    
    print(f"\nProcessing {request_count} requests...")
    for req_num in range(request_count):
        test_data = generate_test_data(chunk_size_bytes)
        
        start = time.perf_counter()
        try:
            compressed, metadata = wrapper.compress(test_data)
        except:
            continue
        
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)
        
        if (req_num + 1) % 100 == 0:
            print(f"  Processed {req_num + 1:,} requests...")
    
    # Analyze distribution
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[int(len(latencies) * 0.50)]
    p95 = latencies_sorted[int(len(latencies) * 0.95)]
    p99 = latencies_sorted[int(len(latencies) * 0.99)]
    
    print(f"\n{'='*80}")
    print(f"DISTRIBUTION ({len(latencies)} measurements):")
    print(f"{'='*80}")
    print(f"  Min:     {min(latencies):.2f} ms")
    print(f"  P50:     {p50:.2f} ms")
    print(f"  P95:     {p95:.2f} ms")
    print(f"  P99:     {p99:.2f} ms")
    print(f"  Max:     {max(latencies):.2f} ms")
    print(f"  Mean:    {statistics.mean(latencies):.2f} ms")
    print(f"  Stdev:   {statistics.stdev(latencies):.2f} ms")
    print(f"  CoV:     {statistics.stdev(latencies) / statistics.mean(latencies):.2%}")
    
    stats = wrapper.get_stats()
    print(f"\nOptimization stats:")
    print(f"  Buffer allocations saved: {stats.get('buffer_allocations_saved', 0)}")
    print(f"  Buffer reuses: {stats.get('buffer_reuses', 0)}")
    
    return {
        'request_count': len(latencies),
        'chunk_size_bytes': chunk_size_bytes,
        'min_ms': min(latencies),
        'p50_ms': p50,
        'p95_ms': p95,
        'p99_ms': p99,
        'max_ms': max(latencies),
        'mean_ms': statistics.mean(latencies),
        'stdev_ms': statistics.stdev(latencies),
        'cov': statistics.stdev(latencies) / statistics.mean(latencies),
    }


# ============================================================================
# CORRECTNESS TEST: Optimization doesn't affect compression
# ============================================================================

def benchmark_correctness_test(engine, test_sizes_kb: List[int] = [1, 10, 64, 256]):
    """
    Verify that optimized pipeline produces identical results
    """
    print(f"\n{'='*80}")
    print(f"CORRECTNESS TEST")
    print(f"{'='*80}")
    
    try:
        from fusion_pipeline_optimizer import FusionPipelineOptimizer
        optimizer = FusionPipelineOptimizer(engine, enable_batch_logging=True)
    except ImportError:
        print("  ERROR: fusion_pipeline_optimizer not available")
        return False
    
    all_pass = True
    
    for size_kb in test_sizes_kb:
        print(f"\nTesting {size_kb} KB...")
        test_data = generate_repeated_data(size_kb * 1024)
        
        try:
            # Original
            compressed_original, meta_orig = engine.compress_chained(test_data)
            
            # Optimized
            compressed_optimized, meta_opt = optimizer.compress_fused(test_data)
            
            # Check if both decompress to original
            decompressed_orig = engine.decompress_chained(compressed_original)
            decompressed_opt = engine.decompress_chained(compressed_optimized)
            
            # Both should equal original
            orig_correct = decompressed_orig == test_data
            opt_correct = decompressed_opt == test_data
            
            if orig_correct and opt_correct:
                print(f"  ✓ Both pipelines decompress correctly")
                print(f"    Original compression ratio: {len(test_data) / len(compressed_original):.2f}x")
                print(f"    Optimized compression ratio: {len(test_data) / len(compressed_optimized):.2f}x")
            else:
                print(f"  ✗ FAILED")
                if not orig_correct:
                    print(f"    Original decompression incorrect")
                if not opt_correct:
                    print(f"    Optimized decompression incorrect")
                all_pass = False
                
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            all_pass = False
    
    print(f"\n{'='*80}")
    if all_pass:
        print(f"✓ All correctness tests PASSED")
    else:
        print(f"✗ Some correctness tests FAILED")
    
    return all_pass


# ============================================================================
# MAIN BENCHMARK SUITE
# ============================================================================

def run_full_benchmark_suite(engine):
    """Run complete optimization benchmark"""
    print(f"\n{'#'*80}")
    print(f"# COBOL PROTOCOL - LATENCY OPTIMIZATION BENCHMARK")
    print(f"#{'#'*78}#")
    print(f"{'#'*80}")
    
    results = {}
    
    # 1. Correctness (must pass first)
    print(f"\n### Phase 1: Correctness Validation ###")
    if not benchmark_correctness_test(engine):
        print(f"\n✗ FAILED: Optimization breaks compression correctness")
        return
    
    # 2. Microbenchmark on various data sizes
    print(f"\n### Phase 2: Microbenchmark (Original vs Optimized) ###")
    for size_kb in [10, 64, 256]:
        test_data = generate_test_data(size_kb * 1024)
        result = benchmark_original_vs_optimized(engine, test_data, num_runs=20)
        results[f'micro_{size_kb}kb'] = result
    
    # 3. Scale test
    print(f"\n### Phase 3: Scale Test (1000+ Requests) ###")
    scale_result = benchmark_scale_test(engine, request_count=1000, chunk_size_bytes=65536)
    results['scale_test'] = scale_result
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    
    # Collect improvement percentages
    improvements = []
    for key, result in results.items():
        if isinstance(result, dict) and 'improvement_pct' in result:
            improvements.append(result['improvement_pct'])
    
    if improvements:
        avg_improvement = statistics.mean(improvements)
        print(f"\nAverage improvement across microbenchmarks: {avg_improvement:.1f}%")
        print(f"Target: 20-45%")
        
        if avg_improvement >= 20:
            print(f"✓ TARGET ACHIEVED ({avg_improvement:.1f}% >= 20%)")
        else:
            print(f"⚠ Below target ({avg_improvement:.1f}% < 20%)")
    
    print(f"\n{'='*80}")
    return results


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Try to import engine
    try:
        from engine import CobolEngine
        print("Loading COBOL Engine...")
        engine = CobolEngine()
        print("✓ Engine loaded")
    except ImportError as e:
        print(f"ERROR: Cannot import CobolEngine: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot initialize engine: {e}")
        sys.exit(1)
    
    # Run benchmark
    try:
        results = run_full_benchmark_suite(engine)
        if results:
            print(f"\n✓ Benchmark complete")
    except Exception as e:
        print(f"\n✗ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
