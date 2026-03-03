"""
COBOL Protocol - Compression Layers Module

This module groups all compression layers (L0-L8) into organized sub-modules:
- core: L0-L4 base layers (classifier, semantic, structural, delta, bitpacking)
- advanced: L5-L8 optimized layers (RLE, patterns, entropy, extreme)
- variants: Alternative implementations and specialized variants
- pipelines: Layer orchestration and compression engine

For backward compatibility, main layers are re-exported here.

Example:
    from src.layers import CobolEngine           # Main orchestrator
    from src.layers.core import Layer1SemanticMapper  # L1 layer
    from src.layers.advanced import OptimizedLayer5Pipeline  # L5 layer
"""

# Main Orchestrator - import first to avoid circular deps
try:
    from .pipelines import CobolEngine
except ImportError:
    CobolEngine = None

# Core Layers (L0-L4) - with fallback
try:
    from .core import (
        Layer0Classifier,
        Layer1SemanticMapper,
        Layer2StructuralMapper,
        Layer3DeltaEncoder,
        Layer4BitPacking,
    )
except ImportError:
    Layer0Classifier = None
    Layer1SemanticMapper = None
    Layer2StructuralMapper = None
    Layer3DeltaEncoder = None
    Layer4BitPacking = None

# Advanced Layers (L5-L8) - with fallback
try:
    from .advanced import (
        OptimizedLayer5Pipeline,
        OptimizedLayer6Pipeline,
        OptimizedLayer7Pipeline,
        OptimizedL5L8Pipeline,
    )
except ImportError:
    OptimizedLayer5Pipeline = None
    OptimizedLayer6Pipeline = None
    OptimizedLayer7Pipeline = None
    OptimizedL5L8Pipeline = None

__all__ = [
    # Orchestrator
    "CobolEngine",
    # Core L0-L4
    "Layer0Classifier",
    "Layer1SemanticMapper",
    "Layer2StructuralMapper",
    "Layer3DeltaEncoder",
    "Layer4BitPacking",
    # Advanced L5-L8
    "OptimizedLayer5Pipeline",
    "OptimizedLayer6Pipeline",
    "OptimizedLayer7Pipeline",
    "OptimizedL5L8Pipeline",
]
