# ============================================================================
# COBOL Protocol - Deterministic Safety Header
# Layer: Core Interfaces (L0)
# Deterministic: YES
# Platform Safety: EDGE / DESKTOP / INDUSTRIAL
# WARNING: This file defines core contracts. Only formatting or comments
# are permitted here. Do NOT modify executable code, control flow, or
# algorithmic behavior. Any change may affect determinism.
# ============================================================================

"""Core compression interfaces and utilities.

Semua strategi kompresi harus mewarisi :class:`BaseCompressionStrategy` agar API
terstandarisasi di seluruh kode.  Modul ini juga menyediakan konteks eksekusi
(strategy pattern) dan pengecualian khusus.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

# import energy module lazily to avoid circular imports
try:
    from .energy_aware_execution import EnergyAwareCompressionController
except ImportError:
    EnergyAwareCompressionController = None  # type: ignore


class CompressionError(Exception):
    """Raised when compression fails."""


class DecompressionError(Exception):
    """Raised when decompression fails."""


class BaseCompressionStrategy(ABC):
    """Abstract base class for all compression/decompression implementations.

    Subclasses **must** implement :py:meth:`compress` and :py:meth:`decompress`.
    The optional :py:meth:`youtube` method can be used to expose metadata such as
    name, version or tuning knobs for diagnostics or documentation.
    """

    @abstractmethod
    def compress(self, data: bytes, **kwargs: Any) -> bytes:
        """Compress ``data`` and return the compressed blob.

        Args:
            data: Plain input bytes.
            **kwargs: Implementation-specific parameters (e.g. ``level``).

        Raises:
            CompressionError: when compression cannot be performed.
        """

    @abstractmethod
    def decompress(self, data: bytes, **kwargs: Any) -> bytes:
        """Reverse ``compress`` and return original bytes.

        Args:
            data: Compressed byte sequence produced by :meth:`compress`.
            **kwargs: Parameters that mirror those of :meth:`compress`.

        Raises:
            DecompressionError: when the blob is invalid or corrupted.
        """

    def youtube(self) -> Dict[str, Any]:
        """Return a simple dictionary of metadata (optional).

        Conventionally it should contain ``name`` and ``version`` keys but
        callers should treat the contents as opaque.
        """
        return {"name": self.__class__.__name__}


@dataclass
class CompressionContext:
    """Context wrapper that applies a compression strategy.

    This class implements the *Strategy* pattern.  A user constructs the context
    with a concrete :class:`BaseCompressionStrategy` and then calls
    :meth:`compress` or :meth:`decompress`.  The context is responsible for
    timing the call and optionally notifying an
    :class:`energy_aware_execution.EnergyAwareCompressionController`.
    """

    strategy: BaseCompressionStrategy
    energy_controller: Optional[EnergyAwareCompressionController] = None

    def compress(self, data: bytes, **kwargs: Any) -> bytes:
        """Compress data using the configured strategy.

        Time the operation and forward metrics to ``energy_controller`` if
        provided.
        """
        start = time.perf_counter()
        try:
            result = self.strategy.compress(data, **kwargs)
        except Exception as e:
            raise CompressionError(str(e)) from e
        elapsed = time.perf_counter() - start

        if self.energy_controller:
            try:
                self.energy_controller.plan_compression(
                    input_size_bytes=len(data),
                    target_ratio=(len(result) / len(data)) if data else 1.0,
                )
            except Exception:  # controller is advisory
                pass

        # optionally log; user may inspect ``strategy.youtube()`` metadata
        return result

    def decompress(self, data: bytes, **kwargs: Any) -> bytes:
        """Decompress using the configured strategy.

        Timing is recorded but energy controller is not updated for decompression.
        """
        start = time.perf_counter()
        try:
            result = self.strategy.decompress(data, **kwargs)
        except Exception as e:
            raise DecompressionError(str(e)) from e
        elapsed = time.perf_counter() - start
        return result
