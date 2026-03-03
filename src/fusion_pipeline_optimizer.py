# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Fusion Pipeline Optimizer - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.fusion_pipeline_optimizer instead.
This module re-exports all symbols from utils.optimization.fusion_pipeline_optimizer for backward compatibility.
"""

from utils.optimization.fusion_pipeline_optimizer import (
    ExecutionContext,
    FusionPipelineOptimizer,
    ContextFreeCompressionWrapper,
    OptimizationProfiler,
)

__all__ = [
    "ExecutionContext",
    "FusionPipelineOptimizer",
    "ContextFreeCompressionWrapper",
    "OptimizationProfiler",
]
