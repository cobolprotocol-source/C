"""Lightweight metrics wrapper with lazy Prometheus client import.

If `prometheus_client` is installed it exposes counters/gauges; otherwise
it falls back to a minimal in-process counter useful for tests and logging.
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_HAS_PROM = False
try:
    from prometheus_client import Counter, Gauge
    _HAS_PROM = True
except Exception:
    _HAS_PROM = False


class Metrics:
    def __init__(self):
        if _HAS_PROM:
            self.evicted = Counter('cobol_evicted_patterns_total', 'Evicted patterns count')
            self.global_patterns = Gauge('cobol_global_patterns', 'Current global pattern count')
        else:
            self._evicted = 0
            self._global_patterns = 0

    def inc_evicted(self, n: int = 1):
        if _HAS_PROM:
            self.evicted.inc(n)
        else:
            self._evicted += n
            logger.debug('evicted incremented by %d (total=%d)', n, self._evicted)

    def set_global_patterns(self, v: int):
        if _HAS_PROM:
            self.global_patterns.set(v)
        else:
            self._global_patterns = v
            logger.debug('global_patterns set=%d', v)


_metrics = Metrics()


def inc_evicted_count(n: int = 1):
    _metrics.inc_evicted(n)


def set_global_patterns(v: int):
    _metrics.set_global_patterns(v)


__all__ = ["Metrics", "inc_evicted_count", "set_global_patterns"]
