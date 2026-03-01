#!/usr/bin/env python3
"""
Complete Integration Example

Shows how to integrate Performance Profile System with the COBOL compression engine.

This example demonstrates:
1. Importing and initializing the engine
2. Wrapping with profile support
3. Compressing data with profiles
4. Monitoring and statistics
5. Handling fallback scenarios
"""

import logging
import sys
from typing import Tuple, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_compression():
    """Example 1: Basic compression with profiles"""
    print("\n" + "=" * 80)
    print("Example 1: Basic Compression with Profiles")
    print("=" * 80)
    
    from profile_integration import create_profile_aware_engine
    
    # Mock engine for demonstration
    class SimpleCompressionEngine:
        def compress(self, data):
            """Simple mock compression"""
            # Return 60% of original size
            compressed = data[:int(len(data) * 0.6)]
            return compressed, {'layer': 'simple'}
        
        def decompress(self, data):
            """Mock decompression"""
            return data
    
    # Create and wrap engine
    base_engine = SimpleCompressionEngine()
    engine = create_profile_aware_engine(base_engine, auto_select=True)
    
    # Get profile info
    print(f"\nActive profile: {engine.get_compression_profile()}")
    print(f"Explanation: {engine.explain_profile_selection()}")
    
    # Compress data
    test_data = b"The quick brown fox jumps over the lazy dog. " * 100
    print(f"\nOriginal size: {len(test_data)} bytes")
    
    result = engine.compress_chunk(test_data, monitor_latency=True)
    print(f"Compressed size: {len(result.compressed_data)} bytes")
    print(f"Compression ratio: {result.stats.compression_ratio:.2f}x")
    print(f"Throughput: {result.stats.throughput_mbps:.2f} MB/s")
    print(f"Latency: {result.stats.elapsed_time_ms:.2f} ms")
    
    return engine


def example_multiple_profiles():
    """Example 2: Test with multiple profiles"""
    print("\n" + "=" * 80)
    print("Example 2: Compression with Different Profiles")
    print("=" * 80)
    
    from profile_integration import create_profile_aware_engine
    
    class SimpleCompressionEngine:
        def compress(self, data):
            # Simulate compression based on data size
            import time
            time.sleep(0.01)  # Simulate work
            compressed = data[:max(1, int(len(data) * 0.7))]
            return compressed, {'layer': 'test'}
        
        def decompress(self, data):
            return data
    
    # Test with different profiles
    profiles = ['EDGE_LOW', 'CLIENT_STANDARD', 'WORKSTATION_PRO']
    test_data = b"Test data " * 1000
    
    print(f"\nCompressing {len(test_data)} bytes with different profiles:\n")
    print(f"{'Profile':<20} {'Throughput':<20} {'Latency':<15} {'Ratio':<10}")
    print("-" * 65)
    
    for profile_name in profiles:
        base_engine = SimpleCompressionEngine()
        engine = create_profile_aware_engine(base_engine, auto_select=False)
        engine.set_compression_profile(profile_name)
        
        result = engine.compress_chunk(test_data, monitor_latency=False)
        print(
            f"{profile_name:<20} "
            f"{result.stats.throughput_mbps:<20.2f} "
            f"{result.stats.elapsed_time_ms:<15.2f} ms "
            f"{result.stats.compression_ratio:<10.2f}x"
        )


def example_monitoring_statistics():
    """Example 3: Monitoring and statistics"""
    print("\n" + "=" * 80)
    print("Example 3: Monitoring and Statistics Collection")
    print("=" * 80)
    
    from profile_integration import create_profile_aware_engine
    
    class SimpleCompressionEngine:
        def compress(self, data):
            import time
            time.sleep(0.005)
            return data[:int(len(data) * 0.65)], {'layer': 'test'}
        
        def decompress(self, data):
            return data
    
    # Create engine and compress multiple chunks
    base_engine = SimpleCompressionEngine()
    engine = create_profile_aware_engine(base_engine, auto_select=True)
    
    print(f"\nActive profile: {engine.get_compression_profile()}\n")
    
    # Compress 5 chunks
    for i in range(5):
        data = f"Chunk {i+1}: ".encode() + b"Test data " * (100 + i*10)
        result = engine.compress_chunk(data, monitor_latency=True)
        print(f"Chunk {i+1}: {len(data):>6} bytes → {len(result.compressed_data):>6} bytes "
              f"({result.stats.throughput_mbps:>6.2f} MB/s)")
    
    # Get statistics
    print("\n" + "-" * 65)
    stats = engine.get_monitoring_stats()
    print(f"\nStatistics:")
    print(f"  Profile: {stats['profile']}")
    print(f"  Total compressions: {stats['monitor']['compressions']}")
    print(f"  Avg throughput: {stats['monitor']['avg_throughput_mbps']:.2f} MB/s")
    print(f"  Avg latency: {stats['monitor']['avg_latency_ms']:.2f} ms")
    print(f"  Fallback rate: {stats['monitor']['fallback_rate']:.1%}")
    print(f"  Fallback count: {len(stats['fallback_history'])}")


def example_manual_profile_selection():
    """Example 4: Manual profile selection"""
    print("\n" + "=" * 80)
    print("Example 4: Manual Profile Selection")
    print("=" * 80)
    
    from profile_integration import create_profile_aware_engine
    
    class SimpleCompressionEngine:
        def compress(self, data):
            return data[:int(len(data) * 0.7)], {'layer': 'test'}
        
        def decompress(self, data):
            return data
    
    # Create engine WITHOUT auto-selection
    base_engine = SimpleCompressionEngine()
    engine = create_profile_aware_engine(base_engine, auto_select=False)
    
    print("\nManually setting profiles:\n")
    
    test_data = b"Test " * 1000
    
    # Test different profiles
    for profile_name in ['EDGE_LOW', 'CLIENT_STANDARD', 'SERVER_GENERAL']:
        success = engine.set_compression_profile(profile_name)
        if success:
            result = engine.compress_chunk(test_data, monitor_latency=False)
            print(f"✓ {profile_name:<20} - Ratio: {result.stats.compression_ratio:.2f}x")
        else:
            print(f"✗ {profile_name:<20} - Failed to set")


def example_error_handling():
    """Example 5: Error handling and recovery"""
    print("\n" + "=" * 80)
    print("Example 5: Error Handling and Recovery")
    print("=" * 80)
    
    from profile_integration import create_profile_aware_engine
    
    class FailingCompressionEngine:
        def __init__(self, fail_on_call: int = 2):
            self.call_count = 0
            self.fail_on_call = fail_on_call
        
        def compress(self, data):
            self.call_count += 1
            if self.call_count == self.fail_on_call:
                raise Exception("Simulated compression failure")
            return data[:int(len(data) * 0.7)], {'layer': 'test'}
        
        def decompress(self, data):
            return data
    
    # Create engine that will fail on 2nd call
    base_engine = FailingCompressionEngine(fail_on_call=2)
    engine = create_profile_aware_engine(base_engine, auto_select=True)
    
    print(f"\nActive profile: {engine.get_compression_profile()}\n")
    
    test_data = b"Test data " * 100
    
    # First compression should succeed
    print("Attempt 1: Compressing...")
    try:
        result = engine.compress_chunk(test_data, monitor_latency=False)
        print(f"✓ Success - Compressed to {len(result.compressed_data)} bytes")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Second compression should fail and trigger fallback
    print("\nAttempt 2: Compressing (will fail)...")
    try:
        result = engine.compress_chunk(test_data, monitor_latency=False)
        print(f"✓ Success - Compressed to {len(result.compressed_data)} bytes")
    except Exception as e:
        print(f"✗ Failed: {e}")
        print("   System attempted error recovery fallback")
    
    # Check fallback history
    stats = engine.get_monitoring_stats()
    if stats['fallback_history']:
        print(f"\nFallback history:")
        for fallback in stats['fallback_history']:
            print(f"  {fallback['from_profile']} → {fallback['to_profile']}")
            print(f"    Reason: {fallback['reason']}")


def example_batch_compression():
    """Example 6: Batch compression"""
    print("\n" + "=" * 80)
    print("Example 6: Batch Compression")
    print("=" * 80)
    
    from profile_integration import create_profile_aware_engine
    
    class SimpleCompressionEngine:
        def compress(self, data):
            return data[:int(len(data) * 0.7)], {'layer': 'test'}
        
        def decompress(self, data):
            return data
    
    # Create engine
    base_engine = SimpleCompressionEngine()
    engine = create_profile_aware_engine(base_engine, auto_select=True)
    
    # Create multiple data chunks
    chunks = [
        b"Chunk 1: " + b"A" * 500,
        b"Chunk 2: " + b"B" * 1000,
        b"Chunk 3: " + b"C" * 1500,
        b"Chunk 4: " + b"D" * 2000,
    ]
    
    print(f"\nCompressing {len(chunks)} chunks:\n")
    
    results = engine.compress_multiple_chunks(chunks, monitor_latency=False)
    
    print(f"{'Chunk':<8} {'Original':<12} {'Compressed':<12} {'Ratio':<8}")
    print("-" * 40)
    
    total_original = 0
    total_compressed = 0
    
    for i, result in enumerate(results, 1):
        orig = result.original_data_size
        comp = len(result.compressed_data)
        ratio = result.stats.compression_ratio
        
        print(f"#{i:<7} {orig:<12} {comp:<12} {ratio:<8.2f}x")
        
        total_original += orig
        total_compressed += comp
    
    print("-" * 40)
    print(f"{'Total':<7} {total_original:<12} {total_compressed:<12} "
          f"{total_original/total_compressed if total_compressed > 0 else 0:<8.2f}x")


def integration_summary():
    """Show integration summary"""
    print("\n" + "=" * 80)
    print("INTEGRATION SUMMARY")
    print("=" * 80)
    
    summary = """
WHAT WAS INTEGRATED:

✓ Performance Profile System (5 static profiles)
  └─ EDGE_LOW, CLIENT_STANDARD, WORKSTATION_PRO, SERVER_GENERAL, DATACENTER_HIGH

✓ Profile-Aware Compression Engine
  └─ Wraps existing engine with profile support
  └─ Auto-selects optimal profile based on hardware
  └─ Monitors compression latency
  └─ Automatic fallback on performance issues

✓ Real-time Monitoring & Statistics
  └─ Per-chunk compression statistics
  └─ Throughput and latency tracking
  └─ Fallback history and audit trail

✓ Integration Components
  ├─ profile_integration.py (main integration module)
  ├─ INTEGRATION_GUIDE.py (usage guide)
  └─ integration_example.py (this file - working examples)

HOW TO USE IN YOUR CODE:

1. Import the integration module:
   >>> from profile_integration import create_profile_aware_engine

2. Wrap your existing compression engine:
   >>> your_engine = YourCompressionEngine()
   >>> profile_engine = create_profile_aware_engine(your_engine)

3. Use for compression:
   >>> result = profile_engine.compress_chunk(data)
   >>> print(f"Profile: {result.profile_name}")
   >>> print(f"Throughput: {result.stats.throughput_mbps:.2f} MB/s")

4. Get statistics:
   >>> stats = profile_engine.get_monitoring_stats()
   >>> print(f"Fallbacks: {len(stats['fallback_history'])}")

BENEFITS:

✓ Automatic performance tuning based on hardware
✓ Deterministic, auditable decisions (no AI/heuristics)
✓ Safe fallback mechanism (one-level only)
✓ Real-time monitoring and statistics
✓ Zero impact on file format or decompression
✓ Language-agnostic (FFI contract for all languages)

NEXT STEPS:

1. Review PERFORMANCE_PROFILES.md for full documentation
2. Review PERFORMANCE_PROFILES_QUICK_REFERENCE.md for quick lookup
3. Test integration with your actual engine
4. Monitor production performance
5. Adjust profiles if needed
"""
    
    print(summary)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PERFORMANCE PROFILE SYSTEM - COMPLETE INTEGRATION EXAMPLE")
    print("=" * 80)
    print("\nVersion: 1.0")
    print("Format: COBOL v1.5.3")
    print("Date: March 1, 2026\n")
    
    try:
        # Run examples
        example_basic_compression()
        example_multiple_profiles()
        example_monitoring_statistics()
        example_manual_profile_selection()
        example_error_handling()
        example_batch_compression()
        
        # Show summary
        integration_summary()
        
        print("\n" + "=" * 80)
        print("✓ All examples completed successfully")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        sys.exit(1)
