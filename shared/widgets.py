"""Common Streamlit controls and page blocks (CLAUDE.md §5 page structure).

Parameters are declared once as ``Param`` specs (mirroring the map's "Manipulable parameters"
table) and rendered with ``parameter_panel``.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class Param:
    """A manipulable model parameter: one slider."""

    key: str
    label: str
    min: float
    max: float
    default: float
    step: float | None = None
    help: str | None = None
    fmt: str | None = None  # e.g. "%.2f", "%d"

    def __post_init__(self) -> None:
        if not (self.min <= self.default <= self.max):
            raise ValueError(f"{self.key}: default {self.default} outside [{self.min}, {self.max}]")


def _is_int_param(p: Param) -> bool:
    return all(isinstance(v, int) for v in (p.min, p.max, p.default)) and (
        p.step is None or isinstance(p.step, int))


def parameter_panel(params: Sequence[Param], *, title: str = "Parameters",
                    sidebar: bool = True, key_prefix: str = "",
                    container=None) -> dict[str, float]:
    """Render one slider per ``Param``; return ``{key: value}``.

    Values are kept in *display units* (e.g. percent as 3.5, not 0.035) so the slider label shows
    exactly the number the model uses; convert in the page. Integer-valued specs give int sliders.
    ``key_prefix`` keeps widget keys unique when two panels share parameter names.
    ``container`` overrides the default placement (sidebar, or an expander when ``sidebar=False``).
    Defaults are written to ``st.session_state`` first, so ``preset_selector`` and the reset
    button can change them without Streamlit's "default value + session state" warning.
    """
    if container is None:
        container = st.sidebar if sidebar else st.expander(title, expanded=True)
        if sidebar:
            container.header(title)
    values: dict[str, float] = {}
    for p in params:
        cast = int if _is_int_param(p) else float
        k = f"{key_prefix}{p.key}"
        if k not in st.session_state:
            st.session_state[k] = cast(p.default)
        values[p.key] = container.slider(
            p.label,
            min_value=cast(p.min), max_value=cast(p.max),
            step=None if p.step is None else cast(p.step),
            help=p.help, format=p.fmt, key=k,
        )
    if container.button("Reset to defaults", key=f"{key_prefix}__reset"):
        for p in params:
            st.session_state[f"{key_prefix}{p.key}"] = (int if _is_int_param(p) else float)(p.default)
        st.rerun()
    return values


def preset_selector(presets: Mapping[str, Mapping[str, object]], *, key_prefix: str = "",
                    label: str = "Preset", container=None, help: str | None = None) -> str:
    """Dropdown of named scenarios; choosing one writes its values into the widgets' state.

    ``presets`` maps a name to ``{param_key: value}`` (keys without ``key_prefix``). Call it
    *before* the widgets it controls. Returns the selected preset name.
    """
    container = container or st
    names = list(presets)
    sel_key = f"{key_prefix}__preset"

    def _apply() -> None:
        for k, v in presets[st.session_state[sel_key]].items():
            st.session_state[f"{key_prefix}{k}"] = v

    if sel_key not in st.session_state:
        st.session_state[sel_key] = names[0]
        _apply()
    return container.selectbox(label, names, key=sel_key, on_change=_apply, help=help)


def seed_input(default: int = 42, *, sidebar: bool = True, key: str = "seed") -> int:
    """Random-seed control for simulations (fixed by default for reproducibility)."""
    container = st.sidebar if sidebar else st
    return int(container.number_input("Random seed", min_value=0, value=default, step=1, key=key))


def section(title: str) -> None:
    """Standard section header (Intuition / Model / Simulator / What to notice / ...)."""
    st.header(title)


def equation(latex: str, symbols: dict[str, str] | None = None, label: str | None = None) -> None:
    """Render an equation and a symbol glossary beneath it.

    ``label`` is the source's equation number, e.g. "Eq. 5.3".
    """
    if label:
        st.caption(label)
    st.latex(latex)
    if symbols:
        st.markdown("\n".join(f"- ${sym}$ — {meaning}" for sym, meaning in symbols.items()))


def what_to_notice(points: Sequence[str]) -> None:
    section("What to notice")
    st.markdown("\n".join(f"- {p}" for p in points))


@dataclass(frozen=True)
class Exercise:
    """One exercise. With ``numeric_answer`` the page shows an input box and checks it.

    ``tolerance`` is absolute, in the same units as ``unit`` (e.g. 0.01 for "%" means 1 bp).
    """

    question: str
    answer: str  # markdown worked answer; revealed in a collapsed expander
    numeric_answer: float | None = None
    tolerance: float = 1e-2
    unit: str = ""
    kind: str = "compute"  # "compute" or "explain" (shown as a tag)


def check_answer(value: float, ex: Exercise) -> bool:
    """True when ``value`` is within the exercise tolerance (pure: unit-tested)."""
    if ex.numeric_answer is None:
        raise ValueError("Exercise has no numeric answer")
    return abs(value - ex.numeric_answer) <= ex.tolerance


def exercises(items: Sequence[Exercise], *, key_prefix: str = "ex") -> None:
    section("Exercises")
    for i, ex in enumerate(items, start=1):
        tag = "Compute" if ex.kind == "compute" else "Explain"
        with st.container(key=f"blex_{key_prefix}_{i}"):
            st.markdown(f'<span class="bl-num">{i}</span><span class="bl-tag">{tag}</span> {ex.question}',
                        unsafe_allow_html=True)
            if ex.numeric_answer is not None:
                c1, c2 = st.columns([2, 3])
                val = c1.number_input(f"Your answer{f' ({ex.unit})' if ex.unit else ''}",
                                      value=None, format="%.6f", key=f"{key_prefix}_{i}",
                                      placeholder="type a number")
                if val is not None:
                    if check_answer(val, ex):
                        c2.success("Correct ✔")
                    else:
                        c2.error(f"Not quite — tolerance ±{ex.tolerance:g} {ex.unit}. Check the units "
                                 "and conventions, then try again.")
            with st.expander("Show worked answer", expanded=False):
                st.markdown(ex.answer)


def source_reference(citation: str, location: str, equations: Sequence[str] = ()) -> None:
    """Final block of each page: citation, chapter/section, equation numbers."""
    section("Source reference")
    lines = [f"- **Source:** {citation}", f"- **Location:** {location}"]
    if equations:
        lines.append(f"- **Equations:** {', '.join(equations)}")
    st.markdown("\n".join(lines))


def metric_row(metrics: dict[str, str | float], *, fmt: str = "{:.4g}") -> None:
    """A row of ``st.metric`` tiles for key outputs."""
    cols = st.columns(len(metrics))
    for col, (name, val) in zip(cols, metrics.items()):
        col.metric(name, fmt.format(val) if isinstance(val, (int, float)) else val)


# --- Teaching blocks (CLAUDE.md §5) ---------------------------------------------------------

def learning_objectives(objectives: Sequence[str], prerequisites: str | None = None) -> None:
    """§5.1: what the learner can do afterwards, plus a one-line prerequisites note."""
    with st.container(key="blobj_main"):
        st.html('<div class="bl-eyebrow">Learning objectives — after this page you can</div>')
        st.markdown("\n".join(f"- {o}" for o in objectives))
        if prerequisites:
            st.caption(f"**Prerequisites:** {prerequisites}")


def how_to_read(text: str, container=None) -> None:
    """One- or two-sentence caption under a chart."""
    (container or st).caption(f"📖 **How to read this chart:** {text}")


@dataclass(frozen=True)
class Tile:
    """A metric tile whose ``note`` states the conclusion, not just the number."""

    label: str
    value: str
    note: str = ""


def tiles(items: Sequence[Tile], container=None) -> None:
    """A row of metric tiles; the first carries the accent colour. Notes render as pill badges."""
    from shared import ui

    labels = [t.label for t in items]
    cols = (container or st).columns(len(items))
    for i, (col, t) in enumerate(zip(cols, items)):
        with col.container(key=ui.tile_key(labels, i)):
            st.metric(t.label, t.value)
            if t.note:
                st.html(ui.badge(t.note))


@dataclass(frozen=True)
class TryThis:
    """Guided experiment: what to move, what to predict, and the explanation."""

    prompt: str
    explanation: str


def try_this(items: Sequence[TryThis]) -> None:
    section("Guided experiments — try this")
    st.markdown("Make a prediction **before** you move the control, then open the explanation.")
    for i, t in enumerate(items, start=1):
        with st.container(key=f"bltry_{i}"):
            st.markdown(f'<span class="bl-num">{i}</span> {t.prompt}', unsafe_allow_html=True)
            with st.expander("What happened and why", expanded=False):
                st.markdown(t.explanation)


def pitfalls(items: Sequence[tuple[str, str]]) -> None:
    """§5.8: (mistake, why it is wrong) pairs."""
    import re

    def _md(x: str) -> str:  # minimal inline markdown for HTML cards
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<i>\1</i>", x))

    section("Common pitfalls")
    st.html("".join(f'<div class="bl-pit"><b>⚠ {_md(m)}</b><br>{_md(why)}</div>' for m, why in items))


def takeaways_and_glossary(takeaways: Sequence[str], glossary: Mapping[str, str]) -> None:
    section("Key takeaways")
    st.markdown("\n".join(f"{i}. {t}" for i, t in enumerate(takeaways, start=1)))
    with st.expander("Glossary", expanded=False):
        st.markdown("\n".join(f"- **{term}** — {d}" for term, d in sorted(glossary.items(),
                                                                         key=lambda kv: kv[0].lower())))
