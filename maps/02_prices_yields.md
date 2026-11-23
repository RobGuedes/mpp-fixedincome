# Bond Prices and Yields — Martellini, Priaulet & Priaulet, Ch. 2 (§2.1–2.3)

## Learning objectives
- Price any fixed cash-flow bond as a sum of discounted cash flows, using either discount factors or one yield.
- Convert rates between compounding frequencies (annual, semiannual, monthly, continuous) and
  between nominal and real.
- Compute a yield to maturity, and explain what it is (an IRR) and what it is not (the return you will earn).
- Derive forward rates and par yields from zero-coupon rates, and interpret forwards as both a lockable
  rate and a break-even.
- Explain the coupon effect, and why the par and zero curves differ from the YTM curve.

## Core ideas
- Pricing in three steps: list the cash flows, get a discount factor for each date, and sum.
  The discount factor B(0,t) is the price of $1 paid at t.
- A rate is meaningless without its compounding convention. Continuous compounding makes the
  algebra clean, and every convention can be converted to every other.
- The YTM is the single rate that reprices the bond. It averages the zero rates and equals the
  realized return only if every coupon is reinvested at that same YTM.
- The forward rate F(0,x,y−x) is implied by two zero rates. It can be locked in today with a
  borrow/lend pair, and it is the future rate that would make all maturities earn the same return.
- The par yield is the coupon that prices a bond at par. The par curve removes the coupon effect
  that makes YTM curves hard to compare.

## Explanation outline
1. *Question:* "Would you pay 95 cents today for $1 in a year?" → time value, discount factors.
2. Discounting a stream: the annuity + principal formula, and why price = par when coupon = yield
   (derive in an expander). Perpetuity as the limit.
3. Conventions: n-times-a-year compounding → effective annual → continuous limit (proof sketch in an
   expander). Real vs. nominal (Fisher).
4. The yield to maturity: definition, solving numerically, the price–yield curve. YTM as total return
   *if* coupons are reinvested at the YTM (Remark 2.3). Then show what happens when they are not.
5. Zero rates, forwards and par yields as three views of one curve. Forward as lockable rate
   (borrow/lend table) and as break-even (Remark 2.5). Instantaneous forward as the limit.
6. Coupon effect: two bonds with the same maturity and different coupons have different YTMs on a
   sloped curve.

## Key equations
- PV(CF_t) = B(0,t)·CF_t, B(0,t) = 1/(1+R(0,t))^t; bond price = Σ B(0,t)·CF_t (Eq. 2.1)
- Level-coupon bond: P_0 = C/y·[1 − (1+y)^−T] + N/(1+y)^T (Eq. 2.2); perpetuity CF/y; semiannual version (Remark 2.1)
- Fisher: 1 + R_real = (1 + R_nominal)/(1 + i) (§2.2.3)
- Effective annual rate R = (1 + R_n/n)^n − 1; continuous R_c: R = e^{R_c} − 1 (§2.2.4–2.2.5)
- Current yield y_c = cN/P (§2.3.1)
- YTM: P = Σ CF_t/(1+y)^t (annual) or Σ CF_t/(1+y_2/2)^t (semiannual) (§2.3.2)
- Forward: F(0,x,y−x) = [(1+R(0,y))^y/(1+R(0,x))^x]^{1/(y−x)} − 1 (Eq. 2.3); instantaneous f(t,s) (Eq. 2.4)
- Par yield: c(n) = [1 − (1+R(0,n))^−n] / Σ_{i=1}^n (1+R(0,i))^−i (Eq. 2.5)

## Manipulable parameters
| name | meaning | range | default |
|---|---|---|---|
| coupon c | annual coupon rate | 0–15 % | 5 % |
| maturity T | years | 1–30 | 10 |
| frequency | payments per year | 1, 2, 4, 12 | 1 |
| yield y | flat discount rate | 0–15 % | 6 % (Ex. 2.4) |
| reinvestment rate | rate at which coupons are reinvested | 0–15 % | = y |
| horizon | holding period for realized return | 1–T | T |
| zero curve | R(0,1..10) via presets (flat/rising/inverted/humped) + level/slope/curvature sliders | ±500 bp | Remark 2.5 curve (4 %→6.25 %) |
| forward start x | start of forward period | 0–9 y | 1 |
| nominal rate, inflation | Fisher | 0–20 %, −2–15 % | 5 %, 2 % |
| compounding n | frequency for conversions | 1, 2, 4, 12, 365, ∞ | 2 |

## Visualizations to build
1. **Cash-flow and PV bars**: each cash flow and its present value, with a running sum to the price.
   Makes "price = sum of discounted cash flows" visible.
2. **Price–yield curve** with the current point, the par line and a premium/discount label. Shows the convexity
   and the price = par at coupon = yield property.
3. **Compounding convergence**: the effective annual rate as n grows from 1 to ∞, converging to e^{R_c} − 1.
4. **Realized return vs. YTM**: horizon return as a function of the reinvestment rate. YTM is
   achieved only when the reinvestment rate equals the YTM.
5. **Three curves, one chart**: zero, 1-year-forward and par curves from the same input curve. The learner
   checks the ordering rule (rising curve: forward > zero > par; falling: reversed). This links to Ch. 3.
6. **Forward lock-in table**: borrow/lend cash flows at 0, x and y that net to a forward loan.

## Validation targets
All reproduced during mapping:
- Ex. 2.2: B(0,3) = 0.863838. Ex. 2.3: PV = 0.961538.
- Ex. 2.4: P = 926.3991. Ex. 2.5: P = 1,000. Ex. 2.6: perpetuity = 2,000.
- Ex. 2.7: real rate = 2.94118 %. Ex. 2.10: 106.1678 (6.1678 % EAR). Ex. 2.11: EAY = 5.5756 %.
- Ex. 2.12: 1.140253. Ex. 2.13: 75.3143. Ex. 2.14: 6.1837 %.
- Ex. 2.15: current yield 7.78 % / 6.36 %.
- Ex. 2.16: 103-23 → y_2 = 6 % (exact price 103.71875 gives 5.998 %; the book rounds to 103.72; tolerance 0.5 bp on the rounded price).
- Ex. 2.17: y = 9.601 %. Ex. 2.18: R(0,2) = 4.26 %.
- Remark 2.3: price 87.57, terminal value 116.55, realized return 10 %.
- Remark 2.5: full table of F(0,1,k), k = 1..9: 5.002, 5.504, 5.670, 5.878, 6.104, 6.191, 6.289, 6.394, 6.503 % (tolerance 0.0005 %).
- Property tests: price = par when c = y, for all frequencies; the par yield prices a par bond; zero/forward/par
  ordering on monotone curves (proved in the Ch. 3 exercises).

## Guided experiments ("Try this")
- Set the coupon equal to the yield, then move the maturity. Predict the price before looking.
- At 10 % yield, change the reinvestment rate to 5 %. Is the realized return above or below 10 %? Why?
- Flip the preset from rising to inverted. Which curve is now on top: zero, forward or par?
- Increase the compounding frequency at a fixed nominal rate. How much does going from daily to continuous change the result?
- Two 10-year bonds, 2 % and 10 % coupons, on a rising curve: which has the higher YTM? (coupon effect)

## Common pitfalls
- Mixing compounding conventions (comparing a semiannual yield with an annual one).
- Reading the YTM as the return you will earn.
- Using the YTM of a 10-year coupon bond as the 10-year discount rate.
- Forgetting that F(0,1,2) in the book's notation means *starting in 1 year, lasting 2 years*.

## Exercises
1. (numeric check) Price a semiannual bond the learner configures, and its YTM back from the price.
2. (numeric check) Effective annual equivalent of a quoted 5.5 % semiannual yield.
3. (numeric check) From a preset zero curve, compute F(0,2,1) and the 3-year par yield.
4. (explain) Using the realized-return chart, explain when a buy-and-hold investor actually earns the YTM.
5. (explain) Why the par curve lies below the zero curve when the curve rises.

## Data needs
Synthetic curves via presets; book example values as fixtures. No precompute.

## Open questions / ambiguities
- Day-count/accrual for fractional periods is not covered in Ch. 2. Proposal: integer periods on this page,
  and fractional periods reuse the Ch. 1 accrual code.
- The book's forward notation F(0,x,θ) uses residual maturity θ, not end date. Proposal: keep the book's notation
  and add an explicit "start/end" label in the UI.
