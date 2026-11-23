"""Visual identity shared by all labs: palettes, fonts, the plotly template and page config.

Each lab gets its own look from a ``BookTheme`` (usually derived from the source's cover) defined in
``labs/<slug>/lab_theme.py`` and activated with ``set_theme``. Until a lab activates one, the neutral
default below (Okabe–Ito, colour-blind safe) is used.

Charts should use colours *by role* (``ROLE["model"]``, ``ROLE["benchmark"]``, ...) and look them up
at call time, so the same concept has the same colour everywhere in a lab.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import plotly.graph_objects as go
import plotly.io as pio


@dataclass(frozen=True)
class BookTheme:
    """A lab's visual identity. Colours are hex strings.

    - ``ink`` / ``on_ink``: the dark chrome (sidebar, banner) and the text drawn on it.
    - ``accent``: the signature colour (title highlight, active nav, sliders, chapter numbers).
    - ``highlight``: markers and call-outs the learner should look at.
    - ``surface`` / ``card``: page background and card background.
    - ``series``: categorical chart colours. Index 0 = main model, 1 = benchmark, 2 = alternative.
    - ``glow``: 2–4 colours for the banner's decorative strip (taken from the cover art).
    """

    name: str
    ink: str
    on_ink: str
    accent: str
    accent_soft: str
    highlight: str
    surface: str
    text: str
    muted: str
    rule: str
    series: tuple[str, ...]
    glow: tuple[str, ...]
    card: str = "#FFFFFF"
    grid: str = "#ECE7E1"
    heading_font: str = "Oswald"
    body_font: str = "Source Sans 3"
    serif_font: str = "Source Serif 4"
    extra: dict[str, str] = field(default_factory=dict)


NEUTRAL = BookTheme(
    name="Book Labs",
    ink="#111827", on_ink="#E5E7EB", accent="#0072B2", accent_soft="#DCEBF5", highlight="#D55E00",
    surface="#F5F6F8", text="#1F2937", muted="#6B7280", rule="#E5E7EB",
    series=("#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#000000"),
    glow=("#0072B2", "#56B4E9"), grid="#E5E7EB", heading_font="Inter", body_font="Inter",
)

# Mutable, module-level state read by plotting helpers at call time. ``set_theme`` updates in place.
ACTIVE: list[BookTheme] = [NEUTRAL]
PALETTE: list[str] = []
ROLE: dict[str, str] = {}
GRID = NEUTRAL.grid
AXIS = "#9CA3AF"
FONT_FAMILY = ""
TEMPLATE_NAME = "booklabs"


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _build_template(t: BookTheme) -> go.layout.Template:
    tpl = go.layout.Template()
    tpl.layout = go.Layout(
        font=dict(family=FONT_FAMILY, size=13, color=t.text),
        title=dict(font=dict(size=17, family=f"'{t.heading_font}', {FONT_FAMILY}", color=t.text),
                   x=0.0, xanchor="left"),
        colorway=list(t.series),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=t.grid, linecolor=AXIS, zeroline=False, ticks="outside", tickcolor=AXIS),
        yaxis=dict(gridcolor=t.grid, linecolor=AXIS, zeroline=False, ticks="outside", tickcolor=AXIS),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0,
                    bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=60, r=34, t=70, b=55),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=t.rule, font=dict(color=t.text)),
    )
    return tpl


def set_theme(t: BookTheme) -> None:
    """Activate a lab's theme for charts (plotly template and role colours). Idempotent."""
    global GRID, FONT_FAMILY
    ACTIVE[0] = t
    PALETTE[:] = list(t.series)
    ROLE.clear()
    ROLE.update({
        "model": t.series[0],       # the lab's main model / estimate
        "benchmark": t.series[1],   # comparison: random walk, fixed coupon, equal weights, ...
        "alt": t.series[2],         # a second competing method
        "data": "#8A817C" if t is not NEUTRAL else "#6B7280",  # observed data points (neutral)
        "truth": t.ink,             # true DGP value / reference lines
        "highlight": t.highlight,   # the thing the learner should look at
        "band": _rgba(t.series[0], 0.16),  # intervals around ``model``
    })
    GRID = t.grid
    FONT_FAMILY = f"'{t.body_font}', -apple-system, 'Segoe UI', Roboto, sans-serif"
    pio.templates[TEMPLATE_NAME] = _build_template(t)
    pio.templates.default = f"plotly_white+{TEMPLATE_NAME}"


set_theme(NEUTRAL)


def active() -> BookTheme:
    return ACTIVE[0]


def page_config(title: str, icon: str = "📘", wide: bool = True) -> None:
    """Set the browser title, icon and layout. Safe to call more than once per run."""
    import streamlit as st  # local import keeps this module usable outside Streamlit

    st.set_page_config(page_title=title, page_icon=icon, layout="wide" if wide else "centered")
