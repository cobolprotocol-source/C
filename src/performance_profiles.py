# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Backward-compatible stub for upgraded file location."""

try:
    from utils.profiling.performance_profiles import (
        PerformanceProfileManager, ProfileDefinition, ProfileParameters,
        ProfileSelection, HardwareInfo, CompressionDepth, PipelineMode,
        ProfileName, set_profile, auto_select_profile, get_active_profile,
        get_profile_parameters, explain_profile_selection, get_manager,
        initialize_profiles,
    )
    __all__ = [
        "PerformanceProfileManager", "ProfileDefinition", "ProfileParameters",
        "ProfileSelection", "HardwareInfo", "CompressionDepth", "PipelineMode",
        "ProfileName", "set_profile", "auto_select_profile",
        "get_active_profile", "get_profile_parameters",
        "explain_profile_selection", "get_manager", "initialize_profiles",
    ]
except ImportError:
    __all__ = []
