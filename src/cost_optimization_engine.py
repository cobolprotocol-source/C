# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Cost Optimization Engine - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.cost_optimization_engine instead.
This module re-exports all symbols from utils.optimization.cost_optimization_engine for backward compatibility.
"""

from utils.optimization.cost_optimization_engine import (
    CloudProvider,
    FPGABoardModel,
    StorageCost,
    ComprehensiveEconomicModel,
)

__all__ = [
    "CloudProvider",
    "FPGABoardModel",
    "StorageCost",
    "ComprehensiveEconomicModel",
]
