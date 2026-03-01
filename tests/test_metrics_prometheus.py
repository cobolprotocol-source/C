import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metrics_prometheus import create_pipeline_metrics_gauges


def test_prometheus_noop():
    update_fn, gauges = create_pipeline_metrics_gauges(5)
    # without prometheus_client, gauges should be empty and update should be callable
    assert isinstance(update_fn, type(lambda: None))
    assert gauges == {}
    # calling it should not raise
    update_fn({1: {'size': 100}})
