# Empirical Properties and Classical Theories of the Term Structure — Martellini, Priaulet & Priaulet, Ch. 3 (§3.1–3.2)

## Learning objectives
- Recognize the four standard curve shapes and relate the par curve's shape to where the zero and forward curves sit.
- State the five stylized facts of yield-curve dynamics and show each in data.
- Run a principal component analysis (PCA) of rate changes, and interpret the first three factors as level, slope and curvature.
- Explain what each classical theory (pure expectations, liquidity premium/preferred habitat,
  segmentation, biased expectations) says forward rates contain, and what each predicts.

## Core ideas
- The term structure is one object seen through several curves (YTM, swap, zero, par, forward,
  instantaneous forward). Only YTM and swap rates are observed; the rest are implied.
- Rising par curve ⇒ zero curve above it and forward curve above both; falling ⇒ reversed.
- Rates mean-revert, rarely go negative, are imperfectly correlated, and are more volatile at the short end.
- Rate changes are highly redundant: three factors usually explain more than 90 % of the variance, and they look like
  level, slope and curvature moves.
- The theories differ on one question: are forward rates forecasts of future short rates, risk
  premia, or both? The answer decides whether long bonds earn more on average.

## Explanation outline
1. *Question:* "What does an inverted curve tell you?" → definitions; the four shapes; the
   par/zero/forward ordering (with the proof as an exercise, as in the book).
2. Stylized facts, each with a live demo:
   - mean reversion: simulate Vasicek vs. CIR (Eq. 3.1–3.2), and show the negative rates Vasicek allows;
   - imperfect correlation: a correlation heatmap;
   - the volatility term structure;
   - the factor structure.
3. PCA step by step: build the correlation matrix of rate changes → eigen-decomposition →
   variance explained → factor loadings (sensitivities c_lk) → reconstruct a curve move with 1, 2, 3 factors.
   Shift/twist/butterfly movements as the loadings in action. Bullish/bearish flattening/steepening.
4. Theories: write the long rate as a geometric average of the short rate and forwards (Eq. 3.6). Then
   change *what the forwards are*:
   - expectations only (Eq. 3.6);
   - premia only (Eq. 3.7);
   - both (Eq. 3.8);
   - segmentation (supply/demand by segment).
   Example 3.2 (flat → rising when hikes are expected) as an animated adjustment.
5. Empirical verdict (§3.2.5–3.2.6): positive, time-varying premium; expectations matter but
   explain little. The pure-expectations vs. pure-premium comparison as a two-column summary.

## Key equations
- Vasicek dr = a(b − r)dt + σ dW (Eq. 3.1); CIR dr = a(b − r)dt + σ√r dW (Eq. 3.2)
- PCA: ΔR(t,θ_k) = Σ_l c_lk C_l,t (+ε); standardized decomposition (Eq. 3.3); sensitivity
  ∂ΔR/∂C_l = c_lk (Eq. 3.4); truncated M-factor model (Eq. 3.5); variance share λ_l / m; per-maturity
  R²_lk = c²_lk / Σ_l c²_lk
- Long rate as average of forwards: 1 + R(t,n) = [Π(1 + F(t,t+k,1))]^{1/n}
- Pure expectations (Eq. 3.6); liquidity premium with 0 < L_2 < … < L_n and decreasing increments (Eq. 3.7);
  biased expectations (Eq. 3.8)

## Manipulable parameters
| name | meaning | range | default |
|---|---|---|---|
| curve preset | flat / rising / falling / humped (Nelson–Siegel parameters) | — | rising |
| a, b, σ, r_0 | Vasicek/CIR speed, mean, vol, start | 0.01–2, 0–15 %, 0–5 %, 0–15 % | 0.3, 5 %, 1.5 %, 3 % |
| model | Vasicek or CIR | — | Vasicek |
| n paths, horizon, seed | simulation | 1–200, 1–30 y | 20, 10 y, 42 |
| factor shocks | size of factor 1/2/3 moves (σ units) | ±3 | 0 |
| number of factors M | used in reconstruction | 1–5 | 3 |
| dataset | synthetic DGP / real snapshot | — | synthetic |
| expected short-rate path | 1-year rate expected in years 1..n (expectations) | ±300 bp per year | flat 5 % |
| liquidity premia | L_n = L_max(1 − e^{−n/κ}) | L_max 0–2 %, κ 1–10 | 0.5 %, 3 |

## Visualizations to build
1. **Shape gallery + ordering**: par, zero and 1y-forward curves for any preset, with the ordering rule shown.
2. **Short-rate simulator**: Vasicek vs. CIR fan chart with the long-run mean line and a "share of paths below 0" metric.
3. **Correlation heatmap** of rate changes; with real or synthetic data and the book's Table 3.1 as an option.
4. **Scree plot** (variance explained, cumulative) and **loadings chart** (c_lk vs. maturity for factors 1–3).
5. **Factor playground**: sliders apply factor shocks to a base curve. Shows shift, twist and butterfly, and
   reconstruction error vs. M.
6. **Theory builder**: stacked decomposition of each zero rate into expected-short-rate and premium parts;
   the learner sets expectations and premia and sees the resulting curve shape.

## Validation targets
- **Table 3.1 → eigenvalues.** The eigen-decomposition of the book's 13×13 correlation matrix gives
  λ = 9.202, 2.429, 0.870, 0.257 (70.8 / 18.7 / 6.7 / 2.0 %). This matches **Table 3.3, 1997 row**
  (9.2186, 2.4148, 0.8821, 0.2489) within the rounding of the 3-decimal correlations. The text says
  Table 3.1 is 1998 data, but the 1998 row (7.20, 3.20…) does not match (see open questions).
  Test: |λ_l − Table 3.3(1997)| < 0.05 for l = 1..4.
- Table 3.4: Σ_l R²_lk = 1 per maturity, and the column means equal the variance shares: an internal
  identity, tested on our own PCA.
- Ex. 3.3: a 5 % → 6 % jump moves the 2-year 5 % bond to 98.17 and the 1-year to 99.06.
- Ex. 3.2: flat 5 % curve plus an expected 100 bp hike → rolling 1-year earns 5.5 % per year vs. 5 % for the 2-year;
  the equilibrium 2-year rate under pure expectations = [(1.05)(1.06)]^{1/2} − 1 = 5.4988 %.
- Monte Carlo (fixed seed): Vasicek sample mean → b and stationary sd → σ/√(2a), within MC error;
  CIR with 2ab ≥ σ² produces no negative rates.
- PCA on synthetic data generated from known level/slope/curvature loadings: recovers the
  variance shares and loadings (up to sign) within tolerance. The method's "true answer" is known.
- Qualitative (real data): first factor > 60 %, first three > 90 % (§3.1.2, Table 3.2 range).

## Guided experiments ("Try this")
- Raise σ in Vasicek until some paths go negative; switch to CIR with the same parameters.
- Set M = 1 and apply a pure-slope move: how big is the reconstruction error?
- Under pure expectations, make the market expect cuts in years 2–3: what shape appears?
- Add a liquidity premium to a flat expected path: why does the curve rise even though nobody expects hikes?

## Common pitfalls
- Reading an upward-sloping curve as proof that rates will rise (it ignores the premium).
- Running PCA on rate *levels* instead of *changes*, or on the covariance matrix when maturities have
  very different volatilities (§3.1.2 discussion of Lardic et al.).
- Treating factor signs as meaningful (eigenvectors are defined only up to sign).

## Exercises
1. (numeric check) Under pure expectations with R(0,1) = 4 % and expected next-year rate 5 %, compute R(0,2).
2. (numeric check) From the Table 3.1 PCA, what share of 5-year rate variance is explained by factor 1?
3. (explain) Using the theory builder, produce a humped curve under expectations only, then under preferred habitat.
4. (explain) Why does a single-factor model suffice for short-dated products but not for curve-spread products?
5. (numeric check) Price change of a 3-year 5 % bond after a 5 % → 6 % shift (extends Ex. 3.3).

## Data needs
- **Synthetic** (default): a factor DGP (Nelson–Siegel factors following AR(1)s) gives a daily zero-curve
  panel with known loadings. Precompute: no (fast); cache with `st.cache_data`.
- **Real** (optional): Brazilian rates from the BCB (SGS series) and/or ANBIMA's public zero-curve files via a
  `precompute/` fetch script; save a parquet snapshot (a few hundred KB) with the download date. State the
  rate convention (BUS/252, compounded) on the page.
- The book's Table 3.1 (13×13 correlations) as a test fixture. It is factual data; we redraw it, not reproduce the figure.

## Open questions / ambiguities
- The Table 3.1 data year: the text says 1998, but its eigenvalues match the 1997 row of Table 3.3. We will document this.
- The book's Table 3.1 has a garbled cell in the text extraction ("0.30.637" → 0.3, 0.637). Verified by
  symmetry and the eigenvalue match; confirm from the PDF image before freezing the fixture.
- Real data source: **decided: Brazil (BCB SGS / ANBIMA public files)**, via a `precompute/` fetch script and
  a saved snapshot in `data/` with the download date. Synthetic data remains the default.
