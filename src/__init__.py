"""
COBOL Protocol - Nafal Faturizki Edition
Ultra-Extreme 8-Layer Decentralized Compression Engine

Package initialization and version information.
"""

__version__ = "1.0.0"
__author__ = "Senior Principal Engineer & Cryptographer"
__license__ = "Proprietary"

from engine import (
    CobolEngine,
    DictionaryManager,
    AdaptiveEntropyDetector,
    Layer1SemanticMapper,
    Layer3DeltaEncoder,
    Dictionary,
    VarIntCodec,
    CompressionMetadata,
)

__all__ = [
    "CobolEngine",
    "DictionaryManager",
    "AdaptiveEntropyDetector",
    "Layer1SemanticMapper",
    "Layer3DeltaEncoder",
    "Dictionary",
    "VarIntCodec",
    "CompressionMetadata",
]
