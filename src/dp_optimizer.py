# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""DP Optimizer - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.dp_optimizer instead.
This module re-exports all symbols from utils.optimization.dp_optimizer for backward compatibility.
"""

from utils.optimization.dp_optimizer import (
    PrivacyBudgetAllocation,
    NoiseCache,
    DPDecision,
    DPWindowAggregation,
    NoiseSamplerBatch,
    DPDecisionCache,
    DPWindowBatcher,
    OptimizedDifferentialPrivacy,
    DPOverheadBenchmark,
)

__all__ = [
    "PrivacyBudgetAllocation",
    "NoiseCache",
    "DPDecision",
    "DPWindowAggregation",
    "NoiseSamplerBatch",
    "DPDecisionCache",
    "DPWindowBatcher",
    "OptimizedDifferentialPrivacy",
    "DPOverheadBenchmark",
]
