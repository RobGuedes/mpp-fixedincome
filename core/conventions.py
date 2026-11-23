"""Bond market conventions: day counts, coupon schedules, accrued interest, price quotes.

Source: Martellini, Priaulet & Priaulet (2003), *Fixed-Income Securities*, §1.1.1
("Main characteristics of a bond", "Market quotes"), Examples 1.4–1.6.

Conventions implemented
-----------------------
- ``"ACT/ACT"``  — for a *year fraction between two arbitrary dates* this is the ISDA rule: the days
  falling in each calendar year are divided by that year's length (365 or 366). This reproduces the
  book's 08/01/1999 → 09/03/2001 example (2.0904). For *accrued interest* on a bond, Act/Act means
  the ICMA rule: days accrued / days in the current coupon period (Example 1.4).
- ``"ACT/365"``, ``"ACT/360"`` — actual days divided by 365 or 360.
- ``"30/360"``  — US bond basis: every month counts 30 days (D1 = 31 → 30; D2 = 31 → 30 when
  D1 ≥ 30). Reproduces the book's 84-day and 335-day examples.

Holidays and business-day adjustments are ignored (documented limitation).
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

CONVENTIONS: tuple[str, ...] = ("ACT/ACT", "ACT/365", "ACT/360", "30/360")


def actual_days(d1: date, d2: date) -> int:
    """Calendar days from ``d1`` to ``d2`` (negative if ``d2`` < ``d1``)."""
    return (d2 - d1).days


def days_30_360(d1: date, d2: date) -> int:
    """Day count under the 30/360 (US bond basis) rule, §1.1.1."""
    day1, day2 = min(d1.day, 30), d2.day
    if day2 == 31 and day1 == 30:
        day2 = 30
    return 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (day2 - day1)


def _act_act_isda(d1: date, d2: date) -> float:
    if d2 < d1:
        return -_act_act_isda(d2, d1)
    if d1.year == d2.year:
        return actual_days(d1, d2) / (366 if calendar.isleap(d1.year) else 365)
    first = actual_days(d1, date(d1.year + 1, 1, 1)) / (366 if calendar.isleap(d1.year) else 365)
    last = actual_days(date(d2.year, 1, 1), d2) / (366 if calendar.isleap(d2.year) else 365)
    return first + (d2.year - d1.year - 1) + last


def day_count(d1: date, d2: date, convention: str) -> int:
    """Number of days the convention counts between two dates (numerator of the year fraction)."""
    convention = convention.upper()
    if convention == "30/360":
        return days_30_360(d1, d2)
    if convention in CONVENTIONS:
        return actual_days(d1, d2)
    raise ValueError(f"Unknown day-count convention {convention!r}; use one of {CONVENTIONS}")


def year_fraction(d1: date, d2: date, convention: str) -> float:
    """Length of [d1, d2] in years under ``convention`` (§1.1.1 day-count type)."""
    convention = convention.upper()
    if convention == "ACT/ACT":
        return _act_act_isda(d1, d2)
    if convention == "ACT/365":
        return actual_days(d1, d2) / 365
    if convention == "ACT/360":
        return actual_days(d1, d2) / 360
    if convention == "30/360":
        return days_30_360(d1, d2) / 360
    raise ValueError(f"Unknown day-count convention {convention!r}; use one of {CONVENTIONS}")


# --- coupon schedule -------------------------------------------------------------------------

def add_months(d: date, months: int, *, eom: bool = False) -> date:
    """Shift ``d`` by a number of months, clamping the day to the month's length.

    With ``eom=True`` a month-end date stays at month-end (end-of-month rule).
    """
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    last = calendar.monthrange(y, m)[1]
    return date(y, m, last if eom else min(d.day, last))


def coupon_dates(maturity: date, frequency: int, start: date) -> list[date]:
    """All coupon dates strictly after ``start`` up to ``maturity``, generated backwards from maturity.

    The returned list also lets callers find the previous coupon date via ``previous_coupon``.
    """
    if frequency not in (1, 2, 4, 12):
        raise ValueError("frequency must be 1, 2, 4 or 12")
    step = 12 // frequency
    eom = maturity.day == calendar.monthrange(maturity.year, maturity.month)[1]
    out: list[date] = []
    k = 0
    while True:
        d = add_months(maturity, -step * k, eom=eom)
        if d <= start:
            break
        out.append(d)
        k += 1
    return out[::-1]


def previous_coupon(maturity: date, frequency: int, settlement: date) -> date:
    """Last coupon date on or before ``settlement``."""
    step = 12 // frequency
    eom = maturity.day == calendar.monthrange(maturity.year, maturity.month)[1]
    k = 0
    while True:
        d = add_months(maturity, -step * k, eom=eom)
        if d <= settlement:
            return d
        k += 1


@dataclass(frozen=True)
class AccruedInterest:
    """Accrued-interest calculation with its intermediate quantities (for the live worked example)."""

    previous_coupon: date
    next_coupon: date
    days_accrued: int          # numerator under the convention
    days_in_period: int        # Act/Act denominator (actual days in the coupon period)
    coupon_per_period: float   # per 100 face
    accrual_fraction: float    # share of the coupon period (Act/Act) or year fraction (other bases)
    accrued: float             # per 100 face


def accrued_interest(coupon_rate: float, frequency: int, maturity: date, settlement: date,
                     convention: str = "ACT/ACT", face: float = 100.0) -> AccruedInterest:
    """Accrued interest at ``settlement`` (§1.1.1, Example 1.4).

    - Act/Act (ICMA): AI = (c/f)·face · days since last coupon / days in coupon period.
    - Other bases: AI = c·face · year_fraction(last coupon, settlement).

    ``coupon_rate`` is a decimal (0.035 for 3.5 %).
    """
    if settlement >= maturity:
        raise ValueError("settlement must be before maturity")
    prev = previous_coupon(maturity, frequency, settlement)
    nxt = coupon_dates(maturity, frequency, settlement)[0]
    cpp = coupon_rate * face / frequency
    period = actual_days(prev, nxt)
    conv = convention.upper()
    if conv == "ACT/ACT":
        n = actual_days(prev, settlement)
        frac = n / period
        ai = cpp * frac
    else:
        n = day_count(prev, settlement, conv)
        frac = year_fraction(prev, settlement, conv)
        ai = coupon_rate * face * frac
    return AccruedInterest(prev, nxt, n, period, cpp, frac, ai)


def cash_flow_schedule(coupon_rate: float, frequency: int, maturity: date, settlement: date,
                       face: float = 100.0) -> list[tuple[date, float]]:
    """Remaining (date, amount) cash flows after ``settlement`` (Example 1.6)."""
    dates = coupon_dates(maturity, frequency, settlement)
    cpn = coupon_rate * face / frequency
    return [(d, cpn + (face if d == maturity else 0.0)) for d in dates]


# --- quotes ----------------------------------------------------------------------------------

def from_32nds(quote: str) -> float:
    """Convert a US Treasury quote "98-28" (handle-32nds) to decimal (Example 1.5).

    A trailing "+" adds half a 32nd ("98-28+" = 98 + 28.5/32).
    """
    q = quote.strip()
    if "-" not in q:
        return float(q)
    handle, ticks = q.split("-", 1)
    plus = ticks.endswith("+")
    t = float(ticks.rstrip("+")) + (0.5 if plus else 0.0)
    if not 0 <= t < 32:
        raise ValueError(f"32nds part must be in [0, 32): {quote!r}")
    return float(handle) + t / 32


def to_32nds(price: float) -> str:
    """Nearest 32nd representation of a decimal price, e.g. 98.875 → "98-28"."""
    handle = int(price // 1)
    ticks = round((price - handle) * 32)
    if ticks == 32:
        handle, ticks = handle + 1, 0
    return f"{handle}-{ticks:02d}"


def gross_price(clean: float, accrued: float) -> float:
    """Gross (dirty, full) price = clean price + accrued interest (§1.1.1)."""
    return clean + accrued


# --- price path at constant yield (for the clean vs. gross saw-tooth) -------------------------

def gross_price_from_yield(coupon_rate: float, frequency: int, maturity: date, settlement: date,
                           yield_rate: float, face: float = 100.0) -> float:
    """Gross price by the street convention: discount each cash flow at (1 + y/f) per period,
    with a fractional first period w = days to next coupon / days in coupon period.

    Pricing is developed in Ch. 2 (Eq. 2.2); it is used here only to draw how the clean and gross
    prices evolve through time at a constant yield.
    """
    flows = cash_flow_schedule(coupon_rate, frequency, maturity, settlement, face)
    prev = previous_coupon(maturity, frequency, settlement)
    nxt = flows[0][0]
    w = actual_days(settlement, nxt) / actual_days(prev, nxt)
    v = 1.0 / (1.0 + yield_rate / frequency)
    return sum(cf * v ** (w + k) for k, (_, cf) in enumerate(flows))


def clean_price_from_yield(coupon_rate: float, frequency: int, maturity: date, settlement: date,
                           yield_rate: float, face: float = 100.0) -> float:
    """Clean price = gross price − accrued interest (Act/Act ICMA accrual)."""
    g = gross_price_from_yield(coupon_rate, frequency, maturity, settlement, yield_rate, face)
    return g - accrued_interest(coupon_rate, frequency, maturity, settlement, "ACT/ACT", face).accrued
