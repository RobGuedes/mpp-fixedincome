"""Visual identity of this lab, taken from the colours of the book's cover (2003 Wiley edition):
a black title band over a glowing red–orange trading screen, white condensed lettering and a
serif italic subtitle. Only the colours and typographic mood are borrowed; no cover art is used.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "shared").is_dir())))

from shared import theme  # noqa: E402

THEME = theme.BookTheme(
    name="Fixed-Income Securities lab",
    ink="#14100E",          # the cover's black band (warm black)
    on_ink="#EEDAB9",       # cream, from the cover's highlights
    accent="#D72906",       # ember red (dominant cover hue)
    accent_soft="#F8E2D3",  # light tint of the accent, for badges
    highlight="#E8892B",    # copper-orange glow, for markers and call-outs
    surface="#F7F3EE",      # warm off-white page
    text="#221B17",
    muted="#7A6B62",
    rule="#E7DDD3",
    grid="#EFE7DE",
    # chart series: ember (model), warm ink (benchmark), copper (alternative), oxblood, slate, amber, teal
    series=("#C42A0B", "#2B2320", "#E8892B", "#7A1C10", "#6E7F8D", "#F2B33D", "#2E7D6E"),
    glow=("#FF6A13", "#D72906", "#FFB347"),
    heading_font="Oswald",
    body_font="Source Sans 3",
    serif_font="Source Serif 4",
)


def activate() -> None:
    theme.set_theme(THEME)


activate()
