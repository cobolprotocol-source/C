# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Auto-tuner - BACKWARD COMPATIBILITY STUB

DEPRECATED: Use utils.optimization.auto_tuner instead.
This module re-exports all symbols from utils.optimization.auto_tuner for backward compatibility.
"""

from utils.optimization.auto_tuner import (
    LayerConfig,
    PipelineConfig,
    AutoTuner,
)

__all__ = [
    "LayerConfig",
    "PipelineConfig",
    "AutoTuner",
]

# For backwards compatibility, also re-export the imports
try:
    from utils.optimization.auto_tuner import DataType, ClassificationResult
    __all__.extend(["DataType", "ClassificationResult"])
except ImportError:
    pass
