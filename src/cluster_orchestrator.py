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
STUB: backward-compatible re-export of cluster_orchestrator.

The real implementation has been migrated to ``runtime.orchestrator.cluster_orchestrator``.
This stub ensures existing imports continue to work.
"""

try:
    from runtime.orchestrator.cluster_orchestrator import (
        MCDCOrchestrator,
        FederationProtocol,
        MobileContainerDC,
        MCDCLocation,
        NetworkLink,
        ReplicationStrategy,
        DeploymentRegion,
        CostOptimizationStrategy,
    )
    __all__ = [
        "MCDCOrchestrator",
        "FederationProtocol",
        "MobileContainerDC",
        "MCDCLocation",
        "NetworkLink",
        "ReplicationStrategy",
        "DeploymentRegion",
        "CostOptimizationStrategy",
    ]
except ImportError:
    __all__ = []
