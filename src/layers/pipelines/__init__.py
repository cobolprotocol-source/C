"""
Compression Pipeline Orchestration

This module provides layer orchestration and compression engines:
- CobolEngine: Main compression orchestrator for L1-L8 pipelines
- DAGCompressionPipeline: DAG-based adaptive layer selection
- AdaptivePipeline: Intelligent pipeline selection based on data properties
- FusionPipelineOptimizer: Optimized layer fusion for performance
- Other specialized engines: HPC, extreme, cost optimization, etc.

These orchestrators manage the execution of compression layers and
handle fallbacks, adaptive selection, and performance optimization.
"""

from .engine import CobolEngine
from .dag import DAGCompressionPipeline
from .adaptive import AdaptivePipeline
from .fused import FusionPipelineOptimizer
from .l5l8 import OptimizedL5L8Pipeline

__all__ = [
    "CobolEngine",
    "DAGCompressionPipeline",
    "AdaptivePipeline",
    "FusionPipelineOptimizer",
    "OptimizedL5L8Pipeline",
]
