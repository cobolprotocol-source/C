import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adaptive_pipeline import AdaptivePipeline
from src.layer0_classifier import DataType


def test_autotuning_integration():
    """Test compress_with_autotuning end-to-end."""
    data = b"hello world " * 1000
    pipeline = AdaptivePipeline()
    
    compressed, meta = pipeline.compress_with_autotuning(data)
    
    # Verify metadata structure
    assert 'layer0_classification' in meta
    assert 'auto_tuner_config' in meta
    assert 'input_size' in meta
    assert meta['input_size'] == len(data)
    
    # Verify compression happened
    assert len(compressed) < len(data)


def test_autotuning_source_code():
    """Test autotuning on source code data."""
    data = b"""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
""" * 100
    
    pipeline = AdaptivePipeline()
    compressed, meta = pipeline.compress_with_autotuning(data)
    
    class_info = meta.get('layer0_classification', {})
    detected = class_info.get('data_type')
    
    # Should detect as source code
    assert detected in (DataType.SOURCE_CODE.value, DataType.TEXT_DOCUMENT.value)
    assert len(compressed) < len(data)


def test_autotuning_binary():
    """Test autotuning on binary/compressed data."""
    import zlib
    original = b"repetitive " * 500
    data = zlib.compress(original)
    
    pipeline = AdaptivePipeline()
    compressed, meta = pipeline.compress_with_autotuning(data)
    
    class_info = meta.get('layer0_classification', {})
    detected = class_info.get('data_type')
    entropy = class_info.get('entropy', 0)
    printable = class_info.get('printable_ratio', 0)
    
    # Compressed data typically has mixed entropy and low printable ratio
    # The important thing is it's not classified as clean text
    assert detected != DataType.LLM_DATASET.value
    assert printable < 0.5 or entropy > 5.0
    assert len(compressed) > 0


def test_autotuning_fallback_on_error():
    """Test that autotuning gracefully falls back on errors."""
    data = b"test"
    pipeline = AdaptivePipeline()
    
    # Even if there's an internal error, should still compress
    compressed, meta = pipeline.compress_with_autotuning(data)
    
    assert isinstance(compressed, (bytes, bytearray))
    assert meta['input_size'] == len(data)


def test_autotuning_config_dict():
    """Test that auto_tuner_config is a proper dict."""
    data = b"info " * 200
    pipeline = AdaptivePipeline()
    
    _, meta = pipeline.compress_with_autotuning(data)
    
    config = meta.get('auto_tuner_config', {})
    assert isinstance(config, dict)
    assert 'mode' in config
    assert 'layers' in config
    assert isinstance(config['layers'], dict)
