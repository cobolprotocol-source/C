from .protocol_bridge import ProtocolLanguage
from typing import Dict, Any, Type
import numpy as np

class DictionaryManager:
    """
    Advanced Dictionary Manager for all layers (L1-L8).
    Fitur: adaptive learning, backup/versioning, hash chaining antar layer, global registry, DictionaryChain, statistik, dan serialization multi-node.
    """
    def __init__(self, header: ProtocolLanguage, input_type: Type, output_type: Type):
        self.header = header
        self.input_type = input_type
        self.output_type = output_type
        self.dictionary: Dict[Any, Any] = {}
        self.reverse_dictionary: Dict[Any, Any] = {}
        self.backup_dictionaries: Dict[str, list] = {}
        self.dictionary_hashes: Dict[str, bytes] = {}
        self.global_registry: Dict[str, Any] = {}
        self.dictionary_chain: list = []
        self.usage_stats: Dict[str, int] = {}
        self.version: int = 1
        self._initialize_base_dictionary()

    def _initialize_base_dictionary(self):
        """Inisialisasi dictionary dasar dan chain."""
        self.dictionary_chain.append(self.dictionary)
"""
Compatibility shim: re-export dictionary manager from src.layers.dictionaries

This file remains at `src/dictionary_manager.py` to keep backwards compat
imports working. The real implementation lives in `src/layers/dictionaries/`.
"""

from src.layers.dictionaries.dictionary_manager import *

__all__ = [
    'DictionaryManager',
    'DictionaryManagerL1',
    'DictionaryManagerL2',
    'DictionaryManagerL3',
    'DictionaryManagerL4',
    'DictionaryManagerL5',
    'DictionaryManagerL6',
    'DictionaryManagerL7',
    'DictionaryManagerL8',
]
        self.dictionary.clear()
