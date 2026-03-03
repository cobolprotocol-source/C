# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Buffer Pool Optimizer - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.buffer_pool_optimizer instead.
This module re-exports all symbols from utils.optimization.buffer_pool_optimizer for backward compatibility.
"""

from utils.optimization.buffer_pool_optimizer import (
    CompressionState,
    LayerContext,
    BufferPool,
    PipelineStateMachine,
    StatefulLayerProcessor,
    ContextFreePipelineWrapper,
    LatencyBreakdownAnalyzer,
)

__all__ = [
    "CompressionState",
    "LayerContext",
    "BufferPool",
    "PipelineStateMachine",
    "StatefulLayerProcessor",
    "ContextFreePipelineWrapper",
    "LatencyBreakdownAnalyzer",
]
