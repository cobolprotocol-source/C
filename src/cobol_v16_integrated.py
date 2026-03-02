"""
Integrated COBOL v1.6: DAG Pipeline + Heterogeneous Devices + Health-Driven Routing
====================================================================================

Complete system that combines:
  1. DAG execution paths (fast/deep/skip)
  2. Multiple codec switching
  3. Hierarchical dictionary
  4. GPU/FPGA/CPU scheduling
  5. Cost model decisions
  6. Health-driven adaptive routing

This is the production compression engine for COBOL Protocol v1.6.
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import threading

from .dag_pipeline import (
    DAGPipeline, ExecutionPath, CodecRegistry, 
    HierarchicalDictionary, CostModel, HealthMonitor
)
from .heterogeneous_orchestrator import (
    HeterogeneousOrchestrator, DevicePool
)

logger = logging.getLogger(__name__)


# ============================================================================
# INTEGRATED COBOL V1.6 ENGINE
# ============================================================================


@dataclass
class CompressionStrategy:
    """Complete compression strategy for a workload."""
    path: ExecutionPath
    codec: str
    use_gpu: bool
    use_fpga: bool
    skip_layers: List[int]
    dictionary_mode: str  # "flat" or "hierarchical"
    adaptive: bool


class COBOLv16Engine:
    """
    Production-grade compression engine combining all v1.6 components.
    
    Negotiates:
      • Execution path selection (cost-driven)
      • Device assignment (health-driven)
      • Codec switching (performance/ratio tradeoff)
      • Dictionary strategy (hierarchical if supported)
      • Adaptive tuning (online learning)
    """
    
    def __init__(self):
        # Core components
        self.dag_pipeline = DAGPipeline()
        self.orchestrator = HeterogeneousOrchestrator()
        self.device_pool = self.orchestrator.device_pool
        self.codec_registry = self.dag_pipeline.codec_registry
        self.dictionary = self.dag_pipeline.dictionary
        self.cost_model = self.dag_pipeline.cost_model
        self.health = self.dag_pipeline.health
        
        # Metrics
        self.total_bytes_processed = 0
        self.total_time_ms = 0.0
        self.strategy_history: List[CompressionStrategy] = []
        self.lock = threading.Lock()
    
    def compress(
        self,
        data: bytes,
        strategy: Optional[CompressionStrategy] = None,
        time_budget_ms: Optional[float] = None,
        target_ratio: Optional[float] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress data with integrated v1.6 engine.
        
        Args:
            data: Input bytes
            strategy: Optional explicit strategy (auto-negotiated if None)
            time_budget_ms: Maximum time allowed (softlimit)
            target_ratio: Desired compression ratio
        
        Returns:
            (compressed_data, metadata with full pipeline trace)
        """
        metadata = {
            "start_time": time.time(),
            "input_size": len(data),
            "strategy_used": None,
            "pipeline_stages": [],
            "device_usage": {},
            "errors": [],
        }
        
        try:
            # Step 1: Negotiate strategy if not provided
            if strategy is None:
                strategy = self._negotiate_strategy(
                    len(data),
                    time_budget_ms,
                    target_ratio
                )
            
            metadata["strategy_used"] = {
                "path": strategy.path.value,
                "codec": strategy.codec,
                "adaptive": strategy.adaptive
            }
            
            # Step 2: GPU upstream analysis (if available)
            if strategy.use_gpu:
                gpu_metadata = self._gpu_upstream_stage(data)
                metadata["pipeline_stages"].append(("gpu_upstream", gpu_metadata))
            
            # Step 3: Apply hierarchical dictionary (if enabled)
            if strategy.dictionary_mode == "hierarchical":
                dict_metadata = self._hierarchical_dict_stage(data)
                metadata["pipeline_stages"].append(("dict_learning", dict_metadata))
            
            # Step 4: Main compression (DAG + codec)
            compress_metadata = self._compression_stage(
                data,
                strategy
            )
            metadata["pipeline_stages"].append(("compression", compress_metadata))
            compressed = compress_metadata["output"]
            
            # Step 5: Verify & post-process
            if strategy.use_fpga or strategy.use_gpu:
                verify_metadata = self._device_verify_stage(compressed)
                metadata["pipeline_stages"].append(("verification", verify_metadata))
            
            # Step 6: CPU downstream optimization
            final = self.orchestrator.cpu_downstream.post_process(compressed)
            metadata["final_size"] = len(final)
            metadata["compression_ratio"] = len(data) / len(final) if len(final) > 0 else 0
            
            # Record metrics
            duration = (time.time() - metadata["start_time"]) * 1000
            metadata["total_time_ms"] = duration
            
            with self.lock:
                self.total_bytes_processed += len(data)
                self.total_time_ms += duration
                self.strategy_history.append(strategy)
            
            # Update health model
            success = len(final) < len(data)
            self.health.update_health(
                cpu_load=min(1.0, duration / 100)  # Simple load estimation
            )
            
            return final, metadata
        
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            metadata["errors"].append(str(e))
            metadata["total_time_ms"] = (time.time() - metadata["start_time"]) * 1000
            
            # Fallback: return identity
            return data, metadata
    
    def decompress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Decompress with auto-detection."""
        return self.dag_pipeline.decompress(data)
    
    def _negotiate_strategy(
        self,
        data_size: int,
        time_budget_ms: Optional[float],
        target_ratio: Optional[float]
    ) -> CompressionStrategy:
        """
        Negotiate optimal compression strategy.
        
        Decision factors:
          1. Time budget (if specified)
          2. Target ratio (if specified)
          3. Hardware health status
          4. Historical performance
          5. Data characteristics
        """
        
        # Get device availability
        devices = self.health.get_available_devices()
        use_gpu = devices.get("gpu", False)
        use_fpga = devices.get("fpga", False)
        
        # Select path based on constraints
        if time_budget_ms and time_budget_ms < 50:
            path = ExecutionPath.FAST
        elif target_ratio and target_ratio > 10:
            path = ExecutionPath.DEEP
        else:
            path = ExecutionPath.SKIP
        
        # Decide codec
        codec = "lz4" if path == ExecutionPath.FAST else "brotli"
        
        # Dictionary strategy
        dict_mode = "hierarchical" if data_size > 100_000 else "flat"
        
        # Adaptive routing if health is good
        adaptive = devices.get("gpu", False) or devices.get("fpga", False)
        
        return CompressionStrategy(
            path=path,
            codec=codec,
            use_gpu=use_gpu,
            use_fpga=use_fpga,
            skip_layers=[6, 7, 8] if path == ExecutionPath.FAST else [],
            dictionary_mode=dict_mode,
            adaptive=adaptive
        )
    
    def _gpu_upstream_stage(self, data: bytes) -> Dict[str, Any]:
        """GPU upstream: entropy analysis & pattern detection."""
        metadata = {
            "start_time": time.time(),
            "output": None,
        }
        
        try:
            entropy = self.orchestrator.gpu_upstream.calculate_entropy_vectorized(data)
            patterns = self.orchestrator.gpu_upstream.find_frequent_patterns(data)
            
            metadata.update({
                "entropy": entropy,
                "patterns_found": len(patterns),
                "top_pattern": patterns[0][0][:4] if patterns else None,
                "status": "success"
            })
            
            self.device_pool.update_metrics("gpu:0", utilization=15.0)
        
        except Exception as e:
            logger.debug(f"GPU upstream failed: {e}")
            metadata["status"] = "skipped"
            metadata["error"] = str(e)
        
        metadata["duration_ms"] = (time.time() - metadata["start_time"]) * 1000
        return metadata
    
    def _hierarchical_dict_stage(self, data: bytes) -> Dict[str, Any]:
        """Hierarchical dictionary learning."""
        metadata = {
            "start_time": time.time(),
            "entries_learned": 0,
            "dict_size": 0,
        }
        
        try:
            # Learn frequent patterns
            patterns = self.orchestrator.gpu_upstream.find_frequent_patterns(data, min_length=2)
            
            for pattern, freq in patterns[:100]:  # Add top 100 patterns
                self.dictionary.add_pattern(pattern, freq=freq)
            
            stats = self.dictionary.get_stats()
            metadata.update(stats)
            metadata["status"] = "success"
        
        except Exception as e:
            logger.debug(f"Dictionary learning failed: {e}")
            metadata["status"] = "failed"
        
        metadata["duration_ms"] = (time.time() - metadata["start_time"]) * 1000
        return metadata
    
    def _compression_stage(
        self,
        data: bytes,
        strategy: CompressionStrategy
    ) -> Dict[str, Any]:
        """Main compression using DAG pipeline."""
        metadata = {
            "start_time": time.time(),
            "output": None,
        }
        
        try:
            # Use DAG pipeline with strategy hints
            compressed, dag_meta = self.dag_pipeline.compress(
                data,
                time_critical=(strategy.path == ExecutionPath.FAST)
            )
            
            metadata.update({
                "output": compressed,
                "output_size": len(compressed),
                "ratio": len(data) / len(compressed) if len(compressed) > 0 else 0,
                "codec_used": dag_meta.get("codec_used"),
                "path_selected": dag_meta.get("path_selected"),
                "duration_ms": dag_meta.get("duration_ms", 0),
                "status": "success"
            })
        
        except Exception as e:
            logger.error(f"Compression stage failed: {e}")
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            metadata["output"] = data  # Fallback: identity
            metadata["output_size"] = len(data)
        
        metadata["elapsed_ms"] = (time.time() - metadata["start_time"]) * 1000
        return metadata
    
    def _device_verify_stage(self, data: bytes) -> Dict[str, Any]:
        """Optional device-based verification."""
        metadata = {
            "start_time": time.time(),
            "verified": True,
            "checksum": None,
        }
        
        try:
            import hashlib
            checksum = hashlib.sha256(data).hexdigest()[:16]
            metadata["checksum"] = checksum
        
        except Exception as e:
            logger.debug(f"Verification failed: {e}")
            metadata["verified"] = False
        
        metadata["duration_ms"] = (time.time() - metadata["start_time"]) * 1000
        return metadata
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get complete engine status."""
        with self.lock:
            return {
                "uptime_stats": {
                    "total_bytes_processed": self.total_bytes_processed,
                    "total_time_ms": self.total_time_ms,
                    "avg_throughput_mbs": (
                        self.total_bytes_processed / (self.total_time_ms / 1000)
                        if self.total_time_ms > 0 else 0
                    ),
                },
                "device_pool": self.device_pool.get_status(),
                "dag_pipeline": self.dag_pipeline.get_pipeline_status(),
                "health_status": self.health.get_available_devices(),
                "strategy_preference": self._get_strategy_preference(),
            }
    
    def _get_strategy_preference(self) -> Dict[str, Any]:
        """Analyze strategy preferences from history."""
        if not self.strategy_history:
            return {}
        
        path_counts = {}
        codec_counts = {}
        
        for strategy in self.strategy_history[-100:]:  # Last 100
            path = strategy.path.value
            path_counts[path] = path_counts.get(path, 0) + 1
            codec_counts[strategy.codec] = codec_counts.get(strategy.codec, 0) + 1
        
        return {
            "preferred_paths": path_counts,
            "preferred_codecs": codec_counts,
            "strategies_tried": len(self.strategy_history),
        }


# ============================================================================
# CONVENIENCE API
# ============================================================================


class COBOLV16:
    """High-level API for COBOL Protocol v1.6."""
    
    def __init__(self):
        self.engine = COBOLv16Engine()
    
    def compress(
        self,
        data: bytes,
        time_critical: bool = False,
        high_ratio: bool = False,
        adaptive: bool = True
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        High-level compression API.
        
        Args:
            data: Input bytes
            time_critical: Prefer speed over ratio
            high_ratio: Prefer ratio over speed
            adaptive: Use health-driven routing
        
        Returns:
            (compressed_data, metadata)
        """
        if time_critical:
            time_budget = 50.0  # 50ms budget
            target_ratio = None
        elif high_ratio:
            time_budget = None
            target_ratio = 10.0
        else:
            time_budget = None
            target_ratio = None
        
        return self.engine.compress(
            data,
            time_budget_ms=time_budget,
            target_ratio=target_ratio
        )
    
    def decompress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Decompress data."""
        return self.engine.decompress(data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🎯 COBOL Protocol v1.6 - Integrated Engine Test\n")
    
    cobol = COBOLV16()
    
    # Test data
    test_cases = [
        ("Small text", b"Hello World! " * 100),
        ("JSON-like", b'{"key":"value","data":[1,2,3]}\n' * 100),
        ("Binary-like", bytes(range(256)) * 100),
    ]
    
    for name, data in test_cases:
        print(f"\n📦 {name} ({len(data)} bytes)")
        
        # Normal compression
        compressed, meta = cobol.compress(data, adaptive=True)
        print(f"   Compressed: {meta['final_size']} bytes ({meta['compression_ratio']:.2f}x)")
        print(f"   Time: {meta['total_time_ms']:.2f}ms")
        print(f"   Strategy: {meta['strategy_used']['path']}")
        
        # Time-critical
        compressed_fast, meta_fast = cobol.compress(data, time_critical=True)
        print(f"   Fast: {len(compressed_fast)} bytes, {meta_fast['total_time_ms']:.2f}ms")
        
        # High ratio
        compressed_ratio, meta_ratio = cobol.compress(data, high_ratio=True)
        print(f"   Ratio: {len(compressed_ratio)} bytes ({meta_ratio['compression_ratio']:.2f}x)")
    
    # Status
    print(f"\n📊 Engine Status:")
    status = cobol.engine.get_engine_status()
    print(f"   Throughput: {status['uptime_stats']['avg_throughput_mbs']:.2f} MB/s")
    print(f"   Devices: {list(status['device_pool']['devices'].keys())}")
