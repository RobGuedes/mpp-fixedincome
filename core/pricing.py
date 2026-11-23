"""Fixed-coupon bond pricing, yield to maturity, current yield and realised (horizon) return.

Source: Martellini, Priaulet & Priaulet (2003), *Fixed-Income Securities*, ch. 2:
Eq. 2.1 (price = Σ B(0,t)·CF_t), Eq. 2.2 and Remark 2.1 (level-coupon closed form),
§2.3.1 (current yield), §2.3.2 (YTM, Examples 2.16–2.17), Remark 2.3 (YTM as a total return).

Conventions: the bond is valued on a coupon date, so all periods are whole (the page on
Ch. 1 handles fractional first periods). ``frequency`` f is the number of coupons per year, and
yields are quoted annually with compounding f (the market convention for a bond's yield).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq


def _periods(maturity_years: float, frequency: int) -> int:
    k = maturity_years * frequency
    if abs(k - round(k)) > 1e-9 or round(k) < 1:
        raise ValueError("maturity × frequency must be a positive whole number of periods")
    return int(round(k))


def cash_flows(coupon_rate: float, maturity_years: float, frequency: int = 1,
               face: float = 100.0) -> tuple[np.ndarray, np.ndarray]:
    """Times (years) and amounts of a level-coupon bullet bond (§2.1, step 1).

    Coupon per period = c·N/f; the last flow adds the face value N.
    """
    k = _periods(maturity_years, frequency)
    t = np.arange(1, k + 1) / frequency
    cf = np.full(k, coupon_rate * face / frequency)
    cf[-1] += face
    return t, cf


def price_from_discount_factors(amounts: np.ndarray, discount_factors: np.ndarray) -> float:
    """Eq. 2.1: price = Σ B(0,t)·CF_t."""
    return float(np.dot(np.asarray(amounts, float), np.asarray(discount_factors, float)))


def price_from_yield(coupon_rate: float, maturity_years: float, yield_rate: float,
                     frequency: int = 1, face: float = 100.0) -> float:
    """Price discounting every flow at one yield: Σ CF_i / (1 + y/f)^i (§2.3.2, Remark 2.1).

    Example 2.4: c = 5 %, T = 10, y = 6 %, N = 1,000 → 926.3991.
    """
    t, cf = cash_flows(coupon_rate, maturity_years, frequency, face)
    v = 1.0 / (1.0 + yield_rate / frequency)
    return float(np.dot(cf, v ** (t * frequency)))


def price_closed_form(coupon_rate: float, maturity_years: float, yield_rate: float,
                      frequency: int = 1, face: float = 100.0) -> float:
    """Annuity + principal closed form, Eq. 2.2 (f = 1) and Remark 2.1 (f = 2), any f:

    P = (c N / y)·[1 − (1 + y/f)^(−fT)] + N (1 + y/f)^(−fT). For y = 0 the limit c N T + N is used.
    """
    k = _periods(maturity_years, frequency)
    if abs(yield_rate) < 1e-14:
        return coupon_rate * face * maturity_years + face
    d = (1.0 + yield_rate / frequency) ** (-k)
    return coupon_rate * face / yield_rate * (1.0 - d) + face * d


def perpetuity_price(cash_flow: float, yield_rate: float) -> float:
    """Limit T → ∞ of the annuity: P = CF / y (§2.2.2, Example 2.6: 100 / 5 % = 2,000)."""
    if yield_rate <= 0:
        raise ValueError("a perpetuity needs a positive yield")
    return cash_flow / yield_rate


def current_yield(coupon_rate: float, price: float, face: float = 100.0) -> float:
    """y_c = c·N / P (§2.3.1, Example 2.15)."""
    return coupon_rate * face / price


def irr(price: float, times: np.ndarray, amounts: np.ndarray, frequency: int = 1) -> float:
    """Single rate y (compounded ``frequency`` times a year) with Σ CF_t (1 + y/f)^(−f t) = price.

    This is the yield to maturity of any fixed cash-flow stream (§2.3.2). Solved by Brent's method;
    the price is a strictly decreasing function of y for positive flows, so the root is unique.
    """
    times, amounts = np.asarray(times, float), np.asarray(amounts, float)
    if price <= 0:
        raise ValueError("price must be positive")

    def f(y: float) -> float:
        return float(np.dot(amounts, (1.0 + y / frequency) ** (-frequency * times))) - price

    # A price above the undiscounted sum of flows needs a negative yield; search down to −50 %/period.
    lo, hi = -0.5 * frequency, 5.0
    return float(brentq(f, lo, hi, xtol=1e-14, rtol=1e-14, maxiter=500))


@dataclass(frozen=True)
class BisectionStep:
    lo: float
    hi: float
    mid: float
    price_at_mid: float


def ytm_bisection_steps(price: float, times: np.ndarray, amounts: np.ndarray, frequency: int = 1,
                        lo: float = 0.0, hi: float = 0.20, n_steps: int = 12) -> list[BisectionStep]:
    """The book's "trial and error" (§2.3.2) made explicit: halve [lo, hi] until it brackets the YTM.

    Teaching aid for the worked example; ``irr`` is the production solver. Price falls as the yield
    rises, so if the price at the midpoint is above the market price the yield must be higher.
    """
    times, amounts = np.asarray(times, float), np.asarray(amounts, float)

    def pv(y: float) -> float:
        return float(np.dot(amounts, (1.0 + y / frequency) ** (-frequency * times)))

    if not pv(hi) <= price <= pv(lo):
        raise ValueError("the starting interval does not bracket the yield")
    steps = []
    for _ in range(n_steps):
        mid = 0.5 * (lo + hi)
        pm = pv(mid)
        steps.append(BisectionStep(lo, hi, mid, pm))
        if pm > price:
            lo = mid
        else:
            hi = mid
    return steps


def yield_to_maturity(price: float, coupon_rate: float, maturity_years: float,
                      frequency: int = 1, face: float = 100.0) -> float:
    """YTM of a level-coupon bond (§2.3.2). Examples 2.16 (y₂ = 6 %) and 2.17 (y = 9.601 %)."""
    t, cf = cash_flows(coupon_rate, maturity_years, frequency, face)
    return irr(price, t, cf, frequency)


@dataclass(frozen=True)
class HorizonReturn:
    """Decomposition of a buy-and-hold result (Remark 2.3), per ``face`` of nominal."""

    price: float               # price paid at the purchase yield
    coupons: float             # sum of coupons received up to the horizon
    interest_on_interest: float  # what reinvesting those coupons added
    sale_value: float          # value at the horizon of the remaining flows (0 at maturity)
    terminal_value: float      # coupons + interest on interest + sale value
    realized: float            # annualised return, compounded f times a year (comparable to the YTM)


def horizon_return(coupon_rate: float, maturity_years: float, purchase_yield: float,
                   reinvestment_rate: float, horizon_years: float | None = None,
                   frequency: int = 1, face: float = 100.0,
                   exit_yield: float | None = None) -> HorizonReturn:
    """Realised return of buying at ``purchase_yield`` and holding to ``horizon_years`` (Remark 2.3).

    Coupons are reinvested at ``reinvestment_rate`` (compounded f times a year) until the horizon.
    If the horizon is before maturity, the bond is sold at ``exit_yield`` (default: the purchase
    yield, i.e. no change in the bond's yield). The realised return R solves
    P·(1 + R/f)^(f H) = terminal value. It equals the YTM only if every coupon is reinvested at the
    YTM *and* the bond is sold (or redeemed) at the YTM.
    """
    horizon_years = maturity_years if horizon_years is None else horizon_years
    k_total = _periods(maturity_years, frequency)
    k_h = _periods(horizon_years, frequency)
    if k_h > k_total:
        raise ValueError("horizon must not exceed maturity")
    exit_yield = purchase_yield if exit_yield is None else exit_yield
    p0 = price_from_yield(coupon_rate, maturity_years, purchase_yield, frequency, face)
    cpn = coupon_rate * face / frequency
    g = 1.0 + reinvestment_rate / frequency
    # coupon i (i = 1..k_h) is reinvested for k_h − i periods
    fv_coupons = sum(cpn * g ** (k_h - i) for i in range(1, k_h + 1))
    coupons = cpn * k_h
    if k_h == k_total:
        sale = face
    else:
        sale = price_from_yield(coupon_rate, (k_total - k_h) / frequency, exit_yield, frequency, face)
    terminal = fv_coupons + sale
    realized = frequency * ((terminal / p0) ** (1.0 / k_h) - 1.0)
    return HorizonReturn(p0, coupons, fv_coupons - coupons, sale, terminal, realized)
