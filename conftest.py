"""
Pytest configuration and fixtures untuk COBOL Protocol test suite
Optimized untuk stability dan performance
"""

import pytest
import sys
import os
import asyncio
from typing import Generator

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


# ============================================================================
# PYTEST HOOKS & CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Disable costly plugins if needed
    config.option.disable_warnings = True
    
    # Set asyncio mode
    if hasattr(config, 'option') and hasattr(config.option, 'asyncio_mode'):
        config.option.asyncio_mode = 'auto'


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    for item in items:
        # Add timeout marker to all tests
        if 'timeout' not in [marker.name for marker in item.iter_markers()]:
            item.add_marker(pytest.mark.timeout(300))
        
        # Add asyncio marker to async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ============================================================================
# FIXTURES - UTILITY
# ============================================================================

@pytest.fixture(scope="session")
def test_data_small():
    """Small test data (1KB)"""
    return b"A" * 1024


@pytest.fixture(scope="session")
def test_data_medium():
    """Medium test data (100KB)"""
    return b"B" * (100 * 1024)


@pytest.fixture(scope="session")
def test_data_large():
    """Large test data (1MB)"""
    return b"C" * (1024 * 1024)


@pytest.fixture(scope="session")
def test_data_random():
    """Random test data"""
    import random
    return bytes(random.randint(0, 255) for _ in range(10000))


# ============================================================================
# FIXTURES - COMPRESSION ENGINES
# ============================================================================

@pytest.fixture
def compression_engine():
    """Get compression engine instance"""
    try:
        from engine import CobolEngine
        return CobolEngine()
    except Exception as e:
        pytest.skip(f"CobolEngine not available: {e}")


# ============================================================================
# FIXTURES - GPU ACCELERATION
# ============================================================================

@pytest.fixture
def gpu_detector():
    """Get GPU detector"""
    try:
        from gpu_acceleration import GPUDetector
        return GPUDetector()
    except Exception:
        return None


@pytest.fixture
def gpu_available(gpu_detector):
    """Check if GPU is available"""
    if gpu_detector is None:
        return False
    return gpu_detector.gpu_available


# ============================================================================
# FIXTURES - DICTIONARY MANAGERS
# ============================================================================

@pytest.fixture
def dictionary_manager():
    """Get dictionary manager"""
    try:
        from engine import DictionaryManager
        return DictionaryManager()
    except Exception as e:
        pytest.skip(f"DictionaryManager not available: {e}")


# ============================================================================
# MARKERS & DECORATORS
# ============================================================================

def requires_gpu(test_func):
    """Decorator to skip test if GPU not available"""
    @pytest.mark.gpu
    def wrapper(*args, **kwargs):
        from gpu_acceleration import GPUDetector
        detector = GPUDetector()
        if not detector.gpu_available:
            pytest.skip("GPU not available")
        return test_func(*args, **kwargs)
    return wrapper


# ============================================================================
# ERROR HANDLING & RECOVERY
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Add cleanup logic here if needed


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add info to test report"""
    outcome = yield
    rep = outcome.get_result()
    
    # Show timing info
    if rep.when == "call":
        rep.sections.append((
            "execution_time",
            f"{call.stop - call.start:.3f}s"
        ))


# ============================================================================
# ASYNCIO SUPPORT
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    
    yield loop
    
    try:
        loop.close()
    except:
        pass


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """Monitor test performance"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def start(self):
        """Start timing"""
        import time
        self.start_time = time.time()
    
    def stop(self):
        """Stop timing"""
        import time
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def get_duration(self):
        """Get duration in seconds"""
        return self.duration if self.duration else 0.0


@pytest.fixture
def perf_monitor():
    """Performance monitor fixture"""
    return PerformanceMonitor()


# ============================================================================
# LOGGING & DEBUGGING
# ============================================================================

@pytest.fixture(autouse=True)
def log_test_info(request):
    """Log test info for debugging"""
    print(f"\n{'='*70}")
    print(f"TEST: {request.node.name}")
    print(f"FILE: {request.node.fspath}")
    print(f"{'='*70}")
    
    yield
    
    print(f"{'='*70}\n")
