"""Lightweight connectors for Pinecone and Milvus.

These helpers avoid hard dependencies: callers should pass an initialized
client when possible. If the corresponding SDK is missing, the helpers raise
informative errors guiding how to provide a client or install the SDK.
"""
from typing import Any, Dict


def upsert_to_pinecone(payload: Dict[str, Any], client: Any = None, index_name: str | None = None):
    """Upsert vectors into Pinecone. `payload` should be the output of
    `prepare_bulk_for_pinecone()` (dict with 'vectors').

    - If `client` is provided, it will be used directly.
    - Otherwise the function will try to import the `pinecone` SDK and use
      the `Index(index_name)` helper.
    """
    if client is not None:
        # try common client shapes (pinecone.Index or pinecone.Client)
        if hasattr(client, 'upsert'):
            return client.upsert(vectors=payload['vectors'])
        if hasattr(client, 'Index') and index_name is not None:
            idx = client.Index(index_name)
            return idx.upsert(vectors=payload['vectors'])

    try:
        import pinecone
    except Exception:
        raise RuntimeError("Pinecone SDK not available. Install 'pinecone-client' or pass an initialized client.")

    if index_name is None:
        raise ValueError('index_name is required when using the pinecone SDK import path')

    idx = pinecone.Index(index_name)
    return idx.upsert(vectors=payload['vectors'])


def upsert_to_milvus(records: list, client: Any = None, collection_name: str | None = None):
    """Insert records into Milvus. `records` should be list of dicts each
    containing 'id', 'values', and optionally 'metadata'.

    - If `client` (pymilvus Collection or connection) is provided, it will
      be used. Otherwise attempts to import `pymilvus`.
    """
    if client is not None:
        # client might be a Collection-like object
        if hasattr(client, 'insert'):
            return client.insert(records)

    try:
        from pymilvus import Collection, connections
    except Exception:
        raise RuntimeError("pymilvus not available. Install 'pymilvus' or pass an initialized client.")

    if collection_name is None:
        raise ValueError('collection_name is required when using the pymilvus import path')

    # assume connections already established by caller
    col = Collection(collection_name)
    # Milvus expects list of fields; here we assume a simple vector-only schema
    vectors = [r['values'] for r in records]
    ids = [r['id'] for r in records]
    # insert as list of tuples if needed
    return col.insert([ids, vectors])
