# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Backward-compatible stub for upgraded file location."""

try:
    from utils.profiling.profile_integration import (
        ProfileAwareCompressionEngine, ProfileMonitor, FallbackHandler,
        CompressionStats, ProfiledCompressedChunk, FallbackReason,
        create_profile_aware_engine, wrap_existing_engine,
    )
    __all__ = [
        "ProfileAwareCompressionEngine", "ProfileMonitor", "FallbackHandler",
        "CompressionStats", "ProfiledCompressedChunk", "FallbackReason",
        "create_profile_aware_engine", "wrap_existing_engine",
    ]
except ImportError:
    __all__ = []
