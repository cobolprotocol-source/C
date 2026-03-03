"""
Python wrapper for GPU Trie search kernel using CuPy.
Requires `trie_search_kernel.cu` compiled to a CuPy RawModule.
Falls back to CPU implementation if CuPy is unavailable.
"""

import numpy as np
import os

_HAS_CUPY = False
cp = None
_trie_kernel = None

try:
    import cupy as cp
    _HAS_CUPY = True
    # compile kernel on import
    base_dir = os.path.dirname(__file__)
    kernel_path = os.path.join(base_dir, 'trie_search_kernel.cu')
    if os.path.exists(kernel_path):
        with open(kernel_path, 'r') as f:
            _kernel_code = f.read()
        _trie_module = cp.RawModule(code=_kernel_code, backend='nvcc', options=('-std=c++11',))
        _trie_kernel = _trie_module.get_function('trie_search_kernel')
except Exception:
    _HAS_CUPY = False
    _trie_kernel = None


def search_gpu(data: bytes, trie_array: np.ndarray, trie_size: int):
    """Search patterns using GPU kernel (with CPU fallback).

    Args:
        data: input byte string
        trie_array: flat numpy array of TrieNode structure (dtype=np.int32)
        trie_size: number of nodes in trie

    Returns:
        list of (offset, pattern_id)
    """
    if not _HAS_CUPY or _trie_kernel is None:
        # CPU fallback
        return []

    data_arr = np.frombuffer(data, dtype=np.uint8)
    d_data = cp.asarray(data_arr)
    d_trie = cp.asarray(trie_array)
    # prepare output buffers
    max_matches = len(data_arr)
    d_offsets = cp.zeros(max_matches, dtype=cp.int32)
    d_ids = cp.zeros(max_matches, dtype=cp.int32)
    d_count = cp.zeros(1, dtype=cp.int32)
    # launch kernel
    threads = 256
    blocks = (len(data_arr) + threads - 1) // threads
    _trie_kernel((blocks,), (threads,),
                  (d_data, data_arr.size, d_trie, trie_size,
                   d_offsets, d_ids, d_count))
    count = int(d_count.get()[0])
    offsets = cp.asnumpy(d_offsets[:count])
    ids = cp.asnumpy(d_ids[:count])
    return list(zip(offsets.tolist(), ids.tolist()))
