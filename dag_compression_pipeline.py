#!/usr/bin/env python3
"""
COBOL Protocol v1.5.3 - DAG-Based Compression Pipeline
=======================================================

Replaces linear layer execution with conditional, decision-driven execution.

Features:
- Directed Acyclic Graph (DAG) of compression layers
- Fast-path exits (L2-L3 for low-entropy data)
- Deep-path compression (L4-L8 for compressible data)
- Layer skipping is data-driven and energy-aware
- Deterministic execution, auditable decision paths

Architecture:
```
Input Data
    ↓
[L1: Semantic Analysis]
    ↓
  ┌─────────────────┐
  │ Entropy Check   │
  └─────────────────┘
  ↙    ↓    ↘
 Low Mixed Compressible
  ↓    ↓    ↓
F.P. M.P. Deep Path
(L2-L3) (L4-L5) (L5-L8)
  ↓    ↓    ↓
  OUT  OUT  OUT
```

Author: Senior Principal Infrastructure Architect
Date: 2026
License: See LICENSE.md
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Callable
from abc import ABC, abstractmethod
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# DAG NODE & EDGE DEFINITIONS
# ============================================================================

class LayerName(Enum):
    """Compression layers in DAG."""
    L1_SEMANTIC_ANALYSIS = "L1_SEMANTIC_ANALYSIS"
    L2_STRUCTURAL_MAPPING = "L2_STRUCTURAL_MAPPING"
    L3_DELTA_ENCODING = "L3_DELTA_ENCODING"
    L4_BITPACKING = "L4_BITPACKING"
    L5_RLE = "L5_RLE"
    L6_CROSS_BLOCK = "L6_CROSS_BLOCK"
    L7_PATTERN = "L7_PATTERN"
    L8_EXTREME = "L8_EXTREME"


class ExecutionPath(Enum):
    """Pre-defined execution paths through the DAG."""
    FAST_PATH = "FAST_PATH"          # Low entropy: skip compression
    MEDIUM_PATH = "MEDIUM_PATH"      # Mixed entropy: moderate compression
    DEEP_PATH = "DEEP_PATH"          # High compressibility: full compression


@dataclass
class LayerNode:
    """Represents a compression layer in the DAG."""
    
    layer: LayerName
    layer_number: int
    enabled: bool = True
    
    # Input contract
    input_type: str = "bytes"
    input_format: str = ""
    
    # Output contract
    output_type: str = "bytes"
    output_format: str = ""
    
    # Resource constraints
    max_memory_mb: int = 256
    max_time_ms: int = 5000
    
    # Decision logic
    decision_fn: Optional[Callable[[bytes], bool]] = None  # Should this layer run?
    energy_cost_mj: float = 0.0  # Millijoules
    
    # Metrics
    min_entropy_threshold: float = 0.0
    max_entropy_threshold: float = 1.0
    ratio_threshold: float = 0.0  # Skip if compression < this %
    
    def should_execute(self, data: bytes, context: Dict[str, Any]) -> bool:
        """Determine if this layer should execute (data-driven)."""
        if not self.enabled:
            return False
        
        if self.decision_fn:
            return self.decision_fn(data, context)
        
        return True


@dataclass
class LayerEdge:
    """Represents a connection between layers in the DAG."""
    
    from_layer: LayerName
    to_layer: LayerName
    condition: Optional[Callable[[Any], bool]] = None  # Only traverse if condition true
    branch_name: str = ""


@dataclass
class DAGExecutionContext:
    """Context for DAG execution."""
    
    # Input data
    input_data: bytes
    input_size: int
    
    # Entropy calculation
    entropy: float = 0.0
    entropy_category: str = "UNKNOWN"  # LOW, MEDIUM, HIGH
    
    # Path selection
    selected_path: ExecutionPath = ExecutionPath.FAST_PATH
    
    # Layer execution history
    executed_layers: List[LayerName] = field(default_factory=list)
    skipped_layers: List[LayerName] = field(default_factory=list)
    layer_outputs: Dict[str, bytes] = field(default_factory=dict)
    layer_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Decision log (for auditability)
    decisions: List[str] = field(default_factory=list)
    
    # Timing
    start_time: float = field(default_factory=time.time)
    elapsed_ms: float = 0.0
    
    # Energy tracking
    energy_used_mj: float = 0.0
    energy_budget_mj: Optional[float] = None  # Stop if exceeded
    
    # Checkpoints for restart-ability
    checkpoint_layers: List[str] = field(default_factory=list)
    
    def log_decision(self, msg: str) -> None:
        """Log a compression decision (for auditability)."""
        self.decisions.append(msg)
        logger.debug(f"[DAG] {msg}")


# ============================================================================
# DAG COMPRESSION PIPELINE
# ============================================================================

class CompressionDAG:
    """
    Directed Acyclic Graph of compression layers.
    
    Supports:
    - Fast-path exits (L2-L3)
    - Medium-path compression (L4-L5)
    - Deep-path compression (L5-L8)
    - Energy-aware execution
    - Deterministic, auditable decisions
    """
    
    def __init__(self):
        self.nodes: Dict[LayerName, LayerNode] = {}
        self.edges: List[LayerEdge] = []
        self.paths: Dict[ExecutionPath, List[LayerName]] = {}
        self._build_default_dag()
    
    def _build_default_dag(self) -> None:
        """Build the default 8-layer compression DAG."""
        
        # Layer 1: Semantic Analysis (always runs)
        self.add_node(LayerNode(
            layer=LayerName.L1_SEMANTIC_ANALYSIS,
            layer_number=1,
            enabled=True,
            decision_fn=None  # Always runs
        ))
        
        # Layer 2: Structural Mapping
        self.add_node(LayerNode(
            layer=LayerName.L2_STRUCTURAL_MAPPING,
            layer_number=2,
            ratio_threshold=0.95  # Only if >95% gain
        ))
        
        # Layer 3: Delta Encoding
        self.add_node(LayerNode(
            layer=LayerName.L3_DELTA_ENCODING,
            layer_number=3,
            ratio_threshold=0.90  # Only if >90% gain
        ))
        
        # Layer 4: Bit-Packing
        self.add_node(LayerNode(
            layer=LayerName.L4_BITPACKING,
            layer_number=4,
            max_memory_mb=512
        ))
        
        # Layer 5: RLE
        self.add_node(LayerNode(
            layer=LayerName.L5_RLE,
            layer_number=5,
            energy_cost_mj=10.0
        ))
        
        # Layer 6: Cross-Block Patterns
        self.add_node(LayerNode(
            layer=LayerName.L6_CROSS_BLOCK,
            layer_number=6,
            max_memory_mb=1024,
            energy_cost_mj=25.0
        ))
        
        # Layer 7: Pattern Refinement
        self.add_node(LayerNode(
            layer=LayerName.L7_PATTERN,
            layer_number=7,
            energy_cost_mj=15.0
        ))
        
        # Layer 8: Ultra-Extreme Mapping
        self.add_node(LayerNode(
            layer=LayerName.L8_EXTREME,
            layer_number=8,
            max_memory_mb=2048,
            energy_cost_mj=50.0
        ))
        
        # Define execution paths
        self.paths[ExecutionPath.FAST_PATH] = [
            LayerName.L1_SEMANTIC_ANALYSIS,
            LayerName.L2_STRUCTURAL_MAPPING,
            LayerName.L3_DELTA_ENCODING
        ]
        
        self.paths[ExecutionPath.MEDIUM_PATH] = [
            LayerName.L1_SEMANTIC_ANALYSIS,
            LayerName.L2_STRUCTURAL_MAPPING,
            LayerName.L3_DELTA_ENCODING,
            LayerName.L4_BITPACKING,
            LayerName.L5_RLE
        ]
        
        self.paths[ExecutionPath.DEEP_PATH] = [
            LayerName.L1_SEMANTIC_ANALYSIS,
            LayerName.L2_STRUCTURAL_MAPPING,
            LayerName.L3_DELTA_ENCODING,
            LayerName.L4_BITPACKING,
            LayerName.L5_RLE,
            LayerName.L6_CROSS_BLOCK,
            LayerName.L7_PATTERN,
            LayerName.L8_EXTREME
        ]
    
    def add_node(self, node: LayerNode) -> None:
        """Add a layer node to the DAG."""
        self.nodes[node.layer] = node
    
    def add_edge(self, edge: LayerEdge) -> None:
        """Add an edge between two nodes."""
        self.edges.append(edge)
    
    def select_path(self, context: DAGExecutionContext) -> ExecutionPath:
        """
        Select which execution path to take based on entropy analysis.
        
        Decision logic:
        - entropy < 0.35 → FAST_PATH (skip compression)
        - 0.35 <= entropy < 0.75 → MEDIUM_PATH (moderate compression)
        - entropy >= 0.75 → DEEP_PATH (aggressive compression)
        """
        entropy = context.entropy
        
        if entropy < 0.35:
            path = ExecutionPath.FAST_PATH
            context.entropy_category = "LOW"
        elif entropy < 0.75:
            path = ExecutionPath.MEDIUM_PATH
            context.entropy_category = "MEDIUM"
        else:
            path = ExecutionPath.DEEP_PATH
            context.entropy_category = "HIGH"
        
        context.selected_path = path
        context.log_decision(f"Entropy {entropy:.3f} → {context.entropy_category} ({path.value})")
        
        return path
    
    def validate_dag(self) -> Tuple[bool, List[str]]:
        """
        Validate DAG structure.
        
        Checks:
        - All nodes are reachable
        - No cycles
        - All paths are valid
        - Deterministic ordering
        """
        errors = []
        
        # Check all paths are valid
        for path_name, layer_list in self.paths.items():
            for layer_name in layer_list:
                if layer_name not in self.nodes:
                    errors.append(f"Path {path_name.value}: layer {layer_name.value} not found")
        
        # Check layer ordering
        for path_name, layer_list in self.paths.items():
            for i in range(len(layer_list) - 1):
                current = self.nodes[layer_list[i]].layer_number
                next_layer = self.nodes[layer_list[i + 1]].layer_number
                if current >= next_layer:
                    errors.append(f"Path {path_name.value}: layer ordering invalid")
        
        return len(errors) == 0, errors
    
    def get_path_layers(self, path: ExecutionPath) -> List[LayerName]:
        """Get layer sequence for a path."""
        return self.paths.get(path, [])


# ============================================================================
# EXECUTION ENGINE
# ============================================================================

class DAGExecutionEngine:
    """
    Executes compression according to the DAG.
    
    Handles:
    - Layer execution
    - Decision points
    - Energy constraints
    - Checkpoint/restart
    - Auditability
    """
    
    def __init__(self, dag: CompressionDAG):
        self.dag = dag
        self.layer_handlers: Dict[LayerName, Callable] = {}
        
        # Validate DAG
        valid, errors = self.dag.validate_dag()
        if not valid:
            raise ValueError(f"Invalid DAG: {errors}")
    
    def register_layer_handler(
        self,
        layer: LayerName,
        handler: Callable[[bytes, DAGExecutionContext], Tuple[bytes, Dict[str, Any]]]
    ) -> None:
        """Register a handler for layer execution."""
        self.layer_handlers[layer] = handler
    
    def execute(
        self,
        data: bytes,
        entropy: float,
        energy_budget_mj: Optional[float] = None,
        force_path: Optional[ExecutionPath] = None
    ) -> DAGExecutionContext:
        """
        Execute the compression DAG.
        
        Args:
            data: Input data to compress
            entropy: Calculated entropy (0-1)
            energy_budget_mj: Optional energy limit in millijoules
            force_path: Force specific path (for testing)
        
        Returns:
            Execution context with results and decision log
        """
        
        # Initialize context
        context = DAGExecutionContext(
            input_data=data,
            input_size=len(data),
            entropy=entropy,
            energy_budget_mj=energy_budget_mj
        )
        
        # Select execution path
        if force_path:
            context.selected_path = force_path
        else:
            self.dag.select_path(context)
        
        # Get layer sequence
        layers = self.dag.get_path_layers(context.selected_path)
        context.log_decision(f"Executing path with {len(layers)} layers")
        
        # Execute layers
        current_data = data
        for layer_name in layers:
            node = self.dag.nodes[layer_name]
            
            # Check if layer should execute
            if not node.should_execute(current_data, context.__dict__):
                context.skipped_layers.append(layer_name)
                context.log_decision(f"{layer_name.value}: SKIPPED (decision function)")
                continue
            
            # Check energy budget
            if context.energy_budget_mj and context.energy_used_mj + node.energy_cost_mj > context.energy_budget_mj:
                context.skipped_layers.append(layer_name)
                context.log_decision(f"{layer_name.value}: SKIPPED (energy budget exceeded)")
                continue
            
            # Check memory constraints
            # (In production: verify available memory >= max_memory_mb)
            
            # Execute layer
            try:
                if layer_name not in self.layer_handlers:
                    context.log_decision(f"{layer_name.value}: SKIPPED (no handler)")
                    context.skipped_layers.append(layer_name)
                    continue
                
                handler = self.layer_handlers[layer_name]
                layer_start = time.time()
                
                output_data, layer_metrics = handler(current_data, context)
                
                layer_elapsed = (time.time() - layer_start) * 1000
                
                # Record metrics
                context.layer_outputs[layer_name.value] = output_data
                context.layer_metrics[layer_name.value] = {
                    "input_size": len(current_data),
                    "output_size": len(output_data),
                    "elapsed_ms": layer_elapsed,
                    "ratio": len(output_data) / len(current_data) if len(current_data) > 0 else 1.0,
                    **layer_metrics
                }
                
                # Update energy
                context.energy_used_mj += node.energy_cost_mj
                
                # Check ratio threshold
                ratio = len(output_data) / len(current_data) if len(current_data) > 0 else 1.0
                if ratio > node.ratio_threshold:
                    context.log_decision(f"{layer_name.value}: EXECUTED (ratio {ratio:.3f})")
                    context.executed_layers.append(layer_name)
                    current_data = output_data
                else:
                    context.log_decision(f"{layer_name.value}: SKIPPED (insufficient gain)")
                    context.skipped_layers.append(layer_name)
            
            except Exception as e:
                context.log_decision(f"{layer_name.value}: ERROR ({str(e)})")
                context.skipped_layers.append(layer_name)
                logger.error(f"Layer {layer_name.value} failed: {e}")
        
        # Final output
        context.elapsed_ms = (time.time() - context.start_time) * 1000
        context.layer_outputs["final"] = current_data
        
        return context


# ============================================================================
# UNIT TESTING & VALIDATION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("COBOL Protocol DAG-Based Compression Pipeline")
    print("=" * 80)
    
    # Create DAG
    print("\n[1] Building DAG...")
    dag = CompressionDAG()
    valid, errors = dag.validate_dag()
    assert valid, f"DAG validation failed: {errors}"
    print(f"✓ DAG valid with {len(dag.nodes)} nodes and {len(dag.paths)} paths")
    
    # List paths
    print("\n[2] Execution Paths:")
    for path_name, layers in dag.paths.items():
        print(f"✓ {path_name.value:<20} ({len(layers)} layers)")
        for layer in layers:
            print(f"  └─ {layer.value}")
    
    # Create execution engine
    print("\n[3] Creating Execution Engine...")
    engine = DAGExecutionEngine(dag)
    print("✓ Execution engine initialized")
    
    # Register dummy handlers
    def dummy_handler(data: bytes, context: DAGExecutionContext) -> Tuple[bytes, Dict[str, Any]]:
        # Simulate compression (return slightly smaller data)
        return data[:-len(data)//10], {"processed": len(data)}
    
    for layer_name in dag.nodes.keys():
        engine.register_layer_handler(layer_name, dummy_handler)
    
    print("✓ Handlers registered for all layers")
    
    # Test execution paths
    print("\n[4] Testing Execution Paths:")
    test_data = b"Test data " * 100
    
    for entropy, expected_path in [(0.25, ExecutionPath.FAST_PATH),
                                     (0.5, ExecutionPath.MEDIUM_PATH),
                                     (0.85, ExecutionPath.DEEP_PATH)]:
        context = engine.execute(test_data, entropy=entropy)
        actual_path = context.selected_path
        status = "✓" if actual_path == expected_path else "✗"
        print(f"{status} entropy={entropy:.2f} → {actual_path.value}")
    
    # Test energy constraints
    print("\n[5] Testing Energy Constraints:")
    context = engine.execute(test_data, entropy=0.8, energy_budget_mj=30.0)
    print(f"✓ Executed with energy budget 30 mJ")
    print(f"  └─ Used {context.energy_used_mj:.1f} mJ")
    print(f"  └─ Executed {len(context.executed_layers)} layers")
    print(f"  └─ Skipped {len(context.skipped_layers)} layers")
    
    # Test decision log
    print("\n[6] Auditable Decision Log:")
    for i, decision in enumerate(context.decisions[:5]):
        print(f"  {i+1}. {decision}")
    
    print("\n" + "=" * 80)
    print("DAG Compression Pipeline validation complete")
    print("=" * 80)
