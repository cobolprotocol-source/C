"""Utilities to package compressed payloads into a COBOL Protocol memory record
ready for insertion into vector databases (Pinecone, Milvus, etc.).

This module intentionally avoids heavy ML dependencies; embedding generation
is left as a pluggable function (callable) so callers can provide their
preferred embedding model. The exporter produces a dict suitable for
insertion into vector stores: `id`, `vector`, `metadata`.
"""
from typing import Callable, Dict, Any, Optional
import hashlib
import time


def make_cobol_memory_record(payload: bytes, *, embedding_fn: Optional[Callable[[bytes], list]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a memory record from compressed payload.

    - `payload`: compressed bytes (COBOL Protocol binary)
    - `embedding_fn`: function(bytes)->list[float]; if None, creates a simple
      hash-based pseudo-vector (not suitable for real similarity search).
    - `metadata`: optional user metadata to attach (timestamps, source, tags)

    Returns a dict: {id, vector, metadata}
    """
    if metadata is None:
        metadata = {}

    # deterministic id from payload
    id_hash = hashlib.sha256(payload).hexdigest()

    # embedding: use provided fn or a stable fallback (not for production)
    if embedding_fn is not None:
        vector = embedding_fn(payload)
    else:
        # fallback: create small pseudo-vector using hash bytes -> float in [-1,1]
        digest = hashlib.md5(payload).digest()
        vector = [((b / 255.0) * 2.0 - 1.0) for b in digest]

    record = {
        "id": id_hash,
        "vector": vector,
        "metadata": {
            "cobol_protocol": True,
            "payload_len": len(payload),
            "created_at": time.time(),
            **(metadata or {}),
        },
    }

    return record


def prepare_bulk_for_pinecone(records: list) -> dict:
    """Prepare a bulk insertion payload for Pinecone-like APIs.

    Expects list of records as returned by `make_cobol_memory_record`.
    Returns a dict ready to pass to Pinecone client upsert.
    """
    vectors = []
    for r in records:
        vectors.append({
            "id": r["id"],
            "values": r["vector"],
            "metadata": r.get("metadata", {}),
        })
    return {"vectors": vectors}
