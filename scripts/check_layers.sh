#!/bin/bash
# Quick layer-by-layer test status

echo "======================================="
echo "COBOL Protocol Layer Tests (Quick Check)"
echo "======================================="
echo ""

# Layer 0 - CPU Fallback
echo "Layer 0 (CPU Fallback):"
cd /workspaces/dev.c && python -m pytest cpu_fallback_test.py -q --tb=no 2>&1 | tail -1

# Layer 1-4 - Core
echo "Layer 1-4 (Core Compression - Bridge):"
cd /workspaces/dev.c && python -m pytest test_bridge_simple.py -q --tb=no 2>&1 | tail -1

# Layer 5-6 - GPU
echo "Layer 5-6 (GPU Acceleration):"
cd /workspaces/dev.c && python -m pytest test_gpu_acceleration.py -q --tb=no 2>&1 | tail -1

# Layer 7 - HPC
echo "Layer 7 (HPC Engine):"
cd /workspaces/dev.c && python -m pytest test_hpc_engine.py::TestSharedMemoryEngine -q --tb=no 2>&1 | tail -1

# Layer 8 - Integration
echo "Layer 8 (COBOL v16):"
cd /workspaces/dev.c && python -m pytest test_cobol_v16.py::TestCOBOLv16::test_engine_initialization -q --tb=no 2>&1 | tail -1

echo ""
echo "======================================="
echo "Summary: Run 'pytest -v' for details"
echo "======================================="
