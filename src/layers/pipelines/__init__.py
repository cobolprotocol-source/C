"""
Compression Pipeline Orchestration

This module provides layer orchestration and compression engines:
- CobolEngine: Main compression orchestrator for L1-L8 pipelines
- DAGExecutionEngine: DAG-based adaptive layer selection
- AdaptivePipeline: Intelligent pipeline selection based on data properties
- FusionPipelineOptimizer: Optimized layer fusion for performance
- OptimizedL5L8Pipeline: L5-L8 advanced compression pipeline
- Other specialized engines: HPC, extreme, cost optimization, etc.

These orchestrators manage the execution of compression layers and
handle fallbacks, adaptive selection, and performance optimization.
"""

try:
    from .engine import CobolEngine
except ImportError as e:
    print(f"⚠️  Warning: Could not import CobolEngine: {e}")
    CobolEngine = None

try:
    from .dag import DAGExecutionEngine as DAGCompressionPipeline
except ImportError:
    try:
        from .dag import DAGExecutionEngine
        DAGCompressionPipeline = DAGExecutionEngine
    except ImportError:
        DAGCompressionPipeline = None

try:
    from .adaptive import AdaptivePipeline
except ImportError:
    AdaptivePipeline = None

try:
    from .fused import FusionPipelineOptimizer
except ImportError:
    FusionPipelineOptimizer = None

try:
    from .l5l8 import OptimizedL5L8Pipeline
except ImportError:
    OptimizedL5L8Pipeline = None

__all__ = [
    "CobolEngine",
    "DAGCompressionPipeline",
    "AdaptivePipeline",
    "FusionPipelineOptimizer",
    "OptimizedL5L8Pipeline",
]
