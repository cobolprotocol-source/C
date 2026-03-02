#!/usr/bin/env python3
"""
COBOL Protocol Test Optimization & Stability Check
Untuk memastikan semua layer (0-8) berjalan dengan stabil dan optimal
"""

import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple


class TestOptimizer:
    """Optimizer untuk test suite"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        self.failed_tests = []
        self.passed_tests = []
        self.skipped_tests = []
    
    def run_test_suite(self, suite_name: str, pytest_args: str) -> bool:
        """Run a test suite with specific arguments"""
        print(f"\n{'='*70}")
        print(f"Running: {suite_name}")
        print(f"{'='*70}")
        
        cmd = f"pytest {pytest_args} -v --tb=short"
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd="/workspaces/dev.c",
                timeout=300,
                capture_output=True,
                text=True
            )
            
            # Parse output
            output = result.stdout + result.stderr
            self.results[suite_name] = {
                'passed': output.count(' PASSED'),
                'failed': output.count(' FAILED'),
                'skipped': output.count(' SKIPPED'),
                'returncode': result.returncode
            }
            
            print(f"✓ {suite_name}: "
                  f"Passed={self.results[suite_name]['passed']}, "
                  f"Failed={self.results[suite_name]['failed']}, "
                  f"Skipped={self.results[suite_name]['skipped']}")
            
            return result.returncode == 0
        
        except subprocess.TimeoutExpired:
            print(f"✗ {suite_name}: TIMEOUT")
            self.results[suite_name] = {'passed': 0, 'failed': -1, 'skipped': 0}
            return False
        
        except Exception as e:
            print(f"✗ {suite_name}: ERROR - {e}")
            self.results[suite_name] = {'passed': 0, 'failed': -1, 'skipped': 0}
            return False
    
    def run_optimization_suite(self):
        """Run complete optimization test suite"""
        
        tests = [
            # Layer 0 - CPU Fallback
            ("Layer 0: CPU Fallback", "cpu_fallback_test.py -xvs"),
            
            # Layer 1-4 - Core Compression
            ("Layer 1-4: Bridge Tests", "test_bridge_simple.py -xvs"),
            
            # Layer 5-6 - Pattern & GPU
            ("Layer 5-6: GPU Acceleration", "test_gpu_acceleration.py -xvs -m gpu"),
            
            # Layer 7 - HPC
            ("Layer 7: HPC Engine", "test_hpc_engine.py -xvs"),
            
            # Layer 8 - Integration
            ("Layer 8: COBOL v16", "test_cobol_v16.py -xvs"),
            
            # Core Engine
            ("Core: Engine Tests", "test_engine.py::TestVarIntCodec -xvs"),
            ("Core: Dictionary", "test_engine.py::TestDictionary -xvs"),
        ]
        
        total_passed = 0
        total_failed = 0
        
        for suite_name, pytest_args in tests:
            success = self.run_test_suite(suite_name, pytest_args)
            if suite_name in self.results:
                total_passed += self.results[suite_name].get('passed', 0)
                total_failed += self.results[suite_name].get('failed', 0)
            
            # Small delay between suites
            time.sleep(1)
        
        self.print_summary(total_passed, total_failed)
    
    def print_summary(self, total_passed: int, total_failed: int):
        """Print optimization summary"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print(f"\n{'='*70}")
        print(f"OPTIMIZATION SUMMARY")
        print(f"{'='*70}")
        
        print(f"\nTotal Duration: {duration:.1f}s")
        print(f"Total Passed: {total_passed}")
        print(f"Total Failed: {total_failed}")
        
        if total_failed == 0:
            print(f"\n✓ ALL TESTS PASSED - Optimization Complete!")
        else:
            print(f"\n⚠ {total_failed} tests failed - Review needed")
        
        print(f"\nResults by Suite:")
        for suite_name, metrics in self.results.items():
            status = "✓" if metrics['failed'] == 0 else "✗"
            print(f"  {status} {suite_name}: "
                  f"P={metrics.get('passed', 0)} "
                  f"F={metrics.get('failed', 0)} "
                  f"S={metrics.get('skipped', 0)}")
    
    def run_quick_test(self):
        """Run quick smoke test"""
        print(f"\n{'='*70}")
        print(f"QUICK SMOKE TEST - All Layers")
        print(f"{'='*70}")
        
        cmd = "pytest --co -q 2>&1 | wc -l"
        result = subprocess.run(cmd, shell=True, cwd="/workspaces/dev.c",
                              capture_output=True, text=True)
        test_count = int(result.stdout.strip())
        print(f"Total tests found: {test_count}")
        
        # Run with short timeout and minimal output
        cmd = ("pytest -q --tb=no "
               "--ignore=test_api_client.py "
               "-k 'not websocket' 2>&1 | tail -5")
        result = subprocess.run(cmd, shell=True, cwd="/workspaces/dev.c",
                              capture_output=True, text=True, timeout=240)
        
        print(result.stdout)


def main():
    """Main entry point"""
    optimizer = TestOptimizer()
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        optimizer.run_quick_test()
    else:
        optimizer.run_optimization_suite()


if __name__ == "__main__":
    main()
