# Compatibility shim: federated dictionary learning implementation moved into
# the dictionaries package.  This module exists so existing imports don't break.

from importlib import import_module

__all__ = [
    # re-export everything from the new location
]

_module = None

def _load():
    global _module
    if _module is None:
        _module = import_module('src.layers.dictionaries.federated_dictionary_learning')
    return _module


def __getattr__(name):
    mod = _load()
    return getattr(mod, name)


def __dir__():
    mod = _load()
    return sorted(set(dir(mod)))
