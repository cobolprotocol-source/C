"""
Core Compression Layers (L0-L4)

Provides the fundamental compression layers:
- L0: Data type classification and entropy analysis
- L1: Semantic mapping and tokenization
- L2: Structural mapping with token-to-ID encoding
- L3: Delta encoding and numeric compression
- L4: Bit-packing and binary pattern compression

Main implementations are in pipelines.engine module.
This module re-exports them for convenience.
"""

# Layer 0 classifier (always available)
try:
    from .classifier import Layer0Classifier, DataType, ClassificationResult
except ImportError:
    Layer0Classifier = None
    DataType = None
    ClassificationResult = None

__all__ = [
    # L0
    "Layer0Classifier",
    "DataType",
    "ClassificationResult",
    # L1-L4 (lazy-loaded to avoid circular imports)
    "Layer1SemanticMapper",
    "Layer2StructuralMapper",
    "Layer3DeltaEncoder",
    "Layer4BitPacking",
]

# Lazy-load higher layer implementations to avoid circular imports with pipelines.engine
_layer_cache = {}

def __getattr__(name):
    """Lazy-load layer implementations on first access."""
    if name in _layer_cache:
        return _layer_cache[name]
    
    if name == "Layer1SemanticMapper":
        from ..pipelines.engine import Layer1SemanticMapper
        _layer_cache[name] = Layer1SemanticMapper
        return Layer1SemanticMapper
    elif name == "Layer2StructuralMapper":
        from ..pipelines.engine import Layer2StructuralMapper
        _layer_cache[name] = Layer2StructuralMapper
        return Layer2StructuralMapper
    elif name == "Layer3DeltaEncoder":
        from ..pipelines.engine import Layer3DeltaEncoder
        _layer_cache[name] = Layer3DeltaEncoder
        return Layer3DeltaEncoder
    elif name == "Layer4BitPacking":
        from ..pipelines.engine import Layer4BitPacking
        _layer_cache[name] = Layer4BitPacking
        return Layer4BitPacking
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
