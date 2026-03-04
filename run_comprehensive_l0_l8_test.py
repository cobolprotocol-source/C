#!/usr/bin/env python3
"""
COBOL Protocol Compression Test Suite - Full L0-L8 Pipeline
============================================================

Runs comprehensive compression tests using the canonical 
CobolPipeline (L0 → L1 → L2 → L3 → L4 → L5 → L6 → L7 → L8)
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Tuple
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
    layers_used: str = "L0-L8"
    error_msg: str = ""

def create_sample_data() -> List[Tuple[str, bytes]]:
    """Create diverse test data samples."""
    samples = [
        ("00_Text_Small_ASCII", b"Hello World! " * 10),
        ("01_Text_Repetitive", b"AAABBBCCCDDDEEEFFF" * 100),
        ("02_Text_Lorem_ipsum", (b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " 
         b"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ") * 20),
        ("03_JSON_Data", b'{"name":"test","value":123,"array":[1,2,3,4,5],"status":"active"}' * 15),
        ("04_Binary_Random", bytes([i % 256 for i in range(8192)])),
        ("05_Binary_Structured", bytes([0xFF, 0x00] * 2048)),
        ("06_HTML_Markup", b"<div class='container'><p>test content</p></div>" * 25),
        ("07_CSV_Records", b"id,name,value,date\n1,test1,100,2026-03-04\n2,test2,200,2026-03-04\n" * 30),
        ("08_Mixed_Content", b"text mixed\x00\x01\x02binary\xFF\xFE\xFD data here" * 50),
        ("09_Large_Repetitive", b"X" * 16384),
    ]
    return samples

def print_header():
    """Print test report header."""
    header = """
╔════════════════════════════════════════════════════════════════════════════════╗
║                   COBOL PROTOCOL COMPRESSION TEST REPORT                       ║
║                        Full L0-L8 Pipeline Compression                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

Test Configuration:
  Pipeline: L0 (Classifier) → L1 (Semantic) → L2 (Structural) → L3 (Delta) →
            L4 (Binary) → L5 (Recursive) → L6 (Recursive) → L7 (Bank) → L8 (Final)
  Mode: Sequential (canonical implementation)
  Timestamp: {0}

""".format(time.strftime('%Y-%m-%d %H:%M:%S'))
    
    print(header)

def compress_with_pipeline(data: bytes) -> Tuple[bytes, dict]:
    """
    Compress using CobolPipeline (official interface).
    Returns tuple of (compressed_data, metadata)
    """
    from src.layers.pipelines.engine import CobolPipeline
    
    pipeline = CobolPipeline()
    result = pipeline.compress(data)
    
    # PipelineResult has: compressed_data, original_size, final_size, ratio, per_layer_stats
    metadata = {
        "ratio": result.ratio,
        "original_size": result.original_size,
        "final_size": result.final_size,
        "layers": len(result.per_layer_stats) if hasattr(result, 'per_layer_stats') else 8,
        "checksum": result.checksum if hasattr(result, 'checksum') else None
    }
    
    return result.compressed_data, metadata

def run_tests() -> List[CompressionResult]:
    """Run all compression tests."""
    results = []
    samples = create_sample_data()
    
    print(f"📝 Running {len(samples)} compression tests...\n")
    print(f"{'#':<3} {'Test Name':<29} {'Original':>12} {'Compressed':>12} "
          f"{'Ratio':>10} {'Time':>8} {'Status':<10}")
    print("─" * 100)
    
    for idx, (test_name, sample_data) in enumerate(samples, 1):
        original_size = len(sample_data)
        
        try:
            start_time = time.perf_counter()
            compressed_data, metadata = compress_with_pipeline(sample_data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            compressed_size = len(compressed_data)
            ratio = compressed_size / original_size if original_size > 0 else 1.0
            savings_percent = (1 - ratio) * 100
            
            status = "✅ OK"
            result = CompressionResult(
                filename=test_name,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=ratio,
                compression_percent=savings_percent,
                time_ms=elapsed_ms,
                status=status,
                error_msg=""
            )
            results.append(result)
            
            # Print result line
            max_name_len = 26
            name_display = test_name[:max_name_len]
            ratio_pct = ratio * 100
            
            print(f"{idx:<3} {name_display:<29} {original_size:>12,d} {compressed_size:>12,d} "
                  f"{ratio_pct:>9.1f}% {elapsed_ms:>7.1f}ms {status:<10}")
            
        except Exception as e:
            error_msg = str(e)[:100]
            status = "❌ FAILED"
            
            result = CompressionResult(
                filename=test_name,
                original_size=original_size,
                compressed_size=0,
                compression_ratio=0,
                compression_percent=0,
                time_ms=0,
                status=status,
                error_msg=error_msg
            )
            results.append(result)
            
            print(f"{idx:<3} {test_name:<29} {original_size:>12,d} {'N/A':>12s} "
                  f"{'N/A':>10s} {'N/A':>8s} {status:<10}")
    
    return results

def print_summary(results: List[CompressionResult]):
    """Print comprehensive summary."""
    print("\n" + "=" * 100)
    print("📊 COMPREHENSIVE COMPRESSION SUMMARY")
    print("=" * 100)
    
    successful = [r for r in results if r.status == "✅ OK"]
    failed = [r for r in results if r.status == "❌ FAILED"]
    
    total_original = sum(r.original_size for r in successful)
    total_compressed = sum(r.compressed_size for r in successful)
    
    if total_original > 0:
        overall_ratio = total_compressed / total_original
        overall_savings = (1 - overall_ratio) * 100
        avg_time = sum(r.time_ms for r in successful) / len(successful) if successful else 0
        min_ratio = min(r.compression_ratio for r in successful) * 100 if successful else 0
        max_ratio = max(r.compression_ratio for r in successful) * 100 if successful else 0
        
        print(f"\n✅ Test Results:")
        print(f"  • Successful: {len(successful)}/{len(results)}")
        print(f"  • Failed: {len(failed)}/{len(results)}")
        
        print(f"\n📈 Compression Statistics:")
        print(f"  • Total Original Size: {total_original:>15,d} bytes")
        print(f"  • Total Compressed Size: {total_compressed:>12,d} bytes")
        print(f"  • Overall Compression Ratio: {overall_ratio*100:>13.2f}%")
        print(f"  • Overall Savings: {overall_savings:>21.2f}%")
        print(f"  • Compression Range: {min_ratio:>21.2f}% - {max_ratio:.2f}%")
        print(f"  • Average Time Per Test: {avg_time:>19.2f} ms")
        
        # Space saved
        space_saved = total_original - total_compressed
        print(f"\n💾 Space Efficiency:")
        print(f"  • Space Saved: {space_saved:>24,d} bytes ({overall_savings:.2f}%)")
        
        # Per-file details
        print(f"\n📋 Per-Test Breakdown:")
        print(f"{'Filename':<32} {'Original':>12} {'Compressed':>12} {'Ratio':>10} {'Savings':>10}")
        print("─" * 80)
        
        for r in successful:
            name_short = r.filename[:30]
            print(f"{name_short:<32} {r.original_size:>12,d} {r.compressed_size:>12,d} "
                  f"{r.compression_ratio*100:>9.1f}% {r.compression_percent:>9.1f}%")
        
        if failed:
            print(f"\n⚠️  Failed Tests (Details):")
            for r in failed:
                print(f"  • {r.filename}: {r.error_msg[:80]}")
    
    print("\n" + "=" * 100 + "\n")

def export_json(results: List[CompressionResult]):
    """Export results to JSON."""
    export_data = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "pipeline": "L0→L1→L2→L3→L4→L5→L6→L7→L8",
        "total_tests": len(results),
        "successful_tests": sum(1 for r in results if r.status == "✅ OK"),
        "failed_tests": sum(1 for r in results if r.status == "❌ FAILED"),
        "results": [
            {
                "filename": r.filename,
                "original_bytes": r.original_size,
                "compressed_bytes": r.compressed_size,
                "compression_ratio": round(r.compression_ratio, 4),
                "savings_percent": round(r.compression_percent, 2),
                "time_ms": round(r.time_ms, 2),
                "status": r.status,
                "error": r.error_msg
            }
            for r in results
        ]
    }
    
    filename = "TEST_RESULTS_L0_L8_COMPRESSION.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ JSON report exported to: {filename}")

def main():
    """Main entry point."""
    print_header()
    
    try:
        # Run compression tests
        results = run_tests()
        
        # Print summary
        print_summary(results)
        
        # Export JSON
        export_json(results)
        
        # Count status
        successful = sum(1 for r in results if r.status == "✅ OK")
        total = len(results)
        
        print(f"\n{'='*100}")
        print(f"{'🎯 TEST EXECUTION COMPLETE':^100s}")
        print(f"{'Results: ' + str(successful) + '/' + str(total) + ' tests successful':^100s}")
        print(f"{'='*100}\n")
        
        return 0 if successful > 0 else 1
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
