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
    from utils.profiling.profile_versioning import (
        ProfileVersionManager, ProfileVersion, VersionStatus,
        ProfileUpgradeManager, ExperimentalVersionManager,
        UpgradeInformation, UpgradeAuditLog,
    )
    __all__ = [
        "ProfileVersionManager", "ProfileVersion", "VersionStatus",
        "ProfileUpgradeManager", "ExperimentalVersionManager",
        "UpgradeInformation", "UpgradeAuditLog",
    ]
except ImportError:
    __all__ = []
