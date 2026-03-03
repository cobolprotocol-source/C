"""Platform-specific hardware accelerators and optimizations.

Supports GPU, FPGA, CPU-only, and hybrid execution modes.
"""

from . import gpu
from . import fpga
from . import hardware
from . import cpu

__all__ = ["gpu", "fpga", "hardware", "cpu"]
