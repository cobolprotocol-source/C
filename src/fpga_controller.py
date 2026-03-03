"""
FPGA Device Controller for COBOL v1.5 - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use platform.fpga.controller instead.
This module re-exports all symbols from platform.fpga.controller for backward compatibility.
"""

from platform.fpga.controller import (
    MemoryTier,
    FPGAState,
    CAMEntry,
    HuffmanTable,
    FPGAMetrics,
    FPGABackend,
    FPGASimulator,
    RealFPGABackend,
    FPGAController,
    FPGACluster,
    PowerCoolingSpecs,
    MobileContainerDC,
    EconomicModel,
)

__all__ = [
    "MemoryTier",
    "FPGAState",
    "CAMEntry",
    "HuffmanTable",
    "FPGAMetrics",
    "FPGABackend",
    "FPGASimulator",
    "RealFPGABackend",
    "FPGAController",
    "FPGACluster",
    "PowerCoolingSpecs",
    "MobileContainerDC",
    "EconomicModel",
]

