# Bonds and Money-Market Instruments — Martellini, Priaulet & Priaulet, Ch. 1 (§1.1–1.2)

Chapter 1 is mostly descriptive: issuer types, ratings and market sectors. The lab covers the parts a
learner can *compute and manipulate*: cash-flow conventions, quotes, accrued interest, floaters and
inflation-linked bonds, and the money market (T-bills, CDs, repo). The descriptive material becomes
short reference text and a glossary, not a simulator.

## Learning objectives
- Turn a bond's term sheet (coupon, frequency, maturity, day count) into a dated cash-flow schedule.
- Explain clean vs. gross (dirty) price, compute accrued interest, and say why prices are quoted clean.
- Convert between price and yield for discount-basis and money-market-basis instruments, and explain
  why the two yields differ.
- Describe how floating-rate notes, inverse floaters and inflation-indexed bonds set their coupons.
- Compute the cash flows and the daily carry of a repo-financed long or short bond position.

## Core ideas
- A bond is defined by its cash flows; conventions (frequency, day count, settlement lag) decide
  *when* and *how much*, and small convention differences change the numbers.
- The market quotes the **clean** price. The buyer pays the clean price **plus accrued interest**:
  the seller's share of the next coupon. This keeps quoted prices from jumping on coupon dates.
- Money-market instruments are short and usually pay no coupon. Their yields use simple-interest
  conventions: either a *discount* yield (on face value) or a *money-market* yield (on price), with a
  360 or 365 year basis.
- Floating and inflation-linked coupons are set by a formula on a reference index. Those formulas
  determine how the bond reacts to rates or inflation.
- A repo is a collateralized loan. Financing a bond position with repo earns (or costs) the
  difference between coupon accrual and repo interest: the **carry**.

## Explanation outline
1. *Question:* "I bought a bond quoted at 96-05. Why did I pay more than that?" → cash flows,
   conventions, clean vs. gross price, accrued interest (Ex. 1.4, 1.5).
2. Day counts: one calendar period, four year-fractions (Act/Act, Act/365, Act/360, 30/360). Show
   the book's 08/01/1999–09/03/2001 example side by side.
3. The bond family: zero-coupon (strips), fixed coupon, floater, inverse floater, inflation-indexed.
   For each, a cash-flow diagram that responds to an index path.
4. The money market: why it uses simple interest; discount vs. money-market yield; the conversion
   formula and why the gap grows with yield and maturity.
5. Repo: mechanics, then financing long and short positions and the carry sign.

## Key equations
- Accrued interest: AI = coupon per period × (days since last coupon / days in coupon period) (§1.1.1, Ex. 1.4)
- Gross price = clean price + AI (§1.1.1)
- 32nds quote: price = handle + ticks/32 (Ex. 1.5)
- Day-count year fractions (§1.1.1): Act/Act, Act/365, Act/360, 30/360
- Discount-basis yield: y_d = (F − P)/F · B/n; P = F(1 − n·y_d/B) (§1.2.3)
- Money-market yield: y_m = B·y_d/(B − n·y_d); P = F/(1 + n·y_m/B) (§1.2.3)
- CD price: P = F(1 + c·n_c/B)/(1 + y_m·n_m/B) (§1.2.4)
- Inflation ratio: IR = CPI_{t+1}/CPI_t − 1; daily inflation reference DIR_t by linear interpolation
  of CPI_{m−3}, CPI_{m−2}; coupon C_t = FV·RC·DIR_t/DIR_initial; redemption FV·DIR_T/DIR_initial (§1.1.1, OATi)
- Floater coupon: index × multiplicative margin and/or + additive margin; inverse floater
  c = a − b·index, floored at 0 (§1.1.1, Ex. 1.10–1.11)
- Repo: cash = gross price × nominal; repayment = cash·(1 + r_repo·d/360);
  daily carry = coupon·N/360 − cash·r_repo/360 (§1.2.8, Ex. 1.25–1.26)

## Manipulable parameters
| name | meaning | range | default |
|---|---|---|---|
| coupon | annual coupon rate | 0–15 % | 3.5 % |
| frequency | coupons per year | 1, 2, 4 | 2 |
| maturity date / settlement date | dates | any | 11/15/2006, 12/11/2001 (Ex. 1.4) |
| day count | convention | Act/Act, Act/365, Act/360, 30/360 | Act/Act |
| clean price | quoted price | 50–150 | 96.15625 |
| T-bill days n, year basis B | money market | 1–365, 360/365 | 90, 360 |
| discount yield y_d | | 0–20 % | 8 % |
| index path (floater) | reference rate scenario | preset paths + level shift ±500 bp | flat 3 % |
| inverse floater a, b, floor | coupon = a − b·index | a 0–20 %, b 0–3, floor 0 % | 16 %, 2 (Ex. 1.11) |
| inflation path | annual CPI growth | −2 to 10 % | 2 % |
| repo rate, horizon, nominal | | 0–10 %, 1–365 days | 4 %, 30 d, 1 M (Ex. 1.25) |

## Visualizations to build
1. **Clean vs. gross price over time** (sawtooth): with a constant yield, the gross price jumps down by
   the coupon on each payment date while the clean price moves smoothly. Teaches why clean is quoted.
2. **Cash-flow timeline** for any bond type (bars on dates, coloured by coupon/principal), reacting to
   the index or inflation path.
3. **Day-count comparison** bar chart: the same period as a year fraction under four conventions.
4. **Discount vs. money-market yield** as a function of maturity and price; shows the gap widening.
5. **Floater vs. fixed vs. inverse-floater coupons** under an index path; shows the coupon floor.
6. **Repo carry** waterfall: coupon accrual minus repo interest = net daily P&L, for long and short.

## Validation targets
All reproduced to the printed precision (checked during mapping):
- Ex. 1.4: AI = 1.75 × 26/181 = 0.25138; gross = 96.40763; amount paid $964,076.3 per $1 M.
- Ex. 1.5: 98-28 = 98.875.
- Day counts (§1.1.1): 01/01/2001→03/25/2001 = 84 (30/360) vs. 83 actual; →12/06/2001 = 335 vs. 339;
  08/01/1999→09/03/2001 = 2.0904 (Act/Act), 2.0931 (Act/365), 2.1222 (Act/360), 2.0888 (30/360).
- Ex. 1.17: y_d = 8 %. Ex. 1.18: P = 99.5399. Ex. 1.19: y_d = 5.887 %, y_m = 5.947 %.
- Ex. 1.20: P = 99.30. Ex. 1.21: P = 100.25 (EUR 80.201 M). Ex. 1.22: P = 99.3825.
- Ex. 1.23: MV = EUR 69,330,727. Ex. 1.24: $100.8375 M.
- Ex. 1.25: cash EUR 1,057,350; repayment 1,060,875 (exact: 1,060,874.5; tolerance €1).
- Ex. 1.26: coupon accrual €138.89/day, repo cost €117.48/day, net €21.41/day.
Tolerance: half a unit in the last printed digit.

## Guided experiments ("Try this")
- Slide the settlement date across a coupon date: predict what happens to the clean and gross prices.
- Switch the day count from Act/Act to 30/360 for a period that crosses February. Which gives more accrued interest, and why?
- Raise the T-bill maturity from 30 to 360 days at a fixed discount yield. Watch the gap between the
  money-market yield and the discount yield.
- Raise the repo rate until the long position's carry turns negative. What is the break-even repo rate?
- Shift the index path up 200 bp: compare fixed, floater and inverse-floater coupons.

## Common pitfalls
- Treating the quoted (clean) price as the amount paid.
- Reading "98-28" as 98.28.
- Comparing a discount yield with a money-market or bond yield without converting.
- Assuming an inverse floater gains when rates fall: its coupon rises, but its price depends on the
  whole curve (§1.1.1 "Uses").

## Exercises
1. (numeric check) Accrued interest and gross price for a bond defined by the learner's settings,
   e.g. the book's Problem 1.1 type of setup.
2. (numeric check) Convert a 1.64 % discount yield on a 101-day bill to a price and to a money-market yield.
3. (numeric check) Break-even repo rate for the Ex. 1.26 long Bund position.
4. (explain) Why is the money-market yield always above the discount yield for the same bill?

## Data needs
Synthetic only. Book example inputs (dates, coupons, prices) are used as presets and test fixtures.
Business-day calendars: ignore holidays, and document this.

## Open questions / ambiguities
- Ex. 1.25 computes the Bund's accrued interest as 5 × 117/360, although Bunds use Act/Act. We reproduce
  the book's number in the test and show the Act/Act value on the page with a note.
- Settlement lags (T+1, T+3…) are country-specific. Should we model them, or let the learner set the
  settlement date directly? Proposal: set it directly.
- Should the descriptive sections (issuer types, ratings scale, sector breakdowns) be on the page?
  Proposal: a short glossary plus our own rating-scale table only. The book's Bloomberg screenshots and
  2001 sector tables are not reproduced.
