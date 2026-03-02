"""
Extreme Engine Module - Layer 8 Ultra-Extreme Mapping
======================================================

This module introduces the global pattern registry and a lightweight
Layer 8 mapper which replaces very large recurring byte sequences with
small metadata pointers.  The goal is to support the final 1:100,000,000
compression leap by recognizing petabyte/terabyte scale patterns and
storing only 4-byte (or smaller) references.

The design is intentionally simplistic—a real implementation would use a
distributed, eventually-consistent registry with sharding, persistence,
and fast lookup (e.g. Cuckoo filters, B-tree, or RocksDB).  For the
purposes of this project we provide a minimal in-memory registry and a
``Layer8UltraExtremeMapper`` class that interacts with it.

Patterns are registered ahead of time ("training" phase) and assigned a
unique 32-bit identifier.  Compression replaces each occurrence of a
registered pattern in the input stream with the byte value ``0xFE``
followed by a varint-encoded pattern ID.  Decompression reverses the
process by looking up the ID in the registry.  An escape byte of
``0xFF`` is reserved for future layers (e.g. semantic escapes).

The ``ExtremeCobolEngine`` class demonstrates how Layer 8 can be
integrated with the existing ``CobolEngine`` pipeline—the new layer runs
*before* the existing L1/L3 stages so that ultra-common patterns are
removed early, further improving downstream compression.

Notes:
- The registry is global to all engines in a deployment and may be
  synchronized via a simple `serialize()`/`deserialize()` API.
- Pattern discovery for a real system would analyze corpora, dedupe,
  and evict old/rare entries.  Here we provide only an `add_pattern`
  helper and rudimentary size tracking.
- The target ratio of 1:100M is aspirational; this code is a proof of
  concept and does not actually attain that figure.

"""

import io
import hashlib
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from engine import CompressionMetadata, CompressionLayer, VarIntCodec, IntegrityError


# ---------------------------------------------------------------------------
# GLOBAL PATTERN REGISTRY
# ---------------------------------------------------------------------------

class GlobalPatternRegistry:
    """In-memory registry mapping large byte patterns to integer IDs.

    In a distributed deployment this object would be replaced by a
    consensus-backed service; here we provide basic serialization so the
    registry can be checkpointed or shipped between containers.
    """

    def __init__(self):
        self.pattern_to_id: Dict[bytes, int] = {}
        self.id_to_pattern: Dict[int, bytes] = {}
        self._next_id: int = 0

    def register(self, pattern: bytes) -> int:
        """Register a new pattern or return an existing ID.

        Patterns longer than a few kilobytes are ideal; the registry does
        not enforce any maximum size but callers should avoid extremely
        short values (they will conflict with lower layers).
        """
        if pattern in self.pattern_to_id:
            return self.pattern_to_id[pattern]
        pid = self._next_id
        self.pattern_to_id[pattern] = pid
        self.id_to_pattern[pid] = pattern
        self._next_id += 1
        return pid

    def lookup(self, pid: int) -> bytes:
        """Return the pattern associated with an ID, or raise KeyError."""
        return self.id_to_pattern[pid]

    def serialize(self) -> bytes:
        """Serialize registry to bytes (simple protobuf-like format).

        Format::
            [num_entries:4][id:4][len:4][pattern bytes]...  
        """
        out = io.BytesIO()
        out.write(struct.pack(">I", len(self.id_to_pattern)))
        for pid, pat in self.id_to_pattern.items():
            out.write(struct.pack(">I", pid))
            out.write(struct.pack(">I", len(pat)))
            out.write(pat)
        return out.getvalue()

    def deserialize(self, data: bytes) -> None:
        """Load registry state from serialized bytes."""
        buf = io.BytesIO(data)
        count_bytes = buf.read(4)
        if not count_bytes:
            return
        count = struct.unpack(">I", count_bytes)[0]
        for _ in range(count):
            pid = struct.unpack(">I", buf.read(4))[0]
            length = struct.unpack(">I", buf.read(4))[0]
            pat = buf.read(length)
            self.pattern_to_id[pat] = pid
            self.id_to_pattern[pid] = pat
            self._next_id = max(self._next_id, pid + 1)


# ---------------------------------------------------------------------------
# LAYER 8: ULTRA-EXTREME MAPPING
# ---------------------------------------------------------------------------

ESCAPE_BYTE = 0xFE  # reserved value for pattern pointers


class Layer8UltraExtremeMapper:
    """Compresses/decompresses using the global pattern registry.

    Compression replaces each registered pattern with an escape byte and
    a varint ID.  Decompression performs the inverse substitution.
    """

    def __init__(self, registry: GlobalPatternRegistry):
        self.registry = registry

    def compress(self, data: bytes) -> Tuple[bytes, CompressionMetadata]:
        original_size = len(data)
        output = bytearray()
        i = 0

        # naive scan: try longest patterns first
        sorted_patterns = sorted(self.registry.pattern_to_id.items(),
                                 key=lambda kv: -len(kv[0]))

        while i < len(data):
            replaced = False
            for pattern, pid in sorted_patterns:
                if data.startswith(pattern, i):
                    # write escape + varint id
                    output.append(ESCAPE_BYTE)
                    output.extend(VarIntCodec.encode(pid))
                    i += len(pattern)
                    replaced = True
                    break
            if not replaced:
                output.append(data[i])
                i += 1

        compressed_bytes = bytes(output)
        metadata = CompressionMetadata(
            block_id=0,
            original_size=original_size,
            compressed_size=len(compressed_bytes),
            compression_ratio=(original_size / len(compressed_bytes)) if len(compressed_bytes) > 0 else 1.0,
            layers_applied=[CompressionLayer.L8_ULTRA_EXTREME_MAPPING],
            integrity_hash=hashlib.sha256(data).digest(),
        )
        return compressed_bytes, metadata

    def decompress(self, data: bytes, metadata: CompressionMetadata) -> bytes:
        output = bytearray()
        i = 0
        while i < len(data):
            byte = data[i]
            if byte == ESCAPE_BYTE:
                # read varint id
                pid, consumed = VarIntCodec.decode(data, i + 1)
                pattern = self.registry.lookup(pid)
                output.extend(pattern)
                i += 1 + consumed
            else:
                output.append(byte)
                i += 1
        result = bytes(output)
        if metadata.integrity_hash:
            if hashlib.sha256(result).digest() != metadata.integrity_hash:
                raise IntegrityError("L8 decompression integrity check failed")
        return result


# ---------------------------------------------------------------------------
# EXTREME COBOL ENGINE WRAPPER
# ---------------------------------------------------------------------------

class ExtremeCobolEngine:
    """Wrapper around the base CobolEngine that injects Layer 8 at the
    beginning of the pipeline.

    This is purely illustrative; it creates its own global registry and
    allows callers to register patterns before compressing.
    """

    def __init__(self, config: dict = None):
        from engine import CobolEngine
        self.registry = GlobalPatternRegistry()
        self.layer8 = Layer8UltraExtremeMapper(self.registry)
        self.inner = CobolEngine(config)

    def register_pattern(self, pattern: bytes) -> int:
        """Add a pattern to the global registry."""
        return self.registry.register(pattern)

    def compress_block(self, data: bytes) -> Tuple[bytes, CompressionMetadata]:
        # first run through L8
        l8_out, l8_meta = self.layer8.compress(data)
        # then delegate to existing engine for remaining layers
        final_out, final_meta = self.inner.compress_block(l8_out)
        # if inner engine did not actually change the data, return only l8 metadata
        if final_out == l8_out:
            # adjust l8_meta to reflect original input size
            l8_meta.original_size = len(data)
            l8_meta.integrity_hash = hashlib.sha256(data).digest()
            return l8_out, l8_meta
        # merge metadata: keep L8 at front of effective layers
        merged = final_meta
        merged.layers_applied.insert(0, CompressionLayer.L8_ULTRA_EXTREME_MAPPING)
        merged.original_size = len(data)
        merged.integrity_hash = hashlib.sha256(data).digest()
        return final_out, merged

    def decompress_block(self, data: bytes, metadata: CompressionMetadata) -> bytes:
        # First undo Layer 8 itself, leaving data that inner engine
        # (L1/L3/etc.) can process normally.  Remove L8 from the metadata
        # before passing along so the inner engine does not try to interpret
        # escape pointers as semantic tokens.
        l8_data = self.layer8.decompress(data, metadata)
        # create a shallow copy of metadata with L8 stripped
        md_copy = CompressionMetadata(
            block_id=metadata.block_id,
            original_size=metadata.original_size,
            compressed_size=metadata.compressed_size,
            compression_ratio=metadata.compression_ratio,
            layers_applied=[l for l in metadata.layers_applied if l != CompressionLayer.L8_ULTRA_EXTREME_MAPPING],
            dictionary_versions=metadata.dictionary_versions,
            integrity_hash=metadata.integrity_hash,
            timestamp=metadata.timestamp,
            entropy_score=metadata.entropy_score,
        )
        return self.inner.decompress_block(l8_data, md_copy)
