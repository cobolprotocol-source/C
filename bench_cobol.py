#!/usr/bin/env python3
"""
COBOL Protocol v1.5.3 - Comprehensive Performance Benchmarking Suite
Native Rust Bindings (PyO3) Performance Analysis

Features:
- Multi-size data generation (1MB, 100MB, 1GB)
- Entropy variation (repetitive, random, mixed)
- Throughput measurement (compression/decompression)
- Resource monitoring (RAM, CPU)
- Baseline comparison (zlib, lz4)
- SHA-256 integrity verification
- Markdown & JSON reporting

Author: Performance Engineering Team
Date: March 1, 2026
"""

import os
import sys
import time
import json
import hashlib
import random
import string
import psutil
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import subprocess

# Try importing compression libraries
try:
    import zlib
    HAS_ZLIB = True
except ImportError:
    HAS_ZLIB = False

try:
    import lz4.frame
    HAS_LZ4 = True
except ImportError:
    HAS_LZ4 = False

# Try importing COBOL Protocol
try:
    from engine import CobolEngine
    HAS_COBOL = True
    COBOL_ENGINE = CobolEngine()
except ImportError:
    HAS_COBOL = False
    COBOL_ENGINE = None


# ============================================================================
# CONFIGURATION
# ============================================================================

class BenchmarkConfig:
    """Benchmark configuration"""
    
    # Data sizes (bytes)
    SIZES = {
        'small': 1 * 1024 * 1024,      # 1 MB
        'medium': 100 * 1024 * 1024,   # 100 MB
        'large': 1 * 1024 * 1024 * 1024  # 1 GB
    }
    
    # Entropy types
    ENTROPY_TYPES = ['repetitive', 'random', 'mixed']
    
    # Warm-up configuration
    WARMUP_ITERATIONS = 3
    WARMUP_SIZE = 10 * 1024 * 1024  # 10 MB
    
    # Performance targets
    TARGET_RAM_MB = 20
    TARGET_COMP_RATIO = 0.5
    
    # Logging
    LOG_LEVEL = logging.INFO


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=BenchmarkConfig.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    name: str
    size_mb: float
    entropy: str
    algo: str
    comp_speed_mbps: float
    decomp_speed_mbps: float
    comp_ratio: float
    peak_ram_mb: float
    cpu_percent: float
    integrity_ok: bool
    error: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class BenchmarkReport:
    """Complete benchmark report"""
    timestamp: str
    platform: str
    python_version: str
    results: List[BenchmarkResult]
    system_info: Dict
    summary: Dict
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'platform': self.platform,
            'python_version': self.python_version,
            'results': [r.to_dict() for r in self.results],
            'system_info': self.system_info,
            'summary': self.summary
        }


# ============================================================================
# DATA GENERATION
# ============================================================================

class DataGenerator:
    """Generate synthetic test data with varying entropy"""
    
    @staticmethod
    def generate_repetitive(size: int) -> bytes:
        """Generate highly repetitive data (high compression ratio)"""
        pattern = b"COBOL_PROTOCOL_v1.5.3" * 100
        return (pattern * (size // len(pattern) + 1))[:size]
    
    @staticmethod
    def generate_random(size: int) -> bytes:
        """Generate random data (low compression ratio)"""
        return os.urandom(size)
    
    @staticmethod
    def generate_mixed(size: int) -> bytes:
        """Generate mixed repetitive + random data (medium compression)"""
        block_size = 1024
        blocks = []
        
        for i in range(size // block_size):
            if i % 2 == 0:
                # Repetitive block
                pattern = b"Block_" + str(i).encode() * 20
                block = (pattern * (block_size // len(pattern) + 1))[:block_size]
            else:
                # Random block
                block = os.urandom(block_size)
            blocks.append(block)
        
        result = b''.join(blocks)
        return result[:size]
    
    @staticmethod
    def generate(size: int, entropy_type: str = 'mixed') -> bytes:
        """Generate test data"""
        if entropy_type == 'repetitive':
            return DataGenerator.generate_repetitive(size)
        elif entropy_type == 'random':
            return DataGenerator.generate_random(size)
        elif entropy_type == 'mixed':
            return DataGenerator.generate_mixed(size)
        else:
            raise ValueError(f"Unknown entropy type: {entropy_type}")
    
    @staticmethod
    def compute_hash(data: bytes) -> str:
        """Compute SHA-256 hash"""
        return hashlib.sha256(data).hexdigest()


# ============================================================================
# RESOURCE MONITORING
# ============================================================================

class ResourceMonitor:
    """Monitor resource usage during benchmarks"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_ram_mb = 0
        self.peak_ram_mb = 0
        self.cpu_percent = 0
        self.start_time = 0
    
    def start(self):
        """Start monitoring"""
        self.initial_ram_mb = self.process.memory_info().rss / (1024 * 1024)
        self.peak_ram_mb = self.initial_ram_mb
        self.start_time = time.perf_counter()
    
    def sample(self):
        """Sample current resource usage"""
        current_ram_mb = self.process.memory_info().rss / (1024 * 1024)
        self.peak_ram_mb = max(self.peak_ram_mb, current_ram_mb)
        self.cpu_percent = self.process.cpu_percent(interval=0.1)
    
    def end(self) -> Dict:
        """End monitoring and return stats"""
        self.sample()
        
        peak_delta_mb = self.peak_ram_mb - self.initial_ram_mb
        end_time = time.perf_counter()
        duration_s = end_time - self.start_time
        
        return {
            'peak_ram_mb': self.peak_ram_mb,
            'peak_ram_delta_mb': peak_delta_mb,
            'cpu_percent': self.cpu_percent,
            'duration_s': duration_s
        }


# ============================================================================
# BENCHMARK RUNNERS
# ============================================================================

class BenchmarkRunner:
    """Base benchmark runner"""
    
    def __init__(self, name: str, algo_name: str):
        self.name = name
        self.algo_name = algo_name
        self.monitor = ResourceMonitor()
    
    def compress(self, data: bytes) -> bytes:
        """Compress data - override in subclass"""
        raise NotImplementedError
    
    def decompress(self, compressed: bytes) -> bytes:
        """Decompress data - override in subclass"""
        raise NotImplementedError
    
    def benchmark(self, data: bytes, entropy: str, iterations: int = 1) -> BenchmarkResult:
        """Run single benchmark"""
        size_mb = len(data) / (1024 * 1024)
        
        try:
            # Compression
            self.monitor.start()
            
            comp_times = []
            compressed_data = None
            
            for i in range(iterations):
                start = time.perf_counter()
                compressed_data = self.compress(data)
                end = time.perf_counter()
                comp_times.append(end - start)
                self.monitor.sample()
            
            comp_stats = self.monitor.end()
            comp_speed_mbps = (size_mb * iterations) / sum(comp_times) if comp_times else 0
            
            # Decompression
            self.monitor.start()
            
            decomp_times = []
            
            for i in range(iterations):
                start = time.perf_counter()
                decompressed_data = self.decompress(compressed_data)
                end = time.perf_counter()
                decomp_times.append(end - start)
                self.monitor.sample()
            
            decomp_stats = self.monitor.end()
            decomp_speed_mbps = (size_mb * iterations) / sum(decomp_times) if decomp_times else 0
            
            # Integrity check
            original_hash = DataGenerator.compute_hash(data)
            recovered_hash = DataGenerator.compute_hash(decompressed_data)
            integrity_ok = original_hash == recovered_hash
            
            # Compression ratio
            comp_ratio = len(compressed_data) / len(data) if len(data) > 0 else 1.0
            
            # Peak RAM
            peak_ram_mb = max(comp_stats['peak_ram_mb'], decomp_stats['peak_ram_mb'])
            
            return BenchmarkResult(
                name=self.name,
                size_mb=size_mb,
                entropy=entropy,
                algo=self.algo_name,
                comp_speed_mbps=comp_speed_mbps,
                decomp_speed_mbps=decomp_speed_mbps,
                comp_ratio=comp_ratio,
                peak_ram_mb=peak_ram_mb,
                cpu_percent=max(comp_stats['cpu_percent'], decomp_stats['cpu_percent']),
                integrity_ok=integrity_ok,
                error=None if integrity_ok else "Integrity check failed!"
            )
        
        except Exception as e:
            logger.error(f"Benchmark failed for {self.algo_name}: {e}")
            return BenchmarkResult(
                name=self.name,
                size_mb=size_mb,
                entropy=entropy,
                algo=self.algo_name,
                comp_speed_mbps=0,
                decomp_speed_mbps=0,
                comp_ratio=0,
                peak_ram_mb=0,
                cpu_percent=0,
                integrity_ok=False,
                error=str(e)
            )


# ============================================================================
# ALGORITHM IMPLEMENTATIONS
# ============================================================================

class CobolBenchmark(BenchmarkRunner):
    """COBOL Protocol benchmark"""
    
    def __init__(self):
        super().__init__("COBOL Protocol v1.5.3", "cobol")
        if not HAS_COBOL:
            raise RuntimeError("COBOL Protocol not available")
    
    def compress(self, data: bytes) -> bytes:
        """Compress using COBOL"""
        return COBOL_ENGINE.compress(data)
    
    def decompress(self, compressed: bytes) -> bytes:
        """Decompress using COBOL"""
        return COBOL_ENGINE.decompress(compressed)


class ZlibBenchmark(BenchmarkRunner):
    """Zlib (Python standard library) benchmark"""
    
    def __init__(self):
        super().__init__("Zlib (Python stdlib)", "zlib")
        if not HAS_ZLIB:
            raise RuntimeError("Zlib not available")
    
    def compress(self, data: bytes) -> bytes:
        """Compress using zlib"""
        return zlib.compress(data, level=6)
    
    def decompress(self, compressed: bytes) -> bytes:
        """Decompress using zlib"""
        return zlib.decompress(compressed)


class LZ4Benchmark(BenchmarkRunner):
    """LZ4 benchmark"""
    
    def __init__(self):
        super().__init__("LZ4 (Fast compression)", "lz4")
        if not HAS_LZ4:
            raise RuntimeError("LZ4 not available")
    
    def compress(self, data: bytes) -> bytes:
        """Compress using LZ4"""
        return lz4.frame.compress(data)
    
    def decompress(self, compressed: bytes) -> bytes:
        """Decompress using LZ4"""
        return lz4.frame.decompress(compressed)


# ============================================================================
# WARM-UP PHASE
# ============================================================================

def warmup_cobol():
    """Warm-up COBOL runtime to ensure Rust objects are loaded"""
    if not HAS_COBOL:
        logger.warning("COBOL Protocol not available, skipping warmup")
        return
    
    logger.info("Warming up COBOL Protocol (loading Rust shared objects)...")
    
    try:
        benchmark = CobolBenchmark()
        
        for i in range(BenchmarkConfig.WARMUP_ITERATIONS):
            data = DataGenerator.generate(BenchmarkConfig.WARMUP_SIZE, 'mixed')
            benchmark.compress(data)
            logger.info(f"  Warmup iteration {i+1}/{BenchmarkConfig.WARMUP_ITERATIONS}")
        
        logger.info("✓ COBOL Protocol warmup complete")
    
    except Exception as e:
        logger.error(f"Warmup failed: {e}")


# ============================================================================
# BENCHMARK SUITE
# ============================================================================

def run_benchmarks(sizes: Optional[List[str]] = None, 
                  entropies: Optional[List[str]] = None,
                  algos: Optional[List[str]] = None) -> BenchmarkReport:
    """Run complete benchmark suite"""
    
    if sizes is None:
        sizes = ['small', 'medium']  # Skip 'large' by default (1GB takes too long)
    if entropies is None:
        entropies = BenchmarkConfig.ENTROPY_TYPES
    if algos is None:
        algos = []
        if HAS_COBOL:
            algos.append('cobol')
        if HAS_ZLIB:
            algos.append('zlib')
        if HAS_LZ4:
            algos.append('lz4')
    
    logger.info(f"Starting benchmark suite")
    logger.info(f"  Sizes: {sizes}")
    logger.info(f"  Entropy types: {entropies}")
    logger.info(f"  Algorithms: {algos}")
    
    # Warmup
    if 'cobol' in algos:
        warmup_cobol()
    
    results = []
    
    # Run benchmarks
    for algo in algos:
        for entropy in entropies:
            for size_name in sizes:
                size = BenchmarkConfig.SIZES[size_name]
                
                logger.info(f"\nBenchmarking {algo} ({size_name}, {entropy})...")
                
                try:
                    # Generate data
                    logger.debug(f"  Generating {size_name} data ({entropy} entropy)...")
                    data = DataGenerator.generate(size, entropy)
                    logger.debug(f"  Data size: {len(data)} bytes")
                    
                    # Run benchmark
                    if algo == 'cobol':
                        benchmark = CobolBenchmark()
                        iterations = 1 if size_name == 'large' else 2
                    elif algo == 'zlib':
                        benchmark = ZlibBenchmark()
                        iterations = 2
                    elif algo == 'lz4':
                        benchmark = LZ4Benchmark()
                        iterations = 2
                    else:
                        logger.warning(f"Unknown algorithm: {algo}")
                        continue
                    
                    result = benchmark.benchmark(data, entropy, iterations=iterations)
                    results.append(result)
                    
                    # Log result
                    status = "✓" if result.integrity_ok else "✗"
                    logger.info(f"  {status} Comp: {result.comp_speed_mbps:.1f} MB/s | "
                              f"Decomp: {result.decomp_speed_mbps:.1f} MB/s | "
                              f"Ratio: {result.comp_ratio:.2%} | "
                              f"RAM: {result.peak_ram_mb:.1f} MB")
                
                except Exception as e:
                    logger.error(f"  ✗ Benchmark failed: {e}")
                    results.append(BenchmarkResult(
                        name=f"{algo} ({size_name}, {entropy})",
                        size_mb=size / (1024 * 1024),
                        entropy=entropy,
                        algo=algo,
                        comp_speed_mbps=0,
                        decomp_speed_mbps=0,
                        comp_ratio=0,
                        peak_ram_mb=0,
                        cpu_percent=0,
                        integrity_ok=False,
                        error=str(e)
                    ))
    
    # Generate report
    report = create_report(results)
    
    return report


def create_report(results: List[BenchmarkResult]) -> BenchmarkReport:
    """Create benchmark report"""
    
    import platform
    
    # System info
    system_info = {
        'cpu_count': psutil.cpu_count(),
        'cpu_freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        'total_ram_gb': psutil.virtual_memory().total / (1024**3),
        'available_ram_gb': psutil.virtual_memory().available / (1024**3),
        'platform': platform.system(),
        'processor': platform.processor(),
    }
    
    # Summary stats
    passed = sum(1 for r in results if r.integrity_ok)
    failed = len(results) - passed
    
    cobol_results = [r for r in results if r.algo == 'cobol']
    zlib_results = [r for r in results if r.algo == 'zlib']
    lz4_results = [r for r in results if r.algo == 'lz4']
    
    def calc_avg_speed(res_list, comp=True):
        if not res_list:
            return 0
        speeds = [r.comp_speed_mbps if comp else r.decomp_speed_mbps for r in res_list if r.integrity_ok]
        return sum(speeds) / len(speeds) if speeds else 0
    
    summary = {
        'total_tests': len(results),
        'passed': passed,
        'failed': failed,
        'success_rate': f"{(passed/len(results)*100):.1f}%" if results else "N/A",
        'cobol_avg_comp_speed': f"{calc_avg_speed(cobol_results, True):.1f} MB/s",
        'cobol_avg_decomp_speed': f"{calc_avg_speed(cobol_results, False):.1f} MB/s",
        'zlib_avg_comp_speed': f"{calc_avg_speed(zlib_results, True):.1f} MB/s",
        'lz4_avg_comp_speed': f"{calc_avg_speed(lz4_results, True):.1f} MB/s",
    }
    
    report = BenchmarkReport(
        timestamp=datetime.now().isoformat(),
        platform=platform.system(),
        python_version=platform.python_version(),
        results=results,
        system_info=system_info,
        summary=summary
    )
    
    return report


# ============================================================================
# REPORTING
# ============================================================================

def generate_markdown_report(report: BenchmarkReport) -> str:
    """Generate markdown table report"""
    
    md = []
    md.append("# COBOL Protocol v1.5.3 - Benchmarking Report\n")
    md.append(f"**Generated**: {report.timestamp}\n")
    md.append(f"**Platform**: {report.platform} | **Python**: {report.python_version}\n\n")
    
    # System Info
    md.append("## System Information\n")
    md.append(f"- **CPU**: {report.system_info['cpu_count']} cores @ {report.system_info['cpu_freq_mhz']:.0f} MHz\n")
    md.append(f"- **Total RAM**: {report.system_info['total_ram_gb']:.1f} GB\n")
    md.append(f"- **Available RAM**: {report.system_info['available_ram_gb']:.1f} GB\n")
    md.append(f"- **Processor**: {report.system_info['processor']}\n\n")
    
    # Summary
    md.append("## Summary\n")
    md.append(f"- **Total Tests**: {report.summary['total_tests']}\n")
    md.append(f"- **Passed**: {report.summary['passed']}\n")
    md.append(f"- **Failed**: {report.summary['failed']}\n")
    md.append(f"- **Success Rate**: {report.summary['success_rate']}\n\n")
    
    md.append("## Average Performance\n")
    if report.summary['cobol_avg_comp_speed']:
        md.append(f"- **COBOL Compression**: {report.summary['cobol_avg_comp_speed']}\n")
        md.append(f"- **COBOL Decompression**: {report.summary['cobol_avg_decomp_speed']}\n")
    if report.summary['zlib_avg_comp_speed']:
        md.append(f"- **Zlib Compression**: {report.summary['zlib_avg_comp_speed']}\n")
    if report.summary['lz4_avg_comp_speed']:
        md.append(f"- **LZ4 Compression**: {report.summary['lz4_avg_comp_speed']}\n")
    md.append("\n")
    
    # Detailed Results Table
    md.append("## Detailed Benchmark Results\n\n")
    md.append("| Algorithm | Size (MB) | Entropy | Comp Speed (MB/s) | Decomp Speed (MB/s) | Ratio | RAM (MB) | CPU % | Status |\n")
    md.append("|-----------|-----------|---------|-------------------|---------------------|-------|----------|-------|--------|\n")
    
    for result in report.results:
        status = "✓ OK" if result.integrity_ok else "✗ FAIL"
        md.append(f"| {result.algo:15} | {result.size_mb:>8.1f} | {result.entropy:10} | "
                 f"{result.comp_speed_mbps:>17.1f} | {result.decomp_speed_mbps:>19.1f} | "
                 f"{result.comp_ratio:>5.2%} | {result.peak_ram_mb:>8.1f} | "
                 f"{result.cpu_percent:>5.1f} | {status:8} |\n")
    
    return "".join(md)


def generate_json_report(report: BenchmarkReport, filename: str = 'benchmark_report.json'):
    """Generate JSON report for CI/CD integration"""
    
    with open(filename, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    logger.info(f"✓ JSON report saved: {filename}")


def print_analysis(report: BenchmarkReport):
    """Print analysis of benchmark results"""
    
    print("\n" + "="*70)
    print("BENCHMARK ANALYSIS & BOTTLENECK IDENTIFICATION")
    print("="*70 + "\n")
    
    # Performance Analysis
    print("📊 PERFORMANCE ANALYSIS\n")
    
    cobol_results = [r for r in report.results if r.algo == 'cobol' and r.integrity_ok]
    zlib_results = [r for r in report.results if r.algo == 'zlib' and r.integrity_ok]
    lz4_results = [r for r in report.results if r.algo == 'lz4' and r.integrity_ok]
    
    if cobol_results:
        avg_cobol_speed = sum(r.comp_speed_mbps for r in cobol_results) / len(cobol_results)
        print(f"✓ COBOL Protocol:")
        print(f"  - Average Compression Speed: {avg_cobol_speed:.1f} MB/s")
        print(f"  - Peak RAM Usage: {max(r.peak_ram_mb for r in cobol_results):.1f} MB")
        print(f"  - Status: {'✓ OPTIMAL' if max(r.peak_ram_mb for r in cobol_results) < BenchmarkConfig.TARGET_RAM_MB else '⚠ REVIEW'}\n")
    
    if zlib_results:
        avg_zlib_speed = sum(r.comp_speed_mbps for r in zlib_results) / len(zlib_results)
        print(f"✓ Zlib:")
        print(f"  - Average Compression Speed: {avg_zlib_speed:.1f} MB/s")
        if cobol_results:
            ratio = avg_cobol_speed / avg_zlib_speed
            print(f"  - COBOL vs Zlib: {ratio:.2f}x {'faster' if ratio > 1 else 'slower'}\n")
    
    if lz4_results:
        avg_lz4_speed = sum(r.comp_speed_mbps for r in lz4_results) / len(lz4_results)
        print(f"✓ LZ4:")
        print(f"  - Average Compression Speed: {avg_lz4_speed:.1f} MB/s")
        if cobol_results:
            ratio = avg_cobol_speed / avg_lz4_speed
            print(f"  - COBOL vs LZ4: {ratio:.2f}x {'faster' if ratio > 1 else 'slower'}\n")
    
    # Bottleneck Analysis
    print("🔍 BOTTLENECK ANALYSIS\n")
    
    failed_tests = [r for r in report.results if not r.integrity_ok]
    if failed_tests:
        print(f"⚠ {len(failed_tests)} test(s) failed:\n")
        for result in failed_tests:
            print(f"  - {result.algo} ({result.size_mb:.1f}MB, {result.entropy}): {result.error}")
        print()
    
    # Resource Usage Analysis
    high_ram = [r for r in report.results if r.peak_ram_mb > BenchmarkConfig.TARGET_RAM_MB and r.integrity_ok]
    if high_ram:
        print(f"⚠ High RAM Usage ({len(high_ram)} tests):")
        for result in high_ram:
            print(f"  - {result.algo} ({result.size_mb:.1f}MB): {result.peak_ram_mb:.1f} MB")
        print()
    
    # Speed Analysis
    slow_tests = [r for r in report.results if r.comp_speed_mbps < 50 and r.integrity_ok]
    if slow_tests:
        print(f"⚠ Low Compression Speed ({len(slow_tests)} tests):")
        for result in slow_tests:
            print(f"  - {result.algo} ({result.size_mb:.1f}MB, {result.entropy}): {result.comp_speed_mbps:.1f} MB/s")
        print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS\n")
    
    if cobol_results:
        ram_ok = all(r.peak_ram_mb < BenchmarkConfig.TARGET_RAM_MB for r in cobol_results)
        speed_ok = all(r.comp_speed_mbps > 100 for r in cobol_results)
        
        if ram_ok and speed_ok:
            print("✓ COBOL Protocol meets performance targets:")
            print("  - RAM usage within limits (<20MB)")
            print("  - Compression speed exceeds 100 MB/s")
            print("  - Ready for production deployment")
        else:
            if not ram_ok:
                print("⚠ Reduce RAM usage:")
                print("  - Consider streaming compression for large files")
                print("  - Optimize internal buffer sizes")
            if not speed_ok:
                print("⚠ Improve compression speed:")
                print("  - Profile Rust code for hot paths")
                print("  - Consider adaptive algorithm selection")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="COBOL Protocol v1.5.3 Benchmarking Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bench_cobol.py                    # Run all benchmarks
  python bench_cobol.py --sizes small      # Only 1MB tests
  python bench_cobol.py --algos cobol zlib # Only COBOL and Zlib
  python bench_cobol.py --entropy random   # Only random data tests
        """
    )
    
    parser.add_argument(
        '--sizes',
        nargs='+',
        choices=['small', 'medium', 'large'],
        default=['small', 'medium'],
        help='Data sizes to test (default: small medium)'
    )
    
    parser.add_argument(
        '--entropy',
        nargs='+',
        choices=['repetitive', 'random', 'mixed'],
        default=BenchmarkConfig.ENTROPY_TYPES,
        dest='entropies',
        help='Entropy types to test (default: all)'
    )
    
    parser.add_argument(
        '--algos',
        nargs='+',
        choices=['cobol', 'zlib', 'lz4'],
        help='Algorithms to benchmark (default: auto-detect available)'
    )
    
    parser.add_argument(
        '--output',
        default='benchmark_report.json',
        help='JSON output filename (default: benchmark_report.json)'
    )
    
    parser.add_argument(
        '--markdown',
        default='benchmark_report.md',
        help='Markdown output filename (default: benchmark_report.md)'
    )
    
    args = parser.parse_args()
    
    # Run benchmarks
    report = run_benchmarks(
        sizes=args.sizes,
        entropies=args.entropies,
        algos=args.algos
    )
    
    # Generate reports
    logger.info("\nGenerating reports...")
    
    # Markdown report
    md_content = generate_markdown_report(report)
    with open(args.markdown, 'w') as f:
        f.write(md_content)
    logger.info(f"✓ Markdown report saved: {args.markdown}")
    
    # JSON report
    generate_json_report(report, args.output)
    
    # Print analysis
    print_analysis(report)
    
    # Print markdown to console
    print("\n" + "="*70)
    print("BENCHMARK RESULTS (MARKDOWN TABLE)")
    print("="*70 + "\n")
    print(md_content)
    
    logger.info(f"✓ All reports generated successfully!")
    
    return 0 if report.summary['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
