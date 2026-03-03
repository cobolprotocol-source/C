#!/bin/bash
# Build Script for GPU-Accelerated Components
# Compiles CUDA kernels and creates shared library

set -e  # Exit on error

echo "======================================================================="
echo "Building GPU-Accelerated COBOL Protocol Components"
echo "======================================================================="

# Check for NVIDIA toolchain
if ! command -v nvcc &> /dev/null; then
    echo "⚠️  CUDA Toolkit not found. Installing optional dependencies..."
    # On Ubuntu
    if command -v apt &> /dev/null; then
        echo "Installing CUDA (this requires sudo)..."
        # This would be: sudo apt install nvidia-cuda-toolkit
        # For now, gracefully skip GPU compilation
        echo "To enable GPU acceleration, install CUDA Toolkit:"
        echo "  Ubuntu: sudo apt install nvidia-cuda-toolkit"
        echo "  CentOS: sudo yum install cuda"
        echo ""
        echo "Continuing without CUDA GPU support (CPU fallback available)"
        exit 0
    fi
fi

# Set output directory
OUTPUT_DIR="."
OUTPUT_LIB="${OUTPUT_DIR}/gpu_entropy_patterns.so"

echo "CUDA compiler: $(nvcc --version | grep release)"
echo "Output: ${OUTPUT_LIB}"

# Compile CUDA kernel
echo ""
echo "Compiling CUDA kernels..."
nvcc \
    -arch=sm_70 \
    -code=sm_70,compute_70 \
    -shared \
    -Xcompiler -fPIC \
    -o "${OUTPUT_LIB}" \
    gpu_entropy_patterns.cu \
    --compiler-options "-O3"

if [ -f "${OUTPUT_LIB}" ]; then
    echo "✅ CUDA compilation successful: ${OUTPUT_LIB}"
    ls -lh "${OUTPUT_LIB}"
else
    echo "❌ CUDA compilation failed"
    exit 1
fi

# Verify shared library
echo ""
echo "Verifying shared library..."
nm -D "${OUTPUT_LIB}" | grep compute_entropy_gpu || true

echo ""
echo "======================================================================="
echo "Build complete!"
echo "======================================================================="
echo ""
echo "To test GPU acceleration:"
echo "  python gpu_accelerator.py"
echo "  python test_gpu_acceleration.py"
