"""Time value of money and rate conventions: discounting, compounding, continuous rates, real rates.

Source: Martellini, Priaulet & Priaulet (2003), *Fixed-Income Securities*, ch. 2, §2.1–2.2
(Examples 2.2–2.3, 2.7–2.14).

A rate is always quoted *annually* with a compounding frequency ``n`` (times per year).
``n = math.inf`` (or the string ``"continuous"``) means continuous compounding. Rates are decimals
(0.05 for 5 %).
"""
from __future__ import annotations

import math

import numpy as np

CONTINUOUS = math.inf


def _n(n: float | str) -> float:
    if isinstance(n, str):
        if n.lower().startswith("cont"):
            return CONTINUOUS
        raise ValueError(f"Unknown compounding {n!r}")
    if n <= 0:
        raise ValueError("compounding frequency must be positive")
    return float(n)


def growth_factor(rate: float, t: float, n: float | str = 1) -> float:
    """Value at ``t`` of 1 invested today: (1 + R_n/n)^(n t), or e^(R_c t) when continuous (§2.2.4–2.2.5)."""
    n = _n(n)
    if math.isinf(n):
        return math.exp(rate * t)
    return (1.0 + rate / n) ** (n * t)


def discount_factor(rate: float, t: float, n: float | str = 1) -> float:
    """B(0,t) = 1 / growth factor; Example 2.2: B(0,3) at 5 % annual = 0.863838 (§2.1)."""
    return 1.0 / growth_factor(rate, t, n)


def present_value(cash_flow: float, t: float, rate: float, n: float | str = 1) -> float:
    """PV(CF_t) = B(0,t)·CF_t (§2.1, Examples 2.3 and 2.13)."""
    return cash_flow * discount_factor(rate, t, n)


def future_value(amount: float, t: float, rate: float, n: float | str = 1) -> float:
    """FV_t(CF_0) = CF_0 · growth factor (Examples 2.8–2.10, 2.12)."""
    return amount * growth_factor(rate, t, n)


def effective_annual_rate(rate: float, n: float | str) -> float:
    """Equivalent annually compounded rate R = (1 + R_n/n)^n − 1, or e^{R_c} − 1 (§2.2.4–2.2.5).

    Example 2.11: 5.5 % semiannual → 5.5756 %. Example 2.14: 6 % continuous → 6.1837 %.
    """
    return growth_factor(rate, 1.0, n) - 1.0


def rate_from_effective(effective: float, n: float | str) -> float:
    """Inverse of ``effective_annual_rate``: the rate compounded ``n`` times a year with the same growth."""
    n = _n(n)
    if math.isinf(n):
        return math.log1p(effective)
    return n * ((1.0 + effective) ** (1.0 / n) - 1.0)


def convert_rate(rate: float, n_from: float | str, n_to: float | str) -> float:
    """Re-express a rate under another compounding frequency, keeping the growth of money unchanged."""
    return rate_from_effective(effective_annual_rate(rate, n_from), n_to)


def compounding_ladder(rate: float, ns: list[float] | tuple[float, ...]) -> np.ndarray:
    """Effective annual rate of a fixed nominal ``rate`` for each frequency in ``ns`` (convergence chart)."""
    return np.array([effective_annual_rate(rate, n) for n in ns])


def real_rate(nominal: float, inflation: float, exact: bool = True) -> float:
    """Fisher relation 1 + R_real = (1 + R_nominal)/(1 + i) (§2.2.3, Example 2.7: 5 %, 2 % → 2.94118 %).

    ``exact=False`` returns the first-order approximation R_nominal − i.
    """
    if exact:
        return (1.0 + nominal) / (1.0 + inflation) - 1.0
    return nominal - inflation
