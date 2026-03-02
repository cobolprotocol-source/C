import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adaptive_pipeline import AdaptivePipeline
from src.vector_indexing import make_cobol_memory_record, prepare_bulk_for_pinecone


def test_staged_scaling_basic():
    data = (b"LOWENTROPY" * 1000) * 10
    p = AdaptivePipeline()
    # small stages to escalate conservatively
    compressed, meta = p.compress_with_staged_scaling(data, stages=[2, 10])
    assert isinstance(compressed, (bytes, bytearray))
    assert 'stages' in meta
    assert meta['input_size'] == len(data)


def test_export_callback_invoked():
    data = b"A" * 1024
    p = AdaptivePipeline()
    calls = []

    def cb(rec):
        calls.append(rec)

    compressed, meta = p.compress_with_staged_scaling(data, stages=[2, 4], export_callback=cb)
    # callback should have been called at each stage (2 stages)
    assert len(calls) == 2
    for rec in calls:
        assert 'payload' in rec and isinstance(rec['payload'], (bytes, bytearray))


def test_export_with_embedding():
    data = b"B" * 512
    p = AdaptivePipeline()
    calls = []

    def cb(rec):
        calls.append(rec)

    # simple embedding fn that returns fixed-length vector
    def embed_fn(payload):
        return [len(payload) % 256] * 8

    compressed, meta = p.compress_with_staged_scaling(data, stages=[2], export_callback=cb, embedding_fn=embed_fn)
    assert len(calls) == 1
    assert 'vector' in calls[0]
    assert calls[0]['vector'] == [len(calls[0]['payload']) % 256] * 8


def test_vector_indexing_packaging():
    sample = b"COBOLPROTO" * 100
    rec = make_cobol_memory_record(sample)
    assert 'id' in rec and 'vector' in rec and 'metadata' in rec
    bulk = prepare_bulk_for_pinecone([rec])
    assert 'vectors' in bulk and isinstance(bulk['vectors'], list)
