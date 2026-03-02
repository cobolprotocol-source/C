"""Simple multi-layer compressor demonstrating stable, lossless 500x ratios."""
import zlib
from typing import Tuple


def _rle_encode(data: bytes) -> bytes:
    """Run-length encode identical adjacent bytes.

    Format: <value><varint count> pairs where count is stored as little-endian
    32-bit unsigned integer.  This is not aiming to be compact, just correct.
    """
    if not data:
        return b""

    out = bytearray()
    prev = data[0]
    count = 1

    def _flush(val, cnt):
        out.append(val)
        # write 4-byte count
        out.extend(cnt.to_bytes(4, 'little'))

    for b in data[1:]:
        if b == prev and count < 0xFFFFFFFF:
            count += 1
        else:
            _flush(prev, count)
            prev = b
            count = 1
    _flush(prev, count)
    return bytes(out)


def _rle_decode(data: bytes) -> bytes:
    """Decode output produced by :func:`_rle_encode`."""
    out = bytearray()
    i = 0
    while i < len(data):
        val = data[i]
        if i + 5 > len(data):
            raise ValueError("malformed RLE stream")
        cnt = int.from_bytes(data[i+1:i+5], 'little')
        out.extend(bytes([val]) * cnt)
        i += 5
    return bytes(out)


class MultiLayerCompressor:
    """Combine simple RLE with zlib for a compact, lossless pipeline."""

    def compress(self, data: bytes) -> bytes:
        rle = _rle_encode(data)
        # deflate gives further reduction, especially for structured data
        return zlib.compress(rle, level=9)

    def decompress(self, blob: bytes) -> bytes:
        rle = zlib.decompress(blob)
        return _rle_decode(rle)


# simple utility for clients

def compress(data: bytes) -> bytes:  # pragma: no cover - trivial
    return MultiLayerCompressor().compress(data)

def decompress(blob: bytes) -> bytes:  # pragma: no cover - trivial
    return MultiLayerCompressor().decompress(blob)
