"""Entrypoint / router of the Fixed-Income Securities lab (Martellini, Priaulet & Priaulet, 2003).

Draws the shared chrome (theme CSS, sidebar navigation, banner) and runs the selected page.
Pages live in ``home.py`` and ``chapters/`` (not ``pages/``, which would clash with st.navigation); each page can also be run on its own for tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(next(p for p in _here.parents if (p / "shared").is_dir())))
sys.path.insert(0, str(_here.parent))

import streamlit as st

import lab_theme
from shared import theme, ui

theme.page_config("Fixed-Income Securities lab", icon="📈")
lab_theme.activate()
ui.inject_css()

home = st.Page("home.py", title="Overview", icon=":material/home:", default=True)
CHAPTERS = [
    (1, st.Page("chapters/01_Instruments_and_conventions.py", title="Bonds and money-market instruments",
                url_path="instruments"), "Bonds & money market"),
    (2, st.Page("chapters/02_Prices_and_yields.py", title="Bond prices and yields",
                url_path="prices-yields"), "Prices & yields"),
]
pg = st.navigation([home] + [p for _, p, _ in CHAPTERS], position="hidden")

ui.sidebar_nav(home, CHAPTERS, brand_accent="Fixed-income", brand_rest="securities lab",
               brand_sub="Martellini, Priaulet & Priaulet")
ui.banner("Fixed-income", "securities lab",
          "The models of <em>Fixed-Income Securities: Valuation, Risk Management and Portfolio Strategies</em>, "
          "by Martellini, Priaulet &amp; Priaulet, to explore in the browser")
pg.run()
