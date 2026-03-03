"""Core package for COBOL Protocol layers.

This package hosts the restructured implementations of layers L0-L8
and helpers like `protocol_bridge` used internally by the core logic.

The top-level `core` package is intentionally lightweight and primarily
serves as a namespace for the individual layer subpackages.  It is
marked as a package by this __init__.py so that imports such as
`from core.l1_structure.layer1_semantic import Layer1Semantic`
continue to work.
"""

__all__ = [
    # expose the major subpackages for convenience
    "l0_classifier",
    "l1_structure",
    "l2_dictionary",
    "l3_reduction",
    "l4_enhancement",
    "l5_entropy",
    "l6_deep",
    "l7_extreme",
    "l8_archival",
    "protocol_bridge",
]
