"""Delegate to the installed, self-contained framework runtime."""
from pathlib import Path
import os
import sys
root = Path(__file__).resolve().parents[1]
os.execv(sys.executable, [sys.executable, str(root / '.research-framework/runtime.pyz'), 'new-unit', str(root), *sys.argv[1:]])
