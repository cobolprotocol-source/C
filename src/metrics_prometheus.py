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
STUB: backward-compatible re-export of metrics_prometheus.

The real implementation has been migrated to ``utils.metrics.metrics_prometheus``.
This stub ensures existing imports continue to work.
"""

try:
    from utils.metrics.metrics_prometheus import (
        create_pipeline_metrics_gauges,
    )
    __all__ = [
        "create_pipeline_metrics_gauges",
    ]
except ImportError:
    __all__ = []
