"""Backward-compatibility package for layer2 v1.1 API.

This subpackage aggregates the various classes that used to live under
``src/layer2`` prior to the reorganization.  It re-exports the
corresponding implementations from ``core/l2_dictionary``.
"""

from core.l2_dictionary.layer2 import (
    StructuralTokenizer,
    Layer2Encoder,
    Layer2Decoder,
    StructuralPattern,
)

# The newer structural-only implementation is still available at the
# top level for the v1.2+ tests.
from src.layer2_structural import Layer2Structural

__all__ = [
    "StructuralTokenizer",
    "Layer2Encoder",
    "Layer2Decoder",
    "StructuralPattern",
    "Layer2Structural",
]
