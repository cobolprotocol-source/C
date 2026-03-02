import numpy as np
import time, os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.layer3_optimized import VectorizedDeltaEncoder


def test_rle_uniform_data():
    # create a large uniform block
    data = bytes([7]) * 100000
    encoder = VectorizedDeltaEncoder(block_size=4096)
    compressed, stats = encoder.compress(data)
    # expect very high compression ratio (>>500)
    assert stats['compression_ratio'] >= 500
    # decompress to verify lossless using the decoder class
    from layer3_optimized import VectorizedDeltaDecoder
    decoder = VectorizedDeltaDecoder()
    decompressed, dstats = decoder.decompress(compressed)
    assert decompressed == data
