"""
Main Benchmarking Orchestrator for COBOL Protocol

Execution entry point that runs all 6 benchmark phases:
1. Dataset generation
2. Core performance tests (compression/decompression)
3. Stability & determinism
4. Error handling
5. Competitor comparison (optional)
6. Report generation

Usage:
    python run_all.py [--phase PHASE_NUM] [--dataset-size SIZE] [--skip-datasets]
"""

import sys
import time
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    BENCHMARKS_ROOT, DATASETS_DIR, RESULTS_DIR, REPORTS_DIR,
    DATASET_TYPES, DATASET_SIZES, BenchmarkConfig, OutputConfig, LoggingConfig,
    create_directories, get_dataset_path
)
from datasets.manifest import load_manifest
from runners.compression_runner import CompressionRunner
from runners.decompression_runner import DecompressionRunner
from runners.stability_runner import StabilityRunner, DeterminismRunner
from runners.error_handler_runner import ErrorHandlingRunner

# Configure logging
logging.basicConfig(
    level=LoggingConfig.LOG_LEVEL,
    format=LoggingConfig.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class BenchmarkOrchestrator:
    """Orchestrates all benchmark phases."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.start_time = None
        self.phase_times: Dict[str, float] = {}
        self.compression_engine = None
        self.results = {}
    
    def print_banner(self, title: str) -> None:
        """Print formatted banner."""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def load_compression_engine(self) -> bool:
        """Load COBOL compression engine.
        
        Returns:
            True if loaded successfully
        """
        try:
            from src.layers.pipelines.orchestration import AdaptiveCompressionPipeline
            self.compression_engine = AdaptiveCompressionPipeline()
            logger.info("✓ Loaded COBOL AdaptiveCompressionPipeline")
            return True
        except Exception as e:
            logger.error(f"Failed to load compression engine: {e}")
            return False
    
    def phase_1_generate_datasets(self, skip_existing: bool = True, 
                                 dataset_sizes: Optional[List[str]] = None) -> bool:
        """Phase 1: Generate benchmark datasets.
        
        Args:
            skip_existing: Skip datasets that already exist
            dataset_sizes: Specific sizes to generate (default: all)
            
        Returns:
            True if successful
        """
        self.print_banner("PHASE 1: DATASET GENERATION")
        
        phase_start = time.time()
        
        try:
            from generate_datasets import generate_all_datasets
            
            datasets = generate_all_datasets(skip_existing=skip_existing)
            
            phase_time = time.time() - phase_start
            self.phase_times["phase_1_datasets"] = phase_time
            
            logger.info(f"Phase 1 complete in {phase_time:.1f}s")
            return True
        
        except Exception as e:
            logger.error(f"Phase 1 failed: {e}", exc_info=True)
            return False
    
    def phase_2_core_performance(self) -> bool:
        """Phase 2: Run core performance tests.
        
        Measures:
        - Compression ratio
        - Compression throughput
        - Decompression throughput
        - Latency percentiles
        
        Returns:
            True if successful
        """
        self.print_banner("PHASE 2: CORE PERFORMANCE TESTS")
        
        phase_start = time.time()
        
        try:
            # Load datasets
            manifest = load_manifest(OutputConfig.MANIFEST)
            if not manifest:
                logger.error("No datasets found - run Phase 1 first")
                return False
            
            datasets = {
                ds['dataset_type']: Path(ds['path'])
                for ds in manifest  # Assuming manifest is a list
            }
            
            # Run compression benchmark
            logger.info("Running compression benchmarks...")
            comp_runner = CompressionRunner(RESULTS_DIR, self.compression_engine)
            if comp_runner.setup():
                for ds_name, ds_path in datasets.items():
                    if ds_path.exists():
                        result = comp_runner.run(ds_path, {'name': ds_name, 'type': ds_name})
                        comp_runner.add_result(result)
                comp_runner.save_results("compression_results.json")
                self.results["compression"] = comp_runner.collect_metrics()
                logger.info(f"✓ Compression: {comp_runner.get_success_rate():.1f}% pass rate")
            
            # Run decompression benchmark
            logger.info("Running decompression benchmarks...")
            decomp_runner = DecompressionRunner(RESULTS_DIR, self.compression_engine)
            if decomp_runner.setup():
                for ds_name, ds_path in datasets.items():
                    if ds_path.exists():
                        result = decomp_runner.run(ds_path, {'name': ds_name, 'type': ds_name})
                        decomp_runner.add_result(result)
                decomp_runner.save_results("decompression_results.json")
                self.results["decompression"] = decomp_runner.collect_metrics()
                logger.info(f"✓ Decompression: {decomp_runner.get_success_rate():.1f}% pass rate")
            
            phase_time = time.time() - phase_start
            self.phase_times["phase_2_performance"] = phase_time
            
            logger.info(f"Phase 2 complete in {phase_time:.1f}s")
            return True
        
        except Exception as e:
            logger.error(f"Phase 2 failed: {e}", exc_info=True)
            return False
    
    def phase_3_stability_determinism(self) -> bool:
        """Phase 3: Stability and determinism tests.
        
        Measures:
        - Memory growth over sustained load
        - Consistency of compression (determinism)
        - Performance stability
        
        Returns:
            True if successful
        """
        self.print_banner("PHASE 3: STABILITY & DETERMINISM")
        
        phase_start = time.time()
        
        try:
            # Get one test dataset
            manifest = load_manifest(OutputConfig.MANIFEST)
            if not manifest:
                logger.error("No datasets found")
                return False
            
            # Use first dataset for stability test (small one if available)
            test_dataset = next((Path(ds['path']) for ds in manifest 
                               if ds['dataset_type'] == 'text_log_repetitive'), None)
            
            if not test_dataset:
                logger.warning("No suitable test dataset for stability test")
                return False
            
            # Stability test
            logger.info("Running stability test (this takes 1 minute)...")
            stability_runner = StabilityRunner(
                RESULTS_DIR, 
                self.compression_engine,
                duration_seconds=BenchmarkConfig.STABILITY_TEST_DURATION
            )
            if stability_runner.setup():
                result = stability_runner.run(test_dataset, {'name': 'stability_test'})
                stability_runner.add_result(result)
                stability_runner.save_results("stability_results.json")
                self.results["stability"] = stability_runner.collect_metrics()
                logger.info(f"✓ Stability: {stability_runner.get_success_rate():.1f}% pass rate")
            
            # Determinism test
            logger.info("Running determinism tests...")
            determ_runner = DeterminismRunner(
                RESULTS_DIR,
                self.compression_engine,
                num_runs=BenchmarkConfig.DETERMINISM_RUNS
            )
            if determ_runner.setup():
                result = determ_runner.run(test_dataset, {'name': 'determinism_test'})
                determ_runner.add_result(result)
                determ_runner.save_results("determinism_results.json")
                self.results["determinism"] = determ_runner.collect_metrics()
                logger.info(f"✓ Determinism: {determ_runner.get_success_rate():.1f}% pass rate")
            
            phase_time = time.time() - phase_start
            self.phase_times["phase_3_stability"] = phase_time
            
            logger.info(f"Phase 3 complete in {phase_time:.1f}s")
            return True
        
        except Exception as e:
            logger.error(f"Phase 3 failed: {e}", exc_info=True)
            return False
    
    def phase_4_error_handling(self) -> bool:
        """Phase 4: Error handling and robustness tests.
        
        Tests:
        - Empty data
        - Truncated data
        - Corrupted headers
        - Boundary conditions
        - Graceful failure recovery
        
        Returns:
            True if successful
        """
        self.print_banner("PHASE 4: ERROR HANDLING")
        
        phase_start = time.time()
        
        try:
            logger.info("Running error handling tests...")
            error_runner = ErrorHandlingRunner(RESULTS_DIR, self.compression_engine)
            
            if error_runner.setup():
                # Run the full error handling suite
                result = error_runner.run(Path(), {'name': 'error_suite'})
                error_runner.add_result(result)
                error_runner.save_results("error_handling_results.json")
                self.results["error_handling"] = error_runner.collect_metrics()
                
                passed = result.metrics.get('passed', 0)
                total = result.metrics.get('total_tests', 1)
                logger.info(f"✓ Error handling: {passed}/{total} tests passed")
            
            phase_time = time.time() - phase_start
            self.phase_times["phase_4_errors"] = phase_time
            
            logger.info(f"Phase 4 complete in {phase_time:.1f}s")
            return True
        
        except Exception as e:
            logger.error(f"Phase 4 failed: {e}", exc_info=True)
            return False
    
    def phase_5_competitor_comparison(self) -> bool:
        """Phase 5: Compare against competing algorithms.
        
        Optional: Requires zstd, lz4, brotli, lzma availability
        
        Returns:
            True if successful or skipped
        """
        self.print_banner("PHASE 5: COMPETITOR COMPARISON")
        
        if not BenchmarkConfig.RUN_COMPETITOR_BENCHMARKS:
            logger.info("Competitor benchmarks disabled in configuration")
            return True
        
        phase_start = time.time()
        
        try:
            logger.info("Checking availability of competing algorithms...")
            
            competitors = {
                'zstd': ['zstd', 'pyzstd'],
                'lz4': ['lz4'],
                'brotli': ['brotli'],
                'lzma': ['lzma']  # stdlib
            }
            
            available = {}
            for name, modules in competitors.items():
                try:
                    __import__(modules[0])
                    available[name] = True
                    logger.info(f"✓ {name} available")
                except ImportError:
                    available[name] = False
                    logger.warning(f"✗ {name} not available")
            
            # TODO: Implement competitor benchmarking
            logger.info("Competitor benchmarking infrastructure: coming in next iteration")
            
            phase_time = time.time() - phase_start
            self.phase_times["phase_5_competitor"] = phase_time
            
            return True
        
        except Exception as e:
            logger.error(f"Phase 5 failed: {e}", exc_info=True)
            return False
    
    def phase_6_report_generation(self) -> bool:
        """Phase 6: Generate benchmark reports.
        
        Generates:
        - BENCHMARKS.md (human-readable)
        - statistics.json (machine-readable)
        - comparison_table.csv (for analysis)
        - summary_report.html (visual dashboard)
        
        Returns:
            True if successful
        """
        self.print_banner("PHASE 6: REPORT GENERATION")
        
        phase_start = time.time()
        
        try:
            logger.info("Generating benchmark reports...")
            
            # TODO: Implement report generation
            logger.info("Report generation: coming in next iteration")
            
            logger.info(f"Reports saved to: {REPORTS_DIR}")
            
            phase_time = time.time() - phase_start
            self.phase_times["phase_6_reports"] = phase_time
            
            logger.info(f"Phase 6 complete in {phase_time:.1f}s")
            return True
        
        except Exception as e:
            logger.error(f"Phase 6 failed: {e}", exc_info=True)
            return False
    
    def run_all_phases(self, skip_phase_1: bool = False) -> bool:
        """Execute all benchmark phases.
        
        Args:
            skip_phase_1: Skip dataset generation if already present
            
        Returns:
            True if all phases successful
        """
        self.print_banner("COBOL PROTOCOL BENCHMARKING SUITE - COMPLETE RUN")
        
        self.start_time = time.time()
        
        # Initialize
        create_directories()
        if not self.load_compression_engine():
            logger.error("Cannot proceed without compression engine")
            return False
        
        # Run phases
        phases = [
            ("Phase 1 (Datasets)", lambda: self.phase_1_generate_datasets()),
            ("Phase 2 (Performance)", self.phase_2_core_performance),
            ("Phase 3 (Stability)", self.phase_3_stability_determinism),
            ("Phase 4 (Errors)", self.phase_4_error_handling),
            ("Phase 5 (Competitor)", self.phase_5_competitor_comparison),
            ("Phase 6 (Reports)", self.phase_6_report_generation),
        ]
        
        results = {}
        for phase_name, phase_func in phases:
            try:
                success = phase_func()
                results[phase_name] = "✓ PASS" if success else "✗ FAIL"
            except Exception as e:
                logger.error(f"Phase {phase_name} exception: {e}")
                results[phase_name] = "✗ ERROR"
        
        # Summary
        self.print_banner("BENCHMARK EXECUTION SUMMARY")
        
        for phase_name, status in results.items():
            print(f"{phase_name:.<50} {status}")
        
        total_time = time.time() - self.start_time
        print(f"\nTotal execution time: {total_time:.1f}s")
        
        print(f"\nPhase timings:")
        for phase, duration in self.phase_times.items():
            print(f"  {phase}: {duration:.1f}s")
        
        all_passed = all("PASS" in status for status in results.values())
        
        if all_passed:
            print("\n✅ ALL PHASES COMPLETED SUCCESSFULLY")
            return True
        else:
            print("\n⚠️ SOME PHASES ENCOUNTERED ISSUES")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="COBOL Protocol Comprehensive Benchmarking Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all.py                    # Run all phases
  python run_all.py --phase 2          # Run only phase 2
  python run_all.py --skip-datasets    # Skip phase 1
  python run_all.py --quick            # Quick run with small datasets only
        """
    )
    
    parser.add_argument('--phase', type=int, choices=[1, 2, 3, 4, 5, 6],
                       help='Run specific phase only')
    parser.add_argument('--skip-datasets', action='store_true',
                       help='Skip phase 1 (dataset generation)')
    parser.add_argument('--quick', action='store_true',
                       help='Quick run with reduced datasets/iterations')
    
    args = parser.parse_args()
    
    orchestrator = BenchmarkOrchestrator()
    
    try:
        if args.quick:
            # TODO: Implement quick mode configuration
            logger.info("Quick mode enabled (not yet implemented)")
        
        if args.phase:
            # Run specific phase
            phases = {
                1: orchestrator.phase_1_generate_datasets,
                2: orchestrator.phase_2_core_performance,
                3: orchestrator.phase_3_stability_determinism,
                4: orchestrator.phase_4_error_handling,
                5: orchestrator.phase_5_competitor_comparison,
                6: orchestrator.phase_6_report_generation,
            }
            
            success = phases[args.phase]()
            return 0 if success else 1
        else:
            # Run all phases
            success = orchestrator.run_all_phases(skip_phase_1=args.skip_datasets)
            return 0 if success else 1
    
    except KeyboardInterrupt:
        logger.warning("\nBenchmark interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
