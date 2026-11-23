"""Ch. 1 validation: reproduce the book's worked examples (Martellini et al. 2003, §1.1–1.2).

Tolerance: half a unit in the last digit the book prints, unless stated otherwise.
"""
from datetime import date

import numpy as np
import pytest

from core import conventions as cv
from core import indexed, money_market as mm, repo


# --- §1.1.1 day counts ---------------------------------------------------------------------

def test_30_360_day_examples():
    assert cv.days_30_360(date(2001, 1, 1), date(2001, 3, 25)) == 84
    assert cv.days_30_360(date(2001, 1, 1), date(2001, 12, 6)) == 335
    assert cv.actual_days(date(2001, 1, 1), date(2001, 3, 25)) == 83
    assert cv.actual_days(date(2001, 1, 1), date(2001, 12, 6)) == 339


@pytest.mark.parametrize("conv, expected", [
    ("ACT/ACT", 2.0904), ("ACT/365", 2.0931), ("ACT/360", 2.1222), ("30/360", 2.0888)])
def test_year_fraction_book_period(conv, expected):
    # The book truncates to 4 decimals (2.09315 -> 2.0931, 2.08889 -> 2.0888), so allow 1e-4.
    yf = cv.year_fraction(date(1999, 8, 1), date(2001, 9, 3), conv)
    assert yf == pytest.approx(expected, abs=1e-4)
    assert int(yf * 1e4) / 1e4 == pytest.approx(expected)


def test_30_360_month_end_rules():
    # D1 = 31 is treated as 30; D2 = 31 becomes 30 only when D1 >= 30.
    assert cv.days_30_360(date(2001, 1, 31), date(2001, 3, 31)) == 60
    assert cv.days_30_360(date(2001, 1, 15), date(2001, 3, 31)) == 76


# --- Example 1.4 / 1.5 / 1.6 ---------------------------------------------------------------

def test_example_1_4_accrued_interest():
    ai = cv.accrued_interest(0.035, 2, date(2006, 11, 15), date(2001, 12, 11), "ACT/ACT")
    assert ai.previous_coupon == date(2001, 11, 15)
    assert ai.next_coupon == date(2002, 5, 15)
    assert ai.days_accrued == 26 and ai.days_in_period == 181
    assert ai.coupon_per_period == pytest.approx(1.75)
    assert ai.accrued == pytest.approx(0.25138, abs=5e-6)
    gross = cv.gross_price(96.15625, ai.accrued)
    assert gross == pytest.approx(96.40763, abs=5e-6)
    assert gross / 100 * 1_000_000 == pytest.approx(964_076.3, abs=0.05)


def test_example_1_5_32nds():
    assert cv.from_32nds("98-28") == 98.875
    assert cv.to_32nds(98.875) == "98-28"
    assert cv.from_32nds("96-05") == 96.15625  # Ex. 1.4 clean price
    assert cv.from_32nds("98-28+") == pytest.approx(98 + 28.5 / 32)


def test_example_1_6_cash_flow_schedule():
    flows = cv.cash_flow_schedule(0.035, 2, date(2006, 11, 15), date(2001, 12, 11), face=1_000_000)
    assert len(flows) == 10
    assert flows[0] == (date(2002, 5, 15), 17_500)
    assert flows[-1] == (date(2006, 11, 15), 1_017_500)
    assert all(cf == 17_500 for _, cf in flows[:-1])


def test_problem_1_4_setup_all_bases():
    """End-of-chapter Exercise 1.4 setup (10 % annual, mat. 04/15/08, settle 10/25/99).

    Book gives no answers; values are derived by hand and serve as the page's answer checks.
    """
    args = (0.10, 1, date(2008, 4, 15), date(1999, 10, 25))
    res = {c: cv.accrued_interest(*args, c).accrued for c in cv.CONVENTIONS}
    assert res["ACT/ACT"] == pytest.approx(10 * 193 / 366)
    assert res["ACT/365"] == pytest.approx(10 * 193 / 365)
    assert res["ACT/360"] == pytest.approx(10 * 193 / 360)
    assert res["30/360"] == pytest.approx(10 * 190 / 360)


# --- clean vs. gross price behaviour (property tests) --------------------------------------

def test_clean_equals_gross_on_coupon_date_and_par_at_coupon_yield():
    mat = date(2006, 11, 15)
    on_cpn = date(2002, 5, 15)
    g = cv.gross_price_from_yield(0.035, 2, mat, on_cpn, 0.05)
    c = cv.clean_price_from_yield(0.035, 2, mat, on_cpn, 0.05)
    assert g == pytest.approx(c)
    # yield = coupon -> clean price exactly 100 on a coupon date
    assert cv.clean_price_from_yield(0.035, 2, mat, on_cpn, 0.035) == pytest.approx(100.0, abs=1e-10)


def test_gross_price_drops_by_coupon_across_payment_date():
    mat = date(2006, 11, 15)
    before = cv.gross_price_from_yield(0.035, 2, mat, date(2002, 5, 14), 0.05)
    after = cv.gross_price_from_yield(0.035, 2, mat, date(2002, 5, 15), 0.05)
    clean_before = cv.clean_price_from_yield(0.035, 2, mat, date(2002, 5, 14), 0.05)
    # Gross drops by the coupon (1.75) less one day of accretion at 5 % (~0.013).
    assert before - after == pytest.approx(1.75 - 0.05 / 365 * before, abs=2e-3)
    assert abs(clean_before - after) < 0.01                # clean price is continuous


# --- §1.2.3–1.2.7 money market -------------------------------------------------------------

def test_example_1_17():
    assert mm.discount_yield(9_800, 10_000, 90, 360) == pytest.approx(0.08)


def test_example_1_18():
    assert mm.price_from_discount_yield(0.0164, 101, 360) == pytest.approx(99.5399, abs=5e-5)
    assert cv.actual_days(date(2001, 12, 17), date(2002, 3, 28)) == 101


def test_example_1_19():
    yd = mm.discount_yield(99, 100, 62, 365)
    assert yd == pytest.approx(0.05887, abs=5e-6)
    assert mm.mm_from_discount(yd, 62, 365) == pytest.approx(0.05947, abs=5e-6)
    # the conversion formula equals the simple return on the price paid
    assert mm.money_market_yield(99, 100, 62, 365) == pytest.approx(mm.mm_from_discount(yd, 62, 365))
    assert mm.discount_from_mm(mm.mm_from_discount(yd, 62, 365), 62, 365) == pytest.approx(yd)


def test_example_1_20():
    assert mm.price_from_mm_yield(0.03172, 80, 360) == pytest.approx(99.30, abs=5e-3)
    assert cv.actual_days(date(2001, 12, 17), date(2002, 3, 7)) == 80


def test_example_1_21_cd():
    assert cv.actual_days(date(2001, 7, 27), date(2002, 4, 29)) == 276
    assert cv.actual_days(date(2001, 8, 13), date(2002, 4, 29)) == 259
    p = mm.cd_price(0.0427, 276, 0.0419, 259, 360)
    assert p == pytest.approx(100.25, abs=5e-3)
    assert p / 100 * 80 == pytest.approx(80.201, abs=5e-4)  # EUR millions


def test_example_1_22_bankers_acceptance():
    assert cv.actual_days(date(2001, 12, 14), date(2002, 4, 10)) == 117
    p = mm.price_from_discount_yield(0.019, 117, 360)
    assert p == pytest.approx(99.3825, abs=5e-5)
    assert p / 100 * 30 == pytest.approx(29.815, abs=5e-4)


def test_example_1_23_commercial_paper():
    assert cv.actual_days(date(2001, 10, 11), date(2002, 1, 15)) == 96
    mv = mm.price_from_mm_yield(0.0362, 96, 360, face=70_000_000)
    assert mv == pytest.approx(69_330_727, abs=0.5)


def test_example_1_24_deposit():
    assert mm.deposit_repayment(100.0, 0.0335, 90, 360) == pytest.approx(100.8375)


def test_mm_yield_exceeds_discount_yield():
    for n in (30, 90, 180, 360):
        for yd in (0.01, 0.05, 0.10):
            assert mm.mm_from_discount(yd, n) > yd


# --- §1.1.1 floaters and inflation-indexed bonds -------------------------------------------

def test_example_1_10_and_1_11_coupons():
    idx = np.array([0.03, 0.05, 0.09])
    np.testing.assert_allclose(indexed.floater_coupon(idx, additive_margin=0.002), idx + 0.002)
    np.testing.assert_allclose(indexed.inverse_floater_coupon(idx, 0.16, 2.0), [0.10, 0.06, 0.0])


def test_dir_interpolation_endpoints():
    # first day of month -> CPI_{m-3}; interpolates linearly through the month
    assert indexed.daily_inflation_reference(date(2001, 4, 1), 100.0, 101.0) == 100.0
    assert indexed.daily_inflation_reference(date(2001, 4, 26), 100.0, 101.0) == pytest.approx(100 + 25 / 30)


def test_indexed_bond_zero_inflation_is_plain_bond():
    cf = indexed.indexed_bond_cash_flows(100, 0.03, 5, 0.0)
    np.testing.assert_allclose(cf["coupon"], 3.0)
    assert cf["redemption"][-1] == pytest.approx(100.0)


def test_indexed_bond_scales_with_cpi():
    cf = indexed.indexed_bond_cash_flows(100, 0.03, 10, 0.02)
    assert cf["index_ratio"][-1] == pytest.approx(1.02 ** 10)
    assert cf["redemption"][-1] == pytest.approx(100 * 1.02 ** 10)


# --- §1.2.8 repo -----------------------------------------------------------------------------

def test_example_1_25_repo():
    # The book accrues the Bund coupon as 5 x 117/360 here (see map open question).
    t = repo.repo_trade(1_000_000, 104.11, 5 * 117 / 360, 0.04, 30)
    assert t.cash_start == pytest.approx(1_057_350, abs=0.5)
    assert t.cash_end == pytest.approx(1_060_875, abs=1.0)  # exact 1,060,874.5; book rounds


def test_example_1_26_carry():
    long = repo.daily_carry_long(1_000_000, 0.05, 1_057_350, 0.04)
    assert long.coupon_income == pytest.approx(138.89, abs=5e-3)
    assert long.repo_cost == pytest.approx(117.48, abs=5e-3)
    assert long.net == pytest.approx(21.41, abs=5e-3)
    short = repo.daily_carry_short(1_000_000, 0.05, 1_057_350, 0.04)
    assert short.net == pytest.approx(-21.41, abs=5e-3)


def test_breakeven_repo_rate_zeroes_carry():
    r = repo.breakeven_repo_rate(1_000_000, 0.05, 1_057_350)
    assert repo.daily_carry_long(1_000_000, 0.05, 1_057_350, r).net == pytest.approx(0.0, abs=1e-9)
    assert r == pytest.approx(0.0472881, abs=1e-6)
