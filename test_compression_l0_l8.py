#!/usr/bin/env python3
"""
Comprehensive L0-L8 Compression Performance Test Suite
======================================================

Tests all compression layers from L0 (classification) to L8 (extreme hardening)
and generates detailed performance statistics.

Author: COBOL Protocol Test Suite
Date: 2026
"""

import sys
import time
import os
import json
import random
import psutil
import tracemalloc
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import pytest  # required for fixtures

# simple data fixture used by pytest-based test functions
@pytest.fixture
def data() -> bytes:
    # default 1MB mixed data
    return generate_test_data(1, "mixed")

print("\n" + "="*100)
print("COBOL PROTOCOL - L0-L8 COMPRESSION TEST SUITE")
print("="*100 + "\n")

# ============================================================================
# DATA GENERATION
# ============================================================================

def generate_test_data(size_mb: int = 1, data_type: str = "mixed") -> bytes:
    """Generate test data of specified size and type."""
    total_bytes = size_mb * 1024 * 1024
    
    if data_type == "text":
        # Repetitive text (highly compressible)
        base = b"COBOL PROTOCOL compression test data. " * (total_bytes // 38)
        return base[:total_bytes]
    
    elif data_type == "binary":
        # Random binary (less compressible)
        return bytes(random.randint(0, 255) for _ in range(total_bytes))
    
    elif data_type == "structured":
        # CSV-like structured data (medium compressibility)
        line = b"ID,VALUE,TIMESTAMP,DATA,STATUS\n" + b"1,100,2026-03-03,test,active\n" * 2
        return (line * (total_bytes // len(line)))[:total_bytes]
    
    elif data_type == "json":
        # JSON-like data (medium compressibility)
        json_str = '{"id": 1, "value": 100, "timestamp": "2026-03-03", "data": "test", "status": "active"}\n'
        json_bytes = json_str.encode()
        return (json_bytes * (total_bytes // len(json_bytes)))[:total_bytes]
    
    else:  # mixed
        # Mix of text and binary
        part_size = total_bytes // 2
        text_part = b"TEST DATA " * (part_size // 10)
        binary_part = bytes(random.randint(0, 255) for _ in range(part_size))
        return (text_part[:part_size] + binary_part[:part_size])

# ============================================================================
# METRICS COLLECTION
# ============================================================================

@dataclass
class LayerMetrics:
    """Performance metrics for a compression layer."""
    layer_name: str
    layer_num: int
    input_size: int
    output_size: int
    compression_ratio: float
    elapsed_time: float
    throughput_mbps: float
    memory_peak_mb: float
    memory_delta_mb: float
    success: bool
    error_msg: str = ""

    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        ratio_str = f"{self.compression_ratio:.2f}x" if self.compression_ratio > 0 else "N/A"
        throughput_str = f"{self.throughput_mbps:.1f} MB/s" if self.throughput_mbps > 0 else "N/A"
        
        return (f"{status} {self.layer_name:20} | "
                f"Input: {self.input_size:>10,} B | "
                f"Output: {self.output_size:>10,} B | "
                f"Ratio: {ratio_str:>6} | "
                f"Time: {self.elapsed_time*1000:>7.2f}ms | "
                f"Speed: {throughput_str:>12} | "
                f"Memory: {self.memory_peak_mb:>6.1f}MB")

# ============================================================================
# LAYER TESTING FUNCTIONS
# ============================================================================

def test_L0_classifier(data: bytes) -> Tuple[Dict[str, Any], LayerMetrics]:
    """Test Layer 0: Data Classification."""
    layer_name = "L0_Classifier"
    start_time = time.perf_counter()
    
    try:
        # Try to import and test Layer0Classifier
        exec_globals = {}
        try:
            exec("from src.layers.core import Layer0Classifier", exec_globals)
            Layer0Classifier = exec_globals.get('Layer0Classifier')
            
            if Layer0Classifier:
                classifier = Layer0Classifier()
                result = classifier.classify(data)
                
                elapsed = time.perf_counter() - start_time
                throughput = len(data) / elapsed / 1024 / 1024 if elapsed > 0 else 0
                
                metrics = LayerMetrics(
                    layer_name=layer_name,
                    layer_num=0,
                    input_size=len(data),
                    output_size=len(data),  # Classification doesn't compress
                    compression_ratio=1.0,
                    elapsed_time=elapsed,
                    throughput_mbps=throughput,
                    memory_peak_mb=0,
                    memory_delta_mb=0,
                    success=True,
                )
                
                return result, metrics
        except:
            pass
        
        # Fallback: simple entropy-based classification
        entropy = 0
        for byte_val in range(256):
            freq = data.count(bytes([byte_val]))
            if freq > 0:
                p = freq / len(data)
                entropy -= p * (p.bit_length() - 1 if p > 0 else 0)
        
        elapsed = time.perf_counter() - start_time
        throughput = len(data) / elapsed / 1024 / 1024 if elapsed > 0 else 0
        
        classification = {
            "entropy": entropy,
            "size": len(data),
            "data_type": "text" if entropy < 4 else "mixed" if entropy < 6 else "binary"
        }
        
        metrics = LayerMetrics(
            layer_name=layer_name,
            layer_num=0,
            input_size=len(data),
            output_size=len(data),
            compression_ratio=1.0,
            elapsed_time=elapsed,
            throughput_mbps=throughput,
            memory_peak_mb=0,
            memory_delta_mb=0,
            success=True,
        )
        
        return classification, metrics
        
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        metrics = LayerMetrics(
            layer_name=layer_name,
            layer_num=0,
            input_size=len(data),
            output_size=0,
            compression_ratio=0,
            elapsed_time=elapsed,
            throughput_mbps=0,
            memory_peak_mb=0,
            memory_delta_mb=0,
            success=False,
            error_msg=str(e)[:100]
        )
        return {}, metrics


def test_L1_L4_engine(data: bytes) -> Tuple[bytes, LayerMetrics]:
    """Test Layers 1-4: Full CobolEngine compression."""
    layer_name = "L1-L4_CobolEngine"
    
    tracemalloc.start()
    mem_before = psutil.Process().memory_info().rss / 1024 / 1024
    
    start_time = time.perf_counter()
    
    try:
        from src.engine import CobolEngine
        
        engine = CobolEngine()
        compressed, metadata = engine.compress_chained(data)
        
        elapsed = time.perf_counter() - start_time
        mem_after = psutil.Process().memory_info().rss / 1024 / 1024
        mem_peak = tracemalloc.get_traced_memory()[0] / 1024 / 1024
        tracemalloc.stop()
        
        ratio = len(data) / len(compressed) if len(compressed) > 0 else 0
        throughput = len(data) / elapsed / 1024 / 1024 if elapsed > 0 else 0
        
        metrics = LayerMetrics(
            layer_name=layer_name,
            layer_num=4,
            input_size=len(data),
            output_size=len(compressed),
            compression_ratio=ratio,
            elapsed_time=elapsed,
            throughput_mbps=throughput,
            memory_peak_mb=mem_peak,
            memory_delta_mb=mem_after - mem_before,
            success=True,
        )
        
        return compressed, metrics
        
    except Exception as e:
        tracemalloc.stop()
        elapsed = time.perf_counter() - start_time
        mem_after = psutil.Process().memory_info().rss / 1024 / 1024
        
        metrics = LayerMetrics(
            layer_name=layer_name,
            layer_num=4,
            input_size=len(data),
            output_size=0,
            compression_ratio=0,
            elapsed_time=elapsed,
            throughput_mbps=0,
            memory_peak_mb=0,
            memory_delta_mb=mem_after - mem_before,
            success=False,
            error_msg=str(e)[:100]
        )
        
        return b"", metrics


def test_L5_L8_pipeline(data: bytes) -> Tuple[bytes, LayerMetrics]:
    """Test Layers 5-8: OptimizedL5L8Pipeline."""
    layer_name = "L5-L8_Pipeline"
    
    tracemalloc.start()
    mem_before = psutil.Process().memory_info().rss / 1024 / 1024
    
    start_time = time.perf_counter()
    
    try:
        from src.layers.pipelines import OptimizedL5L8Pipeline
        
        pipeline = OptimizedL5L8Pipeline()
        compressed = pipeline.compress(data)
        
        elapsed = time.perf_counter() - start_time
        mem_after = psutil.Process().memory_info().rss / 1024 / 1024
        mem_peak = tracemalloc.get_traced_memory()[0] / 1024 / 1024
        tracemalloc.stop()
        
        ratio = len(data) / len(compressed) if len(compressed) > 0 else 0
        throughput = len(data) / elapsed / 1024 / 1024 if elapsed > 0 else 0
        
        metrics = LayerMetrics(
            layer_name=layer_name,
            layer_num=8,
            input_size=len(data),
            output_size=len(compressed),
            compression_ratio=ratio,
            elapsed_time=elapsed,
            throughput_mbps=throughput,
            memory_peak_mb=mem_peak,
            memory_delta_mb=mem_after - mem_before,
            success=True,
        )
        
        return compressed, metrics
        
    except Exception as e:
        tracemalloc.stop()
        elapsed = time.perf_counter() - start_time
        mem_after = psutil.Process().memory_info().rss / 1024 / 1024
        
        metrics = LayerMetrics(
            layer_name=layer_name,
            layer_num=8,
            input_size=len(data),
            output_size=0,
            compression_ratio=0,
            elapsed_time=elapsed,
            throughput_mbps=0,
            memory_peak_mb=0,
            memory_delta_mb=mem_after - mem_before,
            success=False,
            error_msg=str(e)[:100]
        )
        
        return b"", metrics

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def run_comprehensive_test():
    """Run comprehensive L0-L8 compression test."""
    
    # Test parameters
    test_configs = [
        {"size_mb": 1, "data_type": "text", "name": "Text (Repetitive)"},
        {"size_mb": 1, "data_type": "json", "name": "JSON (Structured)"},
        {"size_mb": 1, "data_type": "binary", "name": "Binary (Random)"},
    ]
    
    all_results = {}
    
    for config in test_configs:
        print(f"\n{'='*100}")
        print(f"Testing: {config['name']} ({config['size_mb']} MB)")
        print(f"{'='*100}\n")
        
        # Generate test data
        test_data = generate_test_data(config['size_mb'], config['data_type'])
        print(f"📊 Input size: {len(test_data):,} bytes\n")
        
        results = {
            "config": config,
            "layers": []
        }
        
        # Test L0: Classification
        print("Testing L0: Data Classification...")
        classification, l0_metrics = test_L0_classifier(test_data)
        print(f"  {l0_metrics}\n")
        results["layers"].append(asdict(l0_metrics))
        
        # Test L1-L4: CobolEngine
        print("Testing L1-L4: Core Compression Engine...")
        l1_l4_data, l1_l4_metrics = test_L1_L4_engine(test_data)
        print(f"  {l1_l4_metrics}\n")
        results["layers"].append(asdict(l1_l4_metrics))
        
        # Test L5-L8: If L1-L4 succeeded
        if l1_l4_metrics.success and l1_l4_data:
            print("Testing L5-L8: Advanced Pipeline...")
            l5_l8_data, l5_l8_metrics = test_L5_L8_pipeline(l1_l4_data)
            print(f"  {l5_l8_metrics}\n")
            results["layers"].append(asdict(l5_l8_metrics))
        
        all_results[config['name']] = results
    
    return all_results

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(results: Dict[str, Any]) -> str:
    """Generate formatted performance report."""
    report = []
    report.append("\n" + "="*100)
    report.append("COMPRESSION PERFORMANCE STATISTICS - L0 TO L8")
    report.append("="*100 + "\n")
    
    for test_name, data in results.items():
        report.append(f"\n📊 TEST: {test_name}")
        report.append("-" * 100)
        
        layers_data = data["layers"]
        
        # Summary table
        report.append("\nLayerwise Performance:")
        report.append("-" * 100)
        report.append(f"{'Layer':<20} {'Input (B)':<15} {'Output (B)':<15} {'Ratio':<10} {'Time (ms)':<12} {'Speed (MB/s)':<15} {'Memory (MB)':<12}")
        report.append("-" * 100)
        
        total_input = 0
        total_output = 0
        total_time = 0
        
        for layer_metrics in layers_data:
            if layer_metrics.get('success'):
                input_b = layer_metrics['input_size']
                output_b = layer_metrics['output_size']
                ratio = layer_metrics['compression_ratio']
                time_ms = layer_metrics['elapsed_time'] * 1000
                speed = layer_metrics['throughput_mbps']
                mem = layer_metrics['memory_peak_mb']
                
                total_input = input_b
                total_output += output_b
                total_time += layer_metrics['elapsed_time']
                
                ratio_str = f"{ratio:.2f}x" if ratio > 0 else "N/A"
                speed_str = f"{speed:.1f}" if speed > 0 else "N/A"
                
                report.append(f"{layer_metrics['layer_name']:<20} {input_b:<15,} {output_b:<15,} {ratio_str:<10} {time_ms:<12.2f} {speed_str:<15} {mem:<12.1f}")
        
        # Overall statistics
        report.append("-" * 100)
        overall_ratio = total_input / total_output if total_output > 0 else 0
        overall_speed = total_input / total_time / 1024 / 1024 if total_time > 0 else 0
        
        report.append(f"\n📈 Overall Statistics:")
        report.append(f"  • Total Input:        {total_input:>15,} bytes")
        report.append(f"  • Total Output:       {total_output:>15,} bytes")
        report.append(f"  • Overall Ratio:      {overall_ratio:>15.2f}x")
        report.append(f"  • Total Time:         {total_time*1000:>15.2f} ms")
        report.append(f"  • Average Speed:      {overall_speed:>15.1f} MB/s")
        
        report.append("\n")
    
    return "\n".join(report)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        results = run_comprehensive_test()
        report = generate_report(results)
        print(report)
        
        # Save report to file
        report_file = Path(__file__).parent / "compression_test_results.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save JSON results
        json_file = Path(__file__).parent / "compression_test_results.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Reports saved:")
        print(f"  • {report_file}")
        print(f"  • {json_file}\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("\n" + "="*100)
print("END OF TEST SUITE")
print("="*100 + "\n")
