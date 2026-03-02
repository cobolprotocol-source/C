# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""
Configuration and Constants for COBOL Protocol - Nafal Faturizki Edition
=========================================================================

This module defines all configuration parameters, constants, and tuning knobs
for the 8-layer decentralized compression engine.

Layer Architecture:
- L1-2: Edge nodes performing semantic & structural mapping
- L3-4: Edge nodes performing delta encoding & bit-packing
- L5-7: High-spec nodes performing advanced RLE & pattern detection
- L8: Ultra-extreme instruction mapping with metadata pointers
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple

# ============================================================================
# COMPRESSION TARGETS & PERFORMANCE METRICS
# ============================================================================

TARGET_COMPRESSION_RATIO = 100_000_000  # 1:100M lossless compression
THROUGHPUT_TARGET_MBS = 9.1  # MB/s per core with NumPy vectorization
MIN_ENTROPY_THRESHOLD = 0.4  # Skip compression if entropy > 0.95
MAX_ENTROPY_SKIP_THRESHOLD = 0.95

# ============================================================================
# LAYER CONFIGURATION
# ============================================================================

class CompressionLayer(Enum):
    """Enumeration of the 8 compression layers."""
    L1_SEMANTIC_MAPPING = 1
    L2_STRUCTURAL_MAPPING = 2
    L3_DELTA_ENCODING = 3
    L4_VARIABLE_BITPACKING = 4
    L5_ADVANCED_RLE = 5
    L6_CROSS_BLOCK_PATTERNS = 6
    L7_PATTERN_REFINEMENT = 7
    L8_ULTRA_EXTREME_MAPPING = 8


# ============================================================================
# SECURITY & CRYPTOGRAPHY
# ============================================================================

ENCRYPTION_ALGORITHM = "AES-256-GCM"
HASH_ALGORITHM = "SHA-256"
HASH_OUTPUT_SIZE = 32  # bytes
GCM_TAG_SIZE = 16  # bytes
GCM_NONCE_SIZE = 12  # bytes (96 bits for GCM)
SALT_SIZE = 16  # bytes

# ============================================================================
# LAYER 1: SEMANTIC MAPPING
# ============================================================================

L1_MAX_DICTIONARY_SIZE = 256  # IDs are 1-byte (0-255)
L1_VOCABULARY_THRESHOLD = 0.8  # Use semantic mapping if 80%+ of tokens are frequent
L1_MIN_TOKEN_FREQUENCY = 3  # Minimum occurrences to include in dictionary

# Known semantic patterns for text, JSON, and code
L1_SEMANTIC_PATTERNS = {
    "text_markers": [
        "THE", "AND", "FOR", "THAT", "WITH", "HAVE", "FROM", "ABOUT",
        "WHICH", "THEIR", "WOULD", "THERE", "COULD", "OTHER", "PEOPLE"
    ],
    "json_markers": ["{", "}", "[", "]", ":", ",", "\"", "true", "false", "null"],
    "code_markers": [
        "def", "class", "if", "else", "return", "import", "from", "try",
        "except", "finally", "while", "for", "break", "continue"
    ],
    "numeric_markers": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."]
}

# ============================================================================
# LAYER 3: DELTA ENCODING
# ============================================================================

L3_DELTA_BLOCK_SIZE = 1024  # Process 1KB blocks for delta encoding
L3_DELTA_ORDER = 2  # Delta-of-Delta (second-order differences)
L3_MIN_GAIN_THRESHOLD = 0.05  # Skip delta encoding if < 5% space saved
L3_VARIABLE_LENGTH_ENCODING = True

# Variable-length integer encoding parameters
VARINT_CONTINUATION_BIT = 0x80
VARINT_VALUE_MASK = 0x7F

# ============================================================================
# LAYER 4: VARIABLE BIT-PACKING
# ============================================================================

L4_ZERO_STREAM_DETECTION = True
L4_BIT_WIDTH_MIN = 1
L4_BIT_WIDTH_MAX = 64
L4_CHUNK_SIZE = 256  # Numbers per chunk for bit-width optimization

# ============================================================================
# DICTIONARY MANAGEMENT
# ============================================================================

@dataclass
class DictionaryConfig:
    """Configuration for dictionary-based compression."""
    max_size: int = L1_MAX_DICTIONARY_SIZE
    min_frequency: int = L1_MIN_TOKEN_FREQUENCY
    adaptive: bool = True  # Adapt dictionary based on data patterns
    enable_backup_dicts: bool = True  # Maintain backup dictionaries per layer
    version: int = 1


# ============================================================================
# ADAPTIVE ENTROPY DETECTION
# ============================================================================

@dataclass
class EntropyConfig:
    """Configuration for adaptive entropy detection."""
    sample_size: int = 65536  # Sample size for entropy calculation (64KB)
    min_blocks_to_sample: int = 4  # Minimum blocks to determine entropy
    skip_threshold: float = MAX_ENTROPY_SKIP_THRESHOLD
    enable_per_block: bool = True  # Calculate entropy per block
    cache_results: bool = True  # Cache entropy calculations


# ============================================================================
# PARALLELISM & PERFORMANCE
# ============================================================================

@dataclass
class ParallelizationConfig:
    """Configuration for parallel processing."""
    num_workers: int = os.cpu_count() or 4
    chunk_size: int = 1_000_000  # 1MB chunks for parallel processing
    enable_vectorization: bool = True
    vectorization_batch_size: int = 10_000
    use_async: bool = False  # Use asyncio for I/O bound operations
    unix_pipe_compatible: bool = True  # Support streaming via Unix pipes


# ============================================================================
# INTEGRITY & VALIDATION
# ============================================================================

@dataclass
class IntegrityConfig:
    """Configuration for integrity checking."""
    compute_hashes: bool = True
    hash_algorithm: str = HASH_ALGORITHM
    verify_decompression: bool = True
    checkpoint_interval: int = 10_000_000  # Checkpoint every 10MB
    enable_checksums: bool = True


# ============================================================================
# STORAGE & MEMORY
# ============================================================================

PETABYTE = 1_000_000_000_000_000  # 1 PB in bytes
MAX_MEMORY_ALLOCATION = 16 * 1024 * 1024 * 1024  # 16 GB for buffers
STREAMING_BUFFER_SIZE = 1_000_000  # 1MB streaming buffer
DICTIONARY_MEMORY_BUDGET = 512 * 1024 * 1024  # 512MB for dictionaries

# ============================================================================
# ERROR HANDLING & LOGGING
# ============================================================================

class CompressionError(Exception):
    """Base exception for compression errors."""
    pass


class DecompressionError(Exception):
    """Base exception for decompression errors."""
    pass


class IntegrityError(Exception):
    """Exception raised when integrity check fails."""
    pass


class DictionaryError(Exception):
    """Exception raised for dictionary-related errors."""
    pass


# ============================================================================
# DEFAULT CONFIGURATIONS
# ============================================================================

DEFAULT_ENGINE_CONFIG = {
    "layers_enabled": list(CompressionLayer),
    "dictionaries": DictionaryConfig(),
    "entropy": EntropyConfig(),
    "parallelization": ParallelizationConfig(),
    "integrity": IntegrityConfig(),
    "enable_profiling": False,
    "verbose": False,
}

# ============================================================================
# TUNING PARAMETERS FOR PETABYTE-SCALE PROCESSING
# ============================================================================

PETABYTE_SCALE_TUNING = {
    "streaming_mode": True,  # Process data as stream
    "checkpoint_enabled": True,  # Save checkpoints for restart
    "distributed_mode": True,  # Use distributed processing
    "memory_efficient": True,  # Minimize memory footprint
    "batch_processing": True,  # Process in batches
}
