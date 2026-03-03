#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "===================================="
echo "COBOL Protocol Layer Tests (Quick Check)"
echo "===================================="
echo ""

echo "Layer 0 (CPU Fallback):"
python -m pytest cpu_fallback_test.py -q --tb=no || true

echo "Layer 1-4 (Core Compression - Bridge):"
python -m pytest test_bridge_simple.py -q --tb=no || true

echo "Layer 5-6 (GPU Acceleration):"
python -m pytest test_gpu_acceleration.py -q --tb=no || true

echo "Layer 7 (HPC Engine):"
python -m pytest test_hpc_engine.py::TestSharedMemoryEngine -q --tb=no || true

echo "Layer 8 (COBOL v16):"
python -m pytest test_cobol_v16.py::TestCOBOLv16 -q --tb=no || true
