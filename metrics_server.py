"""Minimal metrics HTTP server helper using prometheus_client if available.

This module exposes `start_metrics_server(port)` which starts a background
thread serving `/metrics`. If `prometheus_client` is not installed this is a
no-op and logs a warning.
"""
import logging
logger = logging.getLogger(__name__)

def start_metrics_server(port: int = 8000):
    try:
        from prometheus_client import start_http_server
    except Exception:
        logger.warning('prometheus_client not installed; metrics endpoint disabled')
        return False

    # start in background
    start_http_server(port)
    logger.info('Prometheus metrics server started at :%d', port)
    return True
