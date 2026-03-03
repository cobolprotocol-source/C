"""
Base Runner Framework for COBOL Benchmarks

Provides abstract base class for all benchmark runners.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    test_name: str
    dataset_type: str
    dataset_size: int
    success: bool
    metrics: Dict[str, Any]
    error: Optional[str] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "dataset_type": self.dataset_type,
            "dataset_size": self.dataset_size,
            "success": self.success,
            "metrics": self.metrics,
            "error": self.error,
            "timestamp": self.timestamp
        }


class BaseRunner(ABC):
    """Abstract base class for all benchmark runners.
    
    Subclasses must implement:
    - setup(): Initialize resources
    - run(): Execute the benchmark
    - collect_metrics(): Gather results
    - cleanup(): Release resources
    """
    
    def __init__(self, name: str, output_dir: Optional[Path] = None):
        """Initialize runner.
        
        Args:
            name: Name of this runner (e.g., "compression", "decompression")
            output_dir: Directory for saving results
        """
        self.name = name
        self.output_dir = output_dir
        self.results = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def setup(self) -> bool:
        """Set up benchmark resources.
        
        Returns:
            True if setup successful, False otherwise
        """
        pass
    
    @abstractmethod
    def run(self, dataset_path: Path, dataset_info: Dict) -> BenchmarkResult:
        """Execute the benchmark on a single dataset.
        
        Args:
            dataset_path: Path to dataset file
            dataset_info: Metadata about the dataset
            
        Returns:
            BenchmarkResult with test outcome
        """
        pass
    
    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect and aggregate benchmark metrics.
        
        Returns:
            Dictionary of aggregated results
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up benchmark resources.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        pass
    
    def save_results(self, filename: Optional[str] = None) -> Path:
        """Save results to JSON file.
        
        Args:
            filename: Output filename (default: "{name}_results.json")
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"{self.name}_results.json"
        
        if not self.output_dir:
            raise ValueError("output_dir not set")
        
        output_file = self.output_dir / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        results_dict = {
            "runner_name": self.name,
            "total_runs": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "aggregated": self.collect_metrics()
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        self.logger.info(f"Saved results to {output_file}")
        return output_file
    
    def execute(self, datasets: Dict[str, Path]) -> bool:
        """Execute full benchmark workflow.
        
        Args:
            datasets: Dictionary of {dataset_name: dataset_path}
            
        Returns:
            True if all tests passed, False otherwise
        """
        try:
            self.logger.info(f"Setting up {self.name} benchmark...")
            if not self.setup():
                self.logger.error("Setup failed")
                return False
            
            self.logger.info(f"Running {self.name} benchmark on {len(datasets)} datasets...")
            for dataset_name, dataset_path in datasets.items():
                self.logger.info(f"  → {dataset_name}")
                result = self.run(dataset_path, {"name": dataset_name})
                self.results.append(result)
            
            self.logger.info(f"Collecting metrics...")
            metrics = self.collect_metrics()
            self.logger.info(f"Metrics collected: {list(metrics.keys())}")
            
            self.logger.info(f"Cleaning up {self.name} benchmark...")
            if not self.cleanup():
                self.logger.warning("Cleanup had issues")
            
            return all(r.success for r in self.results)
        
        except Exception as e:
            self.logger.error(f"Benchmark execution failed: {e}", exc_info=True)
            return False
    
    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)
    
    def get_results(self) -> list[BenchmarkResult]:
        """Get all results."""
        return self.results
    
    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if not self.results:
            return 0.0
        successful = sum(1 for r in self.results if r.success)
        return (successful / len(self.results)) * 100
