import os
import platform
import threading
import time
from typing import List, Dict, Any

# ---------- CPU / SIMD detection -------------------------------------------

def detect_cpu_flags() -> Dict[str, bool]:
    flags = set()
    if os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("flags") or line.startswith("Features"):
                        parts = line.strip().split()
                        flags.update(parts[2:])
                        break
        except Exception:
            pass
    else:
        # fallback: platform.processor may include features
        proc = platform.processor()
        for suf in ("sse4_2", "avx2", "avx512f"):
            if suf in proc.lower():
                flags.add(suf)
    return {"sse4_2": "sse4_2" in flags,
            "avx2": "avx2" in flags,
            "avx512f": "avx512f" in flags}


def get_worker_count() -> int:
    cpu = os.cpu_count() or 1
    return min(cpu, 8)


def enable_simd_if_available() -> None:
    # numpy automatically enables vector instructions; nothing to do here
    pass


# ---------- byte-array pool -------------------------------------------------

class ByteArrayPool:
    """Preallocated fixed-size bytearray buffers for inter-stage communication."""

    def __init__(self, n_buffers: int = 16, buffer_size: int = 1_048_576):
        self._buffers: List[bytearray] = [bytearray(buffer_size) for _ in range(n_buffers)]
        self._lock = threading.Lock()
        self.buffer_size = buffer_size

    def acquire_buffer(self) -> memoryview:
        with self._lock:
            if self._buffers:
                return memoryview(self._buffers.pop())
        # fallback allocation (rare)
        return memoryview(bytearray(self.buffer_size))

    def release_buffer(self, mv: memoryview) -> None:
        buf = mv.obj if isinstance(mv, memoryview) else mv
        with self._lock:
            self._buffers.append(buf)


# ---------- cache-friendly dictionary layout -------------------------------

def apply_cache_friendly_layout(dictionary: Any) -> Any:
    try:
        size = len(dictionary.serialize())
    except Exception:
        return dictionary
    if size <= 256 * 1024:
        return dictionary
    # partition entries 80/20 by frequency
    freqs = getattr(dictionary, "frequencies", {})
    sorted_tokens = sorted(freqs.items(), key=lambda kv: kv[1], reverse=True)
    top_n = max(int(len(sorted_tokens) * 0.2), 1)
    hot = {t for t, _ in sorted_tokens[:top_n]}
    cold = {t for t, _ in sorted_tokens[top_n:]}
    hot_shard = {t: dictionary.token_to_id[t] for t in hot if t in dictionary.token_to_id}
    cold_shard = {t: dictionary.token_to_id[t] for t in cold if t in dictionary.token_to_id}

    def get_id(token):
        if token in hot_shard:
            return hot_shard[token]
        return cold_shard.get(token)

    def get_token(tok_id):
        for t, v in hot_shard.items():
            if v == tok_id:
                return t
        for t, v in cold_shard.items():
            if v == tok_id:
                return t
        return None

    dictionary.hot_shard = hot_shard
    dictionary.cold_shard = cold_shard
    dictionary.get_id = get_id
    dictionary.get_token = get_token
    return dictionary


# ---------- adaptive worker scaling ---------------------------------------

class AdaptiveScaler:
    """Background monitor that logs queue pressure and (optionally) resizes.

    Dynamic resizing is a placeholder; real resizing would require creating new
    ThreadPoolExecutors which is outside the scope of the existing pipeline.
    """

    def __init__(self, channels: List[Any], stage_executors: Dict[str, Any]):
        self.channels = channels
        self.executors = stage_executors
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def _monitor(self) -> None:
        low_count = 0
        while self._running:
            any_high = False
            any_low = True
            for ch in self.channels:
                cap = ch.queue.capacity
                head = ch.queue.head
                tail = ch.queue.tail
                fill = (tail - head) & (cap - 1)
                if fill > 0.8 * cap:
                    any_high = True
                if fill >= 0.2 * cap:
                    any_low = False
            if any_high:
                # placeholder action: log
                # actual worker spawn would be handled here
                # e.g. increase self.executors[ch.consumer_stage]._max_workers
                pass
            if any_low:
                low_count += 1
            else:
                low_count = 0
            if low_count * 0.1 >= 5:
                # after 5 seconds of low load
                pass
            time.sleep(0.1)

    def stop(self) -> None:
        self._running = False
        self._thread.join()
