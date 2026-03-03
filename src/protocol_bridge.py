"""Backward-compatibility wrapper around the core protocol bridge.

The authoritative implementation lives in ``core/protocol_bridge.py``.  Tests
and external code continue to ``import src.protocol_bridge`` but under the
hood we simply re-export the classes from the ``core`` package so that there is
only one canonical definition of ``ProtocolLanguage`` and ``TypedBuffer``.
"""

from core.protocol_bridge import ProtocolLanguage, TypedBuffer, ProtocolBridge

# re-export names for ``from src.protocol_bridge import ...``
__all__ = ["ProtocolLanguage", "TypedBuffer", "ProtocolBridge"]
