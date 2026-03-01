#!/usr/bin/env python3
"""
Performance Profile System Integration Guide

Step-by-step guide for integrating the Performance Profile System
with the COBOL v1.5.3 compression engine.
"""

import logging
from profile_integration import (
    ProfileAwareCompressionEngine,
    create_profile_aware_engine,
    wrap_existing_engine,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_integration():
    """Example 1: Basic integration with existing engine"""
    print("\n" + "=" * 80)
    print("Example 1: Basic Integration with Existing Engine")
    print("=" * 80)
    
    # Assume you have an existing engine instance
    # from engine import SomeCompressionEngine
    # existing_engine = SomeCompressionEngine()
    
    # Wrap it with profile support
    # profile_engine = wrap_existing_engine(existing_engine)
    
    print("""
    Step 1: Import the integration module
    >>> from profile_integration import wrap_existing_engine
    
    Step 2: Wrap your existing engine
    >>> from engine import YourCompressionEngine
    >>> existing_engine = YourCompressionEngine()
    >>> profile_engine = wrap_existing_engine(existing_engine)
    
    Step 3: Use profile-aware compression
    >>> data = b"Your data here"
    >>> result = profile_engine.compress_chunk(data)
    >>> print(f"Profile: {result.profile_name}")
    >>> print(f"Throughput: {result.stats.throughput_mbps:.2f} MB/s")
    """)


def example_2_auto_profile_selection():
    """Example 2: Auto profile selection based on hardware"""
    print("\n" + "=" * 80)
    print("Example 2: Auto Profile Selection")
    print("=" * 80)
    
    print("""
    The system automatically selects the best profile for your hardware.
    
    Example output:
    ```
    Auto-selected profile: SERVER_GENERAL
    Justification: Detected 16 cores, 64 GB RAM
    
    Parameters:
      chunk_size: 512000 bytes
      aes_threads: 8
      compression_depth: HIGH
      pipeline_mode: parallel
    ```
    
    Rules (priority order):
    1. 64+ cores & 256+ GB RAM & AES-NI → DATACENTER_HIGH
    2. 16+ cores & 64+ GB RAM → SERVER_GENERAL
    3. 8+ cores & 32+ GB RAM → WORKSTATION_PRO
    4. 2+ cores & 4+ GB RAM → CLIENT_STANDARD
    5. 1+ cores → EDGE_LOW (default)
    """)


def example_3_manual_profile_selection():
    """Example 3: Manually select specific profile"""
    print("\n" + "=" * 80)
    print("Example 3: Manual Profile Selection")
    print("=" * 80)
    
    print("""
    You can override AUTO selection with manual profile choice:
    
    Step 1: Create engine
    >>> from profile_integration import create_profile_aware_engine
    >>> profile_engine = create_profile_aware_engine(base_engine, auto_select=False)
    
    Step 2: Set specific profile
    >>> profile_engine.set_compression_profile('SERVER_GENERAL')
    Profile set to SERVER_GENERAL: chunk_size=512000, aes_threads=8
    
    Step 3: Compress with selected profile
    >>> result = profile_engine.compress_chunk(data)
    """)


def example_4_monitoring_fallback():
    """Example 4: Monitoring and automatic fallback"""
    print("\n" + "=" * 80)
    print("Example 4: Monitoring and Automatic Fallback")
    print("=" * 80)
    
    print("""
    The system monitors compression latency and automatically falls back
    to a more conservative profile if needed:
    
    Example scenario:
    1. Start with SERVER_GENERAL profile (optimized for throughput)
    2. Monitor each compression:
       - If latency > threshold → automatically fallback
       - Fallback: SERVER_GENERAL → WORKSTATION_PRO
    3. All fallbacks logged with reason and timestamp
    
    Get monitoring stats:
    >>> stats = profile_engine.get_monitoring_stats()
    >>> print(f"Profile: {stats['profile']}")
    >>> print(f"Compressions: {stats['monitor']['compressions']}")
    >>> print(f"Avg throughput: {stats['monitor']['avg_throughput_mbps']:.2f} MB/s")
    >>> print(f"Avg latency: {stats['monitor']['avg_latency_ms']:.2f} ms")
    >>> print(f"Fallback rate: {stats['monitor']['fallback_rate']:.1%}")
    >>> print(f"Fallbacks: {len(stats['fallback_history'])}")
    
    Fallback history:
    >>> for fallback in stats['fallback_history']:
    ...     print(f"{fallback['from_profile']} → {fallback['to_profile']}")
    ...     print(f"  Reason: {fallback['reason']}")
    ...     print(f"  Time: {fallback['timestamp']}")
    """)


def example_5_batch_compression():
    """Example 5: Batch compression with multiple chunks"""
    print("\n" + "=" * 80)
    print("Example 5: Batch Compression")
    print("=" * 80)
    
    print("""
    Compress multiple chunks efficiently:
    
    >>> data_chunks = [chunk1, chunk2, chunk3, ...]
    >>> results = profile_engine.compress_multiple_chunks(data_chunks)
    
    >>> for i, result in enumerate(results):
    ...     print(f"Chunk {i+1}:")
    ...     print(f"  Profile: {result.profile_name}")
    ...     print(f"  Compression ratio: {result.stats.compression_ratio:.2f}")
    ...     print(f"  Throughput: {result.stats.throughput_mbps:.2f} MB/s")
    ...     print(f"  Fallback: {result.stats.fallback_triggered}")
    """)


def example_6_profile_details():
    """Example 6: Get profile details"""
    print("\n" + "=" * 80)
    print("Example 6: Get Profile Details")
    print("=" * 80)
    
    print("""
    Query profile information:
    
    Get active profile:
    >>> profile = profile_engine.get_compression_profile()
    >>> print(f"Active profile: {profile}")
    
    Get explanation:
    >>> explanation = profile_engine.explain_profile_selection()
    >>> print(f"Explanation: {explanation}")
    
    Access profile parameters programmatically:
    >>> from performance_profiles import get_profile_parameters
    >>> params = get_profile_parameters()
    >>> chunk_size = params['chunk_size_bytes']
    >>> aes_threads = params['aes_threads']
    >>> compression_depth = params['compression_depth']
    >>> pipeline_mode = params['pipeline_mode']
    >>> dp_window = params['dp_window_seconds']
    """)


def integration_checklist():
    """Integration checklist"""
    print("\n" + "=" * 80)
    print("Integration Checklist")
    print("=" * 80)
    
    checklist = [
        ("Import profile_integration module", False),
        ("Create base engine instance", False),
        ("Wrap with ProfileAwareCompressionEngine", False),
        ("Set logging level (optional)", False),
        ("Test compression with auto profile", False),
        ("Test manual profile selection", False),
        ("Monitor compression statistics", False),
        ("Test latency-based fallback", False),
        ("Deploy to production", False),
    ]
    
    print("\nBefore deploying to production, complete these tasks:\n")
    for i, (task, completed) in enumerate(checklist, 1):
        status = "✓" if completed else "☐"
        print(f"  {status} {i}. {task}")


def architecture_diagram():
    """Show architecture diagram"""
    print("\n" + "=" * 80)
    print("Architecture Diagram")
    print("=" * 80)
    
    print("""
    Your Application
            │
            ↓
    ┌───────────────────────────────────┐
    │ ProfileAwareCompressionEngine      │
    │  - Auto profile selection          │
    │  - Latency monitoring              │
    │  - Automatic fallback              │
    │  - Statistics collection           │
    └───────────────┬─────────────────────┘
                    │
                    ↓
    ┌───────────────────────────────────┐
    │ PerformanceProfileManager          │
    │  - Profile definitions             │
    │  - Hardware detection              │
    │  - Profile parameters              │
    └───────────────┬─────────────────────┘
                    │
                    ↓
    ┌───────────────────────────────────┐
    │ Base Compression Engine            │
    │  - Layer 1-8 compression           │
    │  - AES encryption                  │
    │  - Dictionary management           │
    └───────────────────────────────────┘
    
    Data Flow:
    1. Input data → ProfileAwareCompressionEngine
    2. Engine applies profile-based tuning:
       - Get profile parameters
       - Set chunk size, AES threads, etc.
       - Monitor compression latency
    3. Delegate to base engine for compression
    4. Collect statistics
    5. Check for fallback trigger
    6. Return compressed data + stats + profile info
    """)


def performance_characteristics():
    """Show performance characteristics"""
    print("\n" + "=" * 80)
    print("Performance Characteristics by Profile")
    print("=" * 80)
    
    profiles = [
        ("EDGE_LOW", "1-2", "<2GB", "8KB", "~10", "1", "IoT, edge"),
        ("CLIENT_STANDARD", "2-8", "4-32GB", "64KB", "~50", "2", "Laptops"),
        ("WORKSTATION_PRO", "8-16", "32GB+", "256KB", "~150", "4", "Workstations"),
        ("SERVER_GENERAL", "16-64", "64GB+", "512KB", "~300", "8", "Servers"),
        ("DATACENTER_HIGH", "64+", "256GB+", "1MB", "~500+", "16", "HPC"),
    ]
    
    print(f"\n{'Profile':<20} {'Cores':<10} {'RAM':<12} {'Chunk':<10} {'Throughput':<12} {'Threads':<8} {'Use Case':<15}")
    print("-" * 100)
    
    for profile, cores, ram, chunk, throughput, threads, use_case in profiles:
        print(f"{profile:<20} {cores:<10} {ram:<12} {chunk:<10} {throughput:<12} {threads:<8} {use_case:<15}")


def troubleshooting_guide():
    """Troubleshooting guide"""
    print("\n" + "=" * 80)
    print("Troubleshooting Guide")
    print("=" * 80)
    
    print("""
    Issue: Profile auto-selection seems wrong
    Solution:
      1. Check hardware: profile_engine.get_monitoring_stats()
      2. Check explanation: profile_engine.explain_profile_selection()
      3. Verify hardware detection: Get CPU cores, RAM, AES-NI support
      4. Check rules in performance_profiles.yaml
    
    Issue: Frequent fallbacks occurring
    Solution:
      1. Check fallback history: stats['fallback_history']
      2. Monitor latency: stats['monitor']['avg_latency_ms']
      3. Consider switching to more conservative profile
      4. Verify system resources are available
    
    Issue: Compression slower than expected
    Solution:
      1. Check which profile is active: get_compression_profile()
      2. Check system resources (CPU, RAM, available cores)
      3. Verify profile parameters are applied correctly
      4. Check if fallback reduced performance
    
    Issue: Out of memory during compression
    Solution:
      1. Try more conservative profile (smaller chunks)
      2. Reduce chunk size in profile parameters
      3. Reduce number of parallel workers
      4. Enable explicit fallback: fallback_handler.check_and_fallback()
    """)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PERFORMANCE PROFILE SYSTEM - INTEGRATION GUIDE")
    print("=" * 80)
    print("\nVersion: 1.0")
    print("Format: COBOL v1.5.3")
    print("Date: March 1, 2026\n")
    
    # Show examples and guides
    example_1_basic_integration()
    example_2_auto_profile_selection()
    example_3_manual_profile_selection()
    example_4_monitoring_fallback()
    example_5_batch_compression()
    example_6_profile_details()
    
    # Show architecture and characteristics
    architecture_diagram()
    performance_characteristics()
    
    # Checklist and troubleshooting
    integration_checklist()
    troubleshooting_guide()
    
    print("\n" + "=" * 80)
    print("For more information, see:")
    print("  - PERFORMANCE_PROFILES.md (full documentation)")
    print("  - PERFORMANCE_PROFILES_QUICK_REFERENCE.md (quick lookup)")
    print("  - profile_integration.py (implementation)")
    print("=" * 80 + "\n")
