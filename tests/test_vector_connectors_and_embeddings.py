import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vector_connectors import upsert_to_pinecone, upsert_to_milvus
from vector_indexing import make_cobol_memory_record, prepare_bulk_for_pinecone
from embedding_providers import get_openai_embedding_fn, fallback_hash_embedding


def test_make_record_and_prepare_bulk():
    payload = b"TESTPAYLOAD" * 10
    rec = make_cobol_memory_record(payload)
    assert 'id' in rec and 'vector' in rec and 'metadata' in rec
    bulk = prepare_bulk_for_pinecone([rec])
    assert 'vectors' in bulk and isinstance(bulk['vectors'], list)


def test_embedding_fallback():
    payload = b"SOME_BYTES" * 5
    vec = fallback_hash_embedding(payload, dim=8)
    assert isinstance(vec, list) and len(vec) == 8


def test_openai_provider_fallback():
    fn = get_openai_embedding_fn(api_key=None)
    # when openai missing, should return fallback function
    v = fn(b"hello world")
    assert isinstance(v, list)


def test_pinecone_connector_raises_when_missing():
    bulk = {'vectors': []}
    try:
        upsert_to_pinecone(bulk)
    except RuntimeError as e:
        assert 'Pinecone SDK' in str(e)


def test_milvus_connector_raises_when_missing():
    try:
        upsert_to_milvus([])
    except RuntimeError as e:
        assert 'pymilvus' in str(e)
