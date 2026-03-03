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
STUB: backward-compatible re-export of profile_versioning.

The real implementation has been migrated to ``utils.profiling.profile_versioning``.
This stub ensures existing imports continue to work.
"""

try:
    from utils.profiling.profile_versioning import (
        ProfileVersionManager,
        ProfileUpgradeManager,
        ExperimentalVersionManager,
        ProfileVersion,
        VersionStatus,
        UpgradeReason,
        FallbackReason,
        load_version_manager,
        create_upgrade_manager,
        create_experimental_manager,
    )
    __all__ = [
        "ProfileVersionManager",
        "ProfileUpgradeManager",
        "ExperimentalVersionManager",
        "ProfileVersion",
        "VersionStatus",
        "UpgradeReason",
        "FallbackReason",
        "load_version_manager",
        "create_upgrade_manager",
        "create_experimental_manager",
    ]
except ImportError:
    __all__ = []
