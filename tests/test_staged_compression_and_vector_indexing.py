import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adaptive_pipeline import AdaptivePipeline
from vector_indexing import make_cobol_memory_record, prepare_bulk_for_pinecone


def test_staged_scaling_basic():
    data = (b"LOWENTROPY" * 1000) * 10
    p = AdaptivePipeline()
    # small stages to escalate conservatively
    compressed, meta = p.compress_with_staged_scaling(data, stages=[2, 10])
    assert isinstance(compressed, (bytes, bytearray))
    assert 'stages' in meta
    assert meta['input_size'] == len(data)


def test_vector_indexing_packaging():
    sample = b"COBOLPROTO" * 100
    rec = make_cobol_memory_record(sample)
    assert 'id' in rec and 'vector' in rec and 'metadata' in rec
    bulk = prepare_bulk_for_pinecone([rec])
    assert 'vectors' in bulk and isinstance(bulk['vectors'], list)
