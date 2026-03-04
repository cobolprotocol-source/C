"""Compatibility shim pointing to moved module in src.layers.variants.legacy_stubs."""
from src.layers.variants.legacy_stubs.layer5_optimized import OptimizedLayer5Pipeline, AdvancedRLEEncoder, AdvancedRLEDecoder
__all__ = ['OptimizedLayer5Pipeline', 'AdvancedRLEEncoder', 'AdvancedRLEDecoder']