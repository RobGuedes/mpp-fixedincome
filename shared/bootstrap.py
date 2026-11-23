"""Make the repo root importable from any lab file.

Usage at the top of ``app.py`` or a page (before ``from shared import ...``)::

    import sys
    from pathlib import Path
    sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "shared").is_dir())))

This module exists to document the pattern; it cannot import itself before the path is set.
"""
from __future__ import annotations

from pathlib import Path


def repo_root(start: str | Path) -> Path:
    """Return the first ancestor of ``start`` that contains a ``shared/`` directory."""
    for parent in Path(start).resolve().parents:
        if (parent / "shared").is_dir():
            return parent
    raise FileNotFoundError(f"No ancestor of {start} contains shared/")
