import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.multi_layer_compressor import MultiLayerCompressor


def test_roundtrip_random():
    import os
    data = os.urandom(1024)
    comp = MultiLayerCompressor()
    blob = comp.compress(data)
    out = comp.decompress(blob)
    assert out == data


def test_high_ratio_repeated():
    # use single-byte data to exercise extreme RLE + zlib
    data = b"A" * 1_000_000  # 1MB of identical bytes
    comp = MultiLayerCompressor()
    blob = comp.compress(data)
    ratio = len(data) / len(blob)
    assert ratio >= 500, f"ratio {ratio:.2f} too low"
    out = comp.decompress(blob)
    assert out == data


def test_rle_encoding():
    from multi_layer_compressor import _rle_encode, _rle_decode
    data = b"AAABBBCCAA"
    enc = _rle_encode(data)
    dec = _rle_decode(enc)
    assert dec == data

