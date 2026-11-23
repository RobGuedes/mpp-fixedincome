"""Coupons set by formula: floating-rate notes, inverse floaters, inflation-indexed bonds (OATi).

Source: Martellini, Priaulet & Priaulet (2003), §1.1.1 "Nonstandard bonds", Examples 1.10–1.14.
Rates are decimals.
"""
from __future__ import annotations

import calendar
from datetime import date

import numpy as np
from numpy.typing import ArrayLike, NDArray


def floater_coupon(index: ArrayLike, *, additive_margin: float = 0.0,
                   multiplicative_margin: float = 1.0, floor: float | None = None,
                   cap: float | None = None) -> NDArray[np.float64]:
    """Coupon rate of a floating-rate note: m·index + s (§1.1.1, Example 1.10 uses m=1, s=20 bp).

    A negative multiplicative margin makes the note an inverse floater; it then needs a floor
    (usually 0) to keep the coupon non-negative.
    """
    c = multiplicative_margin * np.asarray(index, dtype=float) + additive_margin
    if floor is not None:
        c = np.maximum(c, floor)
    if cap is not None:
        c = np.minimum(c, cap)
    return c


def inverse_floater_coupon(index: ArrayLike, a: float, b: float, floor: float = 0.0) -> NDArray[np.float64]:
    """c = max(a − b·index, floor) (§1.1.1, Example 1.11: a = 16 %, b = 2)."""
    return floater_coupon(index, additive_margin=a, multiplicative_margin=-b, floor=floor)


def inflation_rate(cpi_start: float, cpi_end: float) -> float:
    """IR_{t,t+1} = CPI_{t+1}/CPI_t − 1 (§1.1.1)."""
    return cpi_end / cpi_start - 1.0


def daily_inflation_reference(d: date, cpi_m3: float, cpi_m2: float) -> float:
    """OATi daily inflation reference (§1.1.1):

    DIR_t = CPI_{m−3} + (n_t − 1)/ND_m · (CPI_{m−2} − CPI_{m−3})

    where m is the month of ``d``, n_t its day of month and ND_m the number of days in month m.
    The 3-month lag exists because the CPI is published with a delay.
    """
    nd = calendar.monthrange(d.year, d.month)[1]
    return cpi_m3 + (d.day - 1) / nd * (cpi_m2 - cpi_m3)


def indexed_coupon(face: float, real_coupon: float, dir_t: float, dir_initial: float) -> float:
    """C_t = FV × RC × DIR_t / DIR_initial (§1.1.1)."""
    return face * real_coupon * dir_t / dir_initial


def indexed_redemption(face: float, dir_T: float, dir_initial: float) -> float:
    """RV_T = FV × DIR_T / DIR_initial (§1.1.1). No deflation floor is modelled."""
    return face * dir_T / dir_initial


def indexed_accrued(face: float, real_coupon: float, days_accrued: int, days_in_period: int,
                    dir_t: float, dir_initial: float) -> float:
    """AC_t = FV × RC × (accrued days / days in coupon period) × DIR_t/DIR_initial (§1.1.1)."""
    return face * real_coupon * days_accrued / days_in_period * dir_t / dir_initial


def cpi_path(cpi0: float, annual_inflation: ArrayLike, months: int) -> NDArray[np.float64]:
    """Monthly CPI path from a constant or year-by-year annual inflation rate.

    ``annual_inflation`` is a scalar or one rate per year; growth is spread geometrically over
    the 12 months of each year. Returns ``months + 1`` values starting at ``cpi0``.
    """
    rates = np.atleast_1d(np.asarray(annual_inflation, dtype=float))
    out = np.empty(months + 1)
    out[0] = cpi0
    for k in range(1, months + 1):
        r = rates[min((k - 1) // 12, len(rates) - 1)]
        out[k] = out[k - 1] * (1.0 + r) ** (1.0 / 12.0)
    return out


def indexed_bond_cash_flows(face: float, real_coupon: float, years: int,
                            annual_inflation: ArrayLike, cpi0: float = 100.0) -> dict[str, NDArray]:
    """Annual cash flows of a stylized inflation-indexed bond (simplified OATi).

    Simplification for the simulator: the index ratio on each anniversary is CPI_t/CPI_0 from
    ``cpi_path`` (the 3-month lag and daily interpolation are shown separately with
    ``daily_inflation_reference``). Returns years, index ratios, coupons and redemption.
    """
    cpi = cpi_path(cpi0, annual_inflation, 12 * years)
    t = np.arange(1, years + 1)
    ratio = cpi[12 * t] / cpi0
    coupons = face * real_coupon * ratio
    redemption = np.zeros(years)
    redemption[-1] = face * ratio[-1]
    return {"year": t, "index_ratio": ratio, "coupon": coupons, "redemption": redemption}
