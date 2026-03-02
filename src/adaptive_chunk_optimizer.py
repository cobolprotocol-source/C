"""
ADAPTIVE CHUNK OPTIMIZER
========================

Optimizes chunk size dynamically based on:
1. Data entropy analysis
2. System cache hierarchy (L1/L2/L3)
3. Memory bandwidth characteristics

Goals:
- Reduce overhead from small chunks
- Eliminate latency spikes from large chunks
- Stabilize P95/P99 latency
"""

import os
import math
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, List
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# CPU Cache Configuration (typical)
class CacheConfig:
    L1_SIZE = 32 * 1024  # 32 KB (smallest)
    L2_SIZE = 256 * 1024  # 256 KB
    L3_SIZE = 8 * 1024 * 1024  # 8 MB
    
    L1_LINE = 64  # Cache line size (bytes)
    L2_LINE = 512  # Typical L2 line
    L3_LINE = 4096  # L3 typical alignment
    
    # Optimal chunk fitting into cache levels
    L1_CHUNK_LIMIT = L1_SIZE // 2  # 16 KB (leave room for code/data)
    L2_CHUNK_LIMIT = L2_SIZE // 3  # ~85 KB (3 sets of data)
    L3_CHUNK_LIMIT = L3_SIZE // 4  # 2 MB (fit into L3)


@dataclass
class ChunkAnalysis:
    """Analysis results for chunk sizing"""
    original_size: int
    entropy: float  # 0.0 to 8.0 bits per byte
    entropy_category: str  # "low", "medium", "high", "random"
    recommended_chunk_size: int
    reasoning: str
    cache_alignment: int  # Align to this boundary (64, 512, 4096, etc.)
    expected_compression_ratio: float
    estimated_latency_ms: float


class EntropyAnalyzer:
    """Analyzes data entropy to determine optimal chunk size"""
    
    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        """
        Calculate Shannon entropy of data.
        
        Returns:
            Entropy in bits per byte (0.0 to 8.0)
        """
        if not data:
            return 0.0
        
        # Count frequency of each byte value
        frequencies = Counter(data)
        total = len(data)
        
        # Calculate Shannon entropy
        entropy = 0.0
        for freq in frequencies.values():
            p = freq / total
            entropy -= p * math.log2(p)
        
        return entropy
    
    @staticmethod
    def categorize_entropy(entropy: float) -> str:
        """Categorize entropy level"""
        if entropy < 2.0:
            return "low"  # Highly compressible (JSON, text, code)
        elif entropy < 5.0:
            return "medium"  # Moderately compressible
        elif entropy < 7.0:
            return "high"  # Less compressible (images, video)
        else:
            return "random"  # Near-random (encrypted, already compressed)
    
    @staticmethod
    def estimate_compression_ratio(entropy: float) -> float:
        """
        Estimate achievable compression ratio based on entropy.
        
        Using Shannon's source coding theorem:
        lower_bound = entropy / 8  (theoretical best)
        realistic = 0.8 * lower_bound to 1.5 * lower_bound
        """
        theoretical_best = entropy / 8.0
        
        # Realistic compression accounting for overhead
        # If entropy is low, we can achieve close to theoretical
        # If entropy is high, we may expand due to overhead
        if entropy < 2.0:
            # Very compressible - we can achieve 30-50% of theoretical
            return theoretical_best * 0.40
        elif entropy < 5.0:
            # Moderately compressible - 50-70% of theoretical
            return theoretical_best * 0.60
        else:
            # Less compressible - may expand
            return max(theoretical_best * 0.85, 1.0)


class AdaptiveChunkSizer:
    """Determines optimal chunk size based on entropy and system characteristics"""
    
    # Baseline chunk sizes for different entropy categories
    BASELINE_SIZES = {
        "low": 32 * 1024,  # 32 KB (compressible data)
        "medium": 64 * 1024,  # 64 KB (balanced)
        "high": 128 * 1024,  # 128 KB (less compressible)
        "random": 256 * 1024,  # 256 KB (already compressed)
    }
    
    # Minimum and maximum chunk sizes (platform constraints)
    MIN_CHUNK = 256  # Don't go too small (overhead dominates)
    MAX_CHUNK = 2 * 1024 * 1024  # 2 MB max (GC/latency concerns)
    
    @staticmethod
    def calculate_optimal_chunk_size(
        data_size: int,
        entropy: float,
        target_compression_ratio: float = 2.0
    ) -> int:
        """
        Calculate optimal chunk size based on:
        1. Data entropy
        2. Available cache
        3. Target compression ratio
        
        Strategy:
        - Low entropy → smaller chunks (higher compression, more overhead tolerance)
        - High entropy → larger chunks (lower compression, reduce overhead ratio)
        - Cache-aware → fit into L2/L3 where possible
        
        Args:
            data_size: Total data size in bytes
            entropy: Shannon entropy (0-8 bits/byte)
            target_compression_ratio: Goal compression ratio
            
        Returns:
            Optimal chunk size in bytes
        """
        category = EntropyAnalyzer.categorize_entropy(entropy)
        base_size = AdaptiveChunkSizer.BASELINE_SIZES[category]
        
        # Adjust based on compression goal
        est_ratio = EntropyAnalyzer.estimate_compression_ratio(entropy)
        if est_ratio > 0:
            size_adjustment = target_compression_ratio / est_ratio
            adjusted_size = int(base_size * size_adjustment)
        else:
            adjusted_size = base_size
        
        # Clamp to valid range
        chunk_size = max(
            AdaptiveChunkSizer.MIN_CHUNK,
            min(adjusted_size, AdaptiveChunkSizer.MAX_CHUNK)
        )
        
        # Align to cache boundaries for better performance
        cache_alignment = AdaptiveChunkSizer._get_cache_alignment(chunk_size)
        aligned_size = AdaptiveChunkSizer._align_to_boundary(chunk_size, cache_alignment)
        
        return aligned_size
    
    @staticmethod
    def _get_cache_alignment(chunk_size: int) -> int:
        """
        Determine appropriate cache alignment based on chunk size.
        
        Strategy:
        - Chunks < 16 KB: align to L1 (64 bytes)
        - Chunks 16-85 KB: align to L2 (512 bytes)
        - Chunks > 85 KB: align to L3 (4 KB)
        """
        if chunk_size <= CacheConfig.L1_CHUNK_LIMIT:
            return CacheConfig.L1_LINE  # 64 bytes
        elif chunk_size <= CacheConfig.L2_CHUNK_LIMIT:
            return CacheConfig.L2_LINE  # 512 bytes
        else:
            return CacheConfig.L3_LINE  # 4 KB
    
    @staticmethod
    def _align_to_boundary(size: int, alignment: int) -> int:
        """Align size up to nearest alignment boundary"""
        remainder = size % alignment
        if remainder == 0:
            return size
        return size + (alignment - remainder)
    
    @staticmethod
    def calculate_chunk_count(data_size: int, chunk_size: int) -> int:
        """Calculate number of chunks needed"""
        return (data_size + chunk_size - 1) // chunk_size


class LatencyEstimator:
    """Estimates latency based on chunk configuration"""
    
    # Empirical latency components (in ms)
    BASE_LAYER_LATENCY = 5.0  # Per layer (processing)
    CHUNK_OVERHEAD = 0.5  # Per chunk (init, overhead)
    COMPRESSION_LATENCY_PER_MB = 5.0  # Processing rate
    GC_COST_PER_MB = 2.0  # Garbage collection cost
    CACHE_MISS_PENALTY = 0.1  # Per cache miss (typical 100 cycles = 0.1 ms @ 1 GHz)
    
    @staticmethod
    def estimate_latency(
        data_size: int,
        chunk_size: int,
        compression_ratio: float,
        num_layers: int = 4
    ) -> float:
        """
        Estimate total latency for compression operation.
        
        Components:
        1. Base layer processing (constant per layer)
        2. Per-chunk overhead (scales with chunk count)
        3. Actual compression (scales with data size & ratio)
        4. GC cost (scales with allocation count)
        5. Cache effects (scales with cache misses)
        
        Args:
            data_size: Total data size in bytes
            chunk_size: Chunk size in bytes
            compression_ratio: Expected compression ratio
            num_layers: Number of layers (default 4)
            
        Returns:
            Estimated latency in milliseconds
        """
        chunk_count = (data_size + chunk_size - 1) // chunk_size
        
        # Component 1: Base layer latency (per layer, not per chunk)
        base_latency = num_layers * LatencyEstimator.BASE_LAYER_LATENCY
        
        # Component 2: Per-chunk overhead
        chunk_overhead = chunk_count * LatencyEstimator.CHUNK_OVERHEAD
        
        # Component 3: Actual compression (data_size * compression_ratio / throughput)
        data_mb = data_size / (1024 * 1024)
        compression_latency = data_mb * LatencyEstimator.COMPRESSION_LATENCY_PER_MB
        
        # Component 4: GC cost (scales with allocations)
        # More chunks = more allocations but smaller = less collection pressure
        gc_latency = chunk_count * LatencyEstimator.GC_COST_PER_MB * (chunk_size / (1024 * 1024))
        
        # Component 5: Cache effects
        # Small chunks cause more cache misses, large chunks cause evictions
        cache_penalty = LatencyEstimator._estimate_cache_penalty(chunk_size, chunk_count)
        
        total = base_latency + chunk_overhead + compression_latency + gc_latency + cache_penalty
        return total
    
    @staticmethod
    def _estimate_cache_penalty(chunk_size: int, chunk_count: int) -> float:
        """
        Estimate cache miss penalty.
        
        Sweet spot is around L2_CHUNK_LIMIT (85 KB)
        Too small → more context switches & cache evictions
        Too large → cache thrashing & poor locality
        """
        optimal = CacheConfig.L2_CHUNK_LIMIT
        
        if chunk_size < 4096:
            # Way too small - lots of context switching
            penalty = chunk_count * 0.5
        elif chunk_size < optimal * 0.5:
            # Small but reasonable - some context switching
            penalty = chunk_count * 0.1
        elif chunk_size <= optimal * 1.5:
            # Sweet spot - minimal penalty
            penalty = chunk_count * 0.01
        elif chunk_size <= CacheConfig.L3_CHUNK_LIMIT:
            # Getting large - some cache thrashing
            penalty = chunk_count * 0.05
        else:
            # Too large - significant GC and cache eviction
            penalty = chunk_count * 0.2
        
        return penalty


class AdaptiveChunkOptimizer:
    """Main optimizer coordinating chunk analysis and optimization"""
    
    def __init__(self, enable_caching: bool = True):
        """
        Initialize optimizer.
        
        Args:
            enable_caching: Cache analysis results for similar data
        """
        self.enable_caching = enable_caching
        self.analysis_cache: Dict[int, ChunkAnalysis] = {}
    
    def analyze(self, data: bytes, target_compression_ratio: float = 2.0) -> ChunkAnalysis:
        """
        Analyze data and recommend optimal chunk size.
        
        Args:
            data: Input data to compress
            target_compression_ratio: Target compression goal
            
        Returns:
            ChunkAnalysis with recommendations
        """
        data_size = len(data)
        entropy = EntropyAnalyzer.calculate_entropy(data)
        entropy_category = EntropyAnalyzer.categorize_entropy(entropy)
        
        # Calculate optimal chunk size
        chunk_size = AdaptiveChunkSizer.calculate_optimal_chunk_size(
            data_size,
            entropy,
            target_compression_ratio
        )
        
        # Get cache alignment
        cache_alignment = AdaptiveChunkSizer._get_cache_alignment(chunk_size)
        
        # Estimate compression ratio
        est_ratio = EntropyAnalyzer.estimate_compression_ratio(entropy)
        
        # Estimate latency
        chunk_count = AdaptiveChunkSizer.calculate_chunk_count(data_size, chunk_size)
        est_latency = LatencyEstimator.estimate_latency(
            data_size,
            chunk_size,
            est_ratio
        )
        
        # Build reasoning string
        reasoning = self._build_reasoning(
            entropy,
            entropy_category,
            chunk_size,
            data_size,
            chunk_count
        )
        
        result = ChunkAnalysis(
            original_size=data_size,
            entropy=entropy,
            entropy_category=entropy_category,
            recommended_chunk_size=chunk_size,
            reasoning=reasoning,
            cache_alignment=cache_alignment,
            expected_compression_ratio=est_ratio,
            estimated_latency_ms=est_latency
        )
        
        return result
    
    def _build_reasoning(
        self,
        entropy: float,
        category: str,
        chunk_size: int,
        data_size: int,
        chunks: int
    ) -> str:
        """Build human-readable reasoning for recommendation"""
        
        parts = [
            f"Data entropy: {entropy:.2f} bits/byte ({category})",
            f"Recommended chunk: {chunk_size:,} bytes ({chunk_size / 1024:.1f} KB)",
            f"Total chunks: {chunks} (overhead per chunk: ~0.5ms)",
        ]
        
        if category == "low":
            parts.append("→ Low entropy: using smaller chunks to maximize compression")
        elif category == "medium":
            parts.append("→ Medium entropy: balanced chunk size")
        elif category == "high":
            parts.append("→ High entropy: using larger chunks to amortize overhead")
        else:
            parts.append("→ Random data: using largest safe chunk size")
        
        return " | ".join(parts)
    
    def generate_chunks(
        self,
        data: bytes,
        analysis: Optional[ChunkAnalysis] = None
    ) -> List[bytes]:
        """
        Generate chunks using recommended size.
        
        Args:
            data: Data to chunk
            analysis: Pre-computed analysis (or None to compute)
            
        Returns:
            List of chunks
        """
        if analysis is None:
            analysis = self.analyze(data)
        
        chunk_size = analysis.recommended_chunk_size
        chunks = []
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def print_analysis(self, analysis: ChunkAnalysis) -> None:
        """Pretty-print analysis results"""
        print(f"\n{'='*80}")
        print(f"ADAPTIVE CHUNK ANALYSIS")
        print(f"{'='*80}")
        print(f"Data size: {analysis.original_size:,} bytes ({analysis.original_size/1024:.1f} KB)")
        print(f"Entropy: {analysis.entropy:.2f} bits/byte ({analysis.entropy_category})")
        print(f"Recommended chunk size: {analysis.recommended_chunk_size:,} bytes")
        print(f"Cache alignment: {analysis.cache_alignment} bytes")
        print(f"Expected compression ratio: {analysis.expected_compression_ratio:.2f}x")
        print(f"Estimated latency: {analysis.estimated_latency_ms:.2f} ms")
        print(f"\nReasoning: {analysis.reasoning}")
        print(f"{'='*80}\n")


# Helper functions for quick access
def analyze_data(data: bytes) -> ChunkAnalysis:
    """Quick analyze wrapper"""
    optimizer = AdaptiveChunkOptimizer()
    return optimizer.analyze(data)


def get_optimal_chunk_size(data: bytes) -> int:
    """Quick get chunk size"""
    analysis = analyze_data(data)
    return analysis.recommended_chunk_size


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Generate test data with different entropy levels
    test_cases = {
        "low_entropy": b"aaaaabbbbbcccccdddddeeeeeffffgggg" * 100,  # Repetitive
        "medium_entropy": os.urandom(8192),  # Random
        "json_like": b'{"id": 1, "name": "test", "value": 123}\n' * 100,
    }
    
    optimizer = AdaptiveChunkOptimizer()
    
    for name, data in test_cases.items():
        print(f"\n{name}: {len(data)} bytes")
        analysis = optimizer.analyze(data)
        optimizer.print_analysis(analysis)
