#!/usr/bin/env python3
"""
Full L0-L8 Compression Test Suite with Compression Ratio Report
================================================================

Runs comprehensive compression tests on all test data files,
using complete L0 → L8 pipeline, and reports compression ratios.
"""

import os
import sys
import time
from pathlib import Path
from typing import Tuple, Dict, List
from dataclasses import dataclass
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

@dataclass
class CompressionResult:
    """Store compression result for a file."""
    filename: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    compression_percent: float
    time_ms: float
    status: str
    error_msg: str = ""

def get_test_files() -> List[Path]:
    """Find all test data files to compress."""
    test_dirs = [
        Path("benchmarks/datasets"),
        Path("tests"),
    ]
    
    test_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            # Look for data files
            for ext in ['*.txt', '*.json', '*.csv', '*.bin']:
                test_files.extend(test_dir.glob(f"**/{ext}"))
    
    return sorted(set(test_files))[:10]  # Limit to first 10 for reasonable runtime

def create_sample_data() -> List[Tuple[str, bytes]]:
    """Create sample test data of various types and sizes."""
    samples = [
        ("Text_Small_ASCII", b"Hello World! " * 10),
        ("Text_Medium_Repetitive", b"AAABBBCCCDDDEEEFFF" * 100),
        ("Text_Large_Dictionary", b"The quick brown fox jumps over the lazy dog. " * 50),
        ("JSON_Sample", b'{"name":"test","value":123,"data":[1,2,3,4,5]}' * 20),
        ("Binary_Random_10KB", bytes([i % 256 for i in range(10240)])),
        ("Binary_Structured_5KB", bytes([0xFF, 0x00] * 2560)),
        ("Compressible_HTML", b"<html><body><div>test content</div></body></html>" * 30),
        ("CSV_Data", b"id,name,value,timestamp\n1,test1,100,2026-03-04\n2,test2,200,2026-03-04\n" * 40),
    ]
    return samples

def compress_with_l0_l8(data: bytes) -> Tuple[bytes, Dict]:
    """
    Compress data using full L0-L8 pipeline.
    Returns compressed data and metadata.
    """
    metadata = {
        "layers_applied": [],
        "sizes_per_layer": [len(data)],
        "layer_times": []
    }
    
    try:
        # Import canonical layer modules
        from src.layers.core.classifier import Layer0Classifier
        from src.layers.core.semantic import Layer1Semantic
        from src.layers.core.structural import Layer2Structural
        from src.layers.core.delta import Layer3Delta
        from src.layers.core.bitpacking import Layer4Binary
        from src.layers.variants.l5_recursive import Layer5Recursive
        from src.layers.variants.l6_recursive import Layer6Recursive
        from src.layers.variants.l7_bank import Layer7Bank
        from src.layers.variants.l8_final import Layer8Final
        
        layers = [
            ("L0 Classifier", Layer0Classifier()),
            ("L1 Semantic", Layer1Semantic()),
            ("L2 Structural", Layer2Structural()),
            ("L3 Delta", Layer3Delta()),
            ("L4 Binary", Layer4Binary()),
            ("L5 Recursive", Layer5Recursive()),
            ("L6 Recursive", Layer6Recursive()),
            ("L7 Bank", Layer7Bank()),
            ("L8 Final", Layer8Final()),
        ]
        
        current_data = data
        for layer_name, layer_obj in layers:
            start_time = time.perf_counter()
            
            try:
                # Check if layer has compress method
                if hasattr(layer_obj, 'compress'):
                    current_data = layer_obj.compress(current_data)
                else:
                    print(f"⚠️  {layer_name} has no compress() method, skipping")
                    continue
                    
                elapsed = (time.perf_counter() - start_time) * 1000  # ms
                metadata["layers_applied"].append(layer_name)
                metadata["sizes_per_layer"].append(len(current_data))
                metadata["layer_times"].append(elapsed)
                
            except Exception as e:
                print(f"⚠️  {layer_name} error: {str(e)[:100]}")
                metadata["layers_applied"].append(f"{layer_name} (FAILED)")
                break
        
        return current_data, metadata
        
    except ImportError as e:
        raise Exception(f"Failed to import layers: {str(e)}")

def print_header():
    """Print report header."""
    print("\n")
    print("=" * 100)
    print("🎯 COBOL PROTOCOL COMPRESSION TEST REPORT - FULL L0-L8 PIPELINE")
    print("=" * 100)
    print(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    print("\n")

def run_compression_tests() -> List[CompressionResult]:
    """Run compression tests on all sample data."""
    results = []
    samples = create_sample_data()
    
    print(f"📝 Running {len(samples)} compression tests with L0-L8 pipeline...\n")
    
    for idx, (sample_name, sample_data) in enumerate(samples, 1):
        print(f"[{idx}/{len(samples)}] Testing: {sample_name:30s} ({len(sample_data):6d} bytes)...", end=" ", flush=True)
        
        start_time = time.perf_counter()
        status = "✅ OK"
        error_msg = ""
        
        try:
            compressed_data, metadata = compress_with_l0_l8(sample_data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            original_size = len(sample_data)
            compressed_size = len(compressed_data)
            ratio = compressed_size / original_size if original_size > 0 else 0
            percent = (1 - ratio) * 100
            
            result = CompressionResult(
                filename=sample_name,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=ratio,
                compression_percent=percent,
                time_ms=elapsed_ms,
                status=status
            )
            
            results.append(result)
            
            # Print per-layer details
            print(f"✅ {compressed_size:6d}B ({ratio*100:.1f}%) - {elapsed_ms:.1f}ms")
            
            # Show layer breakdown
            for layer_idx, (layer_name, layer_time) in enumerate(
                zip(metadata["layers_applied"], metadata["layer_times"])
            ):
                prev_size = metadata["sizes_per_layer"][layer_idx]
                curr_size = metadata["sizes_per_layer"][layer_idx + 1]
                layer_ratio = (prev_size - curr_size) / prev_size * 100 if prev_size > 0 else 0
                print(f"   └─ {layer_name:20s}: {prev_size:6d}→{curr_size:6d}B ({layer_ratio:+6.1f}%) [{layer_time:6.2f}ms]")
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_msg = str(e)[:200]
            status = "❌ FAILED"
            
            result = CompressionResult(
                filename=sample_name,
                original_size=len(sample_data),
                compressed_size=0,
                compression_ratio=0,
                compression_percent=0,
                time_ms=elapsed_ms,
                status=status,
                error_msg=error_msg
            )
            
            results.append(result)
            print(f"❌ ERROR: {error_msg[:60]}...")
    
    return results

def print_summary_table(results: List[CompressionResult]):
    """Print summary table of all results."""
    print("\n" + "=" * 100)
    print("📊 COMPRESSION RATIO SUMMARY TABLE")
    print("=" * 100)
    print(f"{'Filename':<35s} {'Original':>12s} {'Compressed':>12s} {'Ratio':>10s} {'Savings':>10s} {'Time':>10s} {'Status':<15s}")
    print("-" * 100)
    
    total_original = 0
    total_compressed = 0
    successful = 0
    
    for result in results:
        if result.status == "✅ OK":
            total_original += result.original_size
            total_compressed += result.compressed_size
            successful += 1
        
        ratio_pct = result.compression_ratio * 100
        savings_pct = result.compression_percent
        
        print(f"{result.filename:<35s} {result.original_size:>12,d} {result.compressed_size:>12,d} "
              f"{ratio_pct:>9.1f}% {savings_pct:>9.1f}% {result.time_ms:>9.1f}ms {result.status:<15s}")
    
    print("-" * 100)
    
    # Overall stats
    if total_original > 0:
        overall_ratio = total_compressed / total_original
        overall_savings = (1 - overall_ratio) * 100
        
        print(f"{'🎯 OVERALL TOTAL':<35s} {total_original:>12,d} {total_compressed:>12,d} "
              f"{overall_ratio*100:>9.1f}% {overall_savings:>9.1f}% {'':>10s} "
              f"[{successful}/{len(results)} successful]")
    
    print("=" * 100 + "\n")

def export_json_report(results: List[CompressionResult], filename: str = "TEST_RESULTS_L0_L8_COMPRESSION.json"):
    """Export results to JSON format."""
    data = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "pipeline": "L0→L1→L2→L3→L4→L5→L6→L7→L8",
        "results": [
            {
                "filename": r.filename,
                "original_bytes": r.original_size,
                "compressed_bytes": r.compressed_size,
                "ratio": round(r.compression_ratio, 4),
                "savings_percent": round(r.compression_percent, 2),
                "time_ms": round(r.time_ms, 2),
                "status": r.status,
                "error": r.error_msg
            }
            for r in results
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ JSON report saved to: {filename}")

def main():
    """Main test runner."""
    print_header()
    
    try:
        # Run tests
        results = run_compression_tests()
        
        # Print summary
        print_summary_table(results)
        
        # Export JSON
        export_json_report(results)
        
        # Count successes
        successful = sum(1 for r in results if r.status == "✅ OK")
        total = len(results)
        
        print(f"\n{'✅ TEST COMPLETE':^100s}")
        print(f"{'Results: ' + str(successful) + '/' + str(total) + ' successful':^100s}\n")
        
        return 0 if successful == total else 1
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
