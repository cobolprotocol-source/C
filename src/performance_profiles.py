# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""
STUB: backward-compatible re-export of performance_profiles.

The real implementation has been migrated to ``utils.profiling.performance_profiles``.
This stub ensures existing imports continue to work.
"""

try:
    from utils.profiling.performance_profiles import (
        PerformanceProfileManager,
        ProfileName,
        ProfileParameters,
        ProfileDefinition,
        HardwareInfo,
        ProfileSelection,
        CompressionDepth,
        PipelineMode,
        set_profile,
        auto_select_profile,
        get_active_profile,
        get_profile_parameters,
        explain_profile_selection,
        get_manager,
        initialize_profiles,
    )
    __all__ = [
        "PerformanceProfileManager",
        "ProfileName",
        "ProfileParameters",
        "ProfileDefinition",
        "HardwareInfo",
        "ProfileSelection",
        "CompressionDepth",
        "PipelineMode",
        "set_profile",
        "auto_select_profile",
        "get_active_profile",
        "get_profile_parameters",
        "explain_profile_selection",
        "get_manager",
        "initialize_profiles",
    ]
except ImportError:
    __all__ = []
