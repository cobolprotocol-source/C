"""Configuration constants and enums for Layer 2 (core package).

This module provides the minimal definitions required by other core
modules.  During the refactor we only include what the test suite
actually uses, but the original implementation contained more detailed
settings and enums.
"""

from enum import Enum


class CompressionLayer(Enum):
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6
    L7 = 7
    L8 = 8


# placeholder for maximum dictionary size used by layer2
L1_MAX_DICTIONARY_SIZE = 4096

__all__ = ["CompressionLayer", "L1_MAX_DICTIONARY_SIZE"]
