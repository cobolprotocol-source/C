"""
GPU + FPGA Device Scheduler & Orchestrator
===========================================

Implements heterogeneous device scheduling:
  • GPU upstream processing (for pattern matching, entropy detection)
  • FPGA middle tier (for custom codec implementation)
  • CPU downstream (fallback, post-processing)

Features:
  • Device affinity tracking
  • Work queue management
  • Load balancing
  • Graceful degradation
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
import threading
from collections import deque
import asyncio

logger = logging.getLogger(__name__)

# Try to import GPU accelerator
try:
    from .gpu_accelerator import GPUAccelerator, GPUMetrics
    GPU_ACCEL_AVAILABLE = True
except ImportError:
    GPU_ACCEL_AVAILABLE = False
    logger.debug("GPU Accelerator module not available")


# ============================================================================
# DEVICE TYPES & MANAGEMENT
# ============================================================================


class DeviceType(Enum):
    """Available device types."""
    GPU = "gpu"
    FPGA = "fpga"
    CPU = "cpu"


@dataclass
class DeviceCapabilities:
    """Capabilities of a compute device."""
    device_type: DeviceType
    device_id: int
    compute_capability: Optional[str] = None  # e.g., "cuda:0"
    memory_mb: int = 0
    bandwidth_gbps: float = 0.0
    supported_operations: List[str] = field(default_factory=list)
    latency_us: float = 0.0


@dataclass
class DeviceMetrics:
    """Runtime metrics for a device."""
    device_id: str
    device_type: DeviceType
    available: bool = True
    utilization_percent: float = 0.0
    memory_used_mb: int = 0
    temperature_c: float = 0.0
    error_count: int = 0
    last_error_time: float = 0.0
    successful_tasks: int = 0
    failed_tasks: int = 0


# ============================================================================
# DEVICE POOL & SCHEDULING
# ============================================================================


class DevicePool:
    """
    Manages pool of heterogeneous compute devices.
    
    Maintains:
      • Device inventory
      • Availability & health
      • Utilization metrics
      • Task queues
    """
    
    def __init__(self):
        self.devices: Dict[str, DeviceCapabilities] = {}
        self.metrics: Dict[str, DeviceMetrics] = {}
        self.device_queues: Dict[str, deque] = {}
        self.lock = threading.Lock()
        
        # Initialize detection
        self._detect_devices()
    
    def _detect_devices(self):
        """Detect available compute devices."""
        with self.lock:
            # GPU detection
            try:
                import torch
                gpu_count = torch.cuda.device_count()
                for i in range(gpu_count):
                    device_id = f"gpu:{i}"
                    self.devices[device_id] = DeviceCapabilities(
                        device_type=DeviceType.GPU,
                        device_id=i,
                        compute_capability=f"CUDA {torch.cuda.get_device_capability(i)[0]}",
                        memory_mb=int(torch.cuda.get_device_properties(i).total_memory / (1024**2)),
                        supported_operations=["pattern_match", "entropy_calc", "encoding"],
                        latency_us=1.0  # Very low latency
                    )
                    self.device_queues[device_id] = deque(maxlen=1000)
                    self.metrics[device_id] = DeviceMetrics(
                        device_id=device_id,
                        device_type=DeviceType.GPU
                    )
                logger.info(f"Detected {gpu_count} GPU(s)")
            except (ImportError, RuntimeError):
                logger.debug("No GPU devices detected")
            
            # FPGA detection (simulated for now)
            # In production: use OpenCL, HLS, or vendor APIs
            try:
                # Check for FPGA availability via environment or hardware
                fpga_available = False  # Placeholder
                if fpga_available:
                    device_id = "fpga:0"
                    self.devices[device_id] = DeviceCapabilities(
                        device_type=DeviceType.FPGA,
                        device_id=0,
                        supported_operations=["arithmetic_encode", "custom_codec"],
                        latency_us=10.0
                    )
            except Exception as e:
                logger.debug(f"FPGA detection failed: {e}")
            
            # CPU is always available
            device_id = "cpu:0"
            self.devices[device_id] = DeviceCapabilities(
                device_type=DeviceType.CPU,
                device_id=0,
                supported_operations=["all"],
                latency_us=100.0
            )
            self.device_queues[device_id] = deque(maxlen=10000)
            self.metrics[device_id] = DeviceMetrics(
                device_id=device_id,
                device_type=DeviceType.CPU,
                available=True
            )
    
    def get_device_for_operation(self, operation: str) -> Optional[str]:
        """Get best device for operation."""
        with self.lock:
            # Find devices that support operation
            candidates = []
            for device_id, cap in self.devices.items():
                if "all" in cap.supported_operations or operation in cap.supported_operations:
                    metric = self.metrics.get(device_id)
                    if metric and metric.available:
                        candidates.append((device_id, metric.utilization_percent))
            
            if not candidates:
                return None
            
            # Return least utilized
            return min(candidates, key=lambda x: x[1])[0]
    
    def submit_task(self, device_id: str, task: Dict[str, Any]) -> bool:
        """Submit task to device queue."""
        with self.lock:
            if device_id not in self.device_queues:
                return False
            
            self.device_queues[device_id].append(task)
            return True
    
    def get_queue_depth(self, device_id: str) -> int:
        """Get current queue depth."""
        with self.lock:
            if device_id not in self.device_queues:
                return 0
            return len(self.device_queues[device_id])
    
    def update_metrics(self, device_id: str, 
                      utilization: float = None,
                      memory_mb: int = None,
                      temp_c: float = None,
                      error: bool = False):
        """Update device metrics."""
        with self.lock:
            if device_id not in self.metrics:
                return
            
            metric = self.metrics[device_id]
            
            if utilization is not None:
                metric.utilization_percent = utilization
            if memory_mb is not None:
                metric.memory_used_mb = memory_mb
            if temp_c is not None:
                metric.temperature_c = temp_c
            
            if error:
                metric.error_count += 1
                metric.last_error_time = time.time()
                
                # Mark unavailable if too many errors
                if metric.error_count > 10:
                    metric.available = False
                    logger.warning(f"Device {device_id} marked unavailable")
            else:
                metric.successful_tasks += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get pool status."""
        with self.lock:
            return {
                "devices": {
                    device_id: {
                        "type": cap.device_type.value,
                        "available": self.metrics[device_id].available,
                        "utilization": self.metrics[device_id].utilization_percent,
                        "queue_depth": len(self.device_queues.get(device_id, [])),
                        "errors": self.metrics[device_id].error_count,
                    }
                    for device_id, cap in self.devices.items()
                }
            }


# ============================================================================
# UPSTREAM GPU PROCESSING
# ============================================================================


class GPUUpstream:
    """
    GPU-accelerated upstream processing.
    
    Responsibilities:
      • Pattern matching on large datasets
      • Entropy calculation (vectorized)
      • Dictionary learning
      • Block statistics
    """
    
    def __init__(self, device_pool: DevicePool):
        self.device_pool = device_pool
        self.has_gpu = self._check_gpu()
        
        # Initialize GPU accelerator if available
        if GPU_ACCEL_AVAILABLE:
            try:
                self.gpu_accel = GPUAccelerator(use_cuda=True, use_torch=True)
            except Exception as e:
                logger.debug(f"GPU Accelerator initialization failed: {e}")
                self.gpu_accel = None
        else:
            self.gpu_accel = None
    
    def _check_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def calculate_entropy_vectorized(self, data: bytes) -> float:
        """
        Calculate entropy using GPU acceleration.
        
        Uses GPUAccelerator for fast vectorized computation,
        falls back to CPU if GPU unavailable.
        """
        if self.gpu_accel:
            try:
                metrics = self.gpu_accel.compute_entropy_gpu(data)
                logger.debug(f"Entropy (device={metrics.device_used}): {metrics.entropy:.4f}, "
                           f"time={metrics.computation_time_ms:.2f}ms")
                return metrics.entropy
            except Exception as e:
                logger.debug(f"GPU entropy calculation failed: {e}, falling back to CPU")
        
        return self._calculate_entropy_cpu(data)
    
    @staticmethod
    def _calculate_entropy_cpu(data: bytes) -> float:
        """CPU-based entropy calculation."""
        import math
        
        if len(data) == 0:
            return 0.0
        
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1
        
        entropy = 0.0
        for count in freq:
            if count > 0:
                p = count / len(data)
                entropy -= p * math.log2(p)
        
        return entropy
    
    def find_frequent_patterns(self, data: bytes, min_length: int = 4, top_k: int = 100) -> List[Tuple[bytes, int]]:
        """
        Find frequent byte patterns using GPU acceleration.
        
        Args:
            data: Input bytes
            min_length: Minimum pattern length
            top_k: Number of top patterns to return
            
        Returns:
            List of (pattern, frequency) tuples
        """
        if self.gpu_accel:
            try:
                patterns, frequencies = self.gpu_accel.extract_top_patterns(
                    data,
                    pattern_length=min_length,
                    top_k=top_k
                )
                
                result = list(zip(patterns, frequencies))
                logger.debug(f"Extracted {len(result)} patterns using GPU accelerator")
                return result
            except Exception as e:
                logger.debug(f"GPU pattern extraction failed: {e}, falling back to CPU")
        
        # Fallback: simple CPU-based pattern detection
        patterns: Dict[bytes, int] = {}
        
        for i in range(len(data) - min_length + 1):
            pattern = data[i:i+min_length]
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        # Return top-k patterns
        return sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    def get_gpu_metrics(self) -> Optional[Dict[str, Any]]:
        """Get GPU device metrics."""
        if self.gpu_accel:
            return self.gpu_accel.get_device_info()
        return None


# ============================================================================
# FPGA/CUSTOM CODEC TIER
# ============================================================================


class FPGAMiddleTier:
    """
    FPGA-accelerated middle tier processing.
    
    Implements custom codecs that could be deployed to FPGA:
      • Arithmetic encoding
      • Custom Huffman variants
      • Specialized compression for domain data
    """
    
    def __init__(self, device_pool: DevicePool):
        self.device_pool = device_pool
        self.has_fpga = self._check_fpga()
    
    def _check_fpga(self) -> bool:
        """Check if FPGA is available."""
        # TODO: Implement actual FPGA detection
        # For now, always False
        return False
    
    def arithmetic_encode(self, data: bytes, model: Dict[int, float]) -> bytes:
        """Arithmetic encoding with custom probability model."""
        # Simplified implementation
        # Production: Use optimized arithmetic coder
        import array
        
        if not model:
            # Fallback: use uniform distribution
            model = {i: 1.0/256 for i in range(256)}
        
        # This is a placeholder
        # Real implementation would use proper arithmetic coding
        return data
    
    def arithmetic_decode(self, data: bytes, model: Dict[int, float]) -> bytes:
        """Arithmetic decoding."""
        return data


# ============================================================================
# CPU DOWNSTREAM PROCESSING
# ============================================================================


class CPUDownstream:
    """
    CPU-based downstream processing & fallback.
    
    Responsibilities:
      • Post-processing
      • Format conversion
      • Fallback compression
      • Error handling
    """
    
    def __init__(self, device_pool: DevicePool):
        self.device_pool = device_pool
    
    def post_process(self, data: bytes, format_hint: str = "") -> bytes:
        """Apply post-processing transforms."""
        # Remove trailing zeros if specified
        if format_hint == "trim_zeros":
            return data.rstrip(b'\x00')
        
        # Other post-processing logic
        return data
    
    def fallback_compress(self, data: bytes) -> bytes:
        """Fallback compression using zlib."""
        import zlib
        return zlib.compress(data, level=6)


# ============================================================================
# ORCHESTRATOR
# ============================================================================


class HeterogeneousOrchestrator:
    """
    Coordinates GPU upstream, FPGA middle, CPU downstream.
    
    Pipeline:
      Data → GPU (entropy, patterns) → FPGA (custom codec) → CPU (post-process) → Output
    """
    
    def __init__(self):
        self.device_pool = DevicePool()
        self.gpu_upstream = GPUUpstream(self.device_pool)
        self.fpga_middle = FPGAMiddleTier(self.device_pool)
        self.cpu_downstream = CPUDownstream(self.device_pool)
    
    def compress_heterogeneous(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress using heterogeneous pipeline.
        
        Stages:
          1. GPU: Analyze entropy & patterns
          2. FPGA: Apply custom codec (if available, else fallback)
          3. CPU: Post-process
        """
        metadata = {
            "start_time": time.time(),
            "input_size": len(data),
            "stages": {},
        }
        
        # Stage 1: GPU Upstream
        stage_name = "gpu_upstream"
        try:
            entropy = self.gpu_upstream.calculate_entropy_vectorized(data)
            patterns = self.gpu_upstream.find_frequent_patterns(data)
            
            metadata["stages"][stage_name] = {
                "status": "success",
                "entropy": entropy,
                "patterns_found": len(patterns),
            }
        except Exception as e:
            logger.error(f"GPU upstream failed: {e}")
            metadata["stages"][stage_name] = {"status": "failed", "error": str(e)}
            entropy = self.gpu_upstream._calculate_entropy_cpu(data)
        
        # Stage 2: Codec (FPGA or fallback)
        current = data
        stage_name = "codec"
        try:
            if entropy > 6.0:
                # Already compressed, skip
                compressed = data
            else:
                # Use FPGA or fallback
                if self.fpga_middle.has_fpga:
                    # Would use FPGA arithmetic coder
                    compressed = self.fpga_middle.arithmetic_encode(data, {})
                else:
                    # Fallback to CPU
                    compressed = self.cpu_downstream.fallback_compress(data)
            
            current = compressed
            metadata["stages"][stage_name] = {
                "status": "success",
                "output_size": len(compressed),
                "ratio": len(data) / len(compressed) if len(compressed) > 0 else 0,
            }
        except Exception as e:
            logger.error(f"Codec stage failed: {e}")
            metadata["stages"][stage_name] = {"status": "failed", "error": str(e)}
            metadata["stages"][stage_name]["output_size"] = len(current)
        
        # Stage 3: CPU Downstream
        stage_name = "cpu_downstream"
        try:
            final = self.cpu_downstream.post_process(current)
            metadata["stages"][stage_name] = {
                "status": "success",
                "output_size": len(final),
            }
            current = final
        except Exception as e:
            logger.error(f"CPU downstream failed: {e}")
            metadata["stages"][stage_name] = {"status": "failed", "error": str(e)}
        
        metadata["total_time_ms"] = (time.time() - metadata["start_time"]) * 1000
        metadata["final_size"] = len(current)
        metadata["compression_ratio"] = len(data) / len(current) if len(current) > 0 else 0
        
        return current, metadata
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get status of all devices."""
        return self.device_pool.get_status()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Heterogeneous Device Orchestrator Test\n")
    
    orchestrator = HeterogeneousOrchestrator()
    
    # Device status
    print("📱 Available Devices:")
    status = orchestrator.get_device_status()
    for device_id, info in status["devices"].items():
        print(f"   {device_id}: {info['type']} {'✓' if info['available'] else '✗'}")
    
    # Compression test
    test_data = b"The quick brown fox " * 500
    print(f"\n🧪 Compressing {len(test_data)} bytes...")
    
    compressed, meta = orchestrator.compress_heterogeneous(test_data)
    
    print(f"✅ Result:")
    print(f"   Output size: {meta['final_size']} bytes")
    print(f"   Ratio: {meta['compression_ratio']:.2f}x")
    print(f"   Time: {meta['total_time_ms']:.2f}ms")
    
    print(f"\n📊 Pipeline Stages:")
    for stage, info in meta["stages"].items():
        print(f"   {stage}: {info['status']}")
        if "entropy" in info:
            print(f"      Entropy: {info['entropy']:.2f}")
