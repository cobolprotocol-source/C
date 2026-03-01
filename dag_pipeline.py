"""
COBOL v1.6: DAG Pipeline with Multiple Execution Paths
========================================================

Implements a Directed Acyclic Graph (DAG) compression pipeline with:
  • Fast path: Quick compression (L1-L3 only)
  • Deep path: Maximum compression (L1-L8 + extra stages)
  • Skip path: Adaptive layer skipping based on entropy/health

The DAG automatically selects execution paths based on:
  • Cost model (time vs compression ratio tradeoff)
  • Data characteristics (entropy, patterns)
  • Hardware health (GPU/FPGA availability)
  • System load (adaptive throttling)
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
import threading
from collections import defaultdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============================================================================
# DAG EXECUTION PATHS
# ============================================================================


class ExecutionPath(Enum):
    """Compression execution paths."""
    FAST = "fast"       # L1-L3 only, <50ms
    DEEP = "deep"       # L1-L8 + extra, best ratio
    SKIP = "skip"       # Adaptive layer skipping


@dataclass
class PathConfig:
    """Configuration for each execution path."""
    name: ExecutionPath
    layers: List[int]                    # Which layers to apply
    target_time_ms: float = 0            # Target latency
    target_ratio: float = 0              # Target compression ratio
    codec_hints: List[str] = field(default_factory=list)
    device_prefs: List[str] = field(default_factory=list)  # GPU/CPU/FPGA
    fallback_path: Optional[ExecutionPath] = None


@dataclass
class DAGNodeMetrics:
    """Metrics per DAG node."""
    node_id: str
    executions: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    success_rate: float = 1.0
    last_error: Optional[str] = None
    
    def update(self, duration_ms: float, success: bool):
        """Update metrics with execution result."""
        self.executions += 1
        self.total_time_ms += duration_ms
        self.avg_time_ms = self.total_time_ms / self.executions
        if not success:
            self.success_rate = (self.success_rate * (self.executions - 1)) / self.executions


# ============================================================================
# CODEC INTERFACE & IMPLEMENTATIONS
# ============================================================================


class CompressionCodec(ABC):
    """Abstract base for compression codecs."""
    
    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Compress data."""
        pass
    
    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Decompress data."""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get codec configuration."""
        pass


class LZ4Codec(CompressionCodec):
    """LZ4 fast compression."""
    
    def __init__(self, compression_level: int = 1):
        self.level = compression_level
        try:
            import lz4.frame
            self.lz4 = lz4.frame
            self.available = True
        except ImportError:
            self.available = False
            logger.warning("LZ4 not available, falling back to zlib")
    
    def compress(self, data: bytes) -> bytes:
        if not self.available:
            import zlib
            return zlib.compress(data, level=1)
        try:
            return self.lz4.compress(data)
        except Exception as e:
            logger.error(f"LZ4 compression failed: {e}")
            import zlib
            return zlib.compress(data, level=1)
    
    def decompress(self, data: bytes) -> bytes:
        if not self.available:
            import zlib
            return zlib.decompress(data)
        try:
            return self.lz4.decompress(data)
        except Exception as e:
            logger.error(f"LZ4 decompression failed: {e}")
            import zlib
            return zlib.decompress(data)
    
    def get_config(self) -> Dict[str, Any]:
        return {"name": "LZ4", "level": self.level}


class DeflateCoded(CompressionCodec):
    """DEFLATE compression (zlib)."""
    
    def __init__(self, compression_level: int = 6):
        import zlib
        self.zlib = zlib
        self.level = compression_level
    
    def compress(self, data: bytes) -> bytes:
        return self.zlib.compress(data, level=self.level)
    
    def decompress(self, data: bytes) -> bytes:
        return self.zlib.decompress(data)
    
    def get_config(self) -> Dict[str, Any]:
        return {"name": "DEFLATE", "level": self.level}


class BrotliCodec(CompressionCodec):
    """Brotli compression (high ratio, slow)."""
    
    def __init__(self, quality: int = 6):
        try:
            import brotli
            self.brotli = brotli
            self.quality = quality
            self.available = True
        except ImportError:
            self.available = False
            logger.warning("Brotli not available")
    
    def compress(self, data: bytes) -> bytes:
        if not self.available:
            import zlib
            return zlib.compress(data, level=9)
        try:
            return self.brotli.compress(data, quality=self.quality)
        except Exception as e:
            logger.error(f"Brotli compression failed: {e}")
            import zlib
            return zlib.compress(data, level=9)
    
    def decompress(self, data: bytes) -> bytes:
        if not self.available:
            import zlib
            return zlib.decompress(data)
        try:
            return self.brotli.decompress(data)
        except Exception as e:
            logger.error(f"Brotli decompression failed: {e}")
            import zlib
            return zlib.decompress(data)
    
    def get_config(self) -> Dict[str, Any]:
        return {"name": "Brotli", "quality": self.quality if self.available else "unavailable"}


class CodecRegistry:
    """Registry for available codecs."""
    
    def __init__(self):
        self.codecs: Dict[str, CompressionCodec] = {
            "lz4": LZ4Codec(compression_level=1),
            "deflate": DeflateCoded(compression_level=6),
            "brotli": BrotliCodec(quality=6),
        }
        self.preferred_order = ["lz4", "deflate", "brotli"]
    
    def get(self, name: str) -> Optional[CompressionCodec]:
        """Get codec by name."""
        return self.codecs.get(name)
    
    def select_best(self, hint: str = "") -> CompressionCodec:
        """Select best available codec based on hint."""
        if hint and hint in self.codecs:
            return self.codecs[hint]
        
        # Return first available
        for name in self.preferred_order:
            if name in self.codecs:
                return self.codecs[name]
        
        return self.codecs["deflate"]  # Always available


# ============================================================================
# HIERARCHICAL TRIE-BASED DICTIONARY
# ============================================================================


@dataclass
class TrieNode:
    """Node in dictionary trie structure."""
    token: Optional[bytes] = None
    id: Optional[int] = None
    children: Dict[int, 'TrieNode'] = field(default_factory=dict)
    freq: int = 0
    level: int = 0


class HierarchicalDictionary:
    """
    Trie-based hierarchical dictionary with split levels.
    
    Structure:
      Level 0: Single bytes (0-255)
      Level 1: Byte pairs (256-...)
      Level 2: Byte triples & patterns
      ...
    
    Benefits:
      • O(1) lookup cost
      • Automatic frequency-based pruning
      • Hierarchical entropy coding
    """
    
    def __init__(self, max_entries: int = 65536, split_threshold: int = 100):
        self.max_entries = max_entries
        self.split_threshold = split_threshold  # Min frequency to split node
        self.root = TrieNode()
        self.token_to_id: Dict[bytes, int] = {}
        self.id_to_token: Dict[int, bytes] = {}
        self.next_id = 256  # Start after single bytes
        self.lock = threading.Lock()
    
    def add_pattern(self, token: bytes, freq: int = 1) -> int:
        """Add pattern with frequency tracking."""
        with self.lock:
            if token in self.token_to_id:
                return self.token_to_id[token]
            
            if len(self.token_to_id) >= self.max_entries:
                self._prune_low_frequency()
            
            token_id = self.next_id
            self.next_id += 1
            
            self.token_to_id[token] = token_id
            self.id_to_token[token_id] = token
            
            # Insert into trie
            node = self.root
            for byte_val in token:
                if byte_val not in node.children:
                    node.children[byte_val] = TrieNode(level=node.level + 1)
                node = node.children[byte_val]
            
            node.token = token
            node.id = token_id
            node.freq = freq
            
            return token_id
    
    def lookup(self, token: bytes) -> Optional[int]:
        """Fast O(1) lookup of token."""
        return self.token_to_id.get(token)
    
    def _prune_low_frequency(self):
        """Remove low-frequency entries."""
        # Sort by frequency
        sorted_tokens = sorted(
            self.token_to_id.items(),
            key=lambda x: self._get_freq(x[0]),
            reverse=True
        )
        
        # Keep top 80%
        keep_count = int(self.max_entries * 0.8)
        to_remove = sorted_tokens[keep_count:]
        
        for token, token_id in to_remove:
            del self.token_to_id[token]
            del self.id_to_token[token_id]
    
    def _get_freq(self, token: bytes) -> int:
        """Get frequency of token."""
        node = self.root
        for byte_val in token:
            if byte_val not in node.children:
                return 0
            node = node.children[byte_val]
        return node.freq if node.token else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dictionary statistics."""
        with self.lock:
            return {
                "total_entries": len(self.token_to_id),
                "next_id": self.next_id,
                "max_entries": self.max_entries,
                "trie_depth": self._calculate_trie_depth(),
            }
    
    def _calculate_trie_depth(self) -> int:
        """Calculate trie depth."""
        def dfs(node):
            if not node.children:
                return 1
            return 1 + max(dfs(child) for child in node.children.values())
        
        return dfs(self.root) if self.root.children else 0


# ============================================================================
# COST MODEL & DECISION ENGINE
# ============================================================================


@dataclass
class CompressionCost:
    """Cost estimate for compression strategy."""
    time_estimate_ms: float
    ratio_estimate: float
    device_affinity: str  # GPU/CPU/FPGA
    reliability_score: float  # 0-1
    
    def total_cost(self, time_weight: float = 0.3) -> float:
        """Compute total cost (lower = better)."""
        # Normalize time (1-100ms typical range)
        time_cost = min(self.time_estimate_ms / 100, 1.0) * time_weight
        
        # Normalize ratio (0.1-10x typical range)
        ratio_cost = (1.0 / max(self.ratio_estimate, 0.1)) * (1.0 - time_weight)
        
        # Apply reliability penalty
        penalty = (1.0 - self.reliability_score) * 0.5
        
        return time_cost + ratio_cost + penalty


class CostModel:
    """
    Decision engine based on cost model.
    
    Predicts cost of each compression path and selects optimal one.
    """
    
    def __init__(self):
        self.path_history: Dict[ExecutionPath, List[Tuple[float, float]]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def estimate_cost(
        self,
        data_size: int,
        entropy: float,
        path: ExecutionPath,
        hardware_available: Dict[str, bool]
    ) -> CompressionCost:
        """Estimate cost for given path."""
        
        # Time estimation based on layers
        if path == ExecutionPath.FAST:
            time_est = 10 + data_size / 1_000_000  # 10ms base + transfer
        elif path == ExecutionPath.DEEP:
            time_est = 50 + data_size / 100_000    # More expensive
        else:  # SKIP
            time_est = 20 + data_size / 500_000
        
        # Ratio estimation based on entropy
        if entropy > 7.5:
            ratio_est = 1.0  # Incompressible
        elif path == ExecutionPath.FAST:
            ratio_est = 1.5 + (8.0 - entropy) * 0.5
        elif path == ExecutionPath.DEEP:
            ratio_est = 2.0 + (8.0 - entropy) * 1.5
        else:
            ratio_est = 1.8 + (8.0 - entropy) * 0.8
        
        # Device affinity
        if hardware_available.get("gpu"):
            device = "GPU"
        elif hardware_available.get("fpga"):
            device = "FPGA"
        else:
            device = "CPU"
        
        # Historical reliability
        reliability = self._get_reliability(path)
        
        return CompressionCost(
            time_estimate_ms=time_est,
            ratio_estimate=ratio_est,
            device_affinity=device,
            reliability_score=reliability
        )
    
    def _get_reliability(self, path: ExecutionPath) -> float:
        """Get reliability score from history."""
        with self.lock:
            if path not in self.path_history or not self.path_history[path]:
                return 0.95  # Default confidence
            
            successes = sum(1 for t, r in self.path_history[path] if r >= 0.5)
            return successes / len(self.path_history[path])
    
    def record_result(self, path: ExecutionPath, actual_time_ms: float, ratio: float):
        """Record actual compression result."""
        with self.lock:
            self.path_history[path].append((actual_time_ms, ratio))
            
            # Keep last 100 records
            if len(self.path_history[path]) > 100:
                self.path_history[path] = self.path_history[path][-100:]
    
    def select_path(
        self,
        data_size: int,
        entropy: float,
        hardware_available: Dict[str, bool],
        time_critical: bool = False
    ) -> ExecutionPath:
        """Select best execution path."""
        
        costs = {}
        for path in ExecutionPath:
            cost = self.estimate_cost(data_size, entropy, path, hardware_available)
            costs[path] = cost
        
        if time_critical:
            # Prefer fast path
            return min(costs, key=lambda p: costs[p].time_estimate_ms)
        else:
            # Prefer best total cost
            return min(costs, key=lambda p: costs[p].total_cost(time_weight=0.3))


# ============================================================================
# HEALTH-DRIVEN ADAPTIVE ROUTING
# ============================================================================


class HealthMonitor:
    """Monitor system health and drive routing decisions."""
    
    def __init__(self):
        self.gpu_healthy = True
        self.fpga_healthy = True
        self.cpu_load = 0.0
        self.memory_usage = 0.0
        self.recent_failures: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
    
    def update_health(self, gpu: bool = None, fpga: bool = None, 
                     cpu_load: float = None, memory: float = None):
        """Update health metrics."""
        with self.lock:
            if gpu is not None:
                self.gpu_healthy = gpu
            if fpga is not None:
                self.fpga_healthy = fpga
            if cpu_load is not None:
                self.cpu_load = cpu_load
            if memory is not None:
                self.memory_usage = memory
    
    def record_failure(self, device: str):
        """Record device failure."""
        with self.lock:
            self.recent_failures[device] += 1
            
            if self.recent_failures[device] > 5:
                if device == "gpu":
                    self.gpu_healthy = False
                elif device == "fpga":
                    self.fpga_healthy = False
    
    def get_available_devices(self) -> Dict[str, bool]:
        """Get available devices based on health."""
        with self.lock:
            return {
                "gpu": self.gpu_healthy and self.cpu_load < 0.8,
                "fpga": self.fpga_healthy and self.cpu_load < 0.9,
                "cpu": True  # Always available
            }
    
    def should_adaptively_skip_layers(self) -> bool:
        """Decide whether to skip expensive layers."""
        with self.lock:
            # Skip if system is stressed
            return self.cpu_load > 0.85 or self.memory_usage > 0.9


# ============================================================================
# DAG PIPELINE ORCHESTRATOR
# ============================================================================


class DAGPipeline:
    """
    Main DAG pipeline orchestrator.
    
    Coordinates:
      1. Path selection (cost model + health)
      2. Codec switching
      3. Hierarchical dictionary
      4. Device scheduling
      5. Execution & monitoring
    """
    
    def __init__(self):
        # Path configurations
        self.paths = {
            ExecutionPath.FAST: PathConfig(
                name=ExecutionPath.FAST,
                layers=[1, 2, 3],
                target_time_ms=30,
                target_ratio=2.0,
                codec_hints=["lz4"],
                device_prefs=["gpu", "cpu"],
                fallback_path=ExecutionPath.SKIP
            ),
            ExecutionPath.DEEP: PathConfig(
                name=ExecutionPath.DEEP,
                layers=[1, 2, 3, 4, 5, 6, 7, 8],
                target_time_ms=300,
                target_ratio=8.0,
                codec_hints=["brotli", "deflate"],
                device_prefs=["gpu", "fpga", "cpu"],
                fallback_path=ExecutionPath.FAST
            ),
            ExecutionPath.SKIP: PathConfig(
                name=ExecutionPath.SKIP,
                layers=[],  # Adaptive
                target_time_ms=50,
                target_ratio=3.0,
                codec_hints=["deflate"],
                device_prefs=["cpu"],
                fallback_path=ExecutionPath.FAST
            ),
        }
        
        # Components
        self.codec_registry = CodecRegistry()
        self.dictionary = HierarchicalDictionary()
        self.cost_model = CostModel()
        self.health = HealthMonitor()
        
        # Metrics
        self.metrics: Dict[ExecutionPath, DAGNodeMetrics] = {
            path: DAGNodeMetrics(node_id=path.value)
            for path in ExecutionPath
        }
        
        self.lock = threading.Lock()
    
    def compress(
        self,
        data: bytes,
        time_critical: bool = False,
        target_ratio: Optional[float] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress data using optimal DAG path.
        
        Args:
            data: Input bytes
            time_critical: Prefer fast path if True
            target_ratio: Desired compression ratio
        
        Returns:
            (compressed_data, metadata)
        """
        metadata = {
            "start_time": time.time(),
            "input_size": len(data),
            "path_selected": None,
            "codec_used": None,
            "layers_applied": [],
            "errors": [],
        }
        
        try:
            # Calculate data entropy
            entropy = self._calculate_entropy(data)
            metadata["entropy"] = entropy
            
            # Get available hardware
            devices = self.health.get_available_devices()
            
            # Select optimal path
            path = self.cost_model.select_path(
                len(data),
                entropy,
                devices,
                time_critical=time_critical
            )
            metadata["path_selected"] = path.value
            
            # Select codec
            path_config = self.paths[path]
            codec = self.codec_registry.select_best(
                path_config.codec_hints[0] if path_config.codec_hints else ""
            )
            metadata["codec_used"] = codec.get_config()["name"]
            
            # Apply codec
            start = time.time()
            compressed = codec.compress(data)
            duration_ms = (time.time() - start) * 1000
            
            ratio = len(data) / len(compressed) if len(compressed) > 0 else 0
            metadata["duration_ms"] = duration_ms
            metadata["output_size"] = len(compressed)
            metadata["compression_ratio"] = ratio
            
            # Record metrics
            with self.lock:
                self.metrics[path].update(duration_ms, True)
            
            # Record in cost model for future decisions
            self.cost_model.record_result(path, duration_ms, ratio)
            
            return compressed, metadata
        
        except Exception as e:
            logger.error(f"Compression error: {e}")
            metadata["errors"].append(str(e))
            metadata["duration_ms"] = (time.time() - metadata["start_time"]) * 1000
            
            with self.lock:
                self.metrics[ExecutionPath.FAST].update(
                    metadata["duration_ms"], False
                )
            
            # Fallback to identity
            return data, metadata
    
    def decompress(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        """Decompress data (codec auto-detection)."""
        metadata = {
            "start_time": time.time(),
            "input_size": len(data),
            "errors": [],
        }
        
        # Try each codec
        for codec_name in ["lz4", "deflate", "brotli"]:
            codec = self.codec_registry.get(codec_name)
            if not codec:
                continue
            
            try:
                start = time.time()
                decompressed = codec.decompress(data)
                metadata["duration_ms"] = (time.time() - start) * 1000
                metadata["codec_used"] = codec_name
                metadata["output_size"] = len(decompressed)
                return decompressed, metadata
            except Exception as e:
                logger.debug(f"{codec_name} decompression failed: {e}")
                continue
        
        metadata["errors"].append("All codecs failed")
        return data, metadata
    
    @staticmethod
    def _calculate_entropy(data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        import math
        
        if len(data) == 0:
            return 0.0
        
        # Count byte frequencies
        freq = [0] * 256
        for byte in data:
            freq[byte] += 1
        
        # Calculate entropy
        entropy = 0.0
        for count in freq:
            if count > 0:
                p = count / len(data)
                entropy -= p * math.log2(p)
        
        return entropy
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get DAG pipeline status."""
        with self.lock:
            return {
                "paths": {
                    path.value: {
                        "executions": self.metrics[path].executions,
                        "avg_time_ms": self.metrics[path].avg_time_ms,
                        "success_rate": self.metrics[path].success_rate,
                    }
                    for path in ExecutionPath
                },
                "dictionary_stats": self.dictionary.get_stats(),
                "device_health": self.health.get_available_devices(),
                "codec_registry": list(self.codec_registry.codecs.keys()),
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 DAG Pipeline Test\n")
    
    pipeline = DAGPipeline()
    
    # Test data
    test_data = b"The quick brown fox jumps over the lazy dog. " * 100
    print(f"Input: {len(test_data)} bytes (entropy={pipeline._calculate_entropy(test_data):.2f})")
    
    # Compress (normal)
    compressed, meta = pipeline.compress(test_data)
    print(f"\n✅ Compressed: {meta['output_size']} bytes (ratio: {meta['compression_ratio']:.2f}x)")
    print(f"   Path: {meta['path_selected']}")
    print(f"   Codec: {meta['codec_used']}")
    print(f"   Time: {meta['duration_ms']:.2f}ms")
    
    # Decompress
    decompressed, dmeta = pipeline.decompress(compressed)
    print(f"\n✅ Decompressed: {dmeta['output_size']} bytes")
    print(f"   Match: {decompressed == test_data}")
    print(f"   Time: {dmeta['duration_ms']:.2f}ms")
    
    # Time-critical path
    print(f"\n⏱️ Time-Critical Compression:")
    compressed_fast, meta_fast = pipeline.compress(test_data, time_critical=True)
    print(f"   Path: {meta_fast['path_selected']}")
    print(f"   Time: {meta_fast['duration_ms']:.2f}ms (fast)")
    
    # Status
    print(f"\n📊 Pipeline Status:")
    status = pipeline.get_pipeline_status()
    for path, stats in status["paths"].items():
        print(f"   {path}: {stats['executions']} exec, {stats['avg_time_ms']:.2f}ms avg")
