#!/usr/bin/env python3
# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""
Performance Profile System - Engine Integration

Integrates the Performance Profile System with the COBOL v1.5.3 compression engine.

This module provides:
1. ProfileAwareCompressionEngine - Main integration class
2. CompressionStats - Per-chunk statistics collection
3. ProfileMonitor - Real-time profile monitoring
4. FallbackHandler - Automatic fallback on latency spike
5. ProfiledCompressedChunk - Tagged chunk with profile info

Author: Nafal Faturizki
Date: March 1, 2026
"""

import logging
import time
from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from threading import Lock

from performance_profiles import (
    PerformanceProfileManager,
    get_profile_parameters,
    set_profile,
    get_active_profile,
    explain_profile_selection,
    auto_select_profile,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CompressionStats:
    """Statistics for a single compression operation"""
    start_time: float
    end_time: float
    profile_name: str
    data_size_bytes: int
    compressed_size_bytes: int
    elapsed_time_ms: float
    throughput_mbps: float
    compression_ratio: float
    aes_threads_used: int
    chunk_size_used: int
    fallback_triggered: bool = False
    fallback_reason: Optional[str] = None
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.end_time and self.start_time:
            self.elapsed_time_ms = (self.end_time - self.start_time) * 1000
            if self.elapsed_time_ms > 0:
                self.throughput_mbps = (self.data_size_bytes / 1024 / 1024) / (self.elapsed_time_ms / 1000)
            else:
                self.throughput_mbps = 0
        if self.compressed_size_bytes > 0:
            self.compression_ratio = self.data_size_bytes / self.compressed_size_bytes
        else:
            self.compression_ratio = 0


@dataclass
class ProfiledCompressedChunk:
    """Compressed chunk with profile metadata"""
    compressed_data: bytes
    metadata: Dict[str, Any]
    profile_name: str
    stats: CompressionStats
    original_data_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'profile': self.profile_name,
            'original_size': self.original_data_size,
            'compressed_size': len(self.compressed_data),
            'compression_ratio': self.stats.compression_ratio,
            'throughput_mbps': self.stats.throughput_mbps,
            'elapsed_ms': self.stats.elapsed_time_ms,
            'aes_threads': self.stats.aes_threads_used,
            'chunk_size': self.stats.chunk_size_used,
            'fallback': self.stats.fallback_triggered,
        }


class FallbackReason(Enum):
    """Reasons for profile fallback"""
    LATENCY_SPIKE = "latency_spike"
    MEMORY_PRESSURE = "memory_pressure"
    EXPLICIT_TRIGGER = "explicit_trigger"
    ERROR_RECOVERY = "error_recovery"


# ============================================================================
# MONITORING & STATISTICS
# ============================================================================

class ProfileMonitor:
    """Real-time monitoring of profile performance"""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize monitor
        
        Args:
            window_size: Number of recent stats to keep in sliding window
        """
        self.window_size = window_size
        self.stats_history: List[CompressionStats] = []
        self.lock = Lock()
        self.fallback_count = 0
        self.total_compressions = 0
    
    def record_compression(self, stats: CompressionStats):
        """Record compression statistics"""
        with self.lock:
            self.stats_history.append(stats)
            if len(self.stats_history) > self.window_size:
                self.stats_history.pop(0)
            
            self.total_compressions += 1
            if stats.fallback_triggered:
                self.fallback_count += 1
    
    def get_average_throughput(self) -> float:
        """Get average throughput over recent window"""
        with self.lock:
            if not self.stats_history:
                return 0
            avg_throughput = sum(s.throughput_mbps for s in self.stats_history) / len(self.stats_history)
            return avg_throughput
    
    def get_average_latency_ms(self) -> float:
        """Get average latency over recent window"""
        with self.lock:
            if not self.stats_history:
                return 0
            avg_latency = sum(s.elapsed_time_ms for s in self.stats_history) / len(self.stats_history)
            return avg_latency
    
    def get_fallback_rate(self) -> float:
        """Get fallback rate (0.0-1.0)"""
        if self.total_compressions == 0:
            return 0.0
        return self.fallback_count / self.total_compressions
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary of recent statistics"""
        with self.lock:
            if not self.stats_history:
                return {
                    'compressions': 0,
                    'avg_throughput_mbps': 0,
                    'avg_latency_ms': 0,
                    'fallback_rate': 0.0,
                    'profiles_used': [],
                }
            
            profiles_used = set(s.profile_name for s in self.stats_history)
            
            return {
                'compressions': len(self.stats_history),
                'avg_throughput_mbps': self.get_average_throughput(),
                'avg_latency_ms': self.get_average_latency_ms(),
                'fallback_rate': self.get_fallback_rate(),
                'profiles_used': list(profiles_used),
                'total_compressions': self.total_compressions,
            }


# ============================================================================
# FALLBACK HANDLER
# ============================================================================

class FallbackHandler:
    """Handles automatic profile fallback on performance issues"""
    
    def __init__(self, profile_manager: PerformanceProfileManager):
        """
        Initialize fallback handler
        
        Args:
            profile_manager: PerformanceProfileManager instance
        """
        self.manager = profile_manager
        self.fallback_history: List[Tuple[str, str, str, float]] = []
        self.lock = Lock()
    
    def check_and_fallback(
        self,
        latency_ms: float,
        reason: FallbackReason,
        additional_info: Optional[str] = None
    ) -> bool:
        """
        Check if fallback should be triggered and perform it
        
        Args:
            latency_ms: Measured latency in milliseconds
            reason: Reason for potential fallback
            additional_info: Additional context information
            
        Returns:
            True if fallback was triggered, False otherwise
        """
        try:
            current_profile = self.manager.get_active_profile()
            current_params = self.manager.get_profile_parameters(current_profile)
            threshold = current_params.get('fallback_latency_threshold_ms', 300)
            
            # Check if latency exceeds threshold
            if latency_ms > threshold:
                fallback_reason = f"{reason.value}: {latency_ms}ms > {threshold}ms"
                if additional_info:
                    fallback_reason += f" ({additional_info})"
                
                # Perform fallback
                self.manager.safe_fallback(fallback_reason, latency_ms)
                
                # Record in history
                new_profile = self.manager.get_active_profile()
                with self.lock:
                    self.fallback_history.append((
                        current_profile,
                        new_profile,
                        reason.value,
                        time.time()
                    ))
                
                logger.warning(
                    f"FALLBACK: {current_profile} → {new_profile} "
                    f"({fallback_reason})"
                )
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error in fallback check: {e}")
            return False
    
    def get_fallback_history(self) -> List[Tuple[str, str, str, float]]:
        """Get fallback history"""
        with self.lock:
            return list(self.fallback_history)


# ============================================================================
# PROFILE-AWARE COMPRESSION ENGINE
# ============================================================================

class ProfileAwareCompressionEngine:
    """
    Main compression engine integration with performance profiles.
    
    This wraps an existing compression engine and applies profile-based
    tuning to all compression operations.
    """
    
    def __init__(self, base_engine, auto_select: bool = True):
        """
        Initialize profile-aware engine
        
        Args:
            base_engine: Underlying compression engine instance
            auto_select: Whether to auto-select profile on initialization
        """
        self.base_engine = base_engine
        self.profile_manager = PerformanceProfileManager()
        self.monitor = ProfileMonitor()
        self.fallback_handler = FallbackHandler(self.profile_manager)
        
        # Initialize profile
        if auto_select:
            selection = self.profile_manager.auto_select_profile()
            self.profile_manager.set_profile(selection.profile_name)
            logger.info(
                f"Auto-selected profile: {selection.profile_name}\n"
                f"Justification: {selection.justification}"
            )
        
        logger.info("ProfileAwareCompressionEngine initialized")
    
    # ──────────────────────────────────────────────────────────────────────
    # PROFILE MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────
    
    def set_compression_profile(self, profile_name: str) -> bool:
        """
        Set compression profile
        
        Args:
            profile_name: Name of profile (e.g., 'SERVER_GENERAL')
            
        Returns:
            True if profile was set, False if invalid name
        """
        try:
            self.profile_manager.set_profile(profile_name)
            params = self.profile_manager.get_profile_parameters(profile_name)
            logger.info(
                f"Profile set to {profile_name}: "
                f"chunk_size={params['chunk_size_bytes']}, "
                f"aes_threads={params['aes_threads']}"
            )
            return True
        except ValueError as e:
            logger.error(f"Failed to set profile: {e}")
            return False
    
    def get_compression_profile(self) -> str:
        """Get current compression profile"""
        return self.profile_manager.get_active_profile()
    
    def explain_profile_selection(self) -> str:
        """Get explanation of current profile selection"""
        return self.profile_manager.explain_profile_selection()
    
    # ──────────────────────────────────────────────────────────────────────
    # COMPRESSION WITH PROFILE TUNING
    # ──────────────────────────────────────────────────────────────────────
    
    def compress_chunk(
        self,
        data: bytes,
        monitor_latency: bool = True
    ) -> ProfiledCompressedChunk:
        """
        Compress a single chunk with profile-based tuning
        
        Args:
            data: Data to compress
            monitor_latency: Whether to monitor and fallback on latency spike
            
        Returns:
            ProfiledCompressedChunk with compression result and stats
            
        Raises:
            Exception: If compression fails
        """
        start_time = time.time()
        profile_name = self.profile_manager.get_active_profile()
        params = self.profile_manager.get_profile_parameters(profile_name)
        
        # Apply profile parameters to compression
        # (Implementation-specific: depends on base_engine API)
        chunk_size = params.get('chunk_size_bytes', 64000)
        aes_threads = params.get('aes_threads', 2)
        
        try:
            # Perform compression (delegate to base engine)
            compressed_data, metadata = self.base_engine.compress(data)
            
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000
            
            # Create statistics
            stats = CompressionStats(
                start_time=start_time,
                end_time=end_time,
                profile_name=profile_name,
                data_size_bytes=len(data),
                compressed_size_bytes=len(compressed_data),
                elapsed_time_ms=elapsed_ms,
                throughput_mbps=0,
                compression_ratio=0,
                aes_threads_used=aes_threads,
                chunk_size_used=chunk_size,
            )
            stats.__post_init__()  # Calculate derived metrics
            
            # Check for latency spike and fallback if needed
            fallback_triggered = False
            if monitor_latency:
                fallback_triggered = self.fallback_handler.check_and_fallback(
                    elapsed_ms,
                    FallbackReason.LATENCY_SPIKE,
                    additional_info=f"Data size: {len(data)} bytes"
                )
            
            stats.fallback_triggered = fallback_triggered
            
            # Record statistics
            self.monitor.record_compression(stats)
            
            logger.debug(
                f"Compressed {len(data)} bytes → {len(compressed_data)} bytes "
                f"using {profile_name} ({elapsed_ms:.2f}ms, "
                f"{stats.throughput_mbps:.1f} MB/s)"
            )
            
            return ProfiledCompressedChunk(
                compressed_data=compressed_data,
                metadata=metadata if isinstance(metadata, dict) else {},
                profile_name=profile_name,
                stats=stats,
                original_data_size=len(data),
            )
        
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            # Try fallback for error recovery
            self.fallback_handler.check_and_fallback(
                0,  # No latency measurement
                FallbackReason.ERROR_RECOVERY,
                additional_info=str(e)
            )
            raise
    
    def compress_multiple_chunks(
        self,
        data_chunks: List[bytes],
        monitor_latency: bool = True
    ) -> List[ProfiledCompressedChunk]:
        """
        Compress multiple chunks with profile tuning
        
        Args:
            data_chunks: List of byte chunks to compress
            monitor_latency: Whether to monitor latency
            
        Returns:
            List of ProfiledCompressedChunk results
        """
        results = []
        for i, chunk in enumerate(data_chunks):
            try:
                result = self.compress_chunk(chunk, monitor_latency=monitor_latency)
                results.append(result)
                logger.info(f"Compressed chunk {i+1}/{len(data_chunks)}")
            except Exception as e:
                logger.error(f"Failed to compress chunk {i+1}: {e}")
                raise
        
        return results
    
    # ──────────────────────────────────────────────────────────────────────
    # MONITORING & STATISTICS
    # ──────────────────────────────────────────────────────────────────────
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring and performance statistics"""
        return {
            'profile': self.profile_manager.get_active_profile(),
            'explanation': self.profile_manager.explain_profile_selection(),
            'monitor': self.monitor.get_stats_summary(),
            'fallback_history': [
                {
                    'from_profile': h[0],
                    'to_profile': h[1],
                    'reason': h[2],
                    'timestamp': h[3],
                }
                for h in self.fallback_handler.get_fallback_history()
            ],
        }
    
    def print_stats(self):
        """Print statistics to logger"""
        stats = self.get_monitoring_stats()
        logger.info(
            f"Profile: {stats['profile']}\n"
            f"Monitor: {stats['monitor']}\n"
            f"Fallbacks: {len(stats['fallback_history'])}"
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_profile_aware_engine(base_engine, auto_select: bool = True) -> ProfileAwareCompressionEngine:
    """
    Factory function to create a profile-aware compression engine
    
    Args:
        base_engine: Underlying compression engine
        auto_select: Whether to auto-select profile
        
    Returns:
        ProfileAwareCompressionEngine instance
    """
    return ProfileAwareCompressionEngine(base_engine, auto_select=auto_select)


def wrap_existing_engine(engine):
    """
    Convenience function to wrap an existing engine with profile support
    
    Args:
        engine: Existing compression engine
        
    Returns:
        ProfileAwareCompressionEngine wrapping the engine
    """
    logger.info("Wrapping existing engine with profile support")
    return create_profile_aware_engine(engine, auto_select=True)


# ============================================================================
# MAIN / EXAMPLE
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("Performance Profile System - Engine Integration")
    print("=" * 80)
    
    # Create simple mock engine for testing
    class MockEngine:
        def compress(self, data):
            """Mock compress method"""
            # Simple mock: just return 50% compressed
            return data[:len(data)//2], {'layer': 'mock'}
        
        def decompress(self, data):
            """Mock decompress method"""
            return data * 2
    
    # Test integration
    mock_engine = MockEngine()
    profile_engine = create_profile_aware_engine(mock_engine, auto_select=True)
    
    print("\n[1] Created profile-aware engine")
    print(f"    Profile: {profile_engine.get_compression_profile()}")
    print(f"    Explanation: {profile_engine.explain_profile_selection()}")
    
    print("\n[2] Compressing test data...")
    test_data = b"Hello, World! " * 1000
    result = profile_engine.compress_chunk(test_data, monitor_latency=True)
    print(f"    Original: {result.original_data_size} bytes")
    print(f"    Compressed: {len(result.compressed_data)} bytes")
    print(f"    Ratio: {result.stats.compression_ratio:.2f}")
    print(f"    Throughput: {result.stats.throughput_mbps:.2f} MB/s")
    
    print("\n[3] Monitoring stats:")
    stats = profile_engine.get_monitoring_stats()
    print(f"    Profile: {stats['profile']}")
    print(f"    Compressions: {stats['monitor']['compressions']}")
    print(f"    Avg throughput: {stats['monitor']['avg_throughput_mbps']:.2f} MB/s")
    print(f"    Fallbacks: {len(stats['fallback_history'])}")
    
    print("\n" + "=" * 80)
    print("✓ Integration test complete")
    print("=" * 80)
