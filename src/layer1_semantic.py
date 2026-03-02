# backward‑compatibility shim
from core.l1_structure.layer1_semantic import *  # noqa: F401,F403

__all__ = getattr(__import__('core.l1_structure.layer1_semantic', fromlist=['__all__']), '__all__', [])
