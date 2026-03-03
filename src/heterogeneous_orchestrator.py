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
STUB: backward-compatible re-export of heterogeneous_orchestrator.

The real implementation has been migrated to ``runtime.orchestrator.heterogeneous_orchestrator``.
This stub ensures existing imports continue to work.
"""

try:
    from runtime.orchestrator.heterogeneous_orchestrator import (
        HeterogeneousOrchestrator,
        DevicePool,
        GPUUpstream,
        FPGAMiddleTier,
        CPUDownstream,
        DeviceType,
        DeviceCapabilities,
        DeviceMetrics,
    )
    __all__ = [
        "HeterogeneousOrchestrator",
        "DevicePool",
        "GPUUpstream",
        "FPGAMiddleTier",
        "CPUDownstream",
        "DeviceType",
        "DeviceCapabilities",
        "DeviceMetrics",
    ]
except ImportError:
    __all__ = []
