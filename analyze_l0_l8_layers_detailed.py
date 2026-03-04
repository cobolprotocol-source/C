#!/usr/bin/env python3
"""
COBOL Protocol Compression - Detailed Layer-by-Layer Analysis Report
====================================================================

Provides comprehensive analysis of L0-L8 pipeline with:
- Per-layer compression ratios
- Round-trip verification (compress → decompress)
- Detailed performance metrics
- COBOL encoding format analysis
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict
import json

sys.path.insert(0, str(Path(__file__).parent / 'src'))

def create_test_samples() -> List[Tuple[str, bytes]]:
    """Create diverse test samples."""
    return [
        ("Text_ASCII_Small", b"Hello World! " * 5),
        ("Text_Repetitive", b"AAABBBCCCDDD" * 20),
        ("JSON_Structured", b'{"data":[1,2,3,4,5],"name":"test"}' * 10),
        ("Binary_Random", bytes([(i * 7) % 256 for i in range(4096)])),
        ("CSV_Data", b"id,name,value\n1,test1,100\n2,test2,200\n" * 20),
    ]

def analyze_compression_pipeline():
    """Analyze complete L0-L8 compression pipeline."""
    from src.layers.pipelines.engine import CobolPipeline
    
    print("\n" + "="*100)
    print("COBOL PROTOCOL COMPRESSION TEST - DETAILED LAYER ANALYSIS")
    print("="*100 + "\n")
    
    samples = create_test_samples()
    
    all_results = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "test_samples": len(samples),
        "samples": []
    }
    
    for sample_name, sample_data in samples:
        print(f"\n{'='*100}")
        print(f"📊 TEST: {sample_name}")
        print(f"{'='*100}")
        print(f"Original Size: {len(sample_data):,d} bytes")
        print(f"Sample Data: {sample_data[:60]}...")
        
        try:
            # Compress
            pipeline = CobolPipeline()
            print(f"\n🔄 Compressing with L0→L8 pipeline...")
            start_time = time.perf_counter()
            result = pipeline.compress(sample_data)
            compress_time_ms = (time.perf_counter() - start_time) * 1000
            
            print(f"✅ Compression Complete ({compress_time_ms:.1f}ms)")
            print(f"\n📈 COMPRESSION RESULTS:")
            print(f"  Original Size:       {result.original_size:>12,d} bytes")
            print(f"  Compressed Size:     {result.final_size:>12,d} bytes")
            print(f"  Compression Ratio:   {result.ratio*100:>12.2f}%")
            print(f"  Size Change:         {result.final_size - result.original_size:>+12,d} bytes")
            
            # Analyze per-layer stats
            print(f"\n📋 PER-LAYER BREAKDOWN:")
            print(f"{'Layer':<15} {'Input (B)':>12} {'Output (B)':>12} {'Ratio':>10} {'Change':>10} {'Time (ms)':>10}")
            print("─" * 75)
            
            prev_size = result.original_size
            for layer_stat in result.per_layer_stats:
                layer_name = layer_stat.name
                
                # Determine output size
                if hasattr(layer_stat.data, '__len__'):
                    if isinstance(layer_stat.data, bytes):
                        curr_size = len(layer_stat.data)
                    else:
                        try:
                            curr_size = len(layer_stat.data.tobytes()) if hasattr(layer_stat.data, 'tobytes') else len(layer_stat.data)
                        except:
                            curr_size = 0
                else:
                    curr_size = result.final_size if layer_name == 'L8' else 0
                
                time_ms = layer_stat.metadata.get('time_ms', 0) if layer_stat.metadata else 0
                ratio = (curr_size / prev_size * 100) if prev_size > 0 else 100
                change = curr_size - prev_size
                
                print(f"{layer_name:<15} {prev_size:>12,d} {curr_size:>12,d} "
                      f"{ratio:>9.1f}% {change:>+9,d} {time_ms:>10.2f}")
                
                prev_size = curr_size
            
            # Output format analysis
            print(f"\n📄 OUTPUT FORMAT ANALYSIS:")
            print(f"  First 100 bytes (hex): {result.compressed_data[:100].hex()[:100]}")
            print(f"  First 100 bytes (ascii): {result.compressed_data[:100][:100]}")
            
            # Try decompression if available
            print(f"\n🔙 DECOMPRESSION TEST:")
            try:
                if hasattr(pipeline, 'decompress'):
                    print(f"  Attempting decompression...")
                    decompressed = pipeline.decompress(result.compressed_data)
                    if decompressed == sample_data:
                        print(f"  ✅ ROUND-TRIP SUCCESS: Decompressed data matches original!")
                    else:
                        print(f"  ⚠️  Decompressed data differs from original")
                        print(f"     Original length:     {len(sample_data)} bytes")
                        print(f"     Decompressed length: {len(decompressed)} bytes")
                else:
                    print(f"  ℹ️  Pipeline has no decompress() method")
            except Exception as e:
                print(f"  ⚠️  Decompression not available: {str(e)[:100]}")
            
            # Store results
            sample_result = {
                "name": sample_name,
                "original_size": result.original_size,
                "compressed_size": result.final_size,
                "ratio": result.ratio,
                "time_ms": compress_time_ms,
                "layers": len(result.per_layer_stats),
                "checksum": str(result.checksum if hasattr(result, 'checksum') else None)
            }
            all_results["samples"].append(sample_result)
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    # Print Summary
    print(f"\n\n{'='*100}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*100}\n")
    
    if all_results["samples"]:
        total_original = sum(s["original_size"] for s in all_results["samples"])
        total_compressed = sum(s["compressed_size"] for s in all_results["samples"])
        avg_time = sum(s["time_ms"] for s in all_results["samples"]) / len(all_results["samples"])
        
        print(f"Total Tests:            {len(all_results['samples'])}")
        print(f"Total Original Size:    {total_original:,d} bytes")
        print(f"Total Compressed Size:  {total_compressed:,d} bytes")
        print(f"Overall Ratio:          {(total_compressed/total_original*100):,.2f}%")
        print(f"Average Time/Sample:    {avg_time:.1f} ms")
        
        # Individual results
        print(f"\n{'Sample Name':<25} {'Original':>12} {'Compressed':>12} {'Ratio %':>10}")
        print("─" * 62)
        for s in all_results["samples"]:
            ratio = (s["compressed_size"] / s["original_size"] * 100) if s["original_size"] > 0 else 0
            print(f"{s['name']:<25} {s['original_size']:>12,d} {s['compressed_size']:>12,d} {ratio:>10.1f}")
    
    # Export JSON
    json_file = "TEST_RESULTS_LAYER_ANALYSIS.json"
    with open(json_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Detailed results exported to: {json_file}\n")

if __name__ == "__main__":
    try:
        analyze_compression_pipeline()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
