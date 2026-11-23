"""Ch. 2 — Bond prices and yields: discounting, compounding, YTM, zero/forward/par rates.

Source: Martellini, Priaulet & Priaulet (2003), Fixed-Income Securities, ch. 2 (§2.1–2.3).
UI only; all calculations live in ``core/``.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

_here = Path(__file__).resolve()
sys.path.insert(0, str(next(p for p in _here.parents if (p / "shared").is_dir())))
sys.path.insert(0, str(_here.parents[1]))  # lab root, for ``core``

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import pricing as pr
from core import rates as rt
from core import term_structure as ts
from core.conventions import from_32nds
import lab_theme  # noqa: F401  (activates the lab theme for charts)
from shared import plotting, theme, ui
from shared import widgets as w

ui.chapter_header(
    2, "Bond prices and yields", "Chapter 2 · §2.1–2.3 · Discounting, compounding and the taxonomy of rates",
    lede="One idea prices every fixed-income cash flow: a dollar later is worth less than a dollar now. "
         "This page turns that idea into bond prices, and then untangles the many rates that describe "
         "the same prices: yields, zero rates, forwards and par yields.",
)

# =============================================================================================
# 1. Learning objectives
# =============================================================================================
w.learning_objectives(
    [
        "Price any fixed cash-flow bond as a sum of discounted cash flows, using either a discount factor "
        "per date or a single yield.",
        "Convert a rate between compounding frequencies (annual, semiannual, monthly, continuous), and "
        "between nominal and real terms.",
        "Compute a **yield to maturity**, and explain what it is (an internal rate of return) and what it is "
        "not (the return you will earn).",
        "Derive **forward rates** and **par yields** from zero-coupon rates, and read a forward both as a "
        "rate you can lock in and as a break-even.",
        "Explain the **coupon effect**, and why the zero, par and YTM curves differ when the curve slopes.",
    ],
    prerequisites="Chapter 1 (cash-flow schedules, coupon frequency, 32nds quotes). Basic algebra; "
                  "the continuous-compounding proof uses one derivative.",
)

# =============================================================================================
# 2. Intuition
# =============================================================================================
w.section("Intuition")
st.markdown(
    """
**A question to start.** Someone offers you a contract that pays \\$1 in one year, for sure. Would you pay
95 cents for it today? 99 cents? A dollar? If the one-year rate is 4 %, then 96.15 cents put in the bank
today grows to exactly \\$1 in a year. Paying more than 96.15 cents would be a bad deal, since the bank
does better. Paying less would be a free lunch for you, and the seller would refuse. So the contract is
worth **0.961538**, and that number is called a **discount factor**: the price today of \\$1 paid at a
future date.

**A bond is a basket of such contracts.** A 10-year 5 % bond is ten small payments of 5 and one large payment
of 100, each on its own date. Price each one with its own discount factor and add them up. That is the whole
of bond pricing (the chart below shows it), and everything else on this page is about *where the discount
factors come from* and *how to summarise them in a rate*.

**Many rates, one set of prices.** People rarely quote discount factors. They quote rates, and there are
several kinds, each answering a different question. The **yield to maturity** is the one rate that, applied
to every cash flow, reproduces a bond's price. A **zero-coupon rate** is the rate for one single date. A
**forward rate** is the rate you can lock in today for a loan that starts later. A **par yield** is the coupon
a new bond would need to sell at exactly 100. On top of that, each rate needs a compounding convention, and
"5 %" compounded twice a year is not the same as "5 %" compounded once.

**Why it matters.** Confusing these rates is how money gets lost: comparing a semiannual yield with an annual
one, using a 10-year bond's YTM to discount a 10-year cash flow, or expecting to earn the YTM when coupons
will be reinvested at lower rates. Each section below takes one of these traps apart.
"""
)


@st.cache_data
def _cf_pv(coupon: float, maturity: int, freq: int, y: float) -> pd.DataFrame:
    t, cf = pr.cash_flows(coupon, maturity, freq)
    df = (1 + y / freq) ** (-freq * t)
    return pd.DataFrame({"t": t, "cf": cf, "df": df, "pv": cf * df, "cum": np.cumsum(cf * df)})


def _cf_chart(d: pd.DataFrame, title: str, height: int = 380) -> go.Figure:
    fig = plotting.base_figure(title, "Payment date (years)", "Amount per 100 face", height)
    fig.add_trace(go.Bar(x=d["t"], y=d["cf"], name="Cash flow", marker_color=theme.ROLE["data"], opacity=0.45))
    fig.add_trace(go.Bar(x=d["t"], y=d["pv"], name="Present value", marker_color=theme.ROLE["model"]))
    fig.add_trace(go.Scatter(x=d["t"], y=d["cum"], name="Running sum of PVs → price", mode="lines+markers",
                             line=dict(color=theme.ROLE["truth"], width=2)))
    fig.add_annotation(x=d["t"].iloc[-1], y=d["cum"].iloc[-1], text=f"price {d['cum'].iloc[-1]:.2f}",
                       showarrow=True, arrowhead=0, ax=-60, ay=10, xanchor="right", font=dict(color=theme.ROLE["truth"]))
    fig.update_layout(barmode="overlay", hovermode="x unified")
    return fig


_d = _cf_pv(0.05, 10, 1, 0.06)
st.plotly_chart(_cf_chart(_d, "Example 2.4: a 10-year 5 % bond, every flow discounted at 6 %"),
                width="stretch", theme=None)
w.how_to_read(
    "Pale bars are the promised payments, red bars what each is worth today. Later payments shrink more. The "
    "black line adds the red bars up and ends at the price, 92.64 per 100: the bond is worth "
    "less than its face value because its 5 % coupon is below the 6 % rate investors require."
)

# =============================================================================================
# 3. Model
# =============================================================================================
w.section("Model")
ui.formula_card([
    ("Price = Σ discounted flows", r"P=\sum_t B(0,t)\,CF_t"),
    ("Forward rate", r"F(0,x,y-x)=\Big[\tfrac{(1+R(0,y))^{y}}{(1+R(0,x))^{x}}\Big]^{\frac{1}{y-x}}-1"),
    ("Par yield", r"c(n)=\frac{1-B(0,n)}{\sum_{i=1}^{n}B(0,i)}"),
], key="ch2")
st.markdown("Prices are per 100 of face value unless stated. Rates are annual decimals in formulas and "
            "percentages on screen; *t* is in years.")

st.subheader("Discount factors and the pricing rule")
w.equation(
    r"P=\sum_{t=1}^{T}\frac{CF_t}{\big(1+R(0,t)\big)^{t}}=\sum_{t=1}^{T}B(0,t)\,CF_t",
    {
        "CF_t": "cash flow paid at date t (coupon, plus the face value at maturity)",
        "R(0,t)": "zero-coupon (spot) rate seen today for money paid at t, annually compounded",
        "B(0,t)": "discount factor: today's price of \\$1 paid at t (between 0 and 1 when rates are positive)",
    },
    label="Eq. 2.1, §2.1–2.2.1, Examples 2.2–2.3",
)
st.markdown(
    "In words: a bond is a basket, and its price is the sum of its parts at their own prices. Why must this "
    "hold? If the bond traded below this sum, you could buy it and sell its payments one by one as zero-coupon "
    "bonds (strips, Ch. 1) for a riskless profit; above it, you would do the reverse. Arbitrage pins the price "
    "to the sum. Where the B(0,t) themselves come from, when no zero-coupon bond exists for each date, is the "
    "subject of Chapter 4."
)

st.subheader("One rate for all dates: the level-coupon formula")
w.equation(
    r"P_0=\frac{C}{y}\Big[1-\frac{1}{(1+y)^{T}}\Big]+\frac{N}{(1+y)^{T}},\qquad C=c\,N",
    {"y": "single discount rate applied to every date", "c, C": "coupon rate, and coupon amount per year",
     "N": "face (nominal) value", "T": "years to maturity"},
    label="Eq. 2.2 (annual coupons); Remark 2.1 replaces y by y/2 and T by 2n for semiannual coupons",
)
with st.expander("Derivation: the annuity formula, price = par when c = y, and the perpetuity"):
    st.markdown(
        r"""
Write $v = 1/(1+y)$. The coupons form a geometric series:
$$
C\,(v+v^2+\dots+v^T)=C\,v\,\frac{1-v^T}{1-v}=C\,\frac{1-v^T}{y},
$$
because $v/(1-v) = 1/y$. Adding the discounted face value $N v^T$ gives Eq. 2.2.

**Price = par when the coupon equals the yield.** Put $C=yN$: $P_0 = N(1-v^T)+Nv^T = N$. The coupon pays
exactly the return investors require, so they pay exactly the face value. If $c>y$ the bond pays *more*
than required and trades at a **premium** ($P>N$). If $c<y$ it trades at a **discount**.

**Perpetuity.** Let $T\to\infty$. Then $v^T\to0$ (for $y>0$) and $P_0 = C/y$: a contract paying \$100 a year
forever at 5 % is worth \$2,000 (Example 2.6).

With $f$ coupons a year, the same algebra with the per-period rate $y/f$ over $fT$ periods gives
$P_0 = \frac{cN}{y}\big[1-(1+y/f)^{-fT}\big]+N(1+y/f)^{-fT}$.
"""
    )

st.subheader("Compounding conventions and continuous rates")
w.equation(
    r"1+R=\Big(1+\frac{R_n}{n}\Big)^{n}\;\xrightarrow[n\to\infty]{}\;e^{R_c},\qquad"
    r"PV(CF_t)=CF_t\,e^{-R_c t}",
    {"R_n": "annual rate compounded n times a year (n = 2: semiannual, 12: monthly)",
     "R": "the equivalent **effective annual** rate (compounded once a year)",
     "R_c": "continuously compounded rate"},
    label="§2.2.4–2.2.5, Examples 2.8–2.14",
)
st.markdown(
    "In words: an annual rate is incomplete until you say how often interest is added to the balance. "
    "More frequent compounding earns interest on interest sooner, so the same quoted 6 % grows money faster "
    "monthly (6.1678 % effective) than annually. As *n* grows, the growth converges to a finite limit, "
    "e^{R_c}. Continuous rates are popular in models because discounting becomes e^{−R_c t} and rates add "
    "up across periods."
)
with st.expander("Proof sketch: why (1 + R/n)^{nT} tends to e^{RT}"):
    st.markdown(
        r"""
Take logs: $nT\ln(1+R/n) = RT\cdot\dfrac{\ln(1+R/n)-\ln 1}{R/n}$. As $n\to\infty$, $h=R/n\to 0$ and the
fraction is the difference quotient of $\ln$ at 1, which tends to $\ln'(1)=1$. So the log tends to $RT$ and
the growth factor to $e^{RT}$. Since $e^{x}=1+x+x^2/2+\dots$, the effective rate $e^{R_c}-1$ is slightly
above $R_c$: a continuous 6 % equals 6.1837 % compounded annually (Example 2.14).
"""
    )

st.subheader("Nominal versus real rates")
w.equation(
    r"1+R_{\text{real}}=\frac{1+R_{\text{nominal}}}{1+i}\quad\Rightarrow\quad R_{\text{real}}\approx R_{\text{nominal}}-i",
    {"i": "inflation rate over the same period", r"R_{\text{real}}": "growth of purchasing power"},
    label="§2.2.3, Example 2.7",
)
st.markdown(
    "In words: money grows by 1 + R_nominal, prices by 1 + i, so purchasing power grows by the ratio. The "
    "subtraction is a first-order approximation that is fine at 2 % inflation and badly off at 30 %."
)

st.subheader("Current yield and yield to maturity")
w.equation(
    r"y_c=\frac{cN}{P},\qquad P=\sum_{i=1}^{fT}\frac{CF_i}{(1+y_f/f)^{i}}",
    {"y_c": "current yield: annual coupon over price (ignores the pull to par)",
     "y_f": "yield to maturity, compounded f times a year (f = 1 in France and Germany, 2 in the US and UK)",
     "CF_i": "flow paid at the end of period i"},
    label="§2.3.1–2.3.2, Examples 2.15–2.17",
)
st.markdown(
    "In words: the YTM is the bond's **internal rate of return**, the one rate that discounts all the flows "
    "back to the market price. There is no formula for it; it is found by search (see the worked example). "
    "Because a bond's price falls continuously as the rate rises, there is exactly one such rate, so price and "
    "YTM carry the same information, and markets often quote bonds by their yield. "
    "Two warnings. First, the YTM treats the curve as flat: it is an *average* of the zero rates, weighted "
    "towards the dates with the largest flows. Second, it is a promised return only under a condition: the "
    "investor earns the YTM if every coupon is reinvested at the YTM itself (Remark 2.3, simulator tab ③)."
)

st.subheader("Zero-coupon rates, forward rates and par yields")
w.equation(
    r"F(0,x,y-x)=\left[\frac{(1+R(0,y))^{y}}{(1+R(0,x))^{x}}\right]^{\frac{1}{y-x}}-1,"
    r"\qquad f(0,s)=\lim_{T\to s}F_c(0,s,T-s)",
    {"F(0,x,θ)": "forward rate seen today, starting at year x, for a residual maturity θ = y − x "
                 "(the book's notation: the third argument is a *length*, not an end date)",
     "F_c": "the same forward, continuously compounded",
     "f(0,s)": "instantaneous forward: the rate for an infinitesimal loan starting at s"},
    label="Eq. 2.3 and Eq. 2.4, §2.3.4, Remarks 2.4–2.5",
)
st.markdown(
    "In words: investing to year *y* in one go must give the same result as investing to year *x* and then "
    "rolling into the forward until *y*; otherwise one route is an arbitrage. The forward is the rate that "
    "makes the two routes equal. You can **lock it in** today by lending to *x* and borrowing to *y* (tab ④ "
    "shows the cash flows). It is also a **break-even**: if the 1-year rate in a year turns out equal to "
    "today's F(0,1,1), the 1-year and 2-year zero-coupon bonds earn exactly the same over the coming year."
)
w.equation(
    r"\sum_{i=1}^{n}\frac{100\,c(n)}{(1+R(0,i))^{i}}+\frac{100}{(1+R(0,n))^{n}}=100"
    r"\;\Longrightarrow\;c(n)=\frac{1-(1+R(0,n))^{-n}}{\sum_{i=1}^{n}(1+R(0,i))^{-i}}",
    {"c(n)": "par yield: the annual coupon that makes an n-year bond price exactly 100"},
    label="Eq. 2.5, §2.3.5",
)
with st.expander("Why the three curves are ordered: forward > zero > par on a rising curve"):
    st.markdown(
        r"""
**Zero vs. one-period forwards.** $(1+R(0,n))^n=(1+R(0,1))(1+F(0,1,1))\cdots(1+F(0,n-1,1))$ (Remark 2.4), so the
zero rate is a geometric *average* of the one-year forwards up to $n$. When the average is rising, the newest
term must be above the average: the forward for year $n$ exceeds $R(0,n)$. Just as the latest grade has to
be above your average for the average to go up.

**Par vs. zero.** A par bond pays coupons before maturity, and those early flows are discounted at the
*lower* short rates. Its yield is therefore a blend of $R(0,1),\dots,R(0,n)$, weighted mostly to $R(0,n)$
(the face value), and sits below $R(0,n)$ when the curve rises. On an inverted curve, every inequality flips.

**The coupon effect.** The same logic explains why, on a rising curve, a high-coupon bond has a *lower* YTM
than a low-coupon bond of the same maturity: more of its value comes from early, low-rate dates. A zero-coupon
bond has YTM = $R(0,n)$ exactly. Comparing YTMs across bonds therefore mixes the curve with coupon size, and
the par curve removes that distortion.
"""
    )
ui.note(
    "Bonds are valued on a coupon date, so every period is whole (Ch. 1 handles fractional first periods and "
    "accrued interest). Cash flows are certain: no default, no options. Zero rates are given at annual maturities "
    "1–10 years; the instantaneous forward joins them with a natural cubic spline, a modelling choice that "
    "Ch. 4 compares with alternatives.",
    key="assumptions2", label="Assumptions on this page",
)

# =============================================================================================
# 4. Worked example (live) — Example 2.16
# =============================================================================================
w.section("Worked example (live): from a quoted price to the yield")
st.markdown(
    "Book Example 2.16, re-solved with our code: a 2-year bond with an 8 % coupon paid semiannually, \\$1,000 face "
    "value, quoted at **103-23**. What is its yield to maturity? There is no closed form, so we search: guess a "
    "yield, price the bond, and narrow the guess. Change any input and every step updates."
)
wc = st.columns(5)
we_quote = wc[0].text_input("Quote (handle-32nds)", "103-23", key="we2_quote",
                            help='"103-23" means 103 + 23/32 % of face.')
we_cpn = wc[1].number_input("Coupon (%)", 0.0, 20.0, 8.0, 0.125, format="%.3f", key="we2_cpn")
we_T = wc[2].number_input("Maturity (years)", 1, 30, 2, 1, key="we2_T")
we_f = wc[3].selectbox("Coupons / year", [2, 1, 4, 12], key="we2_f")
we_round = wc[4].toggle("Book rounding (103.72)", value=False, key="we2_round",
                        help="The book rounds 103.71875 to 103.72 before solving.")
we_face = 1000.0

try:
    pct = from_32nds(we_quote)
    if we_round:
        pct = round(pct, 2)
    price = pct / 100 * we_face
    t, cf = pr.cash_flows(we_cpn / 100, we_T, we_f, we_face)
    y_sol = pr.irr(price, t, cf, we_f)
    lo0, hi0 = (min(0.0, y_sol - 0.05), max(0.20, y_sol + 0.05))
    steps = pr.ytm_bisection_steps(price, t, cf, we_f, lo0, hi0, n_steps=10)
except ValueError as e:
    st.error(f"Input problem: {e}")
else:
    st.markdown(f"**Step 1. Decode the quote.** {we_quote} = {pct:.5f} % of face → price "
                f"**{price:,.4f}** per \\${we_face:,.0f}.")
    st.markdown(f"**Step 2. List the cash flows.** {len(t)} payments of {we_cpn / we_f * 10:,.2f} "
                f"(coupon {we_cpn:.3f} % / {we_f} × 1,000), the last one plus the face value.")
    st.markdown(
        r"**Step 3. Search for the yield.** Price falls as the yield rises, so: if the price at the trial yield "
        r"is *above* the market price, the yield must be higher. Halve the interval each time (bisection)."
    )
    trace = pd.DataFrame([
        {"Trial": i + 1, "Interval low (%)": s.lo * 100, "Interval high (%)": s.hi * 100,
         "Trial yield (%)": s.mid * 100, "Price at trial": s.price_at_mid,
         "Verdict": "price too high → raise y" if s.price_at_mid > price else "price too low → lower y"}
        for i, s in enumerate(steps)
    ])
    st.dataframe(trace.style.format({"Interval low (%)": "{:.5f}", "Interval high (%)": "{:.5f}",
                                     "Trial yield (%)": "{:.5f}", "Price at trial": "{:,.4f}"}),
                 hide_index=True, width="stretch")
    st.caption(f"Ten halvings narrow the interval to {(hi0 - lo0) / 2 ** 10 * 1e4:.2f} bp. A production solver "
               "(Brent's method, used for the tiles) gets to machine precision in a handful of steps.")
    st.markdown("**Step 4. Check:** at the solved yield, the discounted flows add back to the price.")
    per = 1 + y_sol / we_f
    chk = pd.DataFrame({"Period i": np.arange(1, len(t) + 1), "Time (years)": t, "Cash flow": cf,
                        f"Discount factor 1/(1+y/{we_f})^i": per ** -np.arange(1, len(t) + 1)})
    chk["Present value"] = chk["Cash flow"] * chk.iloc[:, 3]
    st.dataframe(chk.style.format({"Time (years)": "{:.2f}", "Cash flow": "{:,.2f}",
                                   chk.columns[3]: "{:.6f}", "Present value": "{:,.4f}"}),
                 hide_index=True, width="content")
    w.tiles([
        w.Tile("Yield to maturity", f"{y_sol * 100:.4f} %", f"annual, compounded {we_f}× a year"),
        w.Tile("Per period", f"{y_sol / we_f * 100:.4f} %", f"the rate per {12 // we_f}-month period"),
        w.Tile("Effective annual", f"{rt.effective_annual_rate(y_sol, we_f) * 100:.4f} %",
               "same yield, compounded once a year"),
        w.Tile("Sum of PVs", f"{chk['Present value'].sum():,.4f}", "equals the price: the search converged"),
    ])
    st.caption("Book: y₂/2 = 3 %, y₂ = 6 %. With the exact price 103.71875 our root is 5.9991 %; with the book's "
               "rounded 103.72 it is 5.9985 %. Both round to 6.00 %. See `tests/test_02_prices_yields.py`.")

# =============================================================================================
# 5. Simulator
# =============================================================================================
w.section("Simulator")
st.markdown("Four labs, one per idea. Each tab keeps all of its controls in the card at the top.")
tab_py, tab_cp, tab_rr, tab_zc = st.tabs(
    ["① Price and yield", "② Compounding & real rates", "③ YTM vs. realised return", "④ Zero, forward & par curves"]
)


# --- ① Price and yield ------------------------------------------------------------------------
@st.cache_data
def _price_yield_curve(c: float, T: int, f: int) -> tuple[np.ndarray, np.ndarray]:
    ys = np.linspace(0.0, 0.16, 161)
    return ys, np.array([pr.price_from_yield(c, T, y, f) for y in ys])


@st.fragment
def price_and_yield() -> None:
    card = ui.card("Parameters", key="py")
    presets = {
        "Ex. 2.4 — 5 % 10-year at 6 % (discount)": {"c": 5.0, "T": 10, "f": 1, "y": 6.0},
        "Ex. 2.5 — 5 % 10-year at 5 % (par)": {"c": 5.0, "T": 10, "f": 1, "y": 5.0},
        "Ex. 2.16 — 8 % 2-year semiannual at 6 %": {"c": 8.0, "T": 2, "f": 2, "y": 6.0},
        "Ex. 2.17 — 10 % 3-year at 9.601 % (premium)": {"c": 10.0, "T": 3, "f": 1, "y": 9.601},
        "30-year zero-coupon at 6 %": {"c": 0.0, "T": 30, "f": 1, "y": 6.0},
    }
    w.preset_selector(presets, key_prefix="py_", container=card)
    cols = card.columns(4)
    c = cols[0].slider("Coupon rate c (%)", 0.0, 15.0, step=0.125, format="%.3f%%", key="py_c")
    T = cols[1].slider("Maturity T (years)", 1, 30, step=1, key="py_T")
    f = cols[2].selectbox("Coupons / year f", [1, 2, 4, 12], key="py_f")
    y = cols[3].slider("Yield y (%, compounded f× a year)", 0.0, 15.0, step=0.001, format="%.3f%%", key="py_y")

    d = _cf_pv(c / 100, T, f, y / 100)
    price = float(d["pv"].sum())
    left, right = st.columns(2)
    left.plotly_chart(_cf_chart(d, "Cash flows, their present values and the price", height=400),
                      width="stretch", theme=None)
    w.how_to_read("Each pale bar is a payment; the red bar inside it is its value today. The black line adds "
                  "the red bars and ends at the price.", container=left)

    ys, ps = _price_yield_curve(c / 100, T, f)
    fig = plotting.line_chart(ys * 100, {"Price": ps}, title="Price–yield curve of this bond",
                              x_label="Yield to maturity (%)", y_label="Price (per 100 face)",
                              colors={"Price": theme.ROLE["model"]}, height=400)
    fig.add_hline(y=100, line=dict(color=theme.ROLE["truth"], dash="dot", width=1.5),
                  annotation_text="par (100)", annotation_position="top right")
    if c > 0:
        plotting.add_vline(fig, c, "y = coupon", color=theme.ROLE["truth"], position="bottom left")
    fig.add_trace(go.Scatter(x=[y], y=[price], mode="markers", name="Your bond",
                             marker=dict(color=theme.ROLE["highlight"], size=13,
                                         line=dict(color=theme.ROLE["truth"], width=1.5))))
    right.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("The curve falls and bends upwards (convexity): a rate cut raises the price more than an "
                  "equal rate rise lowers it. It crosses 100 exactly where the yield equals the coupon.",
                  container=right)
    status = ("premium: coupon above yield" if price > 100 + 1e-9 else
              "discount: coupon below yield" if price < 100 - 1e-9 else "par: coupon = yield")
    cy = pr.current_yield(c / 100, price) * 100 if c > 0 else 0.0
    dv01 = (pr.price_from_yield(c / 100, T, (y - 0.01) / 100, f)
            - pr.price_from_yield(c / 100, T, (y + 0.01) / 100, f)) / 2
    w.tiles([
        w.Tile("Price", f"{price:.4f}", status),
        w.Tile("Current yield", f"{cy:.3f} %",
               "above the YTM: ignores the pull down to par" if cy > y + 1e-9 else
               ("below the YTM: ignores the pull up to par" if cy < y - 1e-9 else "equals the YTM at par")),
        w.Tile("Price change per 1 bp", f"{dv01:.4f}", "per 100 face; grows with maturity (Ch. 5)"),
        w.Tile("Share of value in last flow", f"{d['pv'].iloc[-1] / price * 100:.1f} %",
               "the face value dominates" if d['pv'].iloc[-1] / price > 0.5 else "the coupons dominate"),
    ])


with tab_py:
    price_and_yield()


# --- ② Compounding & real rates ----------------------------------------------------------------
@st.fragment
def compounding() -> None:
    card = ui.card("Parameters · compounding", key="cp")
    cols = card.columns(3)
    rate = cols[0].slider("Quoted annual rate (%)", 0.0, 30.0, 6.0, 0.05, format="%.2f%%", key="cp_rate")
    nlabels = {"Annual (1)": 1, "Semiannual (2)": 2, "Quarterly (4)": 4, "Monthly (12)": 12,
               "Daily (365)": 365, "Continuous (∞)": math.inf}
    nsel = cols[1].selectbox("Compounding of the quoted rate", list(nlabels), index=1, key="cp_n")
    T = cols[2].slider("Investment horizon (years)", 0.5, 30.0, 1.0, 0.5, key="cp_T")
    n = nlabels[nsel]
    R = rate / 100

    ns = np.unique(np.round(np.logspace(0, np.log10(365), 60)))
    ear = rt.compounding_ladder(R, list(ns)) * 100
    fig = plotting.line_chart(ns, {"Effective annual rate": ear},
                              title=f"The same quoted {rate:.2f} %, compounded more and more often",
                              x_label="Compounding periods per year n (log scale)", y_label="Effective annual rate (%)",
                              colors={"Effective annual rate": theme.ROLE["model"]}, height=380)
    fig.update_xaxes(type="log")
    pad = max((math.exp(R) - 1 - R) * 100, 0.01)
    fig.update_yaxes(range=[R * 100 - 0.15 * pad, (math.exp(R) - 1) * 100 + 0.25 * pad])
    lim = (math.exp(R) - 1) * 100
    fig.add_hline(y=lim, line=dict(color=theme.ROLE["truth"], dash="dash", width=1.5),
                  annotation_text=f"continuous limit e^R − 1 = {lim:.4f} %", annotation_position="top left")
    marks = [1, 2, 4, 12, 365]
    fig.add_trace(go.Scatter(x=marks, y=rt.compounding_ladder(R, marks) * 100, mode="markers+text",
                             text=["annual", "semiannual", "quarterly", "monthly", "daily"],
                             textposition=["middle right"] * 4 + ["bottom left"], cliponaxis=False,
                             name="Common conventions", marker=dict(color=theme.ROLE["highlight"], size=9)))
    left, right = st.columns([3, 2])
    left.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("Each extra compounding adds interest on interest, but less and less: most of the gain is "
                  "already there at monthly compounding, and daily is within a hair of continuous.", container=left)
    eff = rt.effective_annual_rate(R, n)
    rows = [{"Convention": k, "Equivalent rate (%)": rt.rate_from_effective(eff, v) * 100,
             f"Value of 100 after {T:g} y": 100 * (1 + eff) ** T} for k, v in nlabels.items()]
    right.markdown(f"**Equivalent rates** (all give the same growth as {rate:.2f} % {nsel.split(' ')[0].lower()})")
    right.dataframe(pd.DataFrame(rows).style.format({"Equivalent rate (%)": "{:.4f}",
                                                     f"Value of 100 after {T:g} y": "{:.4f}"}),
                    hide_index=True, width="stretch")
    gap_bp = (eff - R) * 1e4
    w.tiles([
        w.Tile("Effective annual rate", f"{eff * 100:.4f} %", f"what {rate:.2f} % {nsel.split(' ')[0].lower()} really earns"),
        w.Tile("Gap vs. quoted", f"{gap_bp:.1f} bp", "negligible" if gap_bp < 1 else
               ("material: convert before comparing" if gap_bp < 25 else "large: never compare unconverted")),
        w.Tile("Continuous equivalent", f"{rt.convert_rate(R, n, 'continuous') * 100:.4f} %",
               "always the lowest number for the same growth"),
    ])

    st.divider()
    card2 = ui.card("Parameters · nominal vs. real", key="fi")
    k = card2.columns(2)
    nom = k[0].slider("Nominal rate (%)", 0.0, 40.0, 5.0, 0.25, format="%.2f%%", key="fi_nom")
    infl = k[1].slider("Inflation (%)", -2.0, 35.0, 2.0, 0.25, format="%.2f%%", key="fi_infl")
    real = rt.real_rate(nom / 100, infl / 100)
    approx = rt.real_rate(nom / 100, infl / 100, exact=False)
    ii = np.linspace(-2, 35, 149)
    fig2 = plotting.line_chart(
        ii, {"Exact (Fisher)": [rt.real_rate(nom / 100, v / 100) * 100 for v in ii],
             "Approximation R − i": [rt.real_rate(nom / 100, v / 100, exact=False) * 100 for v in ii]},
        title=f"Real rate for a {nom:.2f} % nominal rate as inflation varies", x_label="Inflation (%)",
        y_label="Real rate (%)", colors={"Exact (Fisher)": theme.ROLE["model"],
                                         "Approximation R − i": theme.ROLE["benchmark"]},
        dashed=["Approximation R − i"], height=340)
    fig2.add_trace(go.Scatter(x=[infl], y=[real * 100], mode="markers", name="Your inputs",
                              marker=dict(color=theme.ROLE["highlight"], size=12,
                                          line=dict(color=theme.ROLE["truth"], width=1.5))))
    l2, r2 = st.columns([3, 2])
    l2.plotly_chart(fig2, width="stretch", theme=None)
    w.how_to_read("The two lines touch near zero inflation and drift apart as inflation rises: the "
                  "approximation ignores that inflation also erodes the interest itself.", container=l2)
    w.tiles([
        w.Tile("Real rate (exact)", f"{real * 100:.4f} %", "growth of purchasing power"),
        w.Tile("Approximation error", f"{(approx - real) * 1e4:.1f} bp",
               "harmless" if abs(approx - real) < 0.001 else "too large to ignore"),
    ], container=r2)


with tab_cp:
    compounding()


# --- ③ YTM vs. realised return -----------------------------------------------------------------
@st.fragment
def realised_return() -> None:
    card = ui.card("Parameters", key="rr")
    presets = {
        "Remark 2.3 — 5 % 3-year bought at 10 %": {"c": 5.0, "T": 3, "f": 1, "y": 10.0, "re": 10.0, "H": 3},
        "High coupon, long bond: 10 % 30-year at 10 %": {"c": 10.0, "T": 30, "f": 1, "y": 10.0, "re": 5.0, "H": 30},
        "Zero-coupon 10-year at 6 %": {"c": 0.0, "T": 10, "f": 1, "y": 6.0, "re": 2.0, "H": 10},
        "Semiannual 6 % 10-year at 5 %, sold after 4 years": {"c": 6.0, "T": 10, "f": 2, "y": 5.0, "re": 5.0, "H": 4},
    }
    w.preset_selector(presets, key_prefix="rr_", container=card)
    cols = card.columns(6)
    c = cols[0].slider("Coupon (%)", 0.0, 15.0, step=0.25, format="%.2f%%", key="rr_c")
    T = cols[1].slider("Maturity (years)", 1, 30, step=1, key="rr_T")
    f = cols[2].selectbox("Coupons / year", [1, 2, 4, 12], key="rr_f")
    y = cols[3].slider("YTM at purchase (%)", 0.0, 15.0, step=0.05, format="%.2f%%", key="rr_y")
    re = cols[4].slider("Reinvestment rate (%)", 0.0, 15.0, step=0.05, format="%.2f%%", key="rr_re")
    if st.session_state.get("rr_H", 1) > T:
        st.session_state["rr_H"] = T
    H = cols[5].slider("Horizon (years)", 1, T, step=1, key="rr_H") if T > 1 else 1

    res = pr.horizon_return(c / 100, T, y / 100, re / 100, H, f)
    rr = np.linspace(0, 15, 151)
    real = [pr.horizon_return(c / 100, T, y / 100, v / 100, H, f).realized * 100 for v in rr]
    fig = plotting.line_chart(rr, {"Realised return": real}, title=f"Realised annual return over {H} years",
                              x_label="Reinvestment rate of coupons (%)", y_label="Realised return (% a year)",
                              colors={"Realised return": theme.ROLE["model"]}, height=400)
    plotting.add_hline(fig, y, f"YTM {y:.2f} %")
    fig.add_trace(go.Scatter(x=[re], y=[res.realized * 100], mode="markers", name="Your scenario",
                             marker=dict(color=theme.ROLE["highlight"], size=13,
                                         line=dict(color=theme.ROLE["truth"], width=1.5))))
    left, right = st.columns([3, 2])
    left.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("The line crosses the dotted YTM level exactly where the reinvestment rate equals the YTM. "
                  "The steeper the line, the more the outcome depends on reinvestment: long, high-coupon bonds "
                  "are steepest; a zero-coupon bond is flat. Returns use the same compounding as the YTM.", container=left)
    wf = go.Figure(go.Waterfall(
        x=["Coupons", "Interest on<br>interest", "Principal" if H == T else "Sale price", "Terminal<br>value"],
        measure=["relative", "relative", "relative", "total"],
        y=[res.coupons, res.interest_on_interest, res.sale_value, 0],
        text=[f"{res.coupons:.2f}", f"{res.interest_on_interest:+.2f}", f"{res.sale_value:.2f}",
              f"{res.terminal_value:.2f}"],
        increasing=dict(marker_color=theme.ROLE["alt"]), decreasing=dict(marker_color=theme.ROLE["benchmark"]),
        totals=dict(marker_color=theme.ROLE["model"]), showlegend=False,
    ))
    wf.add_hline(y=res.price, line=dict(color=theme.ROLE["truth"], dash="dot", width=1.5),
                 annotation_text=f"price paid {res.price:.2f}", annotation_position="top left")
    wf.update_layout(title="What the investor holds at the horizon", xaxis_title="Component",
                     yaxis_title="Value per 100 face", height=400, hovermode="closest")
    right.plotly_chart(wf, width="stretch", theme=None)
    w.how_to_read("Interest on interest is the part the YTM silently assumes. The dotted line is what was paid: "
                  "the ratio of the two bars is the total growth.", container=right)
    gap = (res.realized - y / 100) * 1e4
    w.tiles([
        w.Tile("Realised return", f"{res.realized * 100:.3f} %",
               "equals the YTM" if abs(gap) < 0.05 else ("above the YTM" if gap > 0 else "below the YTM")),
        w.Tile("Gap vs. YTM", f"{gap:+.1f} bp", "reinvestment risk at work" if abs(gap) >= 0.05 else "no reinvestment surprise"),
        w.Tile("Interest on interest", f"{res.interest_on_interest / res.terminal_value * 100:.1f} %",
               "of the terminal value"),
        w.Tile("Price paid", f"{res.price:.2f}", f"for {c:.2f} % coupon at {y:.2f} % YTM"),
    ])
    if H < T:
        st.caption("Before maturity the bond is sold at an unchanged yield (the purchase YTM). A change in yield "
                   "would add price risk, which offsets reinvestment risk; Ch. 5–6 build on this (duration).")


with tab_rr:
    realised_return()


# --- ④ Zero, forward & par curves -------------------------------------------------------------
@st.fragment
def curves() -> None:
    card = ui.card("Parameters · zero-coupon curve R(0,1) … R(0,10)", key="zc")
    cols = card.columns(4)
    shape = cols[0].selectbox("Curve shape", list(ts.PRESETS), key="zc_shape")
    lvl = cols[1].slider("Level shift (bp)", -300, 500, 0, 5, key="zc_lvl")
    slp = cols[2].slider("Slope tilt (bp, long − short)", -500, 500, 0, 5, key="zc_slp")
    crv = cols[3].slider("Curvature (bp, at the middle)", -300, 300, 0, 5, key="zc_crv")
    cols2 = card.columns(4)
    x = cols2[0].slider("Forward start x (years)", 0, 9, 1, 1, key="zc_x")
    th = cols2[1].slider("Forward length θ (years)", 1, 10 - x, min(1, 10 - x), 1, key="zc_th") if x < 9 else 1
    N = cols2[2].slider("Maturity for the coupon effect (years)", 2, 10, 10, 1, key="zc_N")
    show_inst = cols2[3].toggle("Show instantaneous forward", value=False, key="zc_inst")

    z = ts.shape_curve(ts.PRESETS[shape], lvl, slp, crv)
    if np.any(z <= -0.99):
        st.warning("Rates this low are not meaningful.")
        return
    k = np.arange(1, 11)
    par = ts.par_yields(z)
    fw1 = ts.one_period_forwards(z)
    fwx = ts.forward_curve(z, x)

    fig = plotting.base_figure("Three views of one curve", "Maturity / end date (years)", "Rate (%, annual compounding)", 440)
    fig.add_trace(go.Scatter(x=k, y=z * 100, name="Zero-coupon R(0,k)", mode="lines+markers",
                             line=dict(color=theme.ROLE["model"], width=2.6)))
    fig.add_trace(go.Scatter(x=k, y=par * 100, name="Par yield c(k)", mode="lines+markers",
                             line=dict(color=theme.ROLE["benchmark"], width=2.2)))
    fig.add_trace(go.Scatter(x=k, y=fw1 * 100, name="1-year forwards F(0,k−1,1)", mode="lines+markers",
                             line=dict(color=theme.ROLE["alt"], width=2.2, dash="dash")))
    if x > 0:
        fig.add_trace(go.Scatter(x=x + np.arange(1, len(fwx) + 1), y=fwx * 100,
                                 name=f"Forwards starting in {x} y, F(0,{x},θ)", mode="lines+markers",
                                 line=dict(color=theme.PALETTE[4], width=2.2, dash="dot")))
    if show_inst:
        g = np.linspace(0, 10, 201)
        fig.add_trace(go.Scatter(x=g, y=(np.exp(ts.instantaneous_forward(z, g)) - 1) * 100,
                                 name="Instantaneous forward f(0,s)", mode="lines",
                                 line=dict(color=theme.ROLE["data"], width=1.6, dash="dashdot")))
    st.plotly_chart(fig, width="stretch", theme=None)
    w.how_to_read("All curves come from the same ten zero rates. Each forward F(0,x,θ) is drawn at its end date "
                  "x + θ. On a rising curve, the dashed 1-year forwards lie on top, then the zero curve, then par; "
                  "on an inverted curve the order flips. The instantaneous forward (spline, shown as an annual "
                  "rate) is the continuous version of the dashed line. Forwards magnify kinks: small changes in the zero "
                  "curve's slope (as in the Remark 2.5 curve) show up as zigzags in the 1-year forwards.")

    rising = bool(np.all(np.diff(z) > 0))
    falling = bool(np.all(np.diff(z) < 0))
    order = ("forward > zero > par (rising curve)" if rising else
             "forward < zero < par (falling curve)" if falling else "mixed shape: the order changes along the curve")
    f_sel = ts.forward_rate(0.0 if x == 0 else z[x - 1], x, z[x + th - 1], x + th)
    w.tiles([
        w.Tile(f"F(0,{x},{th})", f"{f_sel * 100:.3f} %",
               f"rate locked today from year {x} to year {x + th}" if x > 0 else "starts today: equals the zero rate"),
        w.Tile("10-year zero vs. par", f"{z[-1] * 100:.3f} % / {par[-1] * 100:.3f} %",
               f"gap {(z[-1] - par[-1]) * 1e4:+.1f} bp"),
        w.Tile("Ordering", "✔" if (rising or falling) else "—", order),
    ])

    t1, t2 = st.columns([3, 2])
    with t1:
        st.markdown("**The curve in numbers** (Remark 2.5 layout)")
        tab = pd.DataFrame({"k": k, "R(0,k) %": z * 100, "B(0,k)": ts.discount_factors(z),
                            "F(0,k−1,1) %": fw1 * 100, "Par c(k) %": par * 100})
        if x > 0:
            fcol = ["—"] * 10
            for i, v in enumerate(fwx):
                fcol[x + i] = f"{v * 100:.4f}"
            tab[f"F(0,{x},k−{x}) %"] = fcol
        num = [c for c in tab.columns if c != "k" and tab[c].dtype.kind == "f"]
        st.dataframe(tab.style.format({c: "{:.4f}" for c in num}),
                     hide_index=True, width="stretch")
    with t2:
        st.markdown(f"**Locking in F(0,{x},{th}) with a borrow/lend pair** (Remark 2.4)")
        if x == 0:
            st.caption("Set the forward start x ≥ 1 to see the lock-in trade.")
        else:
            lk = ts.forward_lock_in(z, x, x + th)
            lt = pd.DataFrame(
                [["Borrow 1 until year " + str(x + th), 1.0, 0.0, -lk.cash_y],
                 ["Lend 1 until year " + str(x), -1.0, lk.cash_x, 0.0],
                 ["Net", 0.0, lk.cash_x, -lk.cash_y]],
                columns=["Leg", "Today", f"Year {x}", f"Year {x + th}"])
            st.dataframe(lt.style.format({c: "{:+.5f}" for c in lt.columns[1:]}), hide_index=True, width="stretch")
            st.caption(f"Nothing changes hands today. You receive {lk.cash_x:.5f} at year {x} and repay "
                       f"{lk.cash_y:.5f} at year {x + th}: a loan at ({lk.cash_y:.5f}/{lk.cash_x:.5f})"
                       f"^(1/{th}) − 1 = **{lk.implied_rate * 100:.3f} %** a year, the forward rate.")

    st.divider()
    st.markdown(f"**The coupon effect: {N}-year bonds priced on this curve**")
    cs = np.linspace(0, 0.15, 61)
    ytms = [pr.yield_to_maturity(ts.bond_price_from_zeros(cc, N, z), cc, N) * 100 for cc in cs]
    fig2 = plotting.line_chart(cs * 100, {"YTM of the bond": ytms}, title=f"Same maturity ({N} y), different coupons, different YTMs",
                               x_label="Coupon rate (%)", y_label="Yield to maturity (%)",
                               colors={"YTM of the bond": theme.ROLE["model"]}, height=360)
    fig2.add_hline(y=z[N - 1] * 100, line=dict(color=theme.ROLE["truth"], dash="dash", width=1.5),
                   annotation_text=f"zero rate R(0,{N})", annotation_position="top right")
    fig2.add_trace(go.Scatter(x=[par[N - 1] * 100], y=[par[N - 1] * 100], mode="markers", name="Par bond (coupon = YTM)",
                              marker=dict(color=theme.ROLE["highlight"], size=12, line=dict(color=theme.ROLE["truth"], width=1.5))))
    l2, r2 = st.columns([3, 2])
    l2.plotly_chart(fig2, width="stretch", theme=None)
    w.how_to_read("At zero coupon the YTM equals the zero rate (one cash flow, one rate). As the coupon grows, "
                  "more value sits at earlier dates, so the YTM drifts towards the short rates. The marker is the "
                  "par bond: its coupon equals its YTM, the par yield.", container=l2)
    y2 = pr.yield_to_maturity(ts.bond_price_from_zeros(0.02, N, z), 0.02, N)
    y10 = pr.yield_to_maturity(ts.bond_price_from_zeros(0.10, N, z), 0.10, N)
    w.tiles([
        w.Tile("YTM of a 2 % coupon", f"{y2 * 100:.3f} %", f"close to R(0,{N}) = {z[N - 1] * 100:.3f} %"),
        w.Tile("YTM of a 10 % coupon", f"{y10 * 100:.3f} %",
               f"coupon effect {(y10 - y2) * 1e4:+.1f} bp: " + ("high coupon, lower YTM" if y10 < y2 else
                                                               "high coupon, higher YTM" if y10 > y2 else "none on a flat curve")),
    ], container=r2)


with tab_zc:
    curves()

# =============================================================================================
# 6. Guided experiments
# =============================================================================================
w.try_this([
    w.TryThis(
        "**① Price and yield:** set the yield equal to the coupon, then move the maturity from 1 to 30 years. "
        "Predict the price before you look.",
        "The price stays at exactly 100 for every maturity and every coupon frequency. When the coupon pays exactly "
        "the required return, there is nothing to compensate, so the bond is worth its face value. Off par, "
        "maturity matters: the longer the bond, the longer the coupon gap is paid, and the further from 100 the price.",
    ),
    w.TryThis(
        "**③ Realised return:** choose the *High coupon, long bond* preset (10 % 30-year bought at 10 %, "
        "reinvestment 5 %). Is the realised return above or below 10 %? By how much?",
        "Far below: about 7.0 % instead of 10 %. Over 30 years at a 10 % reinvestment rate, interest on interest would be 77 % of the "
        "terminal value. Halve the reinvestment rate and that component shrinks dramatically. "
        "The YTM silently assumed you would reinvest at 10 % for 30 years. Switch to the zero-coupon preset: the "
        "line goes flat, because there are no coupons to reinvest.",
    ),
    w.TryThis(
        "**④ Curves:** switch the curve shape from *Rising* to *Inverted*. Which line is now on top: the 1-year "
        "forwards, the zero curve or the par curve?",
        "The order flips: par on top, then zero, then the forwards. The zero rate is an average of the 1-year "
        "forwards, so when it is falling the newest forward must be below it. The par yield mixes in earlier, "
        "higher short rates, so it sits above the zero rate. Try *Humped*: the order changes along the curve.",
    ),
    w.TryThis(
        "**② Compounding:** at a 6 % quoted rate, switch the compounding from *Daily* to *Continuous*. How much "
        "does the effective annual rate change? Then try 30 %.",
        "At 6 %: from 6.1831 % to 6.1837 %, less than 0.1 bp. Almost all the gain from compounding is there by "
        "monthly. At 30 % the gaps are much bigger (annual 30 % vs. continuous 34.99 %), because interest on "
        "interest grows with the square of the rate. In high-rate markets the convention is never a detail.",
    ),
    w.TryThis(
        "**④ Coupon effect:** keep the *Rising* curve and look at the coupon-effect chart. Which 10-year bond has "
        "the higher YTM, the 2 % coupon or the 10 % coupon? Then flatten the curve with the slope slider.",
        "The 2 % bond: its value is concentrated at year 10, where rates are highest, so its YTM is close to "
        "R(0,10). The 10 % bond gets more of its value from early years at lower rates. Same issuer, same maturity, "
        "different yields, and neither is cheap. Tilt the slope to about −150 bp (on the Remark 2.5 curve) and "
        "the effect nearly vanishes; tilt further and it reverses.",
    ),
])

# =============================================================================================
# 7. What to notice
# =============================================================================================
w.what_to_notice([
    "A bond's price is the sum of its cash flows times their discount factors. Rates are just a way to "
    "express those discount factors.",
    "Price = par exactly when coupon = yield. Premium bonds pay more than the yield, discount bonds less.",
    "A rate without its compounding convention is incomplete. Converting through the effective annual rate makes "
    "any two quotes comparable.",
    "The YTM is an internal rate of return. It is earned only if coupons are reinvested at the YTM and the bond "
    "is held to maturity (or sold at an unchanged yield).",
    "Zero, forward and par rates are three summaries of one curve. Their order on the chart tells you the slope; "
    "on a sloped curve, bonds with different coupons have different YTMs.",
])

# =============================================================================================
# 8. Pitfalls
# =============================================================================================
w.pitfalls([
    ("Comparing a semiannual yield with an annual one.",
     "A US Treasury at 5.50 % (semiannual) and a Bund at 5.55 % (annual) are almost identical: 5.50 % semiannual "
     "is 5.5756 % annual. Convert both to the same compounding before comparing."),
    ("Reading the YTM as the return you will earn.",
     "It is a promise under conditions: reinvestment at the YTM and holding to maturity. With lower reinvestment "
     "rates a long high-coupon bond can miss its YTM by hundreds of basis points."),
    ("Using a 10-year bond's YTM to discount a cash flow due in 10 years.",
     "The YTM averages all the bond's dates. The right rate for a single date is the zero-coupon rate R(0,10), "
     "which differs from the YTM whenever the curve slopes."),
    ("Misreading the forward notation.",
     "In this book F(0,1,2) starts in 1 year and **lasts** 2 years (it ends in year 3). Many other texts write "
     "F(0,1,2) for the forward from year 1 to year 2. Always check whether the last argument is a length or a date."),
])

# =============================================================================================
# 9. Exercises
# =============================================================================================
w.exercises([
    w.Exercise(
        "A 5-year bond has a 10 % coupon paid **semiannually** and a yield to maturity of 7 % (semiannual "
        "compounding). What is its price per 100 face? Use tab ① (preset any, then set c = 10, T = 5, f = 2, "
        "y = 7). Then check the yield back from the price in the worked example (quote 112-15 is close).",
        "Per period: coupon 5, rate 3.5 %, 10 periods. P = 5/0.035 × (1 − 1.035⁻¹⁰) + 100 × 1.035⁻¹⁰ = "
        "41.582 + 70.892 = **112.4749**. It is a premium bond, since the coupon is above the yield. In the "
        "worked example, the quote 112-15 (= 112.46875) with coupon 10, maturity 5, 2 coupons a year gives a "
        "yield of 7.0014 %, close to 7 %. The quote is rounded to a 32nd.",
        numeric_answer=112.4749, tolerance=5e-3, unit="per 100",
    ),
    w.Exercise(
        "A bond yields 7 % with semiannual compounding. What is the equivalent **effective annual** yield? "
        "(Tab ② gives it directly.)",
        "EAY = (1 + 0.07/2)² − 1 = 1.071225 − 1 = **7.1225 %**. The 12.25 bp gap is the interest earned in the "
        "second half-year on the first half-year's interest.",
        numeric_answer=7.1225, tolerance=1e-3, unit="%",
    ),
    w.Exercise(
        "On the Remark 2.5 curve (tab ④, *Rising* preset, all shifts at 0), what is the forward rate **F(0,2,1)**, "
        "the 1-year rate locked in today for the third year? Also read the 3-year par yield.",
        "F(0,2,1) = (1.05³ / 1.045²) − 1 = 1.157625 / 1.092025 − 1 = **6.0072 %**. It is above R(0,3) = 5 % "
        "because the curve rises: to average up to 5 % over three years after 4 % and 5.002 % in years 1 and 2, the third "
        "year must pay about 6 %. The 3-year par yield is 4.9674 %, below R(0,3). Set x = 2, θ = 1 to check both.",
        numeric_answer=6.0072, tolerance=2e-3, unit="%",
    ),
    w.Exercise(
        "Using tab ③, explain when a buy-and-hold investor actually earns the YTM. Which bonds are most exposed "
        "to the gap, and which are immune?",
        "Only when every coupon is reinvested at the YTM until maturity (or the bond is sold at an unchanged "
        "yield). The exposure grows with the size of the coupons and the length of the horizon, because both make "
        "interest on interest a larger share of the terminal value. A zero-coupon bond held to maturity is immune: "
        "there is nothing to reinvest, so its realised return is its YTM whatever happens to rates.",
        kind="explain",
    ),
    w.Exercise(
        "Why does the par curve lie *below* the zero curve when the curve rises? Use the table in tab ④.",
        "A par bond is a portfolio of zero-coupon bonds: coupons at years 1 … n and the face value at n. Its yield is a "
        "blend of R(0,1) … R(0,n), weighted mostly towards R(0,n) because the face value is the largest flow. When "
        "the curve rises, all the earlier rates are lower than R(0,n), so the blend, which is the par yield, is "
        "lower. On an inverted curve the earlier rates are higher, and the par curve lies above the zero curve.",
        kind="explain",
    ),
])

# =============================================================================================
# 10. Takeaways and glossary
# =============================================================================================
w.takeaways_and_glossary(
    [
        "Price = Σ B(0,t)·CF_t. Discount factors are the primitive; rates are a way to quote them.",
        "With one rate y for all dates: P = (C/y)[1 − (1+y)⁻ᵀ] + N(1+y)⁻ᵀ, and P = N when c = y.",
        "State the compounding with every rate. Convert via the effective annual rate (or the continuous rate).",
        "Real rate: (1 + nominal)/(1 + inflation) − 1.",
        "YTM = internal rate of return: a convenient restatement of price, not a forecast of your return.",
        "Forward rates can be locked in today and are the break-even future rates. Par yields are the coupons of "
        "par bonds and remove the coupon effect.",
    ],
    {
        "Discount factor B(0,t)": "today's price of 1 unit of currency paid with certainty at date t.",
        "Present value": "value today of a future cash flow: the cash flow times its discount factor.",
        "Zero-coupon (spot) rate R(0,t)": "the rate for a single payment at t; B(0,t) = (1 + R(0,t))⁻ᵗ.",
        "Yield to maturity (YTM)": "the single discount rate that sets the bond's discounted flows equal to its price; its IRR.",
        "Current yield": "annual coupon divided by price; ignores the gain or loss as the price moves to par.",
        "Coupon rate": "the stated annual interest as a percentage of face value; it fixes the cash flows.",
        "Par, premium, discount bond": "price equal to, above, or below face value: coupon equal to, above, or below the yield.",
        "Perpetuity": "a bond paying a fixed amount forever; price = cash flow / yield.",
        "Compounding frequency": "how many times a year interest is added to the balance (1, 2, 4, 12, 365 or continuously).",
        "Effective annual rate": "the equivalent rate compounded once a year.",
        "Continuously compounded rate": "the limit of infinitely frequent compounding; growth factor e^{R_c t}.",
        "Real interest rate": "growth of purchasing power: (1 + nominal)/(1 + inflation) − 1.",
        "Forward rate F(0,x,θ)": "rate fixed today for a loan starting at x and lasting θ years.",
        "Instantaneous forward f(0,s)": "the forward rate for an infinitesimally short loan starting at s.",
        "Par yield c(n)": "coupon rate at which an n-year bond prices exactly at par on today's zero curve.",
        "Coupon effect": "on a sloped curve, bonds with the same maturity but different coupons have different YTMs.",
        "Reinvestment risk": "the risk that coupons are reinvested at rates below the YTM, lowering the realised return.",
        "Interest on interest": "the interest earned by reinvested coupons.",
    },
)

# =============================================================================================
# 11. Source reference
# =============================================================================================
w.source_reference(
    "L. Martellini, P. Priaulet & S. Priaulet (2003), *Fixed-Income Securities: Valuation, Risk Management "
    "and Portfolio Strategies*, Wiley.",
    "Chapter 2, §2.1 (introduction to pricing), §2.2 (present value, compounding, real rates) and §2.3 "
    "(current yield, YTM, zero, forward and par rates).",
    ["Eq. 2.1 (price as sum of discounted flows)", "Eq. 2.2 and Remark 2.1 (level-coupon bond)",
     "Eq. 2.3 (forward rate)", "Eq. 2.4 (instantaneous forward)", "Eq. 2.5 (par yield)"],
)
st.caption(
    "Worked examples reproduced in tests: 2.2–2.18, Remark 2.3 (YTM as total return) and the full Remark 2.5 "
    "forward table, plus the setup of end-of-chapter Exercise 2.14. The end-of-chapter problems are in the book."
)
