"""
Quick Test of Benchmarking Infrastructure

Verifies that:
1. Base runner loads correctly
2. Compression runner can be instantiated
3. Decompression runner can be instantiated
4. Timer utilities work
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "benchmarks"))

def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    
    try:
        from config import BenchmarkConfig, OutputConfig
        print("✓ config module loaded")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False
    
    try:
        from runners.base_runner import BaseRunner, BenchmarkResult
        print("✓ base_runner module loaded")
    except Exception as e:
        print(f"✗ Failed to load base_runner: {e}")
        return False
    
    try:
        from runners.compression_runner import CompressionRunner
        print("✓ compression_runner module loaded")
    except Exception as e:
        print(f"✗ Failed to load compression_runner: {e}")
        return False
    
    try:
        from runners.decompression_runner import DecompressionRunner
        print("✓ decompression_runner module loaded")
    except Exception as e:
        print(f"✗ Failed to load decompression_runner: {e}")
        return False
    
    try:
        from utils.timer import HighPrecisionTimer, BenchmarkTimer
        print("✓ timer module loaded")
    except Exception as e:
        print(f"✗ Failed to load timer: {e}")
        return False
    
    return True


def test_basic_functionality():
    """Test that basic functionality works."""
    print("\nTesting basic functionality...")
    
    try:
        from utils.timer import HighPrecisionTimer
        
        timer = HighPrecisionTimer("test")
        timer.start()
        
        # Do some work
        x = sum(range(1000))
        
        sample = timer.stop()
        
        if sample.elapsed_seconds > 0:
            print(f"✓ Timer works: {sample.elapsed_us:.2f} μs")
        else:
            print("✗ Timer didn't measure anything")
            return False
    
    except Exception as e:
        print(f"✗ Timer test failed: {e}")
        return False
    
    try:
        from runners.base_runner import BenchmarkResult
        
        result = BenchmarkResult(
            test_name="test",
            dataset_type="text",
            dataset_size=1024,
            success=True,
            metrics={"ratio": 2.5}
        )
        
        if result.to_dict()["success"]:
            print("✓ BenchmarkResult works")
        else:
            print("✗ BenchmarkResult failed")
            return False
    
    except Exception as e:
        print(f"✗ BenchmarkResult test failed: {e}")
        return False
    
    return True


def test_runner_instantiation():
    """Test that runners can be instantiated."""
    print("\nTesting runner instantiation...")
    
    from pathlib import Path
    from runners.compression_runner import CompressionRunner
    from runners.decompression_runner import DecompressionRunner
    from config import RESULTS_DIR
    
    try:
        runner = CompressionRunner(RESULTS_DIR)
        print(f"✓ CompressionRunner created: {runner.name}")
    except Exception as e:
        print(f"✗ Failed to create CompressionRunner: {e}")
        return False
    
    try:
        runner = DecompressionRunner(RESULTS_DIR)
        print(f"✓ DecompressionRunner created: {runner.name}")
    except Exception as e:
        print(f"✗ Failed to create DecompressionRunner: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("COBOL BENCHMARKING INFRASTRUCTURE - QUICK TEST")
    print("=" * 80)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Functionality", test_basic_functionality()))
    results.append(("Runner Instantiation", test_runner_instantiation()))
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
