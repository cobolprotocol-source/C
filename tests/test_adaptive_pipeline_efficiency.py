import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adaptive_pipeline import AdaptivePipeline


def test_adaptive_pipeline_high_ratio():
    # synthetic low-entropy data (repeated pattern)
    pattern = b"ABC123xyz" * 1000
    data = pattern * 1000  # ~9MB of repeated data
    pipeline = AdaptivePipeline()

    compressed, meta = pipeline.compress_with_monitoring(data, adaptive=True)
    ratio = len(data) / len(compressed) if len(compressed) > 0 else 0
    # Assert we hit target ratio
    assert ratio >= 500, f"ratio {ratio:.2f} < 500"

    # decompress and verify lossless
    decompressed, meta2 = pipeline.decompress_with_monitoring(compressed)
    assert decompressed == data

    # ensure metadata reports output sizes correctly
    assert meta['output_size'] == len(compressed)
    assert meta2['output_size'] == len(data)

    # metadata should include per-layer statistics after decompression
    assert isinstance(meta2.get('per_layer_stats'), list)
    # verify we recorded stats for at least layer 3 (delta layer)
    assert any(entry.get('layer') == 3 for entry in meta2['per_layer_stats'])
