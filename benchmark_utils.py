# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Utilities for collecting benchmark environment metadata."""
import platform
import os
import re
from typing import Dict, Optional


def _read_proc_field(path: str, field: str) -> Optional[str]:
    try:
        with open(path, 'r') as f:
            for line in f:
                if line.startswith(field + ':'):
                    return line.split(':', 1)[1].strip()
    except FileNotFoundError:
        pass
    return None


def get_cpu_model() -> str:
    """Return a human-readable CPU model string."""
    # try platform first
    model = platform.processor()
    if model:
        return model
    # fallback to /proc/cpuinfo
    info = _read_proc_field('/proc/cpuinfo', 'model name')
    return info or 'unknown'


def get_total_ram_gb() -> float:
    """Return total RAM in gigabytes (approx)."""
    mem = _read_proc_field('/proc/meminfo', 'MemTotal')
    if mem:
        # value is like "16384256 kB"
        parts = mem.split()
        try:
            kb = float(parts[0])
            return kb / 1024 / 1024
        except Exception:
            pass
    # fallback using platform
    try:
        import subprocess
        out = subprocess.check_output(['grep', 'MemTotal', '/proc/meminfo']).decode()
        kb = float(out.split()[1])
        return kb / 1024 / 1024
    except Exception:
        return 0.0


def collect_environment_info(io_medium: Optional[str] = None, cache_state: str = 'cold') -> Dict[str, str]:
    """Gather metadata required for benchmarks.

    Arguments:
        io_medium: description of the IO medium (e.g. 'NVMe SSD', 'HDD').
        cache_state: either 'cold' or 'warm'.
    """
    return {
        'cpu_model': get_cpu_model(),
        'ram_gb': f"{get_total_ram_gb():.2f}",
        'io_medium': io_medium or 'unspecified',
        'cache_state': cache_state,
        'platform': platform.platform(),
    }
