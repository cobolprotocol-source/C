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
STUB: backward-compatible re-export of metrics.

The real implementation has been migrated to ``utils.metrics.metrics``.
This stub ensures existing imports continue to work.
"""

try:
    from utils.metrics.metrics import (
        Metrics,
        inc_evicted_count,
        set_global_patterns,
    )
    __all__ = [
        "Metrics",
        "inc_evicted_count",
        "set_global_patterns",
    ]
except ImportError:
    __all__ = []
