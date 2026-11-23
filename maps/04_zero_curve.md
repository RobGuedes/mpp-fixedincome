# Deriving the Zero-Coupon Yield Curve — Martellini, Priaulet & Priaulet, Ch. 4 (§4.1–4.3, App. 4.7)

This is the largest and most method-sensitive chapter. Proposal: **one page with five tabs**:
(A) direct methods & bootstrapping, (B) interpolation, (C) splines on the discount function,
(D) parametric curves (Nelson–Siegel, Svensson, extended Vasicek), (E) interbank & credit curves.

## Learning objectives
- Extract discount factors from coupon bond prices by linear algebra (when possible) and by bootstrapping.
- Compare interpolation choices (linear, cubic, log-linear on discount factors) and see their effect on forwards.
- Fit a curve by least squares: a spline on the discount function vs. a parametric zero curve. Explain
  weighting (why short bonds need more weight) and in-sample vs. out-of-sample fit.
- Interpret Nelson–Siegel/Svensson parameters as level, slope and curvature, and connect them to the Ch. 3 PCA.
- Build an interbank curve from deposits, futures and swaps, and a credit-spread curve (disjoint vs. joint).

## Core ideas
- No arbitrage ties every bond price to the discount factors: P = F·B. With enough well-chosen bonds
  you can invert it; in practice you cannot, so you bootstrap and interpolate.
- Interpolation choices that look harmless on the zero curve show up as kinks and wiggles in the
  **forward** curve. Always look at the forwards.
- Indirect methods fit a functional form by least squares. Splines fit prices almost perfectly
  (good for rich/cheap analysis). Parametric forms are smoother, more interpretable, and better for hedging,
  but misfit the long end.
- Price errors are not comparable across maturities: a 1 bp yield error is tiny in price for a
  1-week bill and large for a 20-year bond. Weighting by price sensitivity (Vasicek–Fong) fixes the short end.
- Overfitting is diagnosed out of sample: a minimization set vs. a checking set.

## Explanation outline
1. *Question:* "We see coupon bond prices. How much is $1 in 3 years worth?" → P = F·B, Ex. 4.1 solved live.
2. Why direct inversion fails (dates don't align, there are too few bonds) → bootstrapping, Ex. 4.2 step by step.
3. Interpolation: linear vs. cubic (Ex. 4.3–4.5) vs. log-linear DF. Then show the induced forward curves.
4. From exact fit to best fit: the least-squares program (Eq. 4.3), weights (Remark 4.1), the
   constraint B(0) = 1 (Eq. 4.4–4.5).
5. Splines: why cubic, smoothness constraints (Eq. 4.6), B-spline basis, exponential splines (Eq. 4.7), the
   number and placement of knots, E_min vs. E_verif.
6. Parametric: Nelson–Siegel (Eq. 4.10) derived from the forward form; Svensson (Eq. 4.11); extended
   Vasicek 1 and 2 (Eq. 4.12–4.13). Parameter meanings and sensitivities (Fig. 4.9-type chart, redrawn).
7. Trade-offs (§4.1.3 discussion): pricing vs. hedging, interpretability, long-end concavity.
8. Interbank curve: deposits → futures → swaps (par yields) → zeros, and the segment joints.
9. Credit spreads: disjoint (subtract two fitted curves) vs. joint (additive/multiplicative spread
   function). Why joint gives smoother spreads.

## Key equations
- P_t = F·B_t, B_t = F^{−1}P_t (Eq. 4.1–4.2); R = B^{−1/t} − 1, R_c = −ln B / t
- Bootstrapping recursion (§4.1.2); linear interpolation; cubic interpolation via a 4×4 Vandermonde
  solve; log-linear DF interpolation (§4.2.2: R_c·y linear in y)
- Least squares β* = argmin Σ(P − P̂)² (Eq. 4.3); weights ω_j² = (dP/dy)² = D²P²/(1+y)² (Vasicek–Fong) or T_j², …;
  constrained GLS (Eq. 4.5)
- Cubic polynomial spline with C² joins (Eq. 4.6); B-spline basis; exponential spline (Eq. 4.7), u = f(0,∞)
- Fit metrics: E_min, E_verif (RMS price spread), 0.10 % of price rule (§4.1.3)
- Nelson–Siegel forward and zero forms (Eq. 4.10); Svensson (Eq. 4.11); Vasicek zero curve (Eq. 4.12);
  extended Vasicek 1 (Eq. 4.13) and 2
- Interbank: money-market rate → zero (Act/360 → Act/365); futures price = 100 − forward;
  swap rate as par yield: SR(n)·Σ B(0,i) + B(0,n) = 1
- Credit: B_i = B_0 + S_i (additive) or B_0·T_i (multiplicative ⇒ R_i = R + spread)
- Appendix 4.7: modified Newton's algorithm for nonlinear least squares

## Manipulable parameters
| name | meaning | range | default |
|---|---|---|---|
| bond basket | Ex. 4.1 / Ex. 4.2 / synthetic basket of N bonds | N 5–60 | Ex. 4.1 |
| price noise | std. dev. of price errors added to the synthetic basket | 0–50 cents | 5 cents |
| true curve | NS parameters generating the synthetic basket | as below | rising |
| interpolation | linear / cubic / log-linear DF / natural cubic spline | — | linear |
| method | spline (polynomial, B-spline, exponential), NS, Svensson, Vasicek ext. 1/2 | — | NS |
| knots | number and location of spline knots | 2–8 | [0,1,7,10,20] |
| weights | equal / Vasicek–Fong / T² / D·P/(1+y) | — | Vasicek–Fong |
| β0, β1, β2, β3, τ1, τ2 | NS/Svensson parameters (manual mode) | β ±10 %, τ 0.1–10 | 7, −2, 1, −1 %, 3.33, 0.3 (Ex. 4.8, 4.10) |
| L0, S0, γ0, a | extended Vasicek | — | fitted |
| checking-set share | out-of-sample fraction | 0–50 % | 30 % |
| credit spread shape | true spread curve for the synthetic risky class | level, slope | 100 bp, +5 bp/yr |

## Visualizations to build
1. **Matrix view (Ex. 4.1)**: the cash-flow matrix as a heatmap, solved B and R(0,t) next to it.
2. **Bootstrapping animation (Ex. 4.2)**: each step adds one bond and one solved rate.
3. **Interpolation lab**: zero curve + implied 1y and instantaneous forward curves for each method.
   Linear zeros → saw-tooth forwards.
4. **Fit lab**: fitted vs. true zero curve (synthetic), residuals by bond (bars, min vs. check set),
   E_min/E_verif metrics with the 0.10 % rule as a badge ("adequate" / "possible overfit").
5. **Knots vs. fit**: E_min and E_verif as the number of knots grows (overfitting curve).
6. **NS/Svensson playground**: sliders for each parameter (Figs. 4.6–4.8, 4.13–4.14 redrawn), plus the
   sensitivity curves ∂R/∂β_i (Fig. 4.9 type), linked back to the Ch. 3 PCA loadings.
7. **Weighting effect** (Remark 4.1): short-end zoom with equal vs. Vasicek–Fong weights.
8. **Interbank stitching**: deposit / futures / swap segments in different colours on one zero curve.
9. **Credit spreads**: disjoint vs. joint spread curves over the true spread (synthetic).

## Validation targets
Reproduced during mapping:
- Ex. 4.1: B = 0.9619, 0.91194, 0.85363, 0.78901; R = 3.96, 4.717, 5.417, 6.103 %.
- Ex. 4.2: R(0, 1+2/12) = 5.41 %; R(0,3) = 5.91 % (the 2-year rate 5.79 % is used as an input in the book's equation).
  Still to verify in the tests: R(0,1.75) = 5.69 %, R(0,2) = 5.79 %, which depend on the exact interpolation of earlier points.
- Ex. 4.3: R(0,3.75) = 5.875 %. Ex. 4.4: (a,b,c,d) = (0.0025, −0.0225, 0.07, −0.02); R(0,2.5) = 5.34375 %.
- Remark 4.1: 1-day $100 at 5 %/6 % → 99.9866/99.9840; 1-week at 6 %/6.5 % → 99.888/99.879 (compounding convention to confirm).
- NS limits: R_c(0,θ) → β0 as θ → ∞ and → β0 + β1 as θ → 0; the zero curve is the average of the forward curve
  (numerical integration test).
- Svensson reduces to NS when β3 = 0; Vasicek form (4.12) matches the closed-form Vasicek bond price for γ0 = σ²/a².
- **Synthetic recovery** (main methodological test, fixed seed): price a basket from a known NS curve, add
  noise, refit with each method → RMS zero-rate error < tolerance; E_verif ≥ E_min on average;
  Vasicek–Fong weights reduce short-end error vs. equal weights.
- Spline smoothness: the fitted cubic spline discount function is C² at the knots (finite differences); B(0) = 1 exactly.
- **Tables 4.1–4.2 (qualitative)**: refit the book's 25 + 10 French bonds of 04/26/1996 (maturity, coupon and
  price are given) with VF34 and BS35 knots. Target: both methods' E_min/E_verif below 0.10 %, and the same
  bonds have the largest spreads. Exact replication is unlikely (price basis and day counts are unspecified).
  Document the gap.
- Interbank: the bootstrapped swap curve reprices every input swap at par (to 1e-10).

## Guided experiments ("Try this")
- Switch interpolation from linear to cubic and watch the *forward* curve, not the zero curve.
- Add 30 cents of noise to one 10-year bond: which method's curve moves most?
- Increase the knots from 3 to 8: watch E_min fall and E_verif rise.
- Set equal weights and zoom to 0–6 months (Remark 4.1).
- In the NS playground, find the parameter values that make a humped curve, then try an inverted hump. Why do you need Svensson?

## Common pitfalls
- Judging a curve by its zero rates only (forwards reveal artifacts).
- Treating a perfect in-sample fit as success (overfitting).
- Fitting prices with equal weights and trusting the short end.
- Mixing rate conventions across money-market, futures and swap inputs.
- Ignoring the futures convexity bias (the book ignores it here; mention it as a limitation and link to Ch. 11).

## Exercises
1. (numeric check) Solve a 3-bond version of Ex. 4.1 entered by the learner.
2. (numeric check) Bootstrap the 3-year zero rate given the 1- and 2-year rates and a 3-year bond price.
3. (numeric check) Svensson rate at θ = 2 years for the book's Ex. 4.10 parameters.
4. (explain) Why do spline methods suit rich/cheap analysis while parametric methods suit hedging?
5. (explain) Using the credit tab, why can disjoint spreads be non-smooth when the two curves are fitted separately?

## Data needs
- **Synthetic** baskets priced from known curves (default; makes the true answer known).
- Book data as test fixtures: Ex. 4.1, 4.2 and the Tables 4.1/4.2 bond list (maturity, coupon, market price).
- Optional real snapshot (later): an ECB euro-area AAA yield-curve parameter file, or FRED, for the parametric tab.
- Precompute: none needed. Fits of fewer than 60 bonds run in milliseconds; cache with `st.cache_data`.

## Open questions / ambiguities
- **Scope:** §4.1.3 splines (polynomial, B-spline, exponential) and §4.3 joint credit methods are heavy.
  Proposal: implement all, but credit uses only the additive B-spline version plus the multiplicative NS-spread version.
- Tables 4.1–4.2: are the prices clean or gross? The book doesn't say; we'll test both and report the better fit.
- Ex. 4.2 intermediate rates (5.69 %, 5.79 %) depend on how the 1y9m bond's first coupon date is discounted.
  To resolve in the tests.
- Remark 4.1 price examples: the compounding convention is unstated (annual, Act/365 assumed).
- Example 4.13 data (2001 Euribor futures/swaps): use as a preset? It is factual market data, which is fine for
  a fixture, but synthetic is cleaner for teaching.
