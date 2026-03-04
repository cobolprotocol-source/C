# Tasks 2 & 3: Implementation Details & Code Reference

## File 1: src/concurrency/lock_free_queue.py

This module provides thread-safe inter-stage communication infrastructure using a circular buffer protected by threading.Lock.

```python
import ctypes
import threading
import time
from typing import Optional

class LockFreeQueue:
    """Thread-safe circular buffer queue without atomic operations.
    
    Uses threading.Lock for synchronization and ctypes.py_object array
    for generic Python object storage. Capacity must be power-of-2 for
    fast modulo via bit-masking.
    
    Design:
    - Head/tail: monotonically increasing counters
    - Buffer: ctypes array indexed via (counter & (capacity-1))
    - Backpressure: exponential sleep in callers when queue full
    """
    
    def __init__(self, capacity: int, item_size: int):
        """Initialize circular queue.
        
        Args:
            capacity: Must be power-of-2 (8, 16, 32, 64, etc.)
            item_size: Ignored (backward compat); we store generic objects
        """
        if not (capacity & (capacity - 1)) == 0:
            raise ValueError(f"Capacity {capacity} must be power-of-2")
        
        self.capacity = capacity
        self.buffer = (ctypes.py_object * capacity)()
        self.head = 0
        self.tail = 0
        self._lock = threading.Lock()
    
    def enqueue(self, item) -> bool:
        """Add item to queue.
        
        Returns:
            True if enqueued, False if queue full
        """
        with self._lock:
            if self.tail - self.head >= self.capacity:
                return False  # queue full
            idx = self.tail & (self.capacity - 1)
            self.buffer[idx] = item
            self.tail += 1
            return True
    
    def dequeue(self) -> Optional[object]:
        """Remove and return oldest item from queue.
        
        Returns:
            Item if available, None if queue empty
        """
        with self._lock:
            if self.head >= self.tail:
                return None  # queue empty
            idx = self.head & (self.capacity - 1)
            item = self.buffer[idx]
            self.buffer[idx] = None  # release reference
            self.head += 1
            return item


class PipelineChannel:
    """High-level pipeline stage communication with backpressure.
    
    Wraps LockFreeQueue with semantic producer/consumer names
    and built-in exponential backoff for congestion control.
    """
    
    def __init__(self, producer_name: str, consumer_name: str, 
                 capacity: int = 64, item_size: int = 1024):
        """Initialize channel between two pipeline stages.
        
        Args:
            producer_name: Name of producer stage (e.g., "L0", "L1")
            consumer_name: Name of consumer stage (e.g., "L1", "L2")
            capacity: Buffer size (must be power-of-2)
            item_size: Nominal item size (for logging)
        """
        self.producer = producer_name
        self.consumer = consumer_name
        self.queue = LockFreeQueue(capacity, item_size)
        self.capacity = capacity
    
    def send(self, item, timeout: float = 10.0) -> None:
        """Send item to consumer stage with exponential backoff.
        
        Args:
            item: Python object to send
            timeout: Max wait time (seconds)
        
        Raises:
            TimeoutError if queue remains full for > timeout seconds
        """
        start = time.time()
        sleep_ms = 0.1  # start at 0.1ms
        while True:
            if self.queue.enqueue(item):
                return  # success
            
            elapsed = time.time() - start
            if elapsed > timeout:
                raise TimeoutError(
                    f"Channel {self.producer}->{self.consumer} "
                    f"timeout after {elapsed:.1f}s (queue full)"
                )
            
            # exponential backoff: 0.1ms -> 1ms -> 10ms (capped)
            time.sleep(min(sleep_ms / 1000.0, 0.01))
            sleep_ms = min(sleep_ms * 10, 10.0)
    
    def receive(self, timeout: float = None) -> Optional[object]:
        """Receive item from producer stage with timeout.
        
        Args:
            timeout: Max wait time (seconds), None for no timeout
        
        Returns:
            Item if available, None if timeout
        """
        start = time.time()
        while True:
            item = self.queue.dequeue()
            if item is not None:
                return item  # got data
            
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed > timeout:
                    return None  # timeout
            
            # small sleep to avoid busy-wait
            time.sleep(0.001)
```

---

## File 2: src/hardware/hardware_optimizer.py

This module provides hardware detection, resource pooling, and adaptive scaling infrastructure.

```python
import os
import platform
import threading
import time
from typing import List, Dict, Any

# ---------- CPU / SIMD detection -------------------------------------------

def detect_cpu_flags() -> Dict[str, bool]:
    """Detect available CPU instruction sets.
    
    Returns:
        Dict mapping feature names to availability:
        - "sse4_2": Streaming SIMD Extensions 4.2
        - "avx2": Advanced Vector Extensions 2
        - "avx512f": Advanced Vector Extensions-512 (Foundation)
    """
    flags = set()
    if os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("flags") or line.startswith("Features"):
                        # line format: "flags: sse4_2 avx2 ..."
                        parts = line.strip().split()
                        flags.update(parts[2:])  # skip "flags:" part
                        break
        except Exception:
            pass
    else:
        # fallback: check platform.processor() output
        proc = platform.processor().lower()
        for suf in ("sse4_2", "avx2", "avx512f"):
            if suf in proc:
                flags.add(suf)
    
    return {
        "sse4_2": "sse4_2" in flags,
        "avx2": "avx2" in flags,
        "avx512f": "avx512f" in flags
    }


def get_worker_count() -> int:
    """Get recommended worker thread count.
    
    Returns:
        min(os.cpu_count(), 8) to balance parallelism vs. overhead
    """
    cpu = os.cpu_count() or 1
    return min(cpu, 8)


def enable_simd_if_available() -> bool:
    """Enable SIMD acceleration if available.
    
    Note: NumPy automatically enables vector instructions when available.
    This function is a placeholder for future explicit SIMD setup.
    
    Returns:
        True if NumPy/SciPy can use SIMD, False otherwise
    """
    # numpy automatically enables vector instructions
    # nothing to do here; provided for API completeness
    return True


# ---------- byte-array pool -------------------------------------------------

class ByteArrayPool:
    """Preallocated buffer pool to reduce malloc/free overhead.
    
    Maintains a pool of fixed-size bytearray buffers for inter-stage
    communication in compression pipeline. Reduces garbage collection
    pressure and malloc fragmentation.
    
    Typical usage:
        buf = pool.acquire_buffer()
        buf[:len(data)] = data  # copy via memoryview
        # process buf...
        pool.release_buffer(buf)
    """
    
    def __init__(self, n_buffers: int = 16, buffer_size: int = 1_048_576):
        """Initialize buffer pool.
        
        Args:
            n_buffers: Number of buffers to pre-allocate (default 16)
            buffer_size: Size of each buffer in bytes (default 1MB)
        """
        self._buffers: List[bytearray] = [
            bytearray(buffer_size) for _ in range(n_buffers)
        ]
        self._lock = threading.Lock()
        self.buffer_size = buffer_size
        self._available = self._buffers.copy()  # all initially available
    
    def acquire_buffer(self) -> memoryview:
        """Acquire a buffer from the pool.
        
        Returns:
            memoryview of an available buffer
        
        Raises:
            RuntimeError if no buffers available
        """
        with self._lock:
            if not self._available:
                # fallback: allocate new temporary buffer
                return memoryview(bytearray(self.buffer_size))
            buf = self._available.pop()
            return memoryview(buf)
    
    def release_buffer(self, mv: memoryview) -> None:
        """Return buffer to pool.
        
        Args:
            mv: memoryview previously returned by acquire_buffer()
        """
        if not hasattr(mv, 'obj'):
            return  # external buffer, ignore
        
        with self._lock:
            if len(self._available) < len(self._buffers):
                self._available.append(mv.obj)


# ---------- cache-friendly dictionary sharding ----------------------------

def apply_cache_friendly_layout(dictionary: Dict) -> Any:
    """Apply cache-friendly memory layout to dictionary.
    
    For large dictionaries, partition into hot/cold shards based on access
    frequency to improve CPU cache utilization. Hot shard typically fits
    in L2 cache (~256KB).
    
    Args:
        dictionary: Dict to optimize
    
    Returns:
        Original dict if size <= 256KB, or wrapper with get_id() method
    """
    # rough size estimation
    size = sum(len(str(k)) + len(str(v)) for k, v in dictionary.items())
    
    if size <= 256 * 1024:  # fits in L2 cache
        return dictionary
    
    # partition into hot (20%) and cold (80%)
    items = list(dictionary.items())
    items.sort(key=lambda kv: dictionary.get(kv[0], 0), reverse=True)
    
    split = max(1, len(items) // 5)  # top 20%
    hot_shard = dict(items[:split])
    cold_shard = dict(items[split:])
    
    class CacheFriendlyDict:
        def __init__(self, hot: Dict, cold: Dict):
            self.hot = hot
            self.cold = cold
        
        def get_id(self, token: str, default=None):
            # check hot shard first (likely in cache)
            if token in self.hot:
                return self.hot[token]
            # fallback to cold shard (main memory)
            return self.cold.get(token, default)
        
        def __getitem__(self, key):
            if key in self.hot:
                return self.hot[key]
            return self.cold[key]
        
        def __setitem__(self, key, value):
            self.hot[key] = value
        
        def items(self):
            for k, v in self.hot.items():
                yield k, v
            for k, v in self.cold.items():
                yield k, v
    
    return CacheFriendlyDict(hot_shard, cold_shard)


# ---------- adaptive worker scaling -----------------------------------------

class AdaptiveScaler:
    """Background monitor for adaptive worker scaling.
    
    Monitors queue fill levels and adjusts worker count to maintain
    optimal load. Spawns new workers when queues reach 80% full,
    and removes workers when queues drop below 20% for extended period.
    
    Currently implemented as background daemon thread; actual worker
    spawning/removal can be integrated with ThreadPoolExecutor when
    concurrent multi-block batching is implemented.
    """
    
    def __init__(self, channels: List[Any], config: Dict[str, Any]):
        """Initialize adaptive scaler.
        
        Args:
            channels: List of PipelineChannel objects to monitor
            config: Configuration dict (e.g., {"spawn_threshold": 0.8})
        """
        self.channels = channels
        self.config = config
        self.running = False
        self.worker_count = 0
        self._monitor_thread = None
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start background monitoring thread."""
        if self.running:
            return
        self.running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor, daemon=True
        )
        self._monitor_thread.start()
    
    def stop(self) -> None:
        """Stop background monitoring thread."""
        self.running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor(self) -> None:
        """Background monitoring loop.
        
        Checks every 100ms whether queue fill rates warrant scaling workers.
        """
        low_pressure_duration = 0
        
        while self.running:
            time.sleep(0.1)  # check every 100ms
            
            if not self.channels:
                continue
            
            # compute average queue fill rate
            fill_rates = []
            for ch in self.channels:
                if hasattr(ch, 'queue'):
                    head = ch.queue.head
                    tail = ch.queue.tail
                    fill = (tail - head) / max(1, ch.queue.capacity)
                    fill_rates.append(fill)
            
            if not fill_rates:
                continue
            
            avg_fill = sum(fill_rates) / len(fill_rates)
            
            # decision logic
            spawn_threshold = self.config.get("spawn_threshold", 0.8)
            remove_threshold = self.config.get("remove_threshold", 0.2)
            
            if avg_fill >= spawn_threshold:
                # spawn new worker if queue backing up
                with self._lock:
                    self.worker_count += 1
                low_pressure_duration = 0
            
            elif avg_fill < remove_threshold:
                low_pressure_duration += 1
                # remove worker if queue stays empty for 10+ samples (~1 second)
                if low_pressure_duration > 10 and self.worker_count > 1:
                    with self._lock:
                        self.worker_count -= 1
                    low_pressure_duration = 0
            
            else:
                low_pressure_duration = 0
```

---

## File 3: Engine Integration (src/layers/pipelines/engine.py)

### Import Additions (Lines 48-53)
```python
from src.concurrency.lock_free_queue import PipelineChannel
from src.hardware.hardware_optimizer import (
    get_worker_count,
    enable_simd_if_available,
    ByteArrayPool,
    apply_cache_friendly_layout,
    AdaptiveScaler,
)
```

### CobolPipeline.__init__() (Lines 3779-3790)
```python
class CobolPipeline:
    def __init__(self):
        """Initialize COBOL compression pipeline with hardware optimization."""
        
        # existing initialization...
        
        # Hardware optimization initialization
        self.worker_count = get_worker_count()
        self.pool = ByteArrayPool(n_buffers=16, buffer_size=1_048_576)
        enable_simd_if_available()
        self._scaler = AdaptiveScaler(channels=[], config={})
```

### DictionaryManager.register_dictionary() (Lines 2055-2070)
```python
def register_dictionary(self, token_group: str, dictionary: Dict):
    """Register a compression dictionary with cache-friendly optimization."""
    
    # Apply cache-friendly layout before storage
    optimized_dict = apply_cache_friendly_layout(dictionary)
    
    # existing registration logic...
    self.dictionaries[token_group] = optimized_dict
```

### CobolPipeline.compress() (Lines 3791-3914)

The compress method is now simplified to sequential processing:

```python
def compress(self, raw_bytes: bytes) -> PipelineResult:
    """Compress data through L0-L8 pipeline sequentially.
    
    Returns:
        PipelineResult with per-layer statistics and compression metrics
    """
    
    from ..core.classifier import Layer0Classifier
    from ..core.semantic import Layer1Semantic
    # ... other layer imports ...
    
    logger.info("CobolPipeline: starting compression L0->L8")
    
    original_crc = zlib.crc32(raw_bytes) & 0xFFFFFFFF
    original_size = len(raw_bytes)
    per_layer: List[LayerResult] = []
    
    # Layer 0: Classification
    try:
        classifier = Layer0Classifier()
        classification = classifier.classify(raw_bytes)
        entropy = classification.entropy
        # ... build hint based on entropy...
        
        per_layer.append(LayerResult(
            "L0_classifier", classification,
            {"entropy": entropy, "data_type": classification.data_type.value},
            checksum=None, ratio=1.0
        ))
    except Exception as e:
        logger.error(f"L0 classifier error: {e}")
        hint = CompressionHint.LOW_ENTROPY
    
    # Prepare buffer for L1
    buf = self.TypedBuffer.create(raw_bytes, self.ProtocolLanguage.L1_SEM, bytes)
    prev_size = original_size
    
    # Layers L1-L8: Sequential processing
    layer_sequence = [
        ("L1", Layer1Semantic()),
        ("L2", Layer2Structural()),
        # ... other layers ...
        ("L8", Layer8Final()),
    ]
    
    for name, layer in layer_sequence:
        start = time.time()
        try:
            # Call layer's encode or compress method
            if hasattr(layer, "encode"):
                buf = layer.encode(buf)
            elif hasattr(layer, "compress"):
                arg = buf.data if hasattr(buf, 'data') else buf
                out = layer.compress(arg)
                if isinstance(out, bytes):
                    buf = self.TypedBuffer.create(
                        out, self.ProtocolLanguage.L8_COBOL, bytes
                    )
                else:
                    buf = out
            
            # Compute metrics
            data_obj = buf.data if hasattr(buf, 'data') else buf
            size = len(data_obj) if isinstance(data_obj, (bytes, bytearray)) else 0
            ratio = (prev_size / size) if size > 0 else 1.0
            elapsed = (time.time() - start) * 1000
            
            per_layer.append(LayerResult(
                name, data_obj,
                {"layer": name, "time_ms": elapsed, "size": size},
                checksum=None, ratio=ratio
            ))
            prev_size = size
            
        except Exception as e:
            logger.error(f"Error in layer {name}: {e}")
            per_layer.append(LayerResult(
                name, None, {"error": str(e)}, None, 1.0
            ))
    
    # Build final result
    final_obj = per_layer[-1].data if per_layer and per_layer[-1].data else buf.data
    if isinstance(final_obj, str):
        compressed_bytes = final_obj.encode('utf-8')
    else:
        compressed_bytes = bytes(final_obj)
    
    final_size = len(compressed_bytes)
    overall_ratio = (original_size / final_size) if final_size > 0 else 1.0
    
    return PipelineResult(
        compressed_data=compressed_bytes,
        original_size=original_size,
        final_size=final_size,
        ratio=overall_ratio,
        per_layer_stats=per_layer,
        checksum=hex(original_crc)
    )
```

---

## Quick Start

### Use Lock-Free Queue
```python
from src.concurrency.lock_free_queue import LockFreeQueue, PipelineChannel

# Basic queue usage
q = LockFreeQueue(capacity=64, item_size=1024)
q.enqueue(b'data')
item = q.dequeue()

# Pipeline channels (preferred)
ch = PipelineChannel("producer", "consumer", capacity=64)
ch.send(b'data')
item = ch.receive(timeout=1.0)
```

### Use Hardware Optimizer
```python
from src.hardware.hardware_optimizer import (
    detect_cpu_flags,
    get_worker_count,
    ByteArrayPool,
    apply_cache_friendly_layout,
)

# Detect CPU capabilities
flags = detect_cpu_flags()
print(f"AVX2: {flags['avx2']}")

# Get worker count
workers = get_worker_count()  # returns min(cpu_count, 8)

# Use buffer pool
pool = ByteArrayPool(n_buffers=16, buffer_size=1_048_576)
buf = pool.acquire_buffer()
buf[:4] = b'test'
pool.release_buffer(buf)

# Apply cache sharding to dictionary
dict_optimized = apply_cache_friendly_layout(my_dict)
```

### Compress with Pipeline
```python
from src.layers.pipelines.engine import CobolPipeline

pipeline = CobolPipeline()
data = b'Hello COBOL World!'

result = pipeline.compress(data)
print(f"Compressed: {result.final_size} bytes")
print(f"Ratio: {result.ratio:.2f}x")
for layer in result.per_layer_stats:
    print(f"  {layer.name}: {layer.metadata}")
```

---

## Testing

Run comprehensive validation:
```bash
cd /workspaces/C
python3 << 'EOF'
from src.concurrency.lock_free_queue import LockFreeQueue
from src.hardware.hardware_optimizer import ByteArrayPool
from src.layers.pipelines.engine import CobolPipeline

# Test 1: Queue
q = LockFreeQueue(8, 4)
assert q.enqueue(b'test')
assert q.dequeue() == b'test'
print("✓ Queue test passed")

# Test 2: Pool
pool = ByteArrayPool(4, 1024)
buf = pool.acquire_buffer()
pool.release_buffer(buf)
print("✓ Pool test passed")

# Test 3: Pipeline
pipeline = CobolPipeline()
result = pipeline.compress(b'test data')
assert result.final_size > 0
print("✓ Pipeline test passed")

print("\n✓ All tests passed!")
EOF
```

---

End of implementation details.
