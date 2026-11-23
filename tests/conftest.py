"""Make this lab's ``core`` package importable (lab folders have hyphens, so they aren't packages)."""
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
