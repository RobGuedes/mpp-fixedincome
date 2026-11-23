"""Ch. 1 — Bonds and money-market instruments: conventions, quotes, coupons and repo.

Source: Martellini, Priaulet & Priaulet (2003), Fixed-Income Securities, ch. 1 (§1.1–1.2).
UI only; all calculations live in ``core/``.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(next(p for p in _here.parents if (p / "shared").is_dir())))
sys.path.insert(0, str(_here.parents[1]))  # lab root, for ``core``

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import conventions as cv
from core import indexed, money_market as mm, repo
import lab_theme  # noqa: F401  (activates the lab theme for charts)
from shared import plotting, theme, ui
from shared import widgets as w

ui.chapter_header(
    1, "Bonds and money-market instruments", "Chapter 1 · §1.1–1.2 · Instruments, quotes and conventions",
    lede="How a bond's cash flows, quotes and conventions turn into the money that actually changes hands, "
         "and how the short end of the market (bills, CDs, deposits, repo) is priced.",
)

# =============================================================================================
# 1. Learning objectives
# =============================================================================================
w.learning_objectives(
    [
        "Turn a bond's term sheet (coupon, frequency, maturity, day count) into dated cash flows.",
        "Explain why bonds are quoted **clean** and paid **gross**, and compute accrued interest.",
        "Compute the same period as a year fraction under Act/Act, Act/365, Act/360 and 30/360.",
        "Convert between price, **discount yield** and **money-market yield** for a bill, and explain "
        "why the two yields differ.",
        "Describe how floater, inverse-floater and inflation-linked coupons are set, and compute "
        "the daily **carry** of a repo-financed bond position.",
    ],
    prerequisites="none. This is the first page. Basic percentages and simple interest are enough.",
)

# =============================================================================================
# 2. Intuition
# =============================================================================================
w.section("Intuition")
st.markdown(
    """
**A puzzle to start.** You buy \\$1 million face value of a US Treasury note quoted at **96-05**.
The broker's confirmation asks for **\\$964,076.30**, not \\$961,562.50 (96.15625 % of \\$1 million).
Where do the extra \\$2,513.80 come from? And why is "96-05" not 96.05?

**A bond is a list of dated cash flows.** A 3.5 % semiannual note pays 1.75 per 100 of face value every
six months and 100 at maturity. Everything else on this page answers two practical questions about
that list: *when* exactly each payment happens and *how much* is owed between payments. The answers
are **conventions**: frequency, day-count basis, settlement lag. They are agreed by the market,
not derived from theory. Small differences in conventions change the numbers, so you always have to
know which one applies.

**Coupons belong to whoever held the bond.** The seller owned the note for 26 days since the last
coupon date, so they earned 26/181 of the next 1.75 coupon, even though the buyer will receive all of it.
The buyer compensates the seller up front with the **accrued interest**. The price including it is
the **gross** (dirty, full) price. Screens show the **clean** price, without accrued interest, because the
gross price drops by a full coupon on every payment date (chart below). The clean price
moves only when the market moves, which makes quotes comparable from day to day.

**The money market works on simple interest.** Instruments under one year (Treasury bills, certificates
of deposit, commercial paper, interbank deposits, repo) are quoted with *simple-interest* yields on a
360- or 365-day basis. Some markets quote a **discount yield**, the discount as a fraction of *face value*.
Others quote a **money-market yield**, the interest as a fraction of the *price you pay*. Both describe
the same bill, but the numbers differ. Comparing them without converting is a classic error.

**Why it matters.** Convention errors are not academic: misreading a quote, a day count or a yield basis
gives a wrong price, and in a repo-financed position the sign of the daily carry can flip with a few basis
points of repo rate.
"""
)


@st.cache_data
def _sawtooth(cpn: float, freq: int, mat: date, start: date, end: date, y: float) -> pd.DataFrame:
    days = pd.date_range(start, end, freq="D").date
    clean = [cv.clean_price_from_yield(cpn, freq, mat, d, y) for d in days]
    gross = [cv.gross_price_from_yield(cpn, freq, mat, d, y) for d in days]
    return pd.DataFrame({"date": days, "clean": clean, "gross": gross})


_m = _sawtooth(0.035, 2, date(2006, 11, 15), date(2001, 11, 16), date(2004, 11, 15), 0.04375)
_fig = plotting.line_chart(
    _m["date"], {"Gross (paid) price": _m["gross"], "Clean (quoted) price": _m["clean"]},
    title="The 3.5 % Nov-2006 Treasury note at a constant 4.375 % yield",
    x_label="Settlement date", y_label="Price (% of face)",
    colors={"Gross (paid) price": theme.ROLE["benchmark"], "Clean (quoted) price": theme.ROLE["model"]},
    height=360,
)
st.plotly_chart(_fig, width="stretch", theme=None)
w.how_to_read(
    "With the yield frozen, nothing economic changes, yet the gross price climbs by the accruing coupon "
    "and falls by 1.75 on each payment date (May and November). The clean price drifts smoothly towards "
    "100 at maturity. That smooth path is why the market quotes clean prices."
)

# =============================================================================================
# 3. Model
# =============================================================================================
w.section("Model")
ui.formula_card([
    ("Gross price", r"P_{\text{gross}} = P_{\text{clean}} + \frac{cF}{f}\cdot\frac{d_{\text{acc}}}{d_{\text{period}}}"),
    ("Bill: discount ↔ money-market yield", r"y_m = \frac{B\,y_d}{B-n\,y_d}"),
    ("Repo carry per day", r"\frac{c\,N}{360} - \frac{\text{Cash}_0\, r_{\text{repo}}}{360}"),
], key="ch1")
st.markdown("The three formulas above carry most of the chapter. Below, each one is unpacked. Prices are in "
            "**% of face value** (per 100); rates are annual and written as decimals in formulas.")

st.subheader("Accrued interest and the gross price")
w.equation(
    r"AI = \frac{c\,F}{f}\cdot\frac{d_{\text{accrued}}}{d_{\text{period}}}"
    r"\qquad\qquad P_{\text{gross}} = P_{\text{clean}} + AI",
    {
        "c": "annual coupon rate (e.g. 0.035)",
        "F": "face value (100 when prices are per 100)",
        "f": "coupons per year (1 annual, 2 semiannual, 4 quarterly)",
        r"d_{\text{accrued}}": "days from the last coupon date to the settlement date",
        r"d_{\text{period}}": "actual days in the current coupon period (Act/Act)",
    },
    label="§1.1.1, Example 1.4 (Act/Act, ICMA rule)",
)
st.markdown(
    "In words: the seller is paid the share of the current coupon that corresponds to the share of the "
    "coupon period they held the bond. Under the other bases, AI = c·F·(year fraction since last coupon), "
    "with the year fraction defined below."
)

st.subheader("Day-count conventions")
w.equation(
    r"\tau_{\text{Act/365}}=\frac{D_2-D_1}{365},\quad \tau_{\text{Act/360}}=\frac{D_2-D_1}{360},\quad"
    r"\tau_{30/360}=\frac{360(Y_2-Y_1)+30(M_2-M_1)+(d_2-d_1)}{360}",
    {
        r"D_2-D_1": "actual calendar days between the two dates",
        r"Y,M,d": "year, month, day of each date. Under 30/360 a day 31 is treated as 30",
        r"\tau_{\text{Act/Act}}": "for a general period: days in each calendar year divided by that year's length (365 or 366), summed",
    },
    label="§1.1.1, day-count type",
)
st.markdown(
    "In words: a day-count convention answers *how long is this period in years?* Act/360 treats the year "
    "as 360 days, so it counts each day as slightly more than 1/365 of a year and favours the party "
    "receiving interest. 30/360 pretends every month has 30 days, which makes coupon accruals identical "
    "across months."
)

st.subheader("Money-market yields (simple interest)")
w.equation(
    r"y_d=\frac{F-P}{F}\cdot\frac{B}{n}\;\Leftrightarrow\;P=F\Big(1-\frac{n\,y_d}{B}\Big)"
    r"\qquad y_m=\frac{F-P}{P}\cdot\frac{B}{n}\;\Leftrightarrow\;P=\frac{F}{1+n\,y_m/B}",
    {
        "y_d": "yield on a discount basis (US, euro-area, UK bills)",
        "y_m": "yield on a money-market basis (Japan bills, euro CP/CDs, deposits, repo)",
        "P, F": "price paid and face value repaid at maturity",
        "n": "calendar days to maturity",
        "B": "year basis, 360 or 365 depending on the market",
    },
    label="§1.2.3, Examples 1.17–1.20",
)
with st.expander("Derivation: from discount yield to money-market yield, and why y_m > y_d"):
    st.markdown(
        r"""
Both yields annualise the same dollar discount $F-P$ linearly, with factor $B/n$. They differ only in the
denominator: $y_d$ divides by face value $F$, and $y_m$ divides by the price $P$ actually invested.
Since $P<F$ whenever the yield is positive, $y_m>y_d$.

To convert, substitute $P = F(1-n y_d/B)$ into the definition of $y_m$:
$$
y_m=\frac{F-F(1-n y_d/B)}{F(1-n y_d/B)}\cdot\frac{B}{n}
=\frac{n y_d/B}{1-n y_d/B}\cdot\frac{B}{n}=\frac{B\,y_d}{B-n\,y_d}.
$$
The gap $y_m-y_d = y_d\cdot\frac{n y_d}{B-n y_d}$ grows with **both** the yield level and the maturity.
It is negligible for a 1-week bill at 2 % and large for a 1-year bill at 15 %.
"""
    )

st.markdown("A **certificate of deposit** pays its issue coupon at maturity, so the amount repaid is discounted at the market yield:")
w.equation(
    r"P = F\,\frac{1+c\,n_c/B}{1+y_m\,n_m/B}",
    {"c": "CD rate at issuance", "n_c": "days from issue to maturity", "n_m": "days from settlement to maturity"},
    label="§1.2.4, Example 1.21",
)

st.subheader("Coupons set by a formula")
w.equation(
    r"c_t^{\text{FRN}} = m\cdot I_{t} + s,\qquad c_t^{\text{inverse}}=\max(a-b\,I_t,\;\text{floor})",
    {"I_t": "reference index fixed at the reset date (e.g. 3-month Libor/Euribor, CDI)",
     "m, s": "multiplicative and additive margins", "a, b": "inverse-floater constant and leverage"},
    label="§1.1.1, Examples 1.10–1.11",
)
w.equation(
    r"DIR_t = CPI_{m-3}+\frac{n_t-1}{ND_m}\,(CPI_{m-2}-CPI_{m-3}),\qquad"
    r"C_t = F\cdot RC\cdot\frac{DIR_t}{DIR_{\text{initial}}},\qquad RV_T = F\cdot\frac{DIR_T}{DIR_{\text{initial}}}",
    {"DIR_t": "daily inflation reference, interpolated between two lagged monthly CPIs",
     "n_t, ND_m": "day of the month of date t, and number of days in that month",
     "RC": "real coupon rate", r"DIR_t/DIR_{\text{initial}}": "index ratio: cumulative inflation since the bond's reference date"},
    label="§1.1.1, French OATi",
)
st.markdown(
    "In words: an inflation-indexed bond pays a fixed *real* coupon on a principal that grows with the price "
    "index, so both coupons and redemption keep their purchasing power. The CPI is lagged two to three months "
    "because it is published late. The index is interpolated daily so accrued interest moves smoothly."
)

st.subheader("Repo financing and carry")
w.equation(
    r"\text{Cash}_0 = \tfrac{P_{\text{gross}}}{100}\,N,\qquad \text{Cash}_T=\text{Cash}_0\Big(1+r_{\text{repo}}\frac{d}{360}\Big),"
    r"\qquad \text{carry}_{\text{day}} = \frac{c\,N}{360}-\frac{\text{Cash}_0\,r_{\text{repo}}}{360}",
    {"N": "nominal of bonds delivered as collateral", r"r_{\text{repo}}": "repo rate (Act/360)",
     "d": "repo term in days"},
    label="§1.2.8, Examples 1.25–1.26",
)
st.markdown(
    "In words: a repo is a loan secured by the bond. A trader who is long the bond and finances it in repo "
    "earns the coupon accrual and pays the repo interest. The difference is the **carry**. A short seller "
    "has the mirror-image position."
)
ui.note(
    "Holidays and business-day adjustments are ignored; the settlement date is "
    "set directly (in practice it is trade date + 1 to 3 business days, by market). No repo haircut. Accrued "
    "interest under Act/Act uses actual days in the coupon period (ICMA). Prices from yields use the "
    "street convention, which Chapter 2 explains.",
    key="assumptions", label="Assumptions on this page",
)

# =============================================================================================
# 4. Worked example (live) — Example 1.4
# =============================================================================================
w.section("Worked example (live): from a quote to the cash paid")
st.markdown(
    "Book Example 1.4, re-solved with our code: a 3.5 % semiannual US Treasury maturing 11/15/2006 is bought "
    "for settlement on 12/11/2001 at a quoted 96-05. Change any input to see every step update."
)
wc = st.columns(5)
we_quote = wc[0].text_input("Quote (handle-32nds)", "96-05", key="we_quote",
                            help='"96-05" means 96 + 5/32. A trailing "+" adds half a 32nd.')
we_cpn = wc[1].number_input("Coupon (%)", 0.0, 20.0, 3.5, 0.125, format="%.3f", key="we_cpn")
we_freq = wc[2].selectbox("Coupons / year", [2, 1, 4], key="we_freq")
we_mat = wc[3].date_input("Maturity", date(2006, 11, 15), key="we_mat")
we_set = wc[4].date_input("Settlement", date(2001, 12, 11), key="we_set")
we_conv = st.radio("Day count", cv.CONVENTIONS, horizontal=True, key="we_conv")
we_nom = 1_000_000

try:
    clean = cv.from_32nds(we_quote)
    if we_set >= we_mat:
        raise ValueError("Settlement must be before maturity.")
    ai = cv.accrued_interest(we_cpn / 100, we_freq, we_mat, we_set, we_conv)
except ValueError as e:
    st.error(f"Input problem: {e}")
else:
    gross = cv.gross_price(clean, ai.accrued)
    frac_txt = (f"{ai.days_accrued} / {ai.days_in_period} = {ai.accrual_fraction:.5f} of the period"
                if we_conv == "ACT/ACT" else
                f"{ai.days_accrued} days → year fraction {ai.accrual_fraction:.5f}")
    ai_txt = (f"{ai.coupon_per_period:.4f} × {ai.accrual_fraction:.5f}" if we_conv == "ACT/ACT"
              else f"{we_cpn:.3f} × {ai.accrual_fraction:.5f}")
    steps = pd.DataFrame(
        [
            ("1. Decode the quote", f"{we_quote} = handle + 32nds/32", f"{clean:.5f}"),
            ("2. Last and next coupon dates", "generated backwards from maturity",
             f"{ai.previous_coupon:%m/%d/%Y} → {ai.next_coupon:%m/%d/%Y}"),
            ("3. Coupon per period", f"{we_cpn:.3f} / {we_freq}", f"{ai.coupon_per_period:.4f}"),
            ("4. Accrual", f"{we_conv}: {frac_txt}", f"{ai.accrual_fraction:.5f}"),
            ("5. Accrued interest", ai_txt, f"{ai.accrued:.5f}"),
            ("6. Gross price", f"{clean:.5f} + {ai.accrued:.5f}", f"{gross:.5f}"),
            ("7. Cash for $1 M face", f"{gross:.5f} % × 1,000,000", f"${gross / 100 * we_nom:,.2f}"),
        ],
        columns=["Step", "Computation", "Result"],
    )
    st.table(steps)
    w.tiles([
        w.Tile("Clean (quoted)", f"{clean:.5f}", "what the screen shows"),
        w.Tile("Accrued interest", f"{ai.accrued:.5f}",
               f"seller's share of the next {ai.coupon_per_period:.3f} coupon"),
        w.Tile("Gross (paid)", f"{gross:.5f}", "what the buyer actually pays per 100"),
        w.Tile("Extra cash vs. quote", f"${ai.accrued / 100 * we_nom:,.2f}", "per $1 M face: the accrued interest"),
    ])
    st.caption("Book values (Act/Act): AI = 0.25138, gross = 96.40763, cash = $964,076.3. Our code reproduces them; see `tests/test_01_instruments.py`.")

    with st.expander("Remaining cash flows of this bond (Example 1.6)"):
        flows = cv.cash_flow_schedule(we_cpn / 100, we_freq, we_mat, we_set, face=we_nom)
        st.dataframe(pd.DataFrame(flows, columns=["Date", "Cash flow ($)"]).style.format({"Cash flow ($)": "{:,.0f}"}),
                     hide_index=True, width="content")

# =============================================================================================
# 5. Simulator
# =============================================================================================
w.section("Simulator")
st.markdown("Five labs, one per idea. Each tab keeps all of its controls in the card at the top.")
tab_cg, tab_dc, tab_fl, tab_mm, tab_repo = st.tabs(
    ["① Clean vs. gross", "② Day counts", "③ Floaters & inflation-linked", "④ Money-market yields", "⑤ Repo & carry"]
)


# --- ① Clean vs. gross ----------------------------------------------------------------------
@st.fragment
def clean_vs_gross() -> None:
    card = ui.card("Parameters", key="cg")
    presets = {
        "Ex. 1.4 — US T-note 3.5 % Nov-2006 (semiannual)":
            {"cpn": 3.5, "freq": 2, "y": 4.375, "mat": date(2006, 11, 15), "set": date(2001, 12, 11)},
        "Bund 5 % Jul-2011 (annual), Ex. 1.25":
            {"cpn": 5.0, "freq": 1, "y": 4.5, "mat": date(2011, 7, 4), "set": date(2001, 10, 29)},
        "High coupon 9 % (quarterly), 5 years":
            {"cpn": 9.0, "freq": 4, "y": 6.0, "mat": date(2006, 12, 31), "set": date(2002, 1, 15)},
    }
    c1, c2 = card.columns([3, 2])
    w.preset_selector(presets, key_prefix="cg_", container=c1)
    c2.markdown("&nbsp;")
    cols = card.columns(5)
    cpn = cols[0].slider("Coupon (%)", 0.0, 12.0, step=0.125, format="%.3f%%", key="cg_cpn")
    freq = cols[1].selectbox("Coupons / year", [1, 2, 4], key="cg_freq")
    y = cols[2].slider("Yield (%), held constant", 0.0, 12.0, step=0.125, format="%.3f%%", key="cg_y")
    mat = cols[3].date_input("Maturity", key="cg_mat", min_value=date(1990, 1, 1), max_value=date(2060, 12, 31))
    settle = cols[4].date_input("Settlement (marker)", key="cg_set",
                                min_value=date(1990, 1, 1), max_value=date(2060, 12, 31))
    if settle >= mat:
        st.warning("Settlement must be before maturity.")
        return

    # Start at the coupon date before settlement (earlier dates may precede the bond's issue).
    start = cv.previous_coupon(mat, freq, settle)
    end = min(start + timedelta(days=3 * 365), mat - timedelta(days=1))
    df = _sawtooth(cpn / 100, freq, mat, start, end, y / 100)
    ai_now = cv.accrued_interest(cpn / 100, freq, mat, settle)
    g_now = cv.gross_price_from_yield(cpn / 100, freq, mat, settle, y / 100)
    fig = plotting.line_chart(
        df["date"], {"Gross (paid) price": df["gross"], "Clean (quoted) price": df["clean"]},
        title="Clean and gross price through time at a constant yield",
        x_label="Settlement date", y_label="Price (% of face)",
        colors={"Gross (paid) price": theme.ROLE["benchmark"], "Clean (quoted) price": theme.ROLE["model"]},
    )
    fig.add_trace(go.Scatter(x=[settle], y=[g_now], mode="markers", name="Your settlement date",
                             marker=dict(color=theme.ROLE["highlight"], size=12, line=dict(color=theme.ROLE["truth"], width=1.5))))
    st.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("Dark line = what you pay, red line = what the screen shows. The vertical gap between them is the "
                  "accrued interest: it grows linearly and resets to zero on each coupon date.")
    clean_now = g_now - ai_now.accrued
    prem = "premium (coupon > yield)" if cpn > y else ("discount (coupon < yield)" if cpn < y else "par (coupon = yield)")
    w.tiles([
        w.Tile("Clean price", f"{clean_now:.4f}", f"bond trades at a {prem}"),
        w.Tile("Accrued interest", f"{ai_now.accrued:.4f}",
               f"{ai_now.days_accrued} of {ai_now.days_in_period} days of the coupon period"),
        w.Tile("Gross price", f"{g_now:.4f}", "clean + accrued"),
        w.Tile("Next coupon", f"{ai_now.next_coupon:%d %b %Y}", f"gross will drop by {cpn / freq:.3f}"),
    ])


with tab_cg:
    clean_vs_gross()


# --- ② Day counts --------------------------------------------------------------------------
@st.fragment
def day_counts() -> None:
    card = ui.card("Parameters", key="dc")
    presets = {
        "Book period 08/01/1999 → 09/03/2001": {"d1": date(1999, 8, 1), "d2": date(2001, 9, 3), "cpn": 5.0},
        "Across February 01/31/2001 → 03/01/2001": {"d1": date(2001, 1, 31), "d2": date(2001, 3, 1), "cpn": 5.0},
        "Book 01/01/2001 → 03/25/2001": {"d1": date(2001, 1, 1), "d2": date(2001, 3, 25), "cpn": 5.0},
        "Leap-year February 01/31/2024 → 03/01/2024": {"d1": date(2024, 1, 31), "d2": date(2024, 3, 1), "cpn": 5.0},
    }
    w.preset_selector(presets, key_prefix="dc_", container=card)
    cols = card.columns(3)
    d1 = cols[0].date_input("Start date", key="dc_d1", min_value=date(1980, 1, 1), max_value=date(2070, 1, 1))
    d2 = cols[1].date_input("End date", key="dc_d2", min_value=date(1980, 1, 1), max_value=date(2070, 1, 1))
    cpn = cols[2].slider("Annual coupon on 100 face (%)", 0.0, 15.0, step=0.25, format="%.2f%%", key="dc_cpn")
    if d2 <= d1:
        st.warning("End date must be after start date.")
        return
    rows = []
    for c in cv.CONVENTIONS:
        tau = cv.year_fraction(d1, d2, c)
        rows.append({"Convention": c, "Days": cv.day_count(d1, d2, c),
                     "Years": tau, "Interest /100": cpn * tau})
    df = pd.DataFrame(rows)
    fig = plotting.bar_chart(df["Convention"], {"Year fraction": df["Years"]},
                             title="The same period measured in years under four conventions",
                             x_label="Day-count convention", y_label="Year fraction (years)", height=360)
    fig.update_traces(marker_color=[theme.PALETTE[i] for i in range(4)], text=[f"{v:.4f}" for v in df["Years"]],
                      textposition="outside", showlegend=False)
    lo, hi = df["Years"].min(), df["Years"].max()
    fig.update_yaxes(range=[max(0, lo - (hi - lo) * 3 - 1e-3), hi + (hi - lo) * 1.5 + 1e-3])
    left, right = st.columns([3, 2])
    left.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("Bars start near the smallest value, so small differences are visible. A gap of 0.001 years "
                  "is about a third of a day of interest.", container=left)
    right.dataframe(df.style.format({"Years": "{:.5f}", "Interest /100": "{:.4f}"}),
                    hide_index=True, width="stretch")
    spread = (df["Interest /100"].max() - df["Interest /100"].min())
    w.tiles([
        w.Tile("Act/360 vs Act/365", f"{(cv.year_fraction(d1, d2, 'ACT/360') / cv.year_fraction(d1, d2, 'ACT/365') - 1) * 100:.2f} %",
               "Act/360 always counts 1.39 % more time: it favours the lender"),
        w.Tile("Max − min interest", f"{spread:.4f}", f"per 100 face at {cpn:.2f} %: the price of not checking the convention"),
    ], container=right)
    with st.expander("Aside: the Brazilian convention (BUS/252)"):
        st.markdown(
            "Brazilian government bonds (LTN, NTN-F) and the CDI rate use **business days over 252** with "
            "*compound*, not simple, interest: a factor of $(1+r)^{du/252}$, where *du* counts business days "
            "using the ANBIMA holiday calendar. It is not in the book and needs a holiday calendar, so it is not "
            "computed here. The logic is the same: a convention decides how much time has passed."
        )


with tab_dc:
    day_counts()


# --- ③ Floaters & inflation-linked ---------------------------------------------------------
def _index_path(shape: str, shift_bp: float, years: int) -> np.ndarray:
    t = np.arange(years + 1)
    base = {
        "Flat 3 %": np.full_like(t, 0.03, dtype=float),
        "Rising 2 % → 8 %": 0.02 + 0.06 * t / years,
        "Falling 8 % → 1 %": 0.08 - 0.07 * t / years,
        "Spike (hike then cuts)": 0.03 + 0.05 * np.exp(-((t - years / 3) ** 2) / 4),
    }[shape]
    return base + shift_bp / 1e4


@st.fragment
def floaters() -> None:
    card = ui.card("Parameters · rate-linked coupons (annual resets, 10 years)", key="fl")
    cols = card.columns(5)
    shape = cols[0].selectbox("Index scenario", ["Rising 2 % → 8 %", "Flat 3 %", "Falling 8 % → 1 %",
                                                 "Spike (hike then cuts)"], key="fl_shape")
    shift = cols[1].slider("Shift the whole path (bp)", -300, 500, 0, 25, key="fl_shift")
    fixed = cols[2].slider("Fixed coupon (%)", 0.0, 12.0, 5.0, 0.25, format="%.2f%%", key="fl_fixed")
    margin = cols[3].slider("FRN margin (bp)", -100, 300, 20, 5, key="fl_margin",
                            help="Example 1.10: Libor + 20 bp")
    a = cols[4].slider("Inverse floater a (%)", 0.0, 25.0, 16.0, 0.5, format="%.1f%%", key="fl_a",
                       help="Example 1.11: 16 % − 2 × index")
    cols2 = card.columns(5)
    b = cols2[0].slider("Inverse floater leverage b", 0.0, 4.0, 2.0, 0.25, key="fl_b")
    floor = cols2[1].slider("Inverse floater floor (%)", 0.0, 5.0, 0.0, 0.25, format="%.2f%%", key="fl_floor")

    yrs = 10
    idx = _index_path(shape, shift, yrs)
    t = np.arange(yrs + 1)
    frn = indexed.floater_coupon(idx, additive_margin=margin / 1e4)
    inv = indexed.inverse_floater_coupon(idx, a / 100, b, floor / 100)
    fig = plotting.line_chart(
        t, {"Index": idx * 100, "Fixed": np.full(yrs + 1, fixed), "Floater": frn * 100, "Inverse floater": inv * 100},
        title="Coupon rate set at each reset date", x_label="Reset date (years from issue)", y_label="Coupon rate (%)",
        colors={"Index": theme.ROLE["data"], "Fixed": theme.ROLE["benchmark"], "Floater": theme.ROLE["model"],
                "Inverse floater": theme.ROLE["highlight"]},
        dashed=["Index"], height=380,
    )
    fig.update_traces(line_shape="hv")
    st.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("Steps show coupons fixed for one year at each reset. The floater tracks the index plus its margin. "
                  "The inverse floater moves *b* times as much in the opposite direction until it hits the floor.")
    floored = int((inv <= floor / 100 + 1e-12).sum())
    w.tiles([
        w.Tile("Avg floater coupon", f"{frn.mean() * 100:.2f} %", "follows rates: protects against rising rates"),
        w.Tile("Avg inverse-floater coupon", f"{inv.mean() * 100:.2f} %",
               f"floor binds in {floored} of {yrs + 1} resets" if floored else "floor never binds"),
        w.Tile("Inverse-floater sensitivity", f"−{b:.2f} × index", "a 100 bp rise cuts the coupon by "
               f"{b * 100:.0f} bp"),
    ])

    st.divider()
    card2 = ui.card("Parameters · inflation-indexed bond (annual coupon, OATi-style)", key="il")
    c = card2.columns(4)
    rc = c[0].slider("Real coupon (%)", 0.0, 6.0, 3.0, 0.25, format="%.2f%%", key="il_rc",
                     help="Example 1.14: OATi 3 % 2012")
    infl = c[1].slider("Annual inflation (%)", -2.0, 15.0, 2.0, 0.25, format="%.2f%%", key="il_infl")
    yrs_il = c[2].slider("Maturity (years)", 2, 30, 10, 1, key="il_yrs")
    nominal_cpn = c[3].slider("Nominal bond coupon for comparison (%)", 0.0, 15.0, 5.0, 0.25, format="%.2f%%",
                              key="il_nom")
    cf = indexed.indexed_bond_cash_flows(100.0, rc / 100, yrs_il, infl / 100)
    tt = cf["year"]
    deflator = (1 + infl / 100) ** tt
    nominal_cf = np.full(yrs_il, nominal_cpn) + np.where(tt == yrs_il, 100.0, 0.0)
    il_cf = cf["coupon"] + cf["redemption"]
    fig2 = plotting.bar_chart(
        [str(v) for v in tt],
        {"Indexed bond coupon": cf["coupon"], "Nominal bond coupon": np.full(yrs_il, nominal_cpn)},
        title="Annual coupons in money of the day", x_label="Year", y_label="Coupon per 100 face", height=360,
    )
    fig2.update_traces(marker_color=theme.ROLE["model"], selector=dict(name="Indexed bond coupon"))
    fig2.update_traces(marker_color=theme.ROLE["benchmark"], selector=dict(name="Nominal bond coupon"))
    st.plotly_chart(fig2, width="stretch", theme=None)
    w.how_to_read("The indexed coupon starts at the real coupon and grows with the CPI. The nominal coupon is fixed "
                  "in currency, so its purchasing power erodes. With positive inflation the indexed coupons catch up "
                  "over time; the principal (tiles below) is indexed too.")
    real_il = (il_cf / deflator).sum()
    real_nom = (nominal_cf / deflator).sum()
    w.tiles([
        w.Tile("Final index ratio", f"{cf['index_ratio'][-1]:.3f}", f"CPI grew {(cf['index_ratio'][-1] - 1) * 100:.1f} % over the life"),
        w.Tile("Redemption (nominal)", f"{cf['redemption'][-1]:.2f}", "principal repaid in money of the day"),
        w.Tile("Total real cash flows", f"{real_il:.1f} vs {real_nom:.1f}",
               "indexed vs nominal, in today's purchasing power (undiscounted)"),
    ])
    with st.expander("Live check: the daily inflation reference (DIR) on a given date"):
        k = st.columns(3)
        dd = k[0].date_input("Date t", date(2001, 4, 26), key="il_d")
        cm3 = k[1].number_input("CPI of month m−3", value=100.0, step=0.1, key="il_cm3")
        cm2 = k[2].number_input("CPI of month m−2", value=100.3, step=0.1, key="il_cm2")
        dir_t = indexed.daily_inflation_reference(dd, cm3, cm2)
        import calendar as _cal
        nd = _cal.monthrange(dd.year, dd.month)[1]
        st.latex(rf"DIR = {cm3:.2f} + \frac{{{dd.day}-1}}{{{nd}}}\,({cm2:.2f}-{cm3:.2f}) = {dir_t:.4f}")
        st.caption("On the 1st of the month DIR equals the m−3 CPI, and it moves linearly towards the m−2 CPI through "
                   "the month. The lag exists because the CPI for a month is only published weeks later.")


with tab_fl:
    floaters()


# --- ④ Money-market yields ------------------------------------------------------------------
@st.fragment
def money_market() -> None:
    card = ui.card("Parameters", key="mm")
    presets = {
        "Ex. 1.17 — 90-day US bill, P = 98": {"n": 90, "yd": 8.0, "basis": 360},
        "Ex. 1.18 — 101-day US bill at 1.64 %": {"n": 101, "yd": 1.64, "basis": 360},
        "Ex. 1.19 — 62-day Japan bill, P = 99": {"n": 62, "yd": 5.887, "basis": 365},
        "High-rate regime — 1-year bill at 14 %": {"n": 360, "yd": 14.0, "basis": 360},
    }
    w.preset_selector(presets, key_prefix="mm_", container=card)
    cols = card.columns(3)
    n = cols[0].slider("Days to maturity n", 1, 365, step=1, key="mm_n")
    yd = cols[1].slider("Discount yield y_d (%)", 0.0, 20.0, step=0.001, format="%.3f%%", key="mm_yd")
    basis = cols[2].radio("Year basis B", [360, 365], horizontal=True, key="mm_basis")

    if n * yd / 100 >= basis:
        st.warning("At this yield and maturity the discount would exceed the face value (price ≤ 0).")
        return
    price = mm.price_from_discount_yield(yd / 100, n, basis)
    ym = mm.mm_from_discount(yd / 100, n, basis)
    nn = np.arange(1, 366)
    ok = nn * yd / 100 < basis
    ym_curve = np.where(ok, basis * yd / 100 / np.maximum(basis - nn * yd / 100, 1e-9), np.nan)
    fig = plotting.line_chart(
        nn, {"Money-market yield y_m": ym_curve * 100, "Discount yield y_d": np.full(nn.shape, yd)},
        title="Same price, two yields: the gap widens with maturity",
        x_label="Days to maturity n", y_label="Annualised simple yield (%)",
        colors={"Money-market yield y_m": theme.ROLE["model"], "Discount yield y_d": theme.ROLE["benchmark"]},
        dashed=["Discount yield y_d"], height=380,
    )
    fig.add_trace(go.Scatter(x=[n], y=[ym * 100], mode="markers", name="Your bill",
                             marker=dict(color=theme.ROLE["highlight"], size=12, line=dict(color=theme.ROLE["truth"], width=1.5))))
    st.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("For each maturity, the red line shows the money-market yield of a bill whose price "
                  "corresponds to the dashed discount yield. The vertical distance is the gap you ignore if you "
                  "compare the two quotes directly.")
    gap_bp = (ym - yd / 100) * 1e4
    verdict = "negligible" if gap_bp < 1 else ("material" if gap_bp < 25 else "large: never compare unconverted")
    w.tiles([
        w.Tile("Price (per 100)", f"{price:.4f}", f"discount of {100 - price:.4f} on face"),
        w.Tile("Money-market yield", f"{ym * 100:.4f} %", "return on the amount actually invested"),
        w.Tile("Gap y_m − y_d", f"{gap_bp:.1f} bp", verdict),
    ])
    with st.expander("Other money-market instruments: CD, commercial paper, deposit"):
        k = st.columns(4)
        cdc = k[0].number_input("CD rate at issue (%)", value=4.27, step=0.01, key="cd_c")
        nc = k[1].number_input("Days issue → maturity", value=276, step=1, key="cd_nc")
        cdy = k[2].number_input("Market yield y_m (%)", value=4.19, step=0.01, key="cd_y")
        nm = k[3].number_input("Days settlement → maturity", value=259, step=1, key="cd_nm")
        if nc > 0 and nm > 0:
            p_cd = mm.cd_price(cdc / 100, nc, cdy / 100, nm, 360)
            st.latex(rf"P = 100\,\frac{{1+{cdc:.2f}\%\times{nc}/360}}{{1+{cdy:.2f}\%\times{nm}/360}} = {p_cd:.4f}")
            st.caption("Defaults are Example 1.21 (book: 100.25). The CD trades above par because its issue coupon "
                       "has accrued for 17 days and the market yield fell below the CD rate. Commercial paper "
                       "(Ex. 1.23) and deposits (Ex. 1.24) use the same money-market formulas with no coupon.")


with tab_mm:
    money_market()


# --- ⑤ Repo & carry -------------------------------------------------------------------------
@st.fragment
def repo_carry() -> None:
    card = ui.card("Parameters", key="rp")
    presets = {
        "Ex. 1.25–1.26 — Bund 5 % Jul-2011, repo 4 %":
            {"nom": 1.0, "clean": 104.11, "cpn": 5.0, "aidays": 117, "rr": 4.0, "days": 30},
        "Low-rate regime — repo 0.5 %":
            {"nom": 1.0, "clean": 104.11, "cpn": 5.0, "aidays": 117, "rr": 0.5, "days": 30},
        "Inverted money market — repo 7 %":
            {"nom": 1.0, "clean": 98.0, "cpn": 5.0, "aidays": 60, "rr": 7.0, "days": 30},
    }
    w.preset_selector(presets, key_prefix="rp_", container=card)
    cols = card.columns(6)
    nom = cols[0].slider("Nominal (EUR m)", 0.5, 100.0, step=0.5, format="%.1f", key="rp_nom")
    clean = cols[1].slider("Clean price", 80.0, 120.0, step=0.01, format="%.2f", key="rp_clean")
    cpn = cols[2].slider("Coupon (%)", 0.0, 10.0, step=0.125, format="%.3f%%", key="rp_cpn")
    aidays = cols[3].slider("Accrued days", 0, 360, step=1, key="rp_aidays")
    rr = cols[4].slider("Repo rate (%)", 0.0, 10.0, step=0.01, format="%.2f%%", key="rp_rr")
    days = cols[5].slider("Repo term (days)", 1, 365, step=1, key="rp_days")

    N = nom * 1e6
    ai = cpn * aidays / 360  # the book's Ex. 1.25 accrual basis; see note below
    trade = repo.repo_trade(N, clean, ai, rr / 100, days)
    long_ = repo.daily_carry_long(N, cpn / 100, trade.cash_start, rr / 100)
    be = repo.breakeven_repo_rate(N, cpn / 100, trade.cash_start)

    rates = np.linspace(0, 10, 201)
    net_long = [repo.daily_carry_long(N, cpn / 100, trade.cash_start, r / 100).net for r in rates]
    fig = plotting.line_chart(
        rates, {"Long bond, financed in repo": net_long, "Short bond, cash in reverse repo": [-v for v in net_long]},
        title="Daily carry as a function of the repo rate", x_label="Repo rate (%)", y_label="Net carry per day (EUR)",
        colors={"Long bond, financed in repo": theme.ROLE["model"],
                "Short bond, cash in reverse repo": theme.ROLE["benchmark"]},
        dashed=["Short bond, cash in reverse repo"], height=380,
    )
    left_first = rr <= be * 100
    plotting.add_vline(fig, rr, "your repo rate", position="top left" if left_first else "top right")
    plotting.add_vline(fig, be * 100, f"break-even {be * 100:.3f} %", color=theme.ROLE["truth"],
                       position="top right" if left_first else "top left")
    fig.add_hline(y=0, line=dict(color=theme.AXIS, width=1))
    left, right = st.columns([3, 2])
    left.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("Above zero the position earns money each day it is held. The long and the short are mirror "
                  "images: whatever one earns, the other pays. They cross zero at the break-even repo rate.",
                  container=left)
    wf = go.Figure(go.Waterfall(
        x=["Coupon accrual", "Repo interest", "Net carry"], measure=["relative", "relative", "total"],
        y=[long_.coupon_income, -long_.repo_cost, 0],
        text=[f"{long_.coupon_income:,.2f}", f"−{long_.repo_cost:,.2f}", f"{long_.net:,.2f}"],
        increasing=dict(marker_color=theme.ROLE["alt"]), decreasing=dict(marker_color=theme.ROLE["benchmark"]),
        totals=dict(marker_color=theme.ROLE["model"]), showlegend=False,
    ))
    wf.update_layout(title="Long position: one day of carry", xaxis_title="Component",
                     yaxis_title="EUR per day", height=380, hovermode="closest")
    right.plotly_chart(wf, width="stretch", theme=None)
    sign = "positive carry: holding pays" if long_.net > 0 else "negative carry: holding costs"
    w.tiles([
        w.Tile("Cash at start", f"€{trade.cash_start:,.0f}", f"gross price {trade.gross_price:.4f} × nominal"),
        w.Tile("Cash to repay", f"€{trade.cash_end:,.0f}", f"after {days} days at {rr:.2f} % Act/360"),
        w.Tile("Long carry / day", f"€{long_.net:,.2f}", sign),
        w.Tile("Break-even repo", f"{be * 100:.3f} %", "above this, the long loses money each day"),
    ])
    st.caption("Accrued interest is computed as coupon × days/360, as in the book's Example 1.25. Bunds actually "
               "accrue Act/Act, which would give 5 × 117/365 = 1.6027 instead of 1.6250 and lower the cash leg by "
               "about €224 per €1 m.")


with tab_repo:
    repo_carry()

# =============================================================================================
# 6. Guided experiments
# =============================================================================================
w.try_this([
    w.TryThis(
        "**① Clean vs. gross:** set the yield equal to the coupon. Predict where the clean price sits between "
        "coupon dates, and what the gross price does.",
        "On coupon dates the clean price is exactly 100. Between them it dips very slightly below 100. With a "
        "constant yield, value grows at the compound rate while accrued interest grows linearly, and the "
        "difference is a few hundredths. The gross price still saw-tooths by a full coupon. The jumps come "
        "from the payment, not from any change in value.",
    ),
    w.TryThis(
        "**② Day counts:** choose the preset *Across February*. Which convention counts the most time, and "
        "does 30/360 count more or fewer days than the calendar?",
        "Actual days = 29, but 30/360 counts **31**: January 31 is treated as January 30, February is "
        "treated as 30 days long (30 days to 'February 30'), plus 1 day to March 1. Here 30/360 gives the "
        "largest year fraction (31/360), ahead of Act/360 (29/360). Across February, 30/360 *overstates* time; "
        "across 31-day months it understates it. Over a whole year these errors cancel, but not within a coupon period.",
    ),
    w.TryThis(
        "**④ Money market:** with the *High-rate regime* preset, slide n from 30 to 365 days. Predict the "
        "gap between y_m and y_d at one year before you look.",
        "At y_d = 14 % and n = 360, y_m = 0.14/(1 − 0.14) = 16.28 %, a gap of more than 220 bp. The gap scales "
        "with y_d × (n y_d/B): in a high-rate country, mixing up the two bases is a large error.",
    ),
    w.TryThis(
        "**⑤ Repo:** start from the Ex. 1.25–1.26 preset and raise the clean price to 115 without changing "
        "the repo rate. Does the carry go up or down?",
        "Down. The coupon income depends only on the nominal, but the repo interest is paid on the *cash "
        "borrowed*, which is the gross price × nominal. A richer bond needs more financing, so the break-even "
        "repo rate falls. High-coupon bonds bought at a premium often carry worse than their coupon suggests.",
    ),
    w.TryThis(
        "**③ Floaters:** pick *Rising 2 % → 8 %*, then shift the path by +200 bp. When does the inverse "
        "floater's floor start to bind, and what happens to its coupon after that?",
        "With a = 16 % and b = 2 the coupon hits zero once the index reaches 8 %. After that it stays at the "
        "floor, so further rate rises no longer reduce the coupon, though they still reduce the bond's price. "
        "Raising b brings the floor in sooner. Leverage cuts both ways.",
    ),
])

# =============================================================================================
# 7. What to notice
# =============================================================================================
w.what_to_notice([
    "The clean price is the economically meaningful quote. The gross price adds the accrued interest that "
    "changes mechanically with the calendar.",
    "Day-count conventions change the *measurement of time*, and therefore interest. Act/360 always pays "
    "365/360 − 1 ≈ 1.39 % more than Act/365 for the same rate.",
    "Discount and money-market yields are two linear annualisations of the same discount. The money-market "
    "yield is always higher, and the gap grows with rate level and maturity.",
    "Floaters remove most of the rate risk from the coupon. Inverse floaters add leverage to it, up to the floor.",
    "Repo carry = coupon accrual on the nominal − repo interest on the cash (the gross price). Its sign "
    "decides whether holding a bond position costs or pays.",
])

# =============================================================================================
# 8. Pitfalls
# =============================================================================================
w.pitfalls([
    ("Treating the quoted price as the amount paid.",
     "The quote is clean. Settlement is gross: the accrued interest can be several points of face for an "
     "annual high-coupon bond late in its coupon period."),
    ('Reading "98-28" as 98.28.',
     "US Treasury quotes are in 32nds: 98-28 = 98.875. The error here is 0.595 points, about $5,950 per $1 m."),
    ("Comparing a discount yield with a money-market or bond yield directly.",
     "They divide by different amounts (face vs. price) and may use different year bases. Convert first."),
    ("Assuming an inverse floater gains when rates fall.",
     "Its coupon rises, but its price depends on the whole curve and is leveraged: if long rates rise while "
     "the index falls, it can still lose value."),
])

# =============================================================================================
# 9. Exercises
# =============================================================================================
w.exercises([
    w.Exercise(
        "A 10 % annual-coupon bond (face 100) matures on 04/15/2008. Using the **worked example** above (set the "
        "quote to anything, coupon 10, 1 coupon per year, maturity 04/15/2008, settlement 10/25/1999), compute "
        "the accrued interest under **Act/Act**.",
        "Last coupon 04/15/1999, next 04/15/2000: the period has **366** days (it contains 29 Feb 2000). "
        "Days accrued = 193. AI = 10 × 193/366 = **5.2732**. Under the other bases: Act/365 → 10 × 193/365 = "
        "5.2877; Act/360 → 5.3611; 30/360 → 190 days → 5.2778. The gap of 0.09 points between conventions is "
        "worth €900 per €1 m.",
        numeric_answer=5.2732, tolerance=5e-4, unit="per 100",
    ),
    w.Exercise(
        "A 101-day US Treasury bill trades at a 1.64 % discount yield (Ex. 1.18). What is its money-market yield? "
        "Use tab ④ to check.",
        "y_m = 360 × 0.0164 / (360 − 101 × 0.0164) = **1.6476 %**. The price is 99.5399, and the return on the "
        "amount invested is (100 − 99.5399)/99.5399 × 360/101, which is the same number.",
        numeric_answer=1.6476, tolerance=1e-3, unit="%",
    ),
    w.Exercise(
        "For the Ex. 1.26 long Bund position (EUR 1 m nominal, 5 % coupon, cash borrowed €1,057,350), what repo "
        "rate makes the daily carry exactly zero?",
        "Set c·N/360 = Cash·r/360, so r = c·N/Cash = 0.05 × 1,000,000 / 1,057,350 = **4.7288 %**. Below that "
        "rate the long earns money each day; above it, it loses money. Tab ⑤ shows it as the crossing point.",
        numeric_answer=4.7288, tolerance=2e-3, unit="%",
    ),
    w.Exercise(
        'Convert the Treasury quote **101-13+** to a decimal price.',
        '"+" adds half a 32nd: 101 + 13.5/32 = **101.421875**.',
        numeric_answer=101.421875, tolerance=1e-5, unit="per 100",
    ),
    w.Exercise(
        "Explain, using tab ④, why the money-market yield of a bill is always above its discount yield, and "
        "why the difference matters more in Brazil or Turkey than in Switzerland.",
        "Both annualise the same discount F − P, but y_d divides by the face value and y_m by the smaller price "
        "paid. The gap is y_d·(n y_d)/(B − n y_d): roughly quadratic in the rate level. At 1 % it is a fraction of "
        "a basis point. At 14 % on a one-year bill it exceeds 200 bp.",
        kind="explain",
    ),
])

# =============================================================================================
# 10. Takeaways and glossary
# =============================================================================================
w.takeaways_and_glossary(
    [
        "A bond is its cash-flow schedule. Conventions determine the dates and amounts.",
        "Quoted (clean) price + accrued interest = gross price paid.",
        "Always state the day-count basis and the yield basis next to any rate.",
        "Money-market instruments use simple interest: discount yield (on face) < money-market yield (on price).",
        "Floater coupons follow an index, inverse floaters move against it with leverage, and inflation-linked "
        "bonds index the principal to the CPI.",
        "Repo turns bonds into financing. Carry = coupon accrual − repo cost.",
    ],
    {
        "Accrued interest": "the part of the next coupon earned by the seller since the last coupon date.",
        "Clean price": "quoted price, excluding accrued interest.",
        "Gross (dirty, full) price": "clean price plus accrued interest; the amount actually paid.",
        "Day-count convention": "rule converting a period between two dates into a fraction of a year.",
        "Settlement date": "date on which cash and securities are exchanged (trade date + a market-specific lag).",
        "32nds": "US Treasury price quotation: 98-28 = 98 + 28/32.",
        "Discount yield": "simple annualised discount as a fraction of face value.",
        "Money-market yield": "simple annualised return on the price paid.",
        "Year basis": "number of days per year in a simple-interest formula (360 or 365).",
        "Floating-rate note (FRN)": "bond whose coupon is reset periodically to an index plus a margin.",
        "Inverse floater": "bond whose coupon moves opposite to an index, usually with leverage and a floor.",
        "Inflation-indexed bond": "bond paying a real coupon on a principal indexed to the CPI.",
        "Index ratio": "DIR_t / DIR_initial: the cumulative CPI growth applied to coupons and principal.",
        "Strip": "zero-coupon bond created by separating a government bond's coupons and principal.",
        "Repo": "sale of a security with an agreement to buy it back: a collateralised loan.",
        "Reverse repo": "the same transaction from the cash lender's side: lending cash, receiving securities.",
        "Carry": "income from holding a position (coupon accrual) minus its financing cost (repo interest).",
        "Credit rating": "agency grade of default risk. Investment grade is BBB−/Baa3 or better; below that is speculative grade.",
    },
)

# =============================================================================================
# 11. Source reference
# =============================================================================================
w.source_reference(
    "L. Martellini, P. Priaulet & S. Priaulet (2003), *Fixed-Income Securities: Valuation, Risk Management "
    "and Portfolio Strategies*, Wiley.",
    "Chapter 1, §1.1.1 (bond characteristics, quotes, nonstandard bonds) and §1.2.3–1.2.8 (money market, repo).",
    ["day-count definitions (§1.1.1)", "accrued interest (Ex. 1.4)", "OATi indexation (§1.1.1)",
     "discount and money-market yields (§1.2.3)", "CD price (§1.2.4)", "repo cash flows and carry (§1.2.8)"],
)
st.caption(
    "Worked examples reproduced in tests: 1.4, 1.5, 1.6, 1.17–1.26, and the §1.1.1 day-count examples. "
    "The book's descriptive material (issuer types, market sizes, Bloomberg screens) is summarised only in the glossary."
)
