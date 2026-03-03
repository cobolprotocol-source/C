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

# Import main implementations from pipelines.engine
from ..pipelines.engine import (
    Layer1SemanticMapper,
    Layer2StructuralMapper,
    Layer3DeltaEncoder,
    Layer4BitPacking,
)

# Layer 0 classifier
try:
    from .classifier import Layer0Classifier, DataType, ClassificationResult
except ImportError:
    # Fallback if classifier not available
    Layer0Classifier = None
    DataType = None
    ClassificationResult = None

__all__ = [
    # L0
    "Layer0Classifier",
    "DataType",
    "ClassificationResult",
    # L1-L4 (from engine.py)
    "Layer1SemanticMapper",
    "Layer2StructuralMapper",
    "Layer3DeltaEncoder",
    "Layer4BitPacking",
]
