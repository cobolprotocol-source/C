from .dictionary_manager import (
    DictionaryManager,
    DictionaryManagerL1,
    DictionaryManagerL2,
    DictionaryManagerL3,
    DictionaryManagerL4,
    DictionaryManagerL5,
    DictionaryManagerL6,
    DictionaryManagerL7,
    DictionaryManagerL8,
)

# federated learning modules
from . import federated_learning_framework  # old v1.2 framework code
from . import federated_dictionary_learning    # newer v1.5 code

__all__ = [
    "DictionaryManager",
    "DictionaryManagerL1",
    "DictionaryManagerL2",
    "DictionaryManagerL3",
    "DictionaryManagerL4",
    "DictionaryManagerL5",
    "DictionaryManagerL6",
    "DictionaryManagerL7",
    "DictionaryManagerL8",
    # expose right modules at package level
    "federated_learning_framework",
    "federated_dictionary_learning",
]
