"""Primary entry point for the COBOL compression system.

This script exists so that a single module can be executed (``python -m cobol``
or ``python main.py``) and will bring all of the core packages into scope.
Importing the key subsystems here also prevents them from being flagged as unused
in earlier static analysis runs.

The real work is delegated to :pyfunc:`distributed_framework.main`, which
implements the cluster startup logic.
"""

import asyncio

# pull in core modules to avoid accidental dead‑code removal
# (they may not all be referenced, but importing ensures the interpreter
# loads them and static checks will see the reference).  Only import
# subsystems that are truly "core" to the library.
from .layers.pipelines import engine  # compression engine variants (canonical)
from .layers.pipelines import adaptive  # health monitoring & adaptive control (canonical)
from . import energy_aware_execution  # energy‑aware scheduling
from . import hardware_optimized_layers  # layer definitions
from . import distributed_framework  # cluster orchestrator


def main():
    """Execute the distributed framework entry point.

    Returns whatever :pyfunc:`distributed_framework.main` returns (usually
    ``None``).  This wrapper gives a synchronous entry point for CLI usage.
    """
    # ``distributed_framework.main`` is async so we schedule it on the loop.
    return asyncio.run(distributed_framework.main())


if __name__ == "__main__":
    main()
