# Fixed-Income Securities lab

**Source:** L. Martellini, P. Priaulet, S. Priaulet, *Fixed-Income Securities: Valuation, Risk Management
and Portfolio Strategies*, Wiley Finance (2003).

**Scope (pilot):** Part I–II, chapters 1–4: instruments and market conventions, bond prices and yields,
the term structure (stylized facts, PCA, classical theories), and deriving the zero-coupon curve
(bootstrapping, interpolation, splines, Nelson–Siegel/Svensson, extended Vasicek, credit spreads).

**Audience:** finance students and practitioners who want to understand the mechanics by experimenting,
without the book at hand. Pages explain in depth (see CLAUDE.md §5).

## Status
| # | Module | Map | Core | Tests | Page | Notes |
|---|--------|-----|------|-------|------|-------|
| 01 | Bonds & money-market instruments (ch. 1) | approved | ✔ | ✔ 39 validation + 5 page tests | ✔ | pilot, awaiting review |
| 02 | Bond prices & yields (ch. 2) | approved | ✔ | ✔ 83 validation + 5 page tests | ✔ | awaiting review |
| 03 | Term structure: facts, PCA, theories (ch. 3) | approved | – | – | – | |
| 04 | Deriving the zero-coupon curve (ch. 4) | approved | – | – | – | |

## Visual identity
Colours come from the book's cover (warm black band, ember red, copper glow, cream). They are defined in
`lab_theme.py` and mirrored in `.streamlit/config.toml`. Headings use Oswald, body text Source Sans 3 and
subtitles Source Serif 4. No cover art is used.

## Run locally
```
pip install -r requirements.txt pytest
streamlit run app.py
pytest
```

## Deploy (Streamlit Community Cloud, free)
On share.streamlit.io, create an app from this repository with branch `main` and main file `app.py`.
`.streamlit/config.toml` at the repository root supplies the theme colours.

## Layout
`app.py` is the router, `home.py` the overview, `chapters/` holds the pages, and `core/` the model code
(no Streamlit). `tests/` holds the validation and page tests, `maps/` the chapter plans, and `shared/` the
page chrome, theme and widgets.

## Known limitations
**Module 01**
- Holidays and business-day adjustments are ignored. The settlement date is set directly (no T+n lag).
- Act/Act for a general period uses the ISDA rule. Accrued interest uses ICMA (days / days in the coupon period).
- The book truncates two §1.1.1 year fractions to 4 decimals (2.0931, 2.0888). The tests allow 1e-4.
- Ex. 1.25 accrues the Bund coupon as 5 × 117/360 although Bunds use Act/Act. We reproduce the book in the
  tests, and the page notes the Act/Act value. Our repurchase amount is €1,060,874.5 (book: €1,060,875).
- The inflation-linked simulator uses a simplified annual index ratio. The OATi 3-month lag and daily
  interpolation are shown separately (DIR live check). No deflation floor.
- No repo haircut. Brazilian BUS/252 is described but not computed (it needs the ANBIMA holiday calendar).
- Prices from yields (clean vs. gross chart) use the street convention, explained in module 02.

**Module 02**
- Bonds are valued on a coupon date (whole periods only). Fractional first periods and accrued interest are in module 01.
- Ex. 2.16: the book rounds 103-23 (103.71875) to 103.72 and reports y₂ = 6 %. Our roots are 5.9991 % (exact
  price) and 5.9985 % (rounded price). The test tolerance is 0.5 bp. Ex. 2.17's 9.601 % is rounded, so the page prices
  that preset at 100.9993, not 101.
- The realised-return simulator sells the bond at an unchanged yield when the horizon is before maturity. The trade-off
  between price risk and reinvestment risk is left to the duration chapters.
- The instantaneous forward (Eq. 2.4) joins the annual zero points with a natural cubic spline on −ln B(0,t).
  This is a modelling choice (Ch. 4 compares alternatives). Near t = 0 it can sit below R(0,1).
- The Remark 2.5 curve has kinks, so its 1-year forwards zigzag (e.g. F(0,5,1) = 7.01 %, F(0,6,1) = 6.63 %). This is
  correct arithmetic, not a bug, and the chart caption says so.
- Exercise answers that the book doesn't print (Ex. 2.14 setup: price 100.1360, YTM 4.9686 %) are derived and tested.
