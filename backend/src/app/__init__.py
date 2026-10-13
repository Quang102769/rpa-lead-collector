"""App package root.

Ensures the parent 'src' directory is in sys.path so that 'from app...'
imports work regardless of whether the application is executed as
`src.app.main:app` or with `PYTHONPATH=src`.
"""

import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
