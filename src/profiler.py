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
STUB: backward-compatible re-export of profiler.

The real implementation has been migrated to ``utils.profiling.profiler``.
This stub ensures existing imports continue to work.
"""

try:
    from utils.profiling.profiler import (
        CompressionProfiler,
        CompressionProfile,
        LayerProfile,
        StreamingProfile,
        BottleneckLevel,
        ProfileReporter,
        MemoryTracker,
        GPUMonitor,
    )
    __all__ = [
        "CompressionProfiler",
        "CompressionProfile",
        "LayerProfile",
        "StreamingProfile",
        "BottleneckLevel",
        "ProfileReporter",
        "MemoryTracker",
        "GPUMonitor",
    ]
except ImportError:
    __all__ = []
