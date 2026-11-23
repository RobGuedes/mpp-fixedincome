"""Three views of one curve: zero-coupon rates, forward rates and par yields.

Source: Martellini, Priaulet & Priaulet (2003), *Fixed-Income Securities*, ch. 2, §2.3.3–2.3.5:
zero-coupon rates (Example 2.18), forward rates (Eq. 2.3, Remarks 2.4–2.5), the instantaneous forward
rate (Eq. 2.4) and par yields (Eq. 2.5).

Zero rates are annually compounded, R(0,k) for k = 1..n years, passed as an array ``zeros`` with
``zeros[k-1] = R(0,k)``. The book's forward notation is kept: F(0, x, θ) starts at year x and lasts
θ years (θ is the *residual maturity*, not the end date).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import CubicSpline

# The curve of Remark 2.5 (R(0,1)…R(0,10), %), and stylised shapes for the simulator.
REMARK_2_5 = np.array([4.0, 4.5, 5.0, 5.25, 5.5, 5.75, 5.875, 6.0, 6.125, 6.25]) / 100
_k = np.arange(1, 11)
PRESETS: dict[str, np.ndarray] = {
    "Rising — Remark 2.5 (4 % → 6.25 %)": REMARK_2_5,
    "Flat 5 %": np.full(10, 0.05),
    "Inverted (7 % → 4.5 %)": 0.07 - 0.025 * (1 - np.exp(-(_k - 1) / 3)) / (1 - np.exp(-3)),
    "Humped (peak near 3 years)": 0.04 + 0.025 * (_k / 3) * np.exp(1 - _k / 3),
    "Steep (1 % → 6 %)": 0.01 + 0.05 * (1 - np.exp(-(_k - 1) / 4)) / (1 - np.exp(-9 / 4)),
}


def shape_curve(base: np.ndarray, level_bp: float = 0.0, slope_bp: float = 0.0,
                curvature_bp: float = 0.0) -> np.ndarray:
    """Deform a zero curve: parallel shift, tilt (−slope/2 at the short end, +slope/2 at the long end)
    and a hump peaking mid-curve (+curvature at the middle, 0 at both ends). All inputs in bp."""
    base = np.asarray(base, float)
    n = len(base)
    s = np.linspace(0.0, 1.0, n)
    return base + (level_bp + slope_bp * (s - 0.5) + curvature_bp * 4 * s * (1 - s)) / 1e4


def discount_factors(zeros: np.ndarray) -> np.ndarray:
    """B(0,k) = (1 + R(0,k))^(−k), k = 1..n (§2.3.3)."""
    zeros = np.asarray(zeros, float)
    k = np.arange(1, len(zeros) + 1)
    return (1.0 + zeros) ** (-k)


def zero_rate_from_price(price: float, maturity: float, face: float = 100.0) -> float:
    """R(0,t) from a zero-coupon price: price = face/(1 + R)^t (Example 2.18: 92 → 4.26 %)."""
    return (face / price) ** (1.0 / maturity) - 1.0


def forward_rate(r_x: float, x: float, r_y: float, y: float) -> float:
    """Eq. 2.3: F(0, x, y − x) = [(1 + R(0,y))^y / (1 + R(0,x))^x]^(1/(y−x)) − 1. ``x = 0`` gives R(0,y)."""
    if y <= x:
        raise ValueError("the forward period must end after it starts (y > x)")
    return ((1.0 + r_y) ** y / (1.0 + r_x) ** x) ** (1.0 / (y - x)) - 1.0


def _r(zeros: np.ndarray, k: int) -> float:
    return 0.0 if k == 0 else float(zeros[k - 1])


def forward_curve(zeros: np.ndarray, start: int) -> np.ndarray:
    """θ ↦ F(0, start, θ) for θ = 1..n − start (Remark 2.5 table with start = 1)."""
    zeros = np.asarray(zeros, float)
    n = len(zeros)
    if not 0 <= start < n:
        raise ValueError("start must be in [0, n)")
    return np.array([forward_rate(_r(zeros, start), start, zeros[start + th - 1], start + th)
                     for th in range(1, n - start + 1)])


def one_period_forwards(zeros: np.ndarray) -> np.ndarray:
    """F(0, k−1, 1), k = 1..n: the 1-year rate locked in for year k (the first one is R(0,1))."""
    zeros = np.asarray(zeros, float)
    return np.array([forward_rate(_r(zeros, k - 1), k - 1, zeros[k - 1], k) for k in range(1, len(zeros) + 1)])


def zeros_from_forwards(forwards: np.ndarray) -> np.ndarray:
    """Remark 2.4: R(0,t) = [(1 + R(0,1))(1 + F(0,1,1))…(1 + F(0,t−1,1))]^(1/t) − 1."""
    g = np.cumprod(1.0 + np.asarray(forwards, float))
    t = np.arange(1, len(g) + 1)
    return g ** (1.0 / t) - 1.0


def par_yields(zeros: np.ndarray) -> np.ndarray:
    """Eq. 2.5: c(n) = [1 − B(0,n)] / Σ_{i≤n} B(0,i), for n = 1..N (annual coupons)."""
    b = discount_factors(zeros)
    return (1.0 - b) / np.cumsum(b)


def instantaneous_forward(zeros: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Eq. 2.4 on a fine grid: f(0,s) = d/ds [s·R_c(0,s)], continuously compounded.

    The knots ``s·R_c(0,s)`` = −ln B(0,s) at s = 0, 1, …, n are joined by a cubic spline with a
    natural end condition, then differentiated. Interpolation is a modelling choice (Ch. 4 compares
    methods); on a flat curve it returns the flat continuous rate exactly.
    """
    zeros = np.asarray(zeros, float)
    s = np.arange(0, len(zeros) + 1, dtype=float)
    y = np.concatenate([[0.0], s[1:] * np.log1p(zeros)])
    spline = CubicSpline(s, y, bc_type="natural")
    return spline(np.asarray(grid, float), 1)


def bond_price_from_zeros(coupon_rate: float, maturity: int, zeros: np.ndarray, face: float = 100.0) -> float:
    """Eq. 2.1 with annual coupons and maturity ≤ len(zeros): Σ B(0,k)·CF_k."""
    if not 1 <= maturity <= len(zeros):
        raise ValueError("maturity must be between 1 and the curve length")
    b = discount_factors(zeros)[:maturity]
    cf = np.full(maturity, coupon_rate * face)
    cf[-1] += face
    return float(np.dot(b, cf))


@dataclass(frozen=True)
class LockIn:
    """Remark 2.4: borrow 1 until year y and lend 1 until year x, today."""

    x: int
    y: int
    cash_x: float         # received at x: (1 + R(0,x))^x
    cash_y: float         # paid at y: (1 + R(0,y))^y
    implied_rate: float   # (cash_y / cash_x)^(1/(y−x)) − 1 = F(0, x, y − x)


def forward_lock_in(zeros: np.ndarray, x: int, y: int) -> LockIn:
    """Cash flows of the borrow/lend pair that synthesises a forward loan from x to y (Remark 2.4)."""
    zeros = np.asarray(zeros, float)
    if not 1 <= x < y <= len(zeros):
        raise ValueError("need 1 ≤ x < y ≤ n")
    cx = (1.0 + zeros[x - 1]) ** x
    cy = (1.0 + zeros[y - 1]) ** y
    return LockIn(x, y, cx, cy, (cy / cx) ** (1.0 / (y - x)) - 1.0)


def breakeven_one_year_returns(zeros: np.ndarray) -> np.ndarray:
    """Remark 2.5: 1-year return of each k-year zero (k = 2..n) if, in a year, the (k−1)-year rate
    equals today's forward F(0,1,k−1). Every entry equals R(0,1): the forward is the break-even."""
    zeros = np.asarray(zeros, float)
    fw = forward_curve(zeros, 1)
    k = np.arange(2, len(zeros) + 1)
    p0 = (1.0 + zeros[1:]) ** (-k)
    p1 = (1.0 + fw) ** (-(k - 1))
    return p1 / p0 - 1.0
