"""
COBOL Protocol Benchmarking Suite - Central Configuration

This module defines all constants, paths, and configuration for the
comprehensive benchmarking suite.
"""

import os
from pathlib import Path
from typing import Dict, List

# ============================================================================
# PATHS & DIRECTORIES
# ============================================================================

BENCHMARKS_ROOT = Path(__file__).parent.absolute()
DATASETS_DIR = BENCHMARKS_ROOT / "datasets" / "generated"
RUNNERS_DIR = BENCHMARKS_ROOT / "runners"
RESULTS_DIR = BENCHMARKS_ROOT / "results"
REPORTS_DIR = BENCHMARKS_ROOT / "reports"
CHARTS_DIR = REPORTS_DIR / "charts"
UTILS_DIR = BENCHMARKS_ROOT / "utils"
TESTS_DIR = BENCHMARKS_ROOT / "tests"

# Source code
SRC_ROOT = BENCHMARKS_ROOT.parent / "src"
LAYERS_ROOT = SRC_ROOT / "layers"

# ============================================================================
# DATASET CONFIGURATION
# ============================================================================

DATASET_TYPES = [
    "text_log_repetitive",
    "json_telemetry",
    "mixed_text_binary",
    "high_entropy_random"
]

DATASET_SIZES = {
    "small": 10 * 1024 * 1024,      # 10 MB
    "medium": 100 * 1024 * 1024,    # 100 MB
    "large": 1 * 1024 * 1024 * 1024 # 1 GB (only if RAM allows)
}

SIZE_LABELS = {
    10 * 1024 * 1024: "10MB",
    100 * 1024 * 1024: "100MB",
    1 * 1024 * 1024 * 1024: "1GB"
}

# Deterministic seeds for reproducibility
SEEDS = {
    "text_log_repetitive": 42,
    "json_telemetry": 100,
    "mixed_text_binary": 200,
    "high_entropy_random": 300
}

# ============================================================================
# BENCHMARK CONFIGURATION
# ============================================================================

class BenchmarkConfig:
    """Benchmark execution parameters."""
    
    # Compression runs per dataset
    COMPRESSION_RUNS = 3  # Multiple runs for variance measurement
    
    # Latency sampling
    LATENCY_SAMPLES_PER_RUN = 10
    
    # Stability test duration (seconds)
    STABILITY_TEST_DURATION = 3600  # 1 hour minimum
    
    # Memory tracking interval (seconds)
    MEMORY_SAMPLE_INTERVAL = 5
    
    # Determinism runs
    DETERMINISM_RUNS = 5
    
    # Competitor benchmark
    RUN_COMPETITOR_BENCHMARKS = True
    COMPETITORS = ["zstd", "lz4", "brotli", "lzma"]

# ============================================================================
# COBOL ENGINE CONFIGURATION
# ============================================================================

class CobolConfig:
    """COBOL compression engine parameters."""
    
    # Layer configuration (leave frozen - do not modify algorithms)
    LAYERS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"]
    
    # Model selection (for future performance models)
    DEFAULT_MODEL = "DATACENTER_GENERAL"

# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================

class OutputConfig:
    """Output file and report configuration."""
    
    # JSON results
    COMPRESSION_STATS = RESULTS_DIR / "compression_stats.json"
    DECOMPRESSION_STATS = RESULTS_DIR / "decompression_stats.json"
    LATENCY_STATS = RESULTS_DIR / "latency_stats.json"
    STABILITY_REPORT = RESULTS_DIR / "stability_report.json"
    DETERMINISM_REPORT = RESULTS_DIR / "determinism_report.json"
    ERROR_HANDLING_REPORT = RESULTS_DIR / "error_handling_report.json"
    COMPETITOR_STATS = RESULTS_DIR / "competitor_stats.json"
    SUMMARY = RESULTS_DIR / "summary.json"
    
    # Markdown reports
    BENCHMARKS_MD = REPORTS_DIR / "BENCHMARKS.md"
    STATISTICS_MD = REPORTS_DIR / "STATISTICS.md"
    COMPARISON_CSV = REPORTS_DIR / "comparison_table.csv"
    SUMMARY_HTML = REPORTS_DIR / "summary_report.html"
    
    # Charts
    COMPRESSION_RATIO_CHART = CHARTS_DIR / "compression_ratio_vs_size.png"
    THROUGHPUT_CHART = CHARTS_DIR / "throughput_comparison.png"
    LATENCY_CHART = CHARTS_DIR / "latency_percentiles.png"
    
    # Dataset manifest
    MANIFEST = DATASETS_DIR.parent / "manifest.json"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class LoggingConfig:
    """Logging parameters."""
    
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    LOG_FILE = BENCHMARKS_ROOT / "benchmarks.log"

# ============================================================================
# PERFORMANCE THRESHOLDS (for validation)
# ============================================================================

class ThresholdConfig:
    """Performance validation thresholds."""
    
    # Compression ratio expectations (empirically determined)
    MIN_EXPECTED_COMPRESSION_RATIO = {
        "text_log_repetitive": 0.5,    # At least 2x compression
        "json_telemetry": 0.4,         # At least 2.5x compression
        "mixed_text_binary": 0.8,      # At least 1.25x compression
        "high_entropy_random": 0.95    # Minimal compression (high entropy)
    }
    
    # Throughput expectations (MB/s)
    MIN_EXPECTED_THROUGHPUT = {
        "compression": 10,     # At least 10 MB/s
        "decompression": 10    # At least 10 MB/s
    }
    
    # Memory growth threshold (%)
    MAX_MEMORY_GROWTH_PERCENT = 10
    
    # Determinism tolerance (checksums must match exactly)
    DETERMINISM_TOLERANCE = 0

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_directories():
    """Ensure all benchmark directories exist."""
    for dir_path in [
        DATASETS_DIR, RUNNERS_DIR, RESULTS_DIR, 
        REPORTS_DIR, CHARTS_DIR, UTILS_DIR, TESTS_DIR
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_dataset_path(dataset_type: str, size: int) -> Path:
    """Get path to a specific dataset file."""
    size_label = SIZE_LABELS.get(size, f"{size//1024//1024}MB")
    return DATASETS_DIR / dataset_type / f"{size_label}.bin"

def get_seed(dataset_type: str) -> int:
    """Get deterministic seed for dataset type."""
    return SEEDS.get(dataset_type, 42)

# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    print("COBOL Protocol Benchmarking Configuration")
    print("=" * 80)
    print(f"Benchmarks Root: {BENCHMARKS_ROOT}")
    print(f"Datasets Dir:    {DATASETS_DIR}")
    print(f"Results Dir:     {RESULTS_DIR}")
    print(f"Reports Dir:     {REPORTS_DIR}")
    print()
    print(f"Dataset Types:   {', '.join(DATASET_TYPES)}")
    print(f"Dataset Sizes:   {list(SIZE_LABELS.values())}")
    print()
    print("Creating directories...")
    create_directories()
    print("✅ Configuration loaded successfully")
