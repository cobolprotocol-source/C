# ============================================================================
# COBOL Protocol - Deterministic Safety Header
# Layer: Core Interfaces (L0) - BACKWARD COMPATIBILITY STUB
# Deterministic: YES
# Platform Safety: EDGE / DESKTOP / INDUSTRIAL
# WARNING: This file is deprecated. Use interfaces.compression instead.
# This stub re-exports from the new location for backward compatibility.
# ============================================================================

"""Backward compatibility stub for core compression interfaces.

DEPRECATED: Use interfaces.compression instead.
This module re-exports all symbols from interfaces.compression for backward compatibility.
"""

# Re-export all public symbols from the canonical location
from interfaces.compression import (
    CompressionError,
    DecompressionError,
    BaseCompressionStrategy,
    CompressionContext,
)

__all__ = [
    "CompressionError",
    "DecompressionError",
    "BaseCompressionStrategy",
    "CompressionContext",
]
