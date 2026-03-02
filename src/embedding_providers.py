"""Embedding provider helpers.

Provides a pluggable interface to obtain an embedding function. We include an
OpenAI-backed provider (if the `openai` package is installed) and a
deterministic hash-based fallback for offline testing.
"""
from typing import Callable, Optional, List
import hashlib


def get_openai_embedding_fn(api_key: Optional[str] = None, model: str = "text-embedding-3-small") -> Callable[[bytes], List[float]]:
    """Return a function that computes embeddings using OpenAI's API.

    If `openai` is not installed, returns the fallback embedding function.
    The returned function accepts raw bytes and returns a list[float].
    """
    try:
        import openai
        if api_key:
            openai.api_key = api_key

        def openai_fn(payload: bytes) -> List[float]:
            # OpenAI expects text; decode as latin1 to preserve bytes deterministically
            text = payload.decode('latin1')
            resp = openai.Embedding.create(input=[text], model=model)
            vec = resp['data'][0]['embedding']
            return list(map(float, vec))

        return openai_fn
    except Exception:
        return fallback_hash_embedding


def fallback_hash_embedding(payload: bytes, dim: int = 16) -> List[float]:
    """Deterministic fallback embedding using MD5 digest expanded to floats.

    Not suitable for real similarity but useful for testing/offline workflows.
    """
    digest = hashlib.md5(payload).digest()
    # repeat digest to reach desired dim
    out = []
    i = 0
    while len(out) < dim:
        b = digest[i % len(digest)]
        out.append((b / 255.0) * 2.0 - 1.0)
        i += 1
    return out[:dim]
