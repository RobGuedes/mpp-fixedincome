"""Money-market instruments: T-bills, CDs, bankers' acceptances, commercial paper, deposits.

Source: Martellini, Priaulet & Priaulet (2003), §1.2.3–1.2.7, Examples 1.17–1.24.

All rates are decimals (0.08 for 8 %). ``n`` is calendar days to maturity, ``basis`` the year
basis B (360 or 365). These instruments use *simple* interest: no compounding within the year.
"""
from __future__ import annotations


def _check(n: float, basis: float) -> None:
    if n <= 0:
        raise ValueError("days to maturity n must be positive")
    if basis not in (360, 365):
        raise ValueError("year basis must be 360 or 365")


def discount_yield(price: float, face: float, n: float, basis: float = 360) -> float:
    """Yield on a discount basis: y_d = (F − P)/F · B/n (§1.2.3, Example 1.17).

    The discount is expressed as a fraction of the *face value*, not of the amount invested.
    """
    _check(n, basis)
    return (face - price) / face * basis / n


def price_from_discount_yield(y_d: float, n: float, basis: float = 360, face: float = 100.0) -> float:
    """P = F·(1 − n·y_d/B) (§1.2.3, Examples 1.18, 1.22)."""
    _check(n, basis)
    return face * (1.0 - n * y_d / basis)


def money_market_yield(price: float, face: float, n: float, basis: float = 360) -> float:
    """Yield on a money-market basis, the simple return on the amount invested:
    y_m = (F − P)/P · B/n.  Equivalent to the book's conversion formula (see ``mm_from_discount``).
    """
    _check(n, basis)
    return (face - price) / price * basis / n


def mm_from_discount(y_d: float, n: float, basis: float = 360) -> float:
    """y_m = B·y_d / (B − n·y_d) (§1.2.3, Example 1.19)."""
    _check(n, basis)
    return basis * y_d / (basis - n * y_d)


def discount_from_mm(y_m: float, n: float, basis: float = 360) -> float:
    """Inverse of ``mm_from_discount``: y_d = B·y_m / (B + n·y_m)."""
    _check(n, basis)
    return basis * y_m / (basis + n * y_m)


def price_from_mm_yield(y_m: float, n: float, basis: float = 360, face: float = 100.0) -> float:
    """P = F / (1 + n·y_m/B) (§1.2.3, Examples 1.20, 1.23)."""
    _check(n, basis)
    return face / (1.0 + n * y_m / basis)


def cd_price(coupon: float, n_issue: float, y_m: float, n_settle: float, basis: float = 360,
             face: float = 100.0) -> float:
    """Certificate of deposit paying interest at maturity (§1.2.4, Example 1.21):

    P = F·(1 + c·n_c/B) / (1 + y_m·n_m/B)

    The numerator is the amount repaid at maturity (principal + interest from issue);
    the denominator discounts it from maturity back to settlement at the market yield.
    """
    _check(n_issue, basis)
    _check(n_settle, basis)
    return face * (1.0 + coupon * n_issue / basis) / (1.0 + y_m * n_settle / basis)


def deposit_repayment(amount: float, rate: float, n: float, basis: float = 360) -> float:
    """Principal plus simple interest of an interbank deposit (§1.2.7, Example 1.24)."""
    _check(n, basis)
    return amount * (1.0 + rate * n / basis)
