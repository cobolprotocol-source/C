"""Layer 0: Data Type Classifier (backward-compatible stub).

This module re-exports from core.l0_classifier to maintain backward compatibility
with existing code that imports from src.layer0_classifier.

Actual implementation is in core/l0_classifier/__init__.py
"""

# Re-export all public symbols from the new location
from core.l0_classifier import (
    DataType,
    ClassificationResult,
    Layer0Classifier,
    __all__,
)

__all__ = ['DataType', 'ClassificationResult', 'Layer0Classifier']
