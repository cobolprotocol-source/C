# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""Auto-tuner: Maps detected data types to optimal L1-L8 configurations.

Eliminates manual trial-and-error by recommending layer strategies based
on data characteristics detected by Layer 0 classifier.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from layer0_classifier import DataType, ClassificationResult
import logging

logger = logging.getLogger(__name__)


@dataclass
class LayerConfig:
    """Configuration for a single layer."""
    enabled: bool = True
    strategy: str = "default"
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Full L1-L8 pipeline configuration."""
    mode: str  # "bridge", "maximal", "balanced"
    layers: Dict[int, LayerConfig] = field(default_factory=dict)
    adaptive: bool = True
    skip_unhealthy: bool = True
    notes: str = ""

    def __post_init__(self):
        if not self.layers:
            self.layers = {i: LayerConfig() for i in range(1, 9)}


class AutoTuner:
    """Recommends optimal configurations based on data type classification."""

    # Configuration templates for different data types
    PRESETS = {
        DataType.SOURCE_CODE: {
            "mode": "balanced",
            "notes": "Source code: moderate entropy, high repetition. Optimize L1-L3.",
            "layers": {
                1: LayerConfig(enabled=True, strategy="adaptive"),
                2: LayerConfig(enabled=True, strategy="xor"),
                3: LayerConfig(enabled=True, strategy="delta_rle"),
                4: LayerConfig(enabled=True, strategy="huffman"),
                5: LayerConfig(enabled=True, strategy="dictionary"),
                6: LayerConfig(enabled=True, strategy="gpu_optional"),
                7: LayerConfig(enabled=True, strategy="zlib", params={"level": 6}),
                8: LayerConfig(enabled=False),  # skip final compressor
            }
        },
        DataType.BINARY_LOG: {
            "mode": "maximal",
            "notes": "Binary logs: mixed patterns, time-series. Use all layers.",
            "layers": {
                1: LayerConfig(enabled=True, strategy="byte_pair"),
                2: LayerConfig(enabled=True, strategy="xor"),
                3: LayerConfig(enabled=True, strategy="delta"),
                4: LayerConfig(enabled=True, strategy="huffman"),
                5: LayerConfig(enabled=True, strategy="lz77"),
                6: LayerConfig(enabled=True, strategy="gpu_required"),
                7: LayerConfig(enabled=True, strategy="zlib", params={"level": 9}),
                8: LayerConfig(enabled=True, strategy="multi_layer_rle"),
            }
        },
        DataType.LLM_DATASET: {
            "mode": "balanced",
            "notes": "LLM dataset: text-heavy, varied entropy. Focus on L5.",
            "layers": {
                1: LayerConfig(enabled=True, strategy="adaptive"),
                2: LayerConfig(enabled=False),  # xor not useful
                3: LayerConfig(enabled=True, strategy="delta_rle"),
                4: LayerConfig(enabled=True, strategy="huffman"),
                5: LayerConfig(enabled=True, strategy="dictionary", params={"learn": True}),
                6: LayerConfig(enabled=False),  # hardware not needed
                7: LayerConfig(enabled=True, strategy="zlib", params={"level": 5}),
                8: LayerConfig(enabled=False),
            }
        },
        DataType.EXECUTABLE: {
            "mode": "maximal",
            "notes": "Executable: high entropy, structured code. Use hardware.",
            "layers": {
                1: LayerConfig(enabled=True, strategy="adaptive"),
                2: LayerConfig(enabled=True, strategy="xor"),
                3: LayerConfig(enabled=True, strategy="delta"),
                4: LayerConfig(enabled=True, strategy="huffman"),
                5: LayerConfig(enabled=True, strategy="dictionary"),
                6: LayerConfig(enabled=True, strategy="gpu_required"),
                7: LayerConfig(enabled=True, strategy="zlib", params={"level": 9}),
                8: LayerConfig(enabled=True, strategy="multi_layer_rle"),
            }
        },
        DataType.COMPRESSED: {
            "mode": "bridge",
            "notes": "Already compressed: skip most layers, pass-through.",
            "layers": {
                1: LayerConfig(enabled=False),
                2: LayerConfig(enabled=False),
                3: LayerConfig(enabled=False),
                4: LayerConfig(enabled=False),
                5: LayerConfig(enabled=False),
                6: LayerConfig(enabled=False),
                7: LayerConfig(enabled=False),
                8: LayerConfig(enabled=False),
            }
        },
        DataType.TEXT_DOCUMENT: {
            "mode": "balanced",
            "notes": "Plain text: low entropy, high repetition.",
            "layers": {
                1: LayerConfig(enabled=True, strategy="adaptive"),
                2: LayerConfig(enabled=True, strategy="xor"),
                3: LayerConfig(enabled=True, strategy="delta_rle"),
                4: LayerConfig(enabled=True, strategy="huffman"),
                5: LayerConfig(enabled=True, strategy="dictionary"),
                6: LayerConfig(enabled=False),
                7: LayerConfig(enabled=True, strategy="zlib", params={"level": 7}),
                8: LayerConfig(enabled=False),
            }
        },
        DataType.UNKNOWN: {
            "mode": "bridge",
            "notes": "Unknown data type: use safe default.",
            "layers": {
                1: LayerConfig(enabled=True, strategy="adaptive"),
                2: LayerConfig(enabled=True, strategy="xor"),
                3: LayerConfig(enabled=True, strategy="delta_rle"),
                4: LayerConfig(enabled=False),
                5: LayerConfig(enabled=False),
                6: LayerConfig(enabled=False),
                7: LayerConfig(enabled=False),
                8: LayerConfig(enabled=False),
            }
        },
    }

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def recommend(self, classification: ClassificationResult) -> PipelineConfig:
        """Recommend optimal pipeline config based on classification.
        
        Parameters
        ----------
        classification : ClassificationResult
            Output from Layer0Classifier.classify().
            
        Returns
        -------
        PipelineConfig
            Recommended configuration for L1-L8.
        """
        data_type = classification.data_type
        
        # Start with preset for detected type
        if data_type in self.PRESETS:
            preset = self.PRESETS[data_type].copy()
        else:
            preset = self.PRESETS[DataType.UNKNOWN].copy()
        
        mode = preset.get("mode", "bridge")
        notes = preset.get("notes", "")
        layers_dict = preset.get("layers", {})
        
        # Fine-tune based on entropy level
        if classification.entropy < 2.0:
            # very repetitive: enable aggressive compression
            notes += " [very low entropy detected; enabling extra stages]"
        elif classification.entropy > 7.0:
            # high entropy: may reduce effectiveness
            if data_type == DataType.COMPRESSED:
                notes += " [high entropy; skipping all compression]"
            else:
                notes += " [high entropy; using selective compression]"
        
        # Fine-tune based on confidence
        if classification.confidence < 0.6:
            # low confidence: use conservative bridge mode
            mode = "bridge"
            notes += " [low confidence; using safe bridge mode]"
        
        config = PipelineConfig(
            mode=mode,
            adaptive=True,
            skip_unhealthy=True,
            notes=notes,
        )
        
        # Populate layers from preset
        for layer_num in range(1, 9):
            if layer_num in layers_dict:
                config.layers[layer_num] = layers_dict[layer_num]
            else:
                config.layers[layer_num] = LayerConfig()
        
        self.logger.info(
            f"Recommended config: mode={mode}, type={data_type.value}, "
            f"conf={classification.confidence:.2f}"
        )
        
        return config

    def to_dict(self, config: PipelineConfig) -> Dict[str, Any]:
        """Convert PipelineConfig to dict for serialization/passing to pipeline."""
        return {
            "mode": config.mode,
            "adaptive": config.adaptive,
            "skip_unhealthy": config.skip_unhealthy,
            "layers": {
                layer_num: {
                    "enabled": lc.enabled,
                    "strategy": lc.strategy,
                    "params": lc.params,
                }
                for layer_num, lc in config.layers.items()
            },
            "notes": config.notes,
        }
