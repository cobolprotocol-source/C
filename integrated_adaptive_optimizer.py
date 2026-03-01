"""
INTEGRATED ADAPTIVE OPTIMIZER
==============================

Combines:
1. Adaptive chunk sizing
2. Cache warming
3. Buffer pooling (from buffer_pool_optimizer)
4. P95/P99 latency tracking

Provides unified interface for optimized compression with stability metrics.
"""

import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class LatencySnapshot:
    """Single latency measurement"""
    total_ms: float
    chunking_ms: float
    compression_ms: float
    overhead_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class LatencyStats:
    """Latency statistics for a session"""
    count: int
    mean_ms: float
    median_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    stdev_ms: float
    
    def __repr__(self) -> str:
        return (
            f"LatencyStats(count={self.count}, "
            f"mean={self.mean_ms:.2f}ms, "
            f"p95={self.p95_ms:.2f}ms, "
            f"p99={self.p99_ms:.2f}ms)"
        )


class LatencyTracker:
    """Tracks latency percentiles for stability analysis"""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize tracker.
        
        Args:
            window_size: Keep last N measurements for rolling stats
        """
        self.window_size = window_size
        self.measurements: deque = deque(maxlen=window_size)
    
    def record(self, snapshot: LatencySnapshot) -> None:
        """Record a latency measurement"""
        self.measurements.append(snapshot)
    
    def get_stats(self) -> Optional[LatencyStats]:
        """Get current latency statistics"""
        if not self.measurements:
            return None
        
        values = [m.total_ms for m in self.measurements]
        sorted_values = sorted(values)
        
        # Calculate percentiles
        def percentile(data, p):
            idx = int(len(data) * p / 100.0)
            return data[min(idx, len(data) - 1)]
        
        return LatencyStats(
            count=len(self.measurements),
            mean_ms=statistics.mean(values),
            median_ms=statistics.median(values),
            p50_ms=percentile(sorted_values, 50),
            p95_ms=percentile(sorted_values, 95),
            p99_ms=percentile(sorted_values, 99),
            min_ms=min(values),
            max_ms=max(values),
            stdev_ms=statistics.stdev(values) if len(values) > 1 else 0.0
        )
    
    def has_latency_spike(self, threshold_ms: float = 10.0) -> Tuple[bool, float]:
        """
        Detect if recent measurements exceed threshold.
        
        Returns:
            (has_spike, max_spike_ms)
        """
        if not self.measurements:
            return False, 0.0
        
        recent = list(self.measurements)[-10:]  # Last 10
        spikes = [m.total_ms for m in recent if m.total_ms > threshold_ms]
        
        if spikes:
            return True, max(spikes)
        return False, 0.0


class PercentileOptimizer:
    """Optimizes specifically for P95/P99 latency reduction"""
    
    # Strategy targets
    P95_TARGET = 65.0  # ms
    P99_TARGET = 85.0  # ms
    
    def __init__(self):
        """Initialize percentile optimizer"""
        self.adjustments_made = 0
        self.chunk_size_history: List[int] = []
    
    def recommend_adjustment(
        self,
        current_stats: LatencyStats,
        current_chunk_size: int,
        data_size: int
    ) -> Tuple[int, str]:
        """
        Recommend chunk size adjustment based on P95/P99.
        
        Args:
            current_stats: Current latency statistics
            current_chunk_size: Current chunk size in bytes
            data_size: Total data size in bytes
            
        Returns:
            (new_chunk_size, reasoning)
        """
        reasoning = []
        adjustment_factor = 1.0
        
        # P99 too high → reduce chunk size (less processing per chunk)
        if current_stats.p99_ms > self.P99_TARGET:
            reduction = (current_stats.p99_ms - self.P99_TARGET) / self.P99_TARGET
            adjustment_factor *= (1.0 - min(reduction * 0.2, 0.4))  # Up to 40% reduction
            reasoning.append(f"P99 high ({current_stats.p99_ms:.1f}ms > {self.P99_TARGET}ms)")
        
        # P95 too high → slight reduction
        elif current_stats.p95_ms > self.P95_TARGET:
            reduction = (current_stats.p95_ms - self.P95_TARGET) / self.P95_TARGET
            adjustment_factor *= (1.0 - min(reduction * 0.1, 0.2))  # Up to 20% reduction
            reasoning.append(f"P95 high ({current_stats.p95_ms:.1f}ms > {self.P95_TARGET}ms)")
        
        # High stdev → reduce variance with smaller chunks
        if current_stats.stdev_ms > current_stats.mean_ms * 0.4:  # >40% variance
            adjustment_factor *= 0.95
            reasoning.append(f"High variance (σ={current_stats.stdev_ms:.1f}ms)")
        
        # Large spread (p99 - minimal) → reduce chunk size
        if current_stats.p99_ms - current_stats.min_ms > current_stats.mean_ms:
            adjustment_factor *= 0.95
            reasoning.append(f"Large spread (p99-min={current_stats.p99_ms - current_stats.min_ms:.1f}ms)")
        
        new_chunk_size = max(256, int(current_chunk_size * adjustment_factor))
        
        if not reasoning:
            reasoning.append("Latency within acceptable range")
        
        return new_chunk_size, " | ".join(reasoning)
    
    def should_increase_chunk_size(self, stats: LatencyStats) -> bool:
        """Check if chunk size can be increased"""
        return (
            stats.p95_ms < self.P95_TARGET * 0.8 and  # P95 well below target
            stats.p99_ms < self.P99_TARGET * 0.8 and  # P99 well below target
            stats.stdev_ms < stats.mean_ms * 0.2  # Low variance
        )


class IntegratedAdaptiveOptimizer:
    """Main unified optimizer combining all optimization strategies"""
    
    def __init__(
        self,
        engine=None,
        enable_chunking: bool = True,
        enable_cache_warming: bool = True,
        enable_buffer_pooling: bool = True,
        enable_latency_tracking: bool = True
    ):
        """
        Initialize integrated optimizer.
        
        Args:
            engine: CobolEngine instance (optional)
            enable_chunking: Use adaptive chunking
            enable_cache_warming: Warm caches on session start
            enable_buffer_pooling: Use buffer pooling
            enable_latency_tracking: Track P95/P99 metrics
        """
        self.engine = engine
        self.enable_chunking = enable_chunking
        self.enable_cache_warming = enable_cache_warming
        self.enable_buffer_pooling = enable_buffer_pooling
        self.enable_latency_tracking = enable_latency_tracking
        
        # Import optional dependencies
        try:
            if enable_chunking:
                from adaptive_chunk_optimizer import AdaptiveChunkOptimizer
                self.chunk_optimizer = AdaptiveChunkOptimizer()
            else:
                self.chunk_optimizer = None
        except ImportError:
            logger.warning("adaptive_chunk_optimizer not available")
            self.chunk_optimizer = None
        
        try:
            if enable_cache_warming:
                from cache_warmer import SessionCacheWarmer
                self.cache_warmer = SessionCacheWarmer()
            else:
                self.cache_warmer = None
        except ImportError:
            logger.warning("cache_warmer not available")
            self.cache_warmer = None
        
        try:
            if enable_buffer_pooling:
                from buffer_pool_optimizer import ContextFreePipelineWrapper
                self.buffer_wrapper = ContextFreePipelineWrapper(engine)
            else:
                self.buffer_wrapper = None
        except ImportError:
            logger.warning("buffer_pool_optimizer not available")
            self.buffer_wrapper = None
        
        self.latency_tracker = LatencyTracker() if enable_latency_tracking else None
        self.percentile_opt = PercentileOptimizer()
        self.session_warmup_done = False
    
    def initialize_session(self, sample_data: Optional[bytes] = None) -> Dict:
        """
        Initialize optimization session.
        
        Runs warm-up if enabled and returns setup metrics.
        
        Args:
            sample_data: Sample data for cache warming
            
        Returns:
            Dictionary with initialization metrics
        """
        start = time.perf_counter()
        metrics = {
            "warmup_enabled": self.enable_cache_warming,
            "warmup_time_ms": 0.0,
            "warmup_reduction_ms": 0.0,
        }
        
        if self.enable_cache_warming and self.cache_warmer:
            logger.info("Initializing optimization session...")
            
            sample = sample_data or b"optimization session initialization" * 32
            warmup_metrics = self.cache_warmer.warmup(
                engine_dict_chain=getattr(self.engine, 'dict_manager', None),
                engine_registry=getattr(self.engine, 'global_registry', None)
            )
            
            metrics["warmup_time_ms"] = warmup_metrics.warmup_time_ms
            metrics["warmup_reduction_ms"] = warmup_metrics.estimated_latency_reduction_ms
            metrics["buffers_preallocated"] = warmup_metrics.buffers_preallocated
            metrics["dict_entries_loaded"] = warmup_metrics.dictionary_entries_loaded
            
            self.session_warmup_done = True
            logger.info(f"✓ Session initialized (warmup: {warmup_metrics.warmup_time_ms:.1f}ms)")
        
        return metrics
    
    def compress(
        self,
        data: bytes,
        compression_fn: Callable = None
    ) -> Tuple[bytes, Dict]:
        """
        Compress with adaptive optimizations.
        
        Args:
            data: Data to compress
            compression_fn: Compression function (default: engine.compress_chained)
            
        Returns:
            (compressed_data, metrics)
        """
        snapshot_start = time.perf_counter()
        metrics = {
            "original_size": len(data),
            "chunk_size": 0,
            "chunk_count": 0,
            "compression_ratio": 1.0,
            "total_latency_ms": 0.0,
            "chunk_analysis": None,
            "p95_latency_ms": None,
            "p99_latency_ms": None,
        }
        
        # Step 1: Adaptive chunking
        if self.enable_chunking and self.chunk_optimizer:
            chunk_analysis = self.chunk_optimizer.analyze(data)
            chunk_size = chunk_analysis.recommended_chunk_size
            
            metrics["chunk_size"] = chunk_size
            metrics["chunk_count"] = (len(data) + chunk_size - 1) // chunk_size
            metrics["chunk_analysis"] = {
                "entropy": chunk_analysis.entropy,
                "category": chunk_analysis.entropy_category,
                "cache_alignment": chunk_analysis.cache_alignment,
                "estimated_ratio": chunk_analysis.expected_compression_ratio,
            }
        
        # Step 2: Compression
        chunk_start = time.perf_counter()
        try:
            if self.enable_buffer_pooling and self.buffer_wrapper:
                # Use optimized wrapper if available
                compressed, comp_metadata = self.buffer_wrapper.compress(data)
                metrics["compression_ratio"] = len(data) / len(compressed) if compressed else 1.0
            elif compression_fn:
                # Use provided function
                compressed, comp_metadata = compression_fn(data)
                metrics["compression_ratio"] = len(data) / len(compressed) if compressed else 1.0
            else:
                # Try engine method
                compressed, comp_metadata = self.engine.compress_chained(data)
                metrics["compression_ratio"] = len(data) / len(compressed) if compressed else 1.0
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return data, metrics
        
        # Step 3: Record latency
        total_latency = (time.perf_counter() - snapshot_start) * 1000
        metrics["total_latency_ms"] = total_latency
        
        # Step 4: Track percentiles
        if self.latency_tracker:
            snapshot = LatencySnapshot(
                total_ms=total_latency,
                chunking_ms=metrics.get("chunking_ms", 0),
                compression_ms=(time.perf_counter() - chunk_start) * 1000,
                overhead_ms=total_latency - ((time.perf_counter() - chunk_start) * 1000)
            )
            self.latency_tracker.record(snapshot)
            
            stats = self.latency_tracker.get_stats()
            if stats:
                metrics["p95_latency_ms"] = stats.p95_ms
                metrics["p99_latency_ms"] = stats.p99_ms
                metrics["latency_stats"] = stats
        
        return compressed, metrics
    
    def get_latency_stats(self) -> Optional[LatencyStats]:
        """Get current latency statistics"""
        if not self.latency_tracker:
            return None
        return self.latency_tracker.get_stats()
    
    def print_session_summary(self) -> None:
        """Print optimization session summary"""
        stats = self.get_latency_stats()
        if not stats:
            print("No latency data collected yet")
            return
        
        print(f"\n{'='*80}")
        print(f"ADAPTIVE OPTIMIZATION SESSION SUMMARY")
        print(f"{'='*80}")
        print(f"Total requests: {stats.count}")
        print(f"Mean latency: {stats.mean_ms:.2f} ms")
        print(f"Median latency: {stats.median_ms:.2f} ms")
        print(f"P95 latency: {stats.p95_ms:.2f} ms")
        print(f"P99 latency: {stats.p99_ms:.2f} ms")
        print(f"Range: {stats.min_ms:.2f} - {stats.max_ms:.2f} ms")
        print(f"Std Dev: {stats.stdev_ms:.2f} ms")
        
        # Assessment
        p95_ok = stats.p95_ms <= PercentileOptimizer.P95_TARGET
        p99_ok = stats.p99_ms <= PercentileOptimizer.P99_TARGET
        var_ok = stats.stdev_ms <= stats.mean_ms * 0.3
        
        status = "✓ PASS" if (p95_ok and p99_ok and var_ok) else "✗ NEEDS TUNING"
        
        print(f"\nPercentile Assessment:")
        print(f"  P95 target {PercentileOptimizer.P95_TARGET}ms: {'✓' if p95_ok else '✗'} ({stats.p95_ms:.1f}ms)")
        print(f"  P99 target {PercentileOptimizer.P99_TARGET}ms: {'✓' if p99_ok else '✗'} ({stats.p99_ms:.1f}ms)")
        print(f"  Variance <30%: {'✓' if var_ok else '✗'} ({stats.stdev_ms/stats.mean_ms*100:.1f}%)")
        
        print(f"\nStatus: {status}")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    # Example usage
    import os
    
    # Create optimizer
    optimizer = IntegratedAdaptiveOptimizer(
        enable_chunking=True,
        enable_cache_warming=True,
        enable_buffer_pooling=False,  # Skip if buffer_pool not available
        enable_latency_tracking=True
    )
    
    # Initialize session
    print("Initializing session...")
    init_metrics = optimizer.initialize_session(sample_data=os.urandom(8192))
    print(f"Session initialized: {init_metrics}")
