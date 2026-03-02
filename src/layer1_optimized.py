# backward‑compatibility shim
from core.l1_structure.layer1_optimized import *  # noqa: F401,F403

__all__ = getattr(__import__('core.l1_structure.layer1_optimized', fromlist=['__all__']), '__all__', [])
