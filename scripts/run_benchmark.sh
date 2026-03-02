#!/bin/bash
# Quick benchmark runner for COBOL Protocol

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║   COBOL Protocol v1.5.3 - Performance Benchmarking Suite           ║"
echo "║   Comprehensive Throughput & Resource Efficiency Analysis          ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

cd /workspaces/dev.c

# Check dependencies
echo "Checking dependencies..."
python3 -c "import psutil; print('✓ psutil installed')" || { echo "✗ psutil required"; exit 1; }
python3 -c "import lz4; print('✓ lz4 installed')" || echo "⚠ lz4 optional"
python3 -c "import zlib; print('✓ zlib available')" || echo "⚠ zlib optional"

echo ""
echo "Available benchmark modes:"
echo "  1. Quick Test (1MB only)      - ~30 seconds"
echo "  2. Standard Test (1MB + 100MB) - ~2-3 minutes"
echo "  3. Full Test (1MB + 100MB + 1GB) - ~10-15 minutes"
echo ""

if [ -z "$1" ]; then
    MODE="2"
    echo "Using default: Standard Test"
else
    MODE="$1"
fi

echo ""
echo "Starting benchmarks (Mode $MODE)..."
echo ""

case $MODE in
    1)
        echo "Quick Test Mode (1MB only)"
        python3 bench_cobol.py --sizes small \
            --output benchmark_quick.json \
            --markdown benchmark_quick.md
        ;;
    2)
        echo "Standard Test Mode (1MB + 100MB)"
        python3 bench_cobol.py --sizes small medium \
            --output benchmark_report.json \
            --markdown benchmark_report.md
        ;;
    3)
        echo "Full Test Mode (1MB + 100MB + 1GB)"
        python3 bench_cobol.py --sizes small medium large \
            --output benchmark_full.json \
            --markdown benchmark_full.md
        ;;
    *)
        echo "Invalid mode: $MODE"
        echo "Usage: bash run_benchmark.sh [1|2|3]"
        exit 1
        ;;
esac

echo ""
echo "✓ Benchmarking complete!"
echo ""
echo "Reports generated:"
ls -lh benchmark_*.json benchmark_*.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'

echo ""
echo "View results:"
echo "  - JSON (machine-readable): benchmark_report.json"
echo "  - Markdown (human-readable): benchmark_report.md"
echo ""
