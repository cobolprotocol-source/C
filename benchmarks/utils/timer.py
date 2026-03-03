"""
High-Precision Timing Utilities for COBOL Benchmarks

Provides accurate timing measurements with minimal overhead.
"""

import time
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
import statistics


@dataclass
class TimerSample:
    """A single timing sample."""
    start_time: float
    end_time: float
    elapsed_seconds: float
    
    @property
    def elapsed_ms(self) -> float:
        """Elapsed time in milliseconds."""
        return self.elapsed_seconds * 1000
    
    @property
    def elapsed_us(self) -> float:
        """Elapsed time in microseconds."""
        return self.elapsed_seconds * 1_000_000
    
    @property
    def elapsed_ns(self) -> float:
        """Elapsed time in nanoseconds."""
        return self.elapsed_seconds * 1_000_000_000


class HighPrecisionTimer:
    """High-precision timer using time.perf_counter().
    
    Tracks multiple measurements and provides statistical analysis.
    """
    
    def __init__(self, name: str = "timer"):
        """Initialize timer.
        
        Args:
            name: Name of this timer (for logging)
        """
        self.name = name
        self.samples: list[TimerSample] = []
        self._start_time: Optional[float] = None
    
    def start(self) -> None:
        """Start timing."""
        self._start_time = time.perf_counter()
    
    def stop(self) -> TimerSample:
        """Stop timing and add sample.
        
        Returns:
            TimerSample with timing data
        """
        if self._start_time is None:
            raise RuntimeError("Timer not started")
        
        end_time = time.perf_counter()
        elapsed = end_time - self._start_time
        
        sample = TimerSample(
            start_time=self._start_time,
            end_time=end_time,
            elapsed_seconds=elapsed
        )
        
        self.samples.append(sample)
        self._start_time = None
        
        return sample
    
    def measure(self, func: Callable, *args, **kwargs) -> tuple[Any, TimerSample]:
        """Measure execution time of a function.
        
        Args:
            func: Function to measure
            *args: Positional arguments to func
            **kwargs: Keyword arguments to func
            
        Returns:
            Tuple of (result, TimerSample)
        """
        self.start()
        result = func(*args, **kwargs)
        sample = self.stop()
        return result, sample
    
    def get_stats(self) -> Dict[str, float]:
        """Get statistical summary of samples.
        
        Returns:
            Dictionary with timing statistics
        """
        if not self.samples:
            return {}
        
        times_ms = [s.elapsed_ms for s in self.samples]
        times_us = [s.elapsed_us for s in self.samples]
        
        return {
            "count": len(self.samples),
            "total_ms": sum(times_ms),
            "min_ms": min(times_ms),
            "max_ms": max(times_ms),
            "mean_ms": statistics.mean(times_ms),
            "median_ms": statistics.median(times_ms),
            "stdev_ms": statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
            "p50_us": sorted(times_us)[len(times_us) // 2],
            "p95_us": sorted(times_us)[int(len(times_us) * 0.95)],
            "p99_us": sorted(times_us)[int(len(times_us) * 0.99)] if len(times_us) > 99 else sorted(times_us)[-1]
        }
    
    def reset(self) -> None:
        """Clear all samples."""
        self.samples = []
        self._start_time = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._start_time is not None:
            self.stop()
        return False


class BenchmarkTimer:
    """Simplified timer for benchmarking.
    
    Tracks timing of benchmark operations with named measurements.
    """
    
    def __init__(self):
        """Initialize benchmark timer."""
        self.measurements: Dict[str, HighPrecisionTimer] = {}
    
    def create(self, name: str) -> HighPrecisionTimer:
        """Create a named timer.
        
        Args:
            name: Name of timer
            
        Returns:
            HighPrecisionTimer instance
        """
        if name not in self.measurements:
            self.measurements[name] = HighPrecisionTimer(name)
        return self.measurements[name]
    
    def get(self, name: str) -> Optional[HighPrecisionTimer]:
        """Get a named timer.
        
        Args:
            name: Name of timer
            
        Returns:
            HighPrecisionTimer if exists, None otherwise
        """
        return self.measurements.get(name)
    
    def summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of all measurements.
        
        Returns:
            Dictionary mapping timer names to their statistics
        """
        return {
            name: timer.get_stats()
            for name, timer in self.measurements.items()
        }
    
    def reset_all(self) -> None:
        """Reset all timers."""
        for timer in self.measurements.values():
            timer.reset()
