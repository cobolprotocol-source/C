# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Integrated Adaptive Optimizer - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.integrated_adaptive_optimizer instead.
This module re-exports all symbols from utils.optimization.integrated_adaptive_optimizer for backward compatibility.
"""

from utils.optimization.integrated_adaptive_optimizer import (
    LatencySnapshot,
    LatencyStats,
    LatencyTracker,
    PercentileOptimizer,
    IntegratedAdaptiveOptimizer,
)

__all__ = [
    "LatencySnapshot",
    "LatencyStats",
    "LatencyTracker",
    "PercentileOptimizer",
    "IntegratedAdaptiveOptimizer",
]
