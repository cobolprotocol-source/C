"""
COBOL Protocol Benchmarking Configuration - SMALL (for testing)

Reduced dataset sizes for quick testing and development:
- 1 MB, 10 MB (skips 100MB and 1GB for faster iteration)

Use this config during development with:
  python -c "from config_small import *; ..."
"""

from pathlib import Path
import os

# Base configuration
PROJECT_ROOT = Path(__file__).parent.parent
BENCHMARKS_ROOT = Path(__file__).parent

# Directories
DATASETS_DIR = BENCHMARKS_ROOT / "datasets" / "generated"
RUNNERS_DIR = BENCHMARKS_ROOT / "runners"
RESULTS_DIR = BENCHMARKS_ROOT / "results"
REPORTS_DIR = BENCHMARKS_ROOT / "reports"
UTILS_DIR = BENCHMARKS_ROOT / "utils"
TESTS_DIR = BENCHMARKS_ROOT / "tests"

def create_directories():
    """Create all required directories."""
    for directory in [DATASETS_DIR, RUNNERS_DIR, RESULTS_DIR, REPORTS_DIR, UTILS_DIR, TESTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        # Create subdirectories for datasets
        if directory == DATASETS_DIR:
            for dtype in DATASET_TYPES:
                (directory / dtype).mkdir(parents=True, exist_ok=True)
            (directory.parent / "charts").mkdir(parents=True, exist_ok=True)

# Dataset configuration (SMALL - for testing)
DATASET_TYPES = [
    "text_log_repetitive",
    "json_telemetry", 
    "mixed_text_binary",
    "high_entropy_random"
]

DATASET_SIZES = {
    "small": 1 * 1024 * 1024,      # 1 MB
    "medium": 10 * 1024 * 1024,    # 10 MB
}

# Generator seeds (determinism)
SEEDS = {
    "text_log_repetitive": 42,
    "json_telemetry": 100,
    "mixed_text_binary": 200,
    "high_entropy_random": 300
}

class BenchmarkConfig:
    """Benchmark execution configuration."""
    COMPRESSION_RUNS = 2  # Reduced for testing
    LATENCY_SAMPLES_PER_RUN = 5  # Reduced
    STABILITY_TEST_DURATION = 60  # 1 minute (reduced from 3600)
    MEMORY_SAMPLE_INTERVAL = 2  # seconds
    DETERMINISM_RUNS = 3  # Reduced
    RUN_COMPETITOR_BENCHMARKS = False  # Disabled for testing

class CobolConfig:
    """COBOL Protocol layer configuration."""
    LAYERS = {
        "L0": {"class_name": "HuffmanBaseLz4", "enabled": True},
        "L1": {"class_name": "AdaptiveHuffmanLayer", "enabled": True},
        "L2": {"class_name": "EntropyAnalysisLayer", "enabled": True},
        "L3": {"class_name": "PatternRecognitionLayer", "enabled": True},
        "L4": {"class_name": "ContextModellingLayer", "enabled": True},
        "L5": {"class_name": "AdaptiveShiftingLayer", "enabled": True},
        "L6": {"class_name": "Layer6AdvancedShifting", "enabled": False},
        "L7": {"class_name": "Layer7DynamicModeling", "enabled": False},
        "L8": {"class_name": "Layer8ExascaleOptimization", "enabled": False}
    }
    
    MODELS = {
        "text_log_repetitive": {"preferred_layers": ["L0", "L1", "L2"], "variant": "repetitive"},
        "json_telemetry": {"preferred_layers": ["L0", "L2", "L3"], "variant": "structured"},
        "mixed_text_binary": {"preferred_layers": ["L0", "L1", "L3"], "variant": "mixed"},
        "high_entropy_random": {"preferred_layers": ["L0"], "variant": "random"}
    }

class OutputConfig:
    """Output file paths and formats."""
    # Results (JSON)
    COMPRESSION_STATS = RESULTS_DIR / "compression_stats.json"
    DECOMPRESSION_STATS = RESULTS_DIR / "decompression_stats.json"
    LATENCY_STATS = RESULTS_DIR / "latency_stats.json"
    STABILITY_REPORT = RESULTS_DIR / "stability_report.json"
    DETERMINISM_REPORT = RESULTS_DIR / "determinism_report.json"
    ERROR_HANDLING_REPORT = RESULTS_DIR / "error_handling_report.json"
    COMPETITOR_STATS = RESULTS_DIR / "competitor_stats.json"
    SUMMARY = RESULTS_DIR / "summary.json"
    
    # Reports (Markdown, CSV, HTML)
    BENCHMARKS_MD = REPORTS_DIR / "BENCHMARKS.md"
    STATISTICS_MD = REPORTS_DIR / "STATISTICS.md"
    COMPARISON_CSV = REPORTS_DIR / "comparison_table.csv"
    SUMMARY_HTML = REPORTS_DIR / "summary_report.html"
    
    # Manifest
    MANIFEST = DATASETS_DIR / "manifest.json"

class LoggingConfig:
    """Logging configuration."""
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    LOG_FILE = BENCHMARKS_ROOT / "benchmarks.log"

class ThresholdConfig:
    """Performance validation thresholds."""
    MIN_COMPRESSION_RATIO = 1.1  # At least 10% reduction for non-random data
    MIN_THROUGHPUT = 10  # MB/s
    MAX_CPU_PERCENT = 95  # Don't exceed 95%
    MAX_MEMORY_GROWTH = 500  # MB
    DETERMINISM_TOLERANCE = 0  # Exact match required for checksums

def get_dataset_path(dataset_type: str, size_label: str) -> Path:
    """Get the path for a specific dataset."""
    return DATASETS_DIR / dataset_type / f"{size_label}.bin"

def get_seed(dataset_type: str) -> int:
    """Get the seed for a specific dataset generator."""
    return SEEDS.get(dataset_type, 42)

if __name__ == "__main__":
    create_directories()
    print("COBOL Protocol Benchmarking Configuration (SMALL)")
    print(f"├── Benchmarks Root: {BENCHMARKS_ROOT} {'✅' if BENCHMARKS_ROOT.exists() else '❌'}")
    print(f"├── Datasets Dir: {DATASETS_DIR} {'✅' if DATASETS_DIR.exists() else '❌'}")
    print(f"├── Results Dir: {RESULTS_DIR} {'✅' if RESULTS_DIR.exists() else '❌'}")
    print(f"└── ✅ Configuration loaded successfully")
