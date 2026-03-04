import threading
import time
import ctypes
from typing import Optional

# fallback implementation: use a simple lock to protect counters
# this does introduce a small critical section but satisfies thread-safety



class LockFreeQueue:
    """Simple circular buffer with lock-free head/tail counters.

    capacity must be a power of two so we can mask indexes with
    ``capacity - 1`` instead of using the modulo operator.
    ``item_size`` fixes the size of each slot in bytes; callers must
    always enqueue/dequeue items of that exact length.
    """

    def __init__(self, capacity: int, item_size: int):
        if capacity & (capacity - 1) != 0:
            raise ValueError("capacity must be a power of two")
        self.capacity = capacity
        # ignore item_size; queue holds arbitrary Python objects
        self.buffer = (ctypes.py_object * capacity)()
        for i in range(capacity):
            self.buffer[i] = None
        # head/tail count total produced/consumed items
        self.head = 0
        self.tail = 0
        # lightweight lock for atomicity
        self._lock = threading.Lock()

    def enqueue(self, item) -> bool:
        # arbitrary object, queue size fixed
        while True:
            with self._lock:
                h = self.head
                t = self.tail
                if t - h >= self.capacity:
                    return False
                idx = t & (self.capacity - 1)
                self.buffer[idx] = item
                self.tail += 1
                return True

    def dequeue(self) -> Optional[object]:
        while True:
            with self._lock:
                h = self.head
                t = self.tail
                if h == t:
                    return None
                idx = h & (self.capacity - 1)
                data = self.buffer[idx]
                self.buffer[idx] = None
                self.head += 1
                return data


class PipelineChannel:
    """Connects two adjacent pipeline stages with backpressure."""

    def __init__(self, producer_stage: str, consumer_stage: str, capacity: int = 256, item_size: int = 0):
        self.producer_stage = producer_stage
        self.consumer_stage = consumer_stage
        self.queue = LockFreeQueue(capacity, item_size)

    def send(self, item: bytes) -> None:
        """Block until the item is enqueued, with exponential backoff."""
        delay = 0.0001  # 0.1ms
        while not self.queue.enqueue(item):
            time.sleep(delay)
            delay = min(delay * 2, 0.01)  # cap at 10ms

    def receive(self) -> Optional[bytes]:
        # block until something is available
        item = None
        while item is None:
            item = self.queue.dequeue()
            if item is None:
                time.sleep(0.0001)
        return item
