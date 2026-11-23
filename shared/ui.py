"""Page chrome for all labs: themed CSS, banner, sidebar navigation, chapter header and cards.

Everything is driven by the active ``BookTheme`` (see ``shared/theme.py``), so a lab gets its own
look by defining a theme in ``labs/<slug>/lab_theme.py``. Cards are keyed containers
(``st.container(key=...)``); Streamlit adds a ``st-key-<key>`` class we style below.

Typical router (``app.py``)::

    lab_theme.activate()
    ui.inject_css()
    pg = st.navigation([...], position="hidden")
    ui.sidebar_nav(home, [(1, page1), (2, page2)])
    ui.banner("FIXED-INCOME", "SECURITIES LAB", "subtitle html")
    pg.run()
"""
from __future__ import annotations

import hashlib
from collections.abc import Sequence
from urllib.parse import quote_plus

import streamlit as st

from shared import theme


def _key(prefix: str, *parts: object) -> str:
    h = hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:10]
    return f"{prefix}_{h}"


def _font_link(t: theme.BookTheme) -> str:
    fams = []
    for f, spec in ((t.heading_font, "wght@400;500;600;700"), (t.body_font, "ital,wght@0,400;0,600;0,700;1,400"),
                    (t.serif_font, "ital,wght@0,400;0,600;1,400;1,600")):
        if f and f not in [x[0] for x in fams]:
            fams.append((f, spec))
    q = "&".join(f"family={quote_plus(f)}:{spec}" for f, spec in fams)
    return f"https://fonts.googleapis.com/css2?{q}&display=swap"


def inject_css() -> None:
    """Inject the themed stylesheet. Call once per run, before any content."""
    t = theme.active()
    glow = ", ".join(t.glow)
    g = list(t.glow) + [t.accent] * 3
    css = f"""
<style>
@import url("{_font_link(t)}");
:root {{
  --bl-ink:{t.ink}; --bl-on-ink:{t.on_ink}; --bl-accent:{t.accent}; --bl-accent-soft:{t.accent_soft};
  --bl-hl:{t.highlight}; --bl-surface:{t.surface}; --bl-card:{t.card}; --bl-text:{t.text};
  --bl-muted:{t.muted}; --bl-rule:{t.rule};
  --bl-head:'{t.heading_font}', '{t.body_font}', sans-serif; --bl-body:'{t.body_font}', sans-serif;
  --bl-serif:'{t.serif_font}', Georgia, serif;
}}
html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"],
[data-testid="stWidgetLabel"], .stMarkdown, button, input, textarea, select {{ font-family: var(--bl-body); }}
[data-testid="stAppViewContainer"] {{ background: var(--bl-surface); }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 3.2rem !important; max-width: 1240px; }}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ font-size: 1.02rem; line-height: 1.62; color: var(--bl-text); }}

/* headings */
h1, h2, h3, h4 {{ font-family: var(--bl-head) !important; color: var(--bl-ink) !important; letter-spacing: .01em; }}
[data-testid="stHeading"] h2 {{ font-weight: 600; font-size: 1.85rem; margin-top: 1.6rem;
  padding-bottom: .35rem; border-bottom: 2px solid var(--bl-rule); }}
[data-testid="stHeading"] h2::before {{ content: ""; display: inline-block; width: 10px; height: 1.05rem;
  background: var(--bl-accent); margin-right: .6rem; border-radius: 2px; vertical-align: -1px; }}
[data-testid="stHeading"] h3 {{ font-weight: 500; font-size: 1.3rem; }}
[data-testid="stCaptionContainer"] {{ color: var(--bl-muted); }}

/* sidebar */
[data-testid="stSidebar"] {{ background: var(--bl-ink); border-right: 0; }}
[data-testid="stSidebar"] * {{ color: var(--bl-on-ink); }}
[data-testid="stSidebarHeader"] {{ padding-bottom: 0; }}
.bl-side-brand {{ font-family: var(--bl-head); font-size: 1.15rem; line-height: 1.15; letter-spacing: .04em;
  text-transform: uppercase; margin: 0 0 .2rem 0; }}
.bl-side-brand b {{ color: var(--bl-accent) !important; font-weight: 600; }}
.bl-side-sub {{ font-family: var(--bl-serif); font-style: italic; font-size: .86rem; opacity: .75; margin-bottom: 1rem; }}
.bl-side-label {{ font-size: .72rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase;
  opacity: .65; border-bottom: 1px solid rgba(255,255,255,.14); padding-bottom: .4rem; margin: 1.1rem 0 .3rem 0; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{ border-radius: 4px; padding: .38rem .55rem;
  border-left: 3px solid transparent; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{ background: rgba(255,255,255,.07); }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"],
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"].bl-active {{ background: rgba(255,255,255,.10);
  border-left-color: var(--bl-accent); }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p, [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] span
  {{ font-size: .95rem; color: var(--bl-on-ink) !important; opacity: 1 !important; }}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{ opacity: 1 !important; }}
.st-key-blnav {{ counter-reset: blch; gap: .1rem; }}
.st-key-blnav [data-testid="stPageLink-NavLink"] p::before {{ counter-increment: blch; content: counter(blch);
  display: inline-block; width: 1.6rem; font-weight: 700; color: var(--bl-accent); }}

/* banner */
.bl-banner {{ margin: 0 0 1.4rem 0; border-radius: 14px; overflow: hidden; background: var(--bl-ink);
  box-shadow: 0 6px 24px rgba(0,0,0,.18); }}
.bl-glow {{ height: 46px; background:
  radial-gradient(ellipse 18% 140% at 8% 60%, {g[0]} 0%, transparent 70%),
  radial-gradient(ellipse 14% 120% at 30% 30%, {g[1]} 0%, transparent 70%),
  radial-gradient(ellipse 22% 160% at 55% 80%, {g[2]} 0%, transparent 70%),
  radial-gradient(ellipse 16% 130% at 80% 40%, {g[0]} 0%, transparent 70%),
  radial-gradient(ellipse 12% 120% at 96% 70%, {g[1]} 0%, transparent 70%),
  var(--bl-ink); position: relative; }}
.bl-glow::after {{ content: ""; position: absolute; inset: 0; background:
  repeating-linear-gradient(90deg, rgba(0,0,0,.55) 0 2px, transparent 2px 64px),
  repeating-linear-gradient(0deg, rgba(0,0,0,.45) 0 2px, transparent 2px 15px); }}
.bl-band {{ padding: 1.15rem 2.2rem 1.3rem 2.2rem; border-top: 1px solid rgba(255,255,255,.08); }}
.bl-title {{ font-family: var(--bl-head); font-weight: 600; font-size: 2.7rem; line-height: 1.05;
  color: #FFFFFF; letter-spacing: .02em; text-transform: uppercase; }}
.bl-title .acc {{ color: var(--bl-accent); }}
.bl-rule {{ height: 2px; width: min(560px, 70%); margin: .55rem 0 .6rem 0;
  background: linear-gradient(90deg, {glow}, transparent); }}
.bl-sub {{ font-family: var(--bl-serif); color: var(--bl-on-ink); font-size: 1.05rem; }}
.bl-sub em {{ font-style: italic; }}

/* chapter header */
.bl-chap {{ display: flex; align-items: baseline; gap: 1rem; margin-top: .6rem; }}
.bl-chap-num {{ font-family: var(--bl-head); font-weight: 700; font-size: 3.6rem; line-height: 1; color: var(--bl-accent); }}
.bl-chap-title {{ font-family: var(--bl-head); font-weight: 600; font-size: 2.45rem; line-height: 1.1; color: var(--bl-ink); }}
.bl-chap-kicker {{ color: var(--bl-muted); font-size: .9rem; margin: .35rem 0 .5rem 0; letter-spacing: .02em; }}
.bl-chap-rule {{ height: 2px; width: min(760px, 80%); background: var(--bl-accent); margin-bottom: 1rem; }}
.bl-lede {{ font-family: var(--bl-serif); font-size: 1.18rem; line-height: 1.55; color: var(--bl-text);
  max-width: 900px; margin-bottom: .6rem; }}

/* cards */
[class*="st-key-blcard"], [class*="st-key-blformula"], [class*="st-key-bltry"], [class*="st-key-blex"],
[class*="st-key-blobj"] {{ background: var(--bl-card); border: 1px solid var(--bl-rule); border-radius: 10px;
  padding: 1rem 1.2rem 1.05rem 1.2rem; box-shadow: 0 1px 2px rgba(0,0,0,.03); }}
[class*="st-key-blobj"] {{ border-left: 4px solid var(--bl-accent); }}
[class*="st-key-blnote"] {{ background: var(--bl-accent-soft); border-left: 4px solid var(--bl-hl);
  border-radius: 8px; padding: .8rem 1.1rem; }}
.bl-eyebrow {{ font-size: .72rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase;
  color: var(--bl-muted); margin-bottom: .1rem; }}
[class*="st-key-blformula"] .katex {{ font-size: 1.08em; }}
[class*="st-key-blformula"] [data-testid="stMarkdownContainer"] p {{ margin-bottom: 0; }}

/* metric tiles */
[class*="st-key-bltile"] {{ background: var(--bl-card); border: 1px solid var(--bl-rule); border-top: 3px solid var(--bl-ink);
  border-radius: 8px; padding: .65rem .9rem .75rem .9rem; height: 100%; gap: .25rem; }}
[class*="st-key-bltile"][class*="_first"] {{ border-top-color: var(--bl-accent); }}
[data-testid="stMetricValue"] p {{ font-size: inherit !important; font-family: inherit !important;
  font-weight: inherit !important; color: inherit !important; line-height: 1.15 !important; margin: 0; }}
[data-testid="stMetricLabel"] p {{ font-size: .85rem !important; color: var(--bl-muted) !important; }}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {{ font-family: var(--bl-head) !important;
  font-weight: 600 !important; color: var(--bl-ink) !important; font-size: 1.95rem !important; line-height: 1.15; }}
.bl-badge {{ display: inline-block; background: var(--bl-accent-soft); color: var(--bl-ink); font-weight: 600;
  font-size: .8rem; line-height: 1.35; padding: .2rem .6rem; border-radius: 8px; }}

/* charts, tables, expanders, tabs, alerts */
[data-testid="stPlotlyChart"] {{ background: var(--bl-card); border: 1px solid var(--bl-rule); border-radius: 10px;
  padding: .4rem .5rem .2rem .5rem; }}
[data-testid="stExpander"] details {{ background: var(--bl-card); border: 1px solid var(--bl-rule); border-radius: 8px; }}
[data-testid="stExpander"] summary p {{ font-weight: 600; }}
[data-testid="stTable"] table, [data-testid="stDataFrame"] {{ background: var(--bl-card); }}
[data-baseweb="tab-list"] {{ gap: 1.2rem; border-bottom: 1px solid var(--bl-rule); }}
button[data-baseweb="tab"] p {{ font-family: var(--bl-head); font-size: 1.02rem; letter-spacing: .02em; }}
button[data-baseweb="tab"][aria-selected="true"] p {{ color: var(--bl-accent); }}
[data-baseweb="tab-highlight"] {{ background-color: var(--bl-accent) !important; }}
[data-testid="stAlert"] {{ border-radius: 8px; }}
.bl-num {{ display: inline-flex; align-items: center; justify-content: center; width: 1.6rem; height: 1.6rem;
  border-radius: 50%; background: var(--bl-ink); color: #fff !important; font-family: var(--bl-head);
  font-size: .9rem; margin-right: .45rem; vertical-align: 1px; }}
.bl-pit {{ background: var(--bl-card); border: 1px solid var(--bl-rule); border-left: 4px solid var(--bl-hl);
  border-radius: 8px; padding: .7rem 1rem; margin-bottom: .6rem; }}
.bl-pit b {{ color: var(--bl-ink); }}
.bl-tag {{ display:inline-block; font-size:.72rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
  color: var(--bl-accent); margin-right:.4rem; }}
</style>
"""
    st.html(css)


def banner(accent_text: str, rest: str, subtitle_html: str) -> None:
    """Top banner: a decorative strip in the cover's colours, a two-tone title and a subtitle."""
    st.html(
        f'<div class="bl-banner"><div class="bl-glow"></div><div class="bl-band">'
        f'<div class="bl-title"><span class="acc">{accent_text}</span> {rest}</div>'
        f'<div class="bl-rule"></div><div class="bl-sub">{subtitle_html}</div></div></div>'
    )


def sidebar_nav(home, chapters: Sequence[tuple[int, object, str]], *, brand_accent: str, brand_rest: str,
                brand_sub: str, label: str = "Chapters") -> None:
    """Sidebar: brand, overview link and numbered chapter links.

    ``chapters`` = [(number, st.Page, title)]. Numbers are drawn by CSS counters, so pass the
    chapters in order and starting at 1 (the number is kept for the caller's readability).
    """
    with st.sidebar:
        st.html(f'<div class="bl-side-brand"><b>{brand_accent}</b> {brand_rest}</div>'
                f'<div class="bl-side-sub">{brand_sub}</div>')
        st.page_link(home, label="Overview", icon=":material/home:")
        st.html(f'<div class="bl-side-label">{label}</div>')
        with st.container(key="blnav"):
            for _num, page, title in chapters:
                st.page_link(page, label=title)


def chapter_header(number: int | str, title: str, kicker: str, lede: str | None = None) -> None:
    """Large chapter number + title, a kicker line, an accent rule and an optional serif lede."""
    st.html(
        f'<div class="bl-chap"><span class="bl-chap-num">{number}</span>'
        f'<span class="bl-chap-title">{title}</span></div>'
        f'<div class="bl-chap-kicker">{kicker}</div><div class="bl-chap-rule"></div>'
        + (f'<div class="bl-lede">{lede}</div>' if lede else "")
    )


def eyebrow(text: str, container=None) -> None:
    (container or st).html(f'<div class="bl-eyebrow">{text}</div>')


def card(label: str | None = None, *, key: str):
    """A white card (keyed container) with an optional small-caps label. Use as a context manager."""
    c = st.container(key=f"blcard_{key}")
    if label:
        eyebrow(label, c)
    return c


def formula_card(items: Sequence[tuple[str, str]], *, key: str = "main", per_row: int = 3) -> None:
    """The page's key formulas at a glance: labelled LaTeX in a card, ``per_row`` per row."""
    with st.container(key=f"blformula_{key}"):
        for i in range(0, len(items), per_row):
            cols = st.columns(per_row)
            for col, (label, latex) in zip(cols, items[i:i + per_row]):
                eyebrow(label, col)
                col.latex(latex)


def badge(text: str) -> str:
    """HTML for a pill badge (used in tiles)."""
    return f'<span class="bl-badge">{text}</span>'


def tile_key(labels: Sequence[str], i: int) -> str:
    return _key("bltile", *labels, i) + ("_first" if i == 0 else "")


def note(markdown: str, *, key: str, label: str | None = None) -> None:
    """A tinted call-out card (assumptions, caveats) in the lab's colours, instead of st.info."""
    with st.container(key=f"blnote_{key}"):
        if label:
            eyebrow(label)
        st.markdown(markdown)
