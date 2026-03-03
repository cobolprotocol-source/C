# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Adaptive Chunk Optimizer - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.adaptive_chunk_optimizer instead.
This module re-exports all symbols from utils.optimization.adaptive_chunk_optimizer for backward compatibility.
"""

from utils.optimization.adaptive_chunk_optimizer import (
    CacheConfig,
    ChunkAnalysis,
    EntropyAnalyzer,
    AdaptiveChunkSizer,
    LatencyEstimator,
    AdaptiveChunkOptimizer,
    analyze_data,
    get_optimal_chunk_size,
)

__all__ = [
    "CacheConfig",
    "ChunkAnalysis",
    "EntropyAnalyzer",
    "AdaptiveChunkSizer",
    "LatencyEstimator",
    "AdaptiveChunkOptimizer",
    "analyze_data",
    "get_optimal_chunk_size",
]
