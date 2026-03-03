# Common pytest configuration for COBOL Protocol tests.
# Ensure that the project root is on sys.path so that `import src` works
# regardless of the directory from which pytest is invoked.

import sys
from pathlib import Path

root = Path(__file__).parent.parent.resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
