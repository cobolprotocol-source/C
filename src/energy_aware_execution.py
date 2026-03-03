#!/usr/bin/env python3

"""
Energy-Aware Execution Layer - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.energy_aware instead.
This module re-exports all symbols from utils.optimization.energy_aware for backward compatibility.
"""

from utils.optimization.energy_aware import (
    EnergyMeasure,
    EnergyProfile,
    EnergyBudget,
    MemoryAccessPattern,
    StopConditionType,
    CompressionStopCondition,
    SIMDArchitecture,
    SIMDBatchConfig,
    SIMDCompressionKernel,
    NUMANode,
    NUMAScheduler,
    EnergyExecutionStats,
    EnergyAwareCompressionController,
)

__all__ = [
    "EnergyMeasure",
    "EnergyProfile",
    "EnergyBudget",
    "MemoryAccessPattern",
    "StopConditionType",
    "CompressionStopCondition",
    "SIMDArchitecture",
    "SIMDBatchConfig",
    "SIMDCompressionKernel",
    "NUMANode",
    "NUMAScheduler",
    "EnergyExecutionStats",
    "EnergyAwareCompressionController",
]
