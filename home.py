"""Overview page: what the lab covers, the learning path and the module list."""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(next(p for p in _here.parents if (p / "shared").is_dir())))
sys.path.insert(0, str(_here.parent))

import streamlit as st

import lab_theme  # noqa: F401  (activates the lab's chart theme)
from shared import ui

ui.chapter_header(
    "◆", "An interactive lab on fixed-income markets",
    "Martellini, Priaulet & Priaulet · Fixed-Income Securities (Wiley, 2003) · Part I–II, chapters 1–4",
    lede="Explorable models for the first part of the book. Each page explains one chapter in its own words, "
         "re-solves the book's worked examples live, and lets you change every input. Every number the book "
         "prints for these examples is reproduced by automated tests.",
)

st.header("Modules")
MODULES = [
    (1, "Bonds and money-market instruments", "chapters/01_Instruments_and_conventions.py",
     "Clean vs. gross price, accrued interest, day counts, floaters and inflation-linked bonds, bill yields, "
     "repo carry."),
    (2, "Bond prices and yields", "chapters/02_Prices_and_yields.py",
     "Discounting, compounding, yield to maturity vs. realised return, forward rates, par yields."),
    (3, "The term structure: facts, factors, theories", None,
     "Curve shapes, Vasicek vs. CIR, PCA of Brazilian (BCB) and synthetic curves, expectations vs. premia."),
    (4, "Deriving the zero-coupon curve", None,
     "Bootstrapping, interpolation, splines, Nelson–Siegel/Svensson, interbank and credit curves."),
]
cols = st.columns(2)
for i, (num, title, path, blurb) in enumerate(MODULES):
    with cols[i % 2]:
        with ui.card(f"Chapter {num}", key=f"mod{num}"):
            st.markdown(f"### {title}")
            st.markdown(blurb)
            if path:
                st.page_link(path, label="Open the lab", icon=":material/arrow_forward:")
            else:
                st.caption("Coming soon")

st.header("How to use this lab")
c1, c2 = st.columns([3, 2])
with c1:
    st.markdown(
        """
**Suggested path:** go through the modules in order. Each one uses the conventions and tools of the one before.

**On each page:**
1. **Predict, then play.** Read the objectives and the intuition, then open the simulator. Before moving a
   control, say what you expect. The *Try this* prompts are built for this, and a wrong prediction is the
   most useful thing that can happen to you here.
2. **Read the model.** When a chart surprises you, the *Model* section has the equation and what it says in
   words. Open the derivations when you want to know *why*.
3. **Check yourself.** Do the exercises before opening the worked answers. The numeric ones check your answer.
4. **Go to the book** for what the lab does not reproduce: institutional detail, market data of the time,
   and the end-of-chapter problems. The *Source reference* at the bottom of each page says where to look.
"""
    )
with c2:
    with ui.card("Lab or book first?", key="labbook"):
        st.markdown(
            "**Lab first, book second, lab again.** Play with a page for 20–30 minutes to build intuition and "
            "collect questions. Then read the chapter with those questions in mind: you will read faster and "
            "retain more. Then come back and do the exercises.\n\n"
            "Read alongside the lab from the start only for chapters heavy in institutional detail."
        )

st.header("About")
st.markdown(
    """
- All explanations are written for this lab, and charts are regenerated from our own code. No text or figures
  are copied from the book. The colour scheme is inspired by the book's cover.
- Data are synthetic unless a page says otherwise. Real data (Brazilian rates from the BCB) are loaded
  from a saved snapshot, never from a live API.
- Conventions and simplifications are stated on each page (e.g. holidays are ignored in day counts).
"""
)
