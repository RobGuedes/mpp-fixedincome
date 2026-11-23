"""Repo financing of bond positions.

Source: Martellini, Priaulet & Priaulet (2003), §1.2.8, Examples 1.25–1.26.
Repo interest accrues on an Actual/360 basis. Rates are decimals; prices per 100 face.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoTrade:
    """Cash legs of a repo, with the quantities the page shows step by step."""

    nominal: float
    clean_price: float
    accrued: float
    gross_price: float
    cash_start: float      # cash received by the bond lender (= cash borrower) at the start
    repo_interest: float
    cash_end: float        # cash repaid to repurchase the bond


def repo_trade(nominal: float, clean_price: float, accrued: float, repo_rate: float,
               days: int, basis: float = 360) -> RepoTrade:
    """Start cash = gross price × nominal; end cash = start cash × (1 + r·d/360) (Example 1.25).

    No haircut is applied (the book ignores it).
    """
    gross = clean_price + accrued
    start = gross / 100.0 * nominal
    interest = start * repo_rate * days / basis
    return RepoTrade(nominal, clean_price, accrued, gross, start, interest, start + interest)


@dataclass(frozen=True)
class Carry:
    coupon_income: float   # per day
    repo_cost: float       # per day
    net: float             # per day; > 0 means positive carry for the long


def daily_carry_long(nominal: float, coupon_rate: float, cash_borrowed: float, repo_rate: float,
                     coupon_basis: float = 360, repo_basis: float = 360) -> Carry:
    """Daily carry of a long bond position financed by repo (Example 1.26).

    Earns the coupon accrual on the nominal and pays repo interest on the cash borrowed
    (the gross price). The book accrues the coupon on a 360-day basis in this example.
    """
    income = coupon_rate * nominal / coupon_basis
    cost = cash_borrowed * repo_rate / repo_basis
    return Carry(income, cost, income - cost)


def daily_carry_short(nominal: float, coupon_rate: float, cash_lent: float, reverse_repo_rate: float,
                      coupon_basis: float = 360, repo_basis: float = 360) -> Carry:
    """Daily carry of a short position financed by reverse repo: the mirror image of the long.

    Earns reverse-repo interest on the cash lent and owes the coupon accrual on the bond sold.
    ``Carry.coupon_income`` is reported as the coupon owed; ``net`` = repo interest − coupon.
    """
    owed = coupon_rate * nominal / coupon_basis
    earned = cash_lent * reverse_repo_rate / repo_basis
    return Carry(owed, earned, earned - owed)


def breakeven_repo_rate(nominal: float, coupon_rate: float, cash: float,
                        coupon_basis: float = 360, repo_basis: float = 360) -> float:
    """Repo rate at which the long position's daily carry is exactly zero."""
    return coupon_rate * nominal / coupon_basis * repo_basis / cash
