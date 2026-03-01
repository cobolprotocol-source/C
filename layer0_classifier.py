"""Layer 0: Data Type Classifier for autonomous pipeline configuration.

This module implements intelligent data type detection via sampling and heuristic
analysis to enable zero-configuration compression. It identifies:
- Source code (human-readable, structured)
- Binary logs (mixed binary/text, timestamps)
- LLM datasets (natural language, JSON-like)
- Executable/binary (high entropy, magic numbers)
- Compressed/encrypted (max entropy)
- Plain text/documents
"""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Classification of data types."""
    SOURCE_CODE = "source_code"
    BINARY_LOG = "binary_log"
    LLM_DATASET = "llm_dataset"
    EXECUTABLE = "executable"
    COMPRESSED = "compressed"
    TEXT_DOCUMENT = "text_document"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of data type classification."""
    data_type: DataType
    confidence: float  # 0.0 to 1.0
    entropy: float    # Shannon entropy
    printable_ratio: float
    magic_bytes: Optional[str] = None
    details: Dict[str, float] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class Layer0Classifier:
    """Data type classifier using heuristic analysis on sample."""

    def __init__(self, sample_size: int = 8192):
        """Initialize classifier.
        
        Parameters
        ----------
        sample_size : int
            Number of bytes to sample from start of data.
        """
        self.sample_size = sample_size
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def classify(self, data: bytes) -> ClassificationResult:
        """Classify data type by sampling and analysis.
        
        Parameters
        ----------
        data : bytes
            Input data to classify.
            
        Returns
        -------
        ClassificationResult
            Classification with confidence and metadata.
        """
        if len(data) == 0:
            return ClassificationResult(
                data_type=DataType.UNKNOWN,
                confidence=0.0,
                entropy=0.0,
                printable_ratio=0.0,
            )

        sample = data[:self.sample_size]
        entropy = self._compute_entropy(sample)
        printable_ratio = self._compute_printable_ratio(sample)
        magic_bytes = self._detect_magic(sample)
        
        # collect detailed metrics
        details = {
            "entropy": entropy,
            "printable_ratio": printable_ratio,
            "null_byte_ratio": self._null_byte_ratio(sample),
            "low_entropy_ratio": self._low_entropy_runs(sample),
        }

        # heuristic classification
        if magic_bytes:
            data_type, conf = self._classify_by_magic(magic_bytes)
        else:
            data_type, conf = self._classify_by_heuristics(
                entropy, printable_ratio, details
            )

        return ClassificationResult(
            data_type=data_type,
            confidence=conf,
            entropy=entropy,
            printable_ratio=printable_ratio,
            magic_bytes=magic_bytes,
            details=details,
        )

    def _compute_entropy(self, data: bytes) -> float:
        """Compute Shannon entropy of data sample."""
        if len(data) == 0:
            return 0.0
        
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1
        
        import math
        entropy = 0.0
        for count in freq.values():
            p = count / len(data)
            entropy -= p * math.log2(p)
        
        return entropy

    def _compute_printable_ratio(self, data: bytes) -> float:
        """Ratio of printable ASCII + whitespace bytes."""
        if len(data) == 0:
            return 0.0
        
        printable = sum(
            1 for b in data
            if (32 <= b < 127) or b in (9, 10, 13)  # ASCII + tab/newline/CR
        )
        return printable / len(data)

    def _null_byte_ratio(self, data: bytes) -> float:
        """Ratio of null bytes."""
        if len(data) == 0:
            return 0.0
        return sum(1 for b in data if b == 0) / len(data)

    def _low_entropy_runs(self, data: bytes, window: int = 64) -> float:
        """Estimate ratio of low-entropy runs (repetitive sections)."""
        if len(data) < window:
            return 0.0
        
        low_count = 0
        for i in range(len(data) - window):
            chunk = data[i:i+window]
            ent = self._compute_entropy(chunk)
            if ent < 3.0:  # threshold for low entropy
                low_count += 1
        
        return low_count / (len(data) - window) if len(data) > window else 0.0

    def _detect_magic(self, data: bytes) -> Optional[str]:
        """Detect file magic numbers/signatures."""
        if len(data) < 4:
            return None
        
        magic_sigs = {
            b'\x7fELF': 'elf_executable',
            b'PK\x03\x04': 'zip_archive',
            b'\x1f\x8b\x08': 'gzip_archive',
            b'BM': 'bmp_image',
            b'GIF8': 'gif_image',
            b'\xff\xd8\xff': 'jpeg_image',
            b'\x89PNG': 'png_image',
            b'%PDF': 'pdf_document',
            b'MZ': 'windows_executable',
            b'\x00\x00\x01\x00': 'windows_icon',
            b'\xfd7zXZ\x00': '7z_archive',
        }
        
        for magic, sig_name in magic_sigs.items():
            if data.startswith(magic):
                return sig_name
        
        return None

    def _classify_by_magic(self, magic_bytes: str) -> Tuple[DataType, float]:
        """Classify based on detected magic bytes."""
        if 'executable' in magic_bytes or 'elf' in magic_bytes:
            return DataType.EXECUTABLE, 0.95
        elif 'archive' in magic_bytes or 'compress' in magic_bytes.lower():
            return DataType.COMPRESSED, 0.90
        else:
            return DataType.UNKNOWN, 0.5

    def _classify_by_heuristics(
        self, entropy: float, printable_ratio: float, details: Dict[str, float]
    ) -> Tuple[DataType, float]:
        """Classify using entropy and byte pattern heuristics."""
        
        null_ratio = details.get('null_byte_ratio', 0.0)
        low_entropy_ratio = details.get('low_entropy_ratio', 0.0)
        
        # very high entropy -> likely compressed or encrypted
        if entropy > 7.5:
            return DataType.COMPRESSED, 0.80
        
        # very low printable ratio + nulls -> likely binary
        if printable_ratio < 0.3 and null_ratio > 0.1:
            return DataType.BINARY_LOG, 0.75
        
        # high printable + low-moderate entropy + repetitive -> likely source code
        if printable_ratio > 0.85 and entropy < 4.5 and low_entropy_ratio > 0.15:
            return DataType.SOURCE_CODE, 0.85
        
        # high printable + medium-to-high entropy -> likely LLM dataset or text
        if printable_ratio > 0.80:
            # check if low entropy despite high printable (typical text docs)
            if entropy < 4.0:
                return DataType.TEXT_DOCUMENT, 0.85
            elif entropy > 5.0:
                return DataType.LLM_DATASET, 0.70
            else:
                return DataType.TEXT_DOCUMENT, 0.75
        
        # medium printable, mixed entropy -> binary logs
        if 0.3 <= printable_ratio <= 0.8 and 4.0 <= entropy <= 6.5:
            return DataType.BINARY_LOG, 0.70
        
        return DataType.UNKNOWN, 0.5
