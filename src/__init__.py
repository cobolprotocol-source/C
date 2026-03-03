"""
COBOL Protocol - Nafal Faturizki Edition
Ultra-Extreme 8-Layer Decentralized Compression Engine

Package initialization and version information.
"""

__version__ = "1.0.0"
__author__ = "Senior Principal Engineer & Cryptographer"
__license__ = "Proprietary"

# Import from the actual implementation files
try:
    from .layers.pipelines.engine import (
        CobolEngine,
        DictionaryManager,
        AdaptiveEntropyDetector,
        Layer1SemanticMapper,
        Layer3DeltaEncoder,
        Dictionary,
        VarIntCodec,
        CompressionMetadata,
    )
except ImportError as e:
    print(f"⚠️  Warning loading core classes: {e}")
    # Fallback: try loading from the backward-compat stubs
    try:
        from .engine import CobolEngine
    except:
        CobolEngine = None
    
    DictionaryManager = None
    AdaptiveEntropyDetector = None
    Layer1SemanticMapper = None
    Layer3DeltaEncoder = None
    Dictionary = None
    VarIntCodec = None
    CompressionMetadata = None

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
