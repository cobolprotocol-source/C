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
STUB: backward-compatible re-export of profile_integration.

The real implementation has been migrated to ``utils.profiling.profile_integration``.
This stub ensures existing imports continue to work.
"""

try:
    from utils.profiling.profile_integration import (
        ProfileAwareCompressionEngine,
        ProfileMonitor,
        FallbackHandler,
        CompressionStats,
        ProfiledCompressedChunk,
        FallbackReason,
        create_profile_aware_engine,
        wrap_existing_engine,
    )
    __all__ = [
        "ProfileAwareCompressionEngine",
        "ProfileMonitor",
        "FallbackHandler",
        "CompressionStats",
        "ProfiledCompressedChunk",
        "FallbackReason",
        "create_profile_aware_engine",
        "wrap_existing_engine",
    ]
except ImportError:
    __all__ = []
