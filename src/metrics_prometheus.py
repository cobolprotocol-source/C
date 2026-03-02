"""Prometheus helper for AdaptivePipeline per-stage metrics.

This module provides a non-blocking way to create/update Gauges for each
pipeline layer. It only requires `prometheus_client` when actually used; the
functions become no-ops when the library is not installed.
"""
from typing import Any, Callable, Dict


def create_pipeline_metrics_gauges(num_layers: int):
    """Return (update_fn, gauges) where update_fn(metrics_data) updates gauges.

    If `prometheus_client` is unavailable, returns a no-op update function and
    an empty gauges dict.
    """
    try:
        from prometheus_client import Gauge
    except Exception:
        def noop_update(_):
            return
        return noop_update, {}

    gauges = {}
    for i in range(1, num_layers + 1):
        g = Gauge(f"cobol_pipeline_layer_{i}_size_bytes", f"Size after layer {i}")
        gauges[i] = g

    def update_fn(per_layer_stats: Dict[int, Dict[str, Any]]):
        # per_layer_stats expected as {layer: {"size": int, ...}}
        for layer, g in gauges.items():
            entry = per_layer_stats.get(layer)
            if entry is None:
                continue
            size = entry.get('size', 0)
            try:
                g.set(size)
            except Exception:
                pass

    return update_fn, gauges
