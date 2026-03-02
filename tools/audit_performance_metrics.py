#!/usr/bin/env python3
"""Performance & Metrics Audit for COBOL Multi-Layer Compression System.

Measures:
- Throughput (MB/s)
- CPU usage (%)
- Memory footprint (MB)
- Energy efficiency (J/MB) via src/energy_aware_execution.py
"""
import sys
import time
import psutil
import json
import pathlib
import statistics
from typing import Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from src import (
    huffman_parallel,
    layer1_semantic,
    layer2_structural,
    layer3_delta,
    layer4_binary,
    layer5_recursive,
    layer6_recursive,
    layer7_bank,
    layer8_final,
    engine,
    protocol_bridge,
)

try:
    from src import energy_aware_execution
    HAS_ENERGY = True
except ImportError:
    HAS_ENERGY = False

# Test data
SMALL_DATA = b"Hello world! " * 100  # ~1.3 KB
MEDIUM_DATA = b"The quick brown fox jumps over the lazy dog. " * 1000  # ~45 KB
LARGE_DATA = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10000  # ~570 KB

class PerformanceAuditor:
    """Audit performance metrics across compression algorithms."""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.process = psutil.Process()
    
    def measure_compression(
        self, name: str, compressor, data: bytes, iterations: int = 3
    ) -> Dict:
        """Measure compression performance metrics."""
        
        # Detect compression method
        compress_method = None
        decompress_method = None
        use_buffer = False
        
        # Check for compress/decompress
        if hasattr(compressor, 'compress') and callable(compressor.compress):
            compress_method = compressor.compress
            decompress_method = compressor.decompress
        # Check for encode/decode (Layer methods)
        elif hasattr(compressor, 'encode') and callable(compressor.encode):
            compress_method = compressor.encode
            decompress_method = compressor.decode
            use_buffer = True
        # Check for compress_block/decompress_block
        elif hasattr(compressor, 'compress_block') and callable(compressor.compress_block):
            compress_method = compressor.compress_block
            decompress_method = compressor.decompress_block
        else:
            raise ValueError(f"No suitable compression method found on {type(compressor)}")
        
        throughputs = []
        cpu_usages = []
        memory_deltas = []
        compression_ratios = []
        
        for _ in range(iterations):
            # Baseline
            self.process.memory_info()  # warm cache
            mem_before = self.process.memory_info().rss / 1024 / 1024  # MB
            cpu_before = psutil.cpu_percent(interval=0.05)
            t_start = time.perf_counter()
            
            # Prepare input (TypedBuffer if needed)
            if use_buffer:
                input_data = protocol_bridge.TypedBuffer.create(
                    data, protocol_bridge.ProtocolLanguage.L1_SEM, bytes
                )
            else:
                input_data = data
            
            # Compress
            compressed = compress_method(input_data)
            
            # Extract bytes for size calculation
            if use_buffer and hasattr(compressed, 'data'):
                # For TypedBuffer, estimate size of contained data
                result_size = len(str(compressed.data).encode()) if isinstance(compressed.data, (str, list)) else len(compressed.data)
            else:
                result_size = len(compressed) if isinstance(compressed, bytes) else len(str(compressed).encode())
            
            # Measure
            t_elapsed = time.perf_counter() - t_start
            mem_after = self.process.memory_info().rss / 1024 / 1024  # MB
            cpu_after = psutil.cpu_percent(interval=0.05)
            
            # Compute metrics
            throughput = len(data) / (t_elapsed * 1024 * 1024) if t_elapsed > 0 else 0  # MB/s
            memory_delta = mem_after - mem_before  # MB
            cpu_usage = (cpu_before + cpu_after) / 2  # %
            compression_ratio = result_size / len(data) if len(data) > 0 else 0  # ratio
            
            throughputs.append(throughput)
            cpu_usages.append(cpu_usage)
            memory_deltas.append(memory_delta)
            compression_ratios.append(compression_ratio)
        
        # Decompression
        decomp_throughputs = []
        decomp_times = []
        for _ in range(iterations):
            # Prepare input
            if use_buffer:
                input_data = protocol_bridge.TypedBuffer.create(
                    data, protocol_bridge.ProtocolLanguage.L1_SEM, bytes
                )
            else:
                input_data = data
            
            compressed = compress_method(input_data)
            t_start = time.perf_counter()
            _ = decompress_method(compressed)
            t_elapsed = time.perf_counter() - t_start
            decomp_throughput = len(data) / (t_elapsed * 1024 * 1024) if t_elapsed > 0 else 0
            decomp_throughputs.append(decomp_throughput)
            decomp_times.append(t_elapsed)
        
        # Estimate energy (if available)
        energy_score = None
        if HAS_ENERGY:
            try:
                ctrl = energy_aware_execution.EnergyAwareCompressionController()
                avg_ratio = statistics.mean(compression_ratios)
                avg_time = statistics.mean([t / 1000 for t in [t * 1000 for t in throughputs]])  # convert back
                energy_score = ctrl.estimate_joules_per_mb(avg_ratio, avg_time) if hasattr(ctrl, 'estimate_joules_per_mb') else None
            except Exception:
                energy_score = None
        
        return {
            'name': name,
            'data_size_kb': len(data) / 1024,
            'compress': {
                'avg_throughput_mbs': statistics.mean(throughputs),
                'stdev_throughput_mbs': statistics.stdev(throughputs) if len(throughputs) > 1 else 0,
                'avg_cpu_percent': statistics.mean(cpu_usages),
                'avg_memory_delta_mb': statistics.mean(memory_deltas),
                'avg_compression_ratio': statistics.mean(compression_ratios),
            },
            'decompress': {
                'avg_throughput_mbs': statistics.mean(decomp_throughputs),
                'stdev_throughput_mbs': statistics.stdev(decomp_throughputs) if len(decomp_throughputs) > 1 else 0,
                'avg_time_seconds': statistics.mean(decomp_times),
            },
            'energy_score_jmb': energy_score,
            'iterations': iterations,
        }
    
    def audit(self):
        """Run full audit on key algorithms."""
        
        print("=" * 100)
        print("PERFORMANCE & METRICS AUDIT - COBOL Multi-Layer Compression System")
        print("=" * 100)
        
        # Dictionary of algorithms to test
        algorithms = {
            'Layer 1 (Semantic)': layer1_semantic.Layer1Semantic(),
            'Layer 2 (Structural)': layer2_structural.Layer2Structural(),
            'Layer 3 (Delta)': layer3_delta.Layer3Delta(),
            'Layer 4 (Binary)': layer4_binary.Layer4Binary(),
            'Layer 5 (Recursive)': layer5_recursive.Layer5Recursive(),
            'Layer 6 (Recursive)': layer6_recursive.Layer6Recursive(),
            'Layer 7 (Bank)': layer7_bank.Layer7Bank(),
            'Layer 8 (Final)': layer8_final.Layer8Final(),
        }
        
        # Test each algorithm on different data sizes
        test_sets = [
            ('Small', SMALL_DATA),
            ('Medium', MEDIUM_DATA),
            ('Large', LARGE_DATA),
        ]
        
        print("\n📊 RUNNING PERFORMANCE MEASUREMENTS...\n")
        
        for alg_name, compressor in algorithms.items():
            print(f"Testing {alg_name}...")
            self.results[alg_name] = {}
            
            for data_label, data in test_sets:
                try:
                    result = self.measure_compression(
                        f"{alg_name} - {data_label}",
                        compressor,
                        data,
                        iterations=3
                    )
                    self.results[alg_name][data_label] = result
                except Exception as e:
                    print(f"  ⚠️  {data_label}: Error — {str(e)[:80]}")
                    self.results[alg_name][data_label] = {'error': str(e)}
        
        self.print_report()
        self.save_results()
    
    def print_report(self):
        """Print human-readable performance report."""
        
        print("\n" + "=" * 100)
        print("PERFORMANCE AUDIT RESULTS")
        print("=" * 100)
        
        for alg_name, sizes in self.results.items():
            print(f"\n{'='*80}")
            print(f"  {alg_name}")
            print(f"{'='*80}")
            
            for size_label, metrics in sizes.items():
                if 'error' in metrics:
                    print(f"  {size_label}: ERROR")
                    continue
                
                print(f"\n  {size_label} Data ({metrics['data_size_kb']:.1f} KB)")
                print(f"    Compression:")
                print(f"      • Throughput: {metrics['compress']['avg_throughput_mbs']:.2f} ± {metrics['compress']['stdev_throughput_mbs']:.2f} MB/s")
                print(f"      • CPU Usage: {metrics['compress']['avg_cpu_percent']:.1f}%")
                print(f"      • Memory Delta: {metrics['compress']['avg_memory_delta_mb']:.2f} MB")
                print(f"      • Compression Ratio: {metrics['compress']['avg_compression_ratio']:.2%}")
                
                print(f"    Decompression:")
                print(f"      • Throughput: {metrics['decompress']['avg_throughput_mbs']:.2f} ± {metrics['decompress']['stdev_throughput_mbs']:.2f} MB/s")
                print(f"      • Time: {metrics['decompress']['avg_time_seconds']*1000:.2f} ms")
                
                if metrics['energy_score_jmb']:
                    print(f"    Energy:")
                    print(f"      • Efficiency: {metrics['energy_score_jmb']:.4f} J/MB")
    
    def save_results(self):
        """Save results to JSON."""
        output_path = pathlib.Path('performance_audit_results.json')
        output_path.write_text(json.dumps(self.results, indent=2))
        print(f"\n✅ Results saved to {output_path}")

if __name__ == '__main__':
    auditor = PerformanceAuditor()
    auditor.audit()
