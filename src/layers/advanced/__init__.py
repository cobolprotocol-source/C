"""
Advanced Compression Layers (L5-L8)

Provides optimized higher-level compression layers:
- L5: Advanced Run-Length Encoding (RLE) with pattern detection
- L6: Cross-block pattern registry and metadata compression
- L7: Entropy coding using Huffman and Arithmetic coding
- L8: Extreme hardening with AES-256-GCM encryption and indexing

These layers build on top of L1-L4 core layers for maximum compression.
"""

from .rle import (
    OptimizedLayer5Pipeline,
    AdvancedRLEEncoder,
    AdvancedRLEDecoder,
)
from .patterns import OptimizedLayer6Pipeline
from .entropy import OptimizedLayer7Pipeline
from .extreme import OptimizedL5L8Pipeline

__all__ = [
    # L5
    "OptimizedLayer5Pipeline",
    "AdvancedRLEEncoder",
    "AdvancedRLEDecoder",
    # L6
    "OptimizedLayer6Pipeline",
    # L7
    "OptimizedLayer7Pipeline",
    # L5-L8 Combined
    "OptimizedL5L8Pipeline",
]
