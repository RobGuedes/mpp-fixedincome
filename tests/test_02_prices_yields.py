"""Ch. 2 validation: reproduce the book's worked examples (Martellini et al. 2003, §2.1–2.3).

Tolerance: half a unit in the last digit the book prints, unless stated otherwise.
"""
import math

import numpy as np
import pytest

from core import pricing as p
from core import rates as r
from core import term_structure as ts
from core.conventions import from_32nds


# --- §2.1–2.2 discounting --------------------------------------------------------------------

def test_example_2_2_discount_factor():
    assert r.discount_factor(0.05, 3) == pytest.approx(0.863838, abs=5e-7)


def test_example_2_3_present_value_and_round_trip():
    pv = r.present_value(1.0, 1, 0.04)
    assert pv == pytest.approx(0.961538, abs=5e-7)
    assert r.future_value(pv, 1, 0.04) == pytest.approx(1.0)


def test_example_2_4_level_coupon_bond():
    assert p.price_from_yield(0.05, 10, 0.06, 1, 1000) == pytest.approx(926.3991, abs=5e-5)
    assert p.price_closed_form(0.05, 10, 0.06, 1, 1000) == pytest.approx(926.3991, abs=5e-5)


def test_example_2_5_par_when_coupon_equals_yield():
    assert p.price_from_yield(0.05, 10, 0.05, 1, 1000) == pytest.approx(1000.0, abs=1e-9)


def test_example_2_6_perpetuity():
    assert p.perpetuity_price(100, 0.05) == pytest.approx(2000.0)
    # The annuity converges to the perpetuity as T grows.
    long_annuity = p.price_closed_form(1.0, 2000, 0.05, 1, 100) - 100 * 1.05 ** -2000
    assert long_annuity == pytest.approx(2000.0, rel=1e-9)


@pytest.mark.parametrize("freq", [1, 2, 4, 12])
@pytest.mark.parametrize("c", [0.0, 0.02, 0.05, 0.12])
@pytest.mark.parametrize("T", [1, 5, 30])
def test_closed_form_matches_sum_and_par_property(freq, c, T):
    """Eq. 2.2 / Remark 2.1 equal the explicit sum; price = par whenever c = y (all frequencies)."""
    for y in (0.0, 0.01, 0.07, 0.15):
        assert p.price_closed_form(c, T, y, freq) == pytest.approx(p.price_from_yield(c, T, y, freq), rel=1e-12)
    if c > 0:
        assert p.price_from_yield(c, T, c, freq) == pytest.approx(100.0, abs=1e-9)


def test_semiannual_remark_2_1_formula():
    # N c / y [1 − (1 + y/2)^−2n] + N (1 + y/2)^−2n with N = 100, c = 8 %, y = 6 %, n = 2 years.
    expected = 100 * 0.08 / 0.06 * (1 - 1.03 ** -4) + 100 * 1.03 ** -4
    assert p.price_from_yield(0.08, 2, 0.06, 2) == pytest.approx(expected, rel=1e-13)


# --- §2.2.3–2.2.5 conventions ------------------------------------------------------------------

def test_example_2_7_fisher():
    assert r.real_rate(0.05, 0.02) == pytest.approx(0.0294118, abs=5e-8)
    assert r.real_rate(0.05, 0.02, exact=False) == pytest.approx(0.03)


def test_examples_2_8_to_2_10_compounding():
    assert r.future_value(100, 2, 0.06, 2) == pytest.approx(100 * 1.03 ** 4)          # Ex. 2.8
    assert r.future_value(100, 3, 0.08, 2) == pytest.approx(100 * 1.04 ** 6)          # Ex. 2.9 (4 % per half-year)
    assert r.future_value(100, 1, 0.06, 12) == pytest.approx(106.1678, abs=5e-5)      # Ex. 2.10
    assert r.effective_annual_rate(0.06, 12) == pytest.approx(0.061678, abs=5e-7)


def test_example_2_11_effective_annual_yield():
    assert r.effective_annual_rate(0.055, 2) == pytest.approx(0.055756, abs=5e-7)


def test_examples_2_12_to_2_14_continuous():
    assert r.future_value(1, 2.5, 0.0525, "continuous") == pytest.approx(1.140253, abs=5e-7)
    assert r.present_value(100, 6.3, 0.045, math.inf) == pytest.approx(75.3143, abs=5e-5)
    assert r.effective_annual_rate(0.06, "continuous") == pytest.approx(0.061837, abs=5e-7)


def test_compounding_converges_to_continuous_and_round_trips():
    ladder = r.compounding_ladder(0.10, [1, 2, 4, 12, 365, 1e6])
    assert np.all(np.diff(ladder) > 0)                               # more frequent → higher EAR
    assert ladder[-1] == pytest.approx(math.exp(0.10) - 1, abs=1e-6)
    for n_from in (1, 2, 12, math.inf):
        for n_to in (1, 4, 365, math.inf):
            back = r.convert_rate(r.convert_rate(0.07, n_from, n_to), n_to, n_from)
            assert back == pytest.approx(0.07, abs=1e-12)


# --- §2.3.1–2.3.2 current yield and YTM -------------------------------------------------------

def test_example_2_15_current_yield():
    assert p.current_yield(0.07, 900, 1000) == pytest.approx(0.0778, abs=5e-5)
    assert p.current_yield(0.07, 1100, 1000) == pytest.approx(0.0636, abs=5e-5)


def test_example_2_16_ytm_semiannual():
    exact = from_32nds("103-23")
    assert exact == pytest.approx(103.71875)
    # Book rounds the price to 103.72 and reports y2 = 6 %. Our root on 103.72 is 5.9985 %: within 0.5 bp.
    assert p.yield_to_maturity(1037.2, 0.08, 2, 2, 1000) == pytest.approx(0.06, abs=5e-5)
    assert p.yield_to_maturity(exact * 10, 0.08, 2, 2, 1000) == pytest.approx(0.06, abs=5e-5)
    assert p.yield_to_maturity(p.price_from_yield(0.08, 2, 0.06, 2), 0.08, 2, 2) == pytest.approx(0.06, abs=1e-12)


def test_example_2_17_ytm_annual():
    assert p.yield_to_maturity(1010, 0.10, 3, 1, 1000) == pytest.approx(0.09601, abs=5e-6)


@pytest.mark.parametrize("freq", [1, 2, 4, 12])
def test_ytm_inverts_price(freq):
    for y in (-0.005, 0.0, 0.03, 0.11):
        price = p.price_from_yield(0.04, 7, y, freq)
        assert p.yield_to_maturity(price, 0.04, 7, freq) == pytest.approx(y, abs=1e-10)


def test_remark_2_3_ytm_as_total_return():
    h = p.horizon_return(0.05, 3, 0.10, reinvestment_rate=0.10)
    assert h.price == pytest.approx(87.57, abs=5e-3)
    assert h.terminal_value == pytest.approx(116.55, abs=5e-3)
    assert h.realized == pytest.approx(0.10, abs=1e-12)


def test_realized_return_vs_reinvestment_rate():
    """YTM is earned only at reinvestment = YTM; above it the investor earns more, below it less."""
    lo = p.horizon_return(0.10, 10, 0.10, 0.05).realized
    mid = p.horizon_return(0.10, 10, 0.10, 0.10).realized
    hi = p.horizon_return(0.10, 10, 0.10, 0.15).realized
    assert mid == pytest.approx(0.10)
    assert lo < mid < hi
    # A zero-coupon bond has nothing to reinvest: realised return = YTM whatever the rate.
    assert p.horizon_return(0.0, 10, 0.10, 0.02).realized == pytest.approx(0.10)


def test_horizon_before_maturity_at_unchanged_yield_earns_ytm():
    h = p.horizon_return(0.06, 10, 0.08, 0.08, horizon_years=4, frequency=2)
    assert h.realized == pytest.approx(0.08, abs=1e-12)
    # A rise in the exit yield lowers the sale price and the realised return.
    assert p.horizon_return(0.06, 10, 0.08, 0.08, 4, 2, exit_yield=0.09).realized < 0.08


# --- §2.3.3–2.3.5 zero, forward and par -------------------------------------------------------

def test_example_2_18_zero_rate():
    assert ts.zero_rate_from_price(92, 2) == pytest.approx(0.0426, abs=5e-5)


def test_remark_2_5_forward_table():
    expected = np.array([5.002, 5.504, 5.670, 5.878, 6.104, 6.191, 6.289, 6.394, 6.503]) / 100
    np.testing.assert_allclose(ts.forward_curve(ts.REMARK_2_5, 1), expected, atol=5e-6)


def test_remark_2_5_break_even_prices_and_returns():
    # 2-year zero: 91.573 today, 95.236 in a year at F(0,1,1); every zero returns R(0,1) = 4 %.
    assert 100 / 1.045 ** 2 == pytest.approx(91.573, abs=5e-4)
    assert 100 / (1 + ts.forward_curve(ts.REMARK_2_5, 1)[0]) == pytest.approx(95.236, abs=5e-4)
    np.testing.assert_allclose(ts.breakeven_one_year_returns(ts.REMARK_2_5), 0.04, atol=1e-12)


def test_remark_2_4_lock_in_and_forward_chain():
    lk = ts.forward_lock_in(ts.REMARK_2_5, 1, 2)
    assert lk.cash_x == pytest.approx(1.04)
    assert lk.cash_y == pytest.approx(1.045 ** 2)
    assert lk.implied_rate == pytest.approx(1.045 ** 2 / 1.04 - 1)
    for x, y in [(1, 3), (2, 7), (4, 10)]:
        z = ts.REMARK_2_5
        assert ts.forward_lock_in(z, x, y).implied_rate == pytest.approx(ts.forward_rate(z[x - 1], x, z[y - 1], y))
    np.testing.assert_allclose(ts.zeros_from_forwards(ts.one_period_forwards(ts.REMARK_2_5)), ts.REMARK_2_5,
                               atol=1e-14)


def test_par_yield_prices_par_bond():
    for z in ts.PRESETS.values():
        for n, c in enumerate(ts.par_yields(z), start=1):
            assert ts.bond_price_from_zeros(c, n, z) == pytest.approx(100.0, abs=1e-10)


@pytest.mark.parametrize("name", ["Rising — Remark 2.5 (4 % → 6.25 %)", "Steep (1 % → 6 %)"])
def test_ordering_rising_curve(name):
    """Rising curve: one-period forward > zero > par (beyond year 1)."""
    z = ts.PRESETS[name]
    fw, par = ts.one_period_forwards(z)[1:], ts.par_yields(z)[1:]
    assert np.all(fw > z[1:]) and np.all(z[1:] > par)


def test_ordering_falling_curve():
    z = ts.PRESETS["Inverted (7 % → 4.5 %)"]
    fw, par = ts.one_period_forwards(z)[1:], ts.par_yields(z)[1:]
    assert np.all(fw < z[1:]) and np.all(z[1:] < par)


def test_flat_curve_all_views_coincide():
    z = ts.PRESETS["Flat 5 %"]
    np.testing.assert_allclose(ts.forward_curve(z, 3), 0.05, atol=1e-14)
    np.testing.assert_allclose(ts.par_yields(z), 0.05, atol=1e-14)
    np.testing.assert_allclose(ts.instantaneous_forward(z, np.linspace(0, 10, 41)), math.log(1.05), atol=1e-12)


def test_instantaneous_forward_is_limit_of_short_forwards():
    """Eq. 2.4: the continuous forward over [s, s+h] tends to f(0,s) as h → 0 (on the spline curve)."""
    z = ts.REMARK_2_5
    s, h = 3.4, 1e-5
    from scipy.interpolate import CubicSpline
    knots = np.arange(0, 11.0)
    spl = CubicSpline(knots, np.concatenate([[0.0], knots[1:] * np.log1p(z)]), bc_type="natural")
    fc = (spl(s + h) - spl(s)) / h
    assert ts.instantaneous_forward(z, np.array([s]))[0] == pytest.approx(fc, abs=1e-6)
    # Integrating f from 0 to k recovers −ln B(0,k) at every knot.
    grid = np.linspace(0, 10, 20001)
    integral = np.concatenate([[0], np.cumsum((ts.instantaneous_forward(z, grid)[1:]
                                               + ts.instantaneous_forward(z, grid)[:-1]) / 2 * np.diff(grid))])
    for k in range(1, 11):
        assert integral[k * 2000] == pytest.approx(-math.log(ts.discount_factors(z)[k - 1]), abs=1e-8)


def test_coupon_effect_on_rising_curve():
    """§2.3.5: same maturity, rising curve → the higher-coupon bond has the lower YTM."""
    z = ts.REMARK_2_5
    ytm = {}
    for c in (0.02, 0.10):
        price = ts.bond_price_from_zeros(c, 10, z)
        ytm[c] = p.yield_to_maturity(price, c, 10)
    assert ytm[0.10] < ytm[0.02] < z[-1]


def test_problem_2_14_setup():
    """End-of-chapter Exercise 2.14 setup (zero curve 4, 4.5, 4.75, 4.9, 5 %; 5-year 5 % bond).

    The book gives no answers; values are derived here and serve as the page's answer checks.
    """
    z = np.array([4.0, 4.5, 4.75, 4.9, 5.0]) / 100
    price = ts.bond_price_from_zeros(0.05, 5, z)
    assert price == pytest.approx(100.1360, abs=5e-5)
    assert p.yield_to_maturity(price, 0.05, 5) == pytest.approx(0.049686, abs=5e-7)


def test_shape_curve_controls():
    base = ts.REMARK_2_5
    np.testing.assert_allclose(ts.shape_curve(base, level_bp=100) - base, 0.01)
    tilt = ts.shape_curve(base, slope_bp=100) - base
    assert tilt[0] == pytest.approx(-0.005) and tilt[-1] == pytest.approx(0.005)
    hump = ts.shape_curve(base, curvature_bp=100) - base
    assert hump[0] == pytest.approx(0) and hump[-1] == pytest.approx(0) and hump.max() <= 0.01 + 1e-12


def test_bisection_trace_converges_to_ytm():
    t, cf = p.cash_flows(0.08, 2, 2, 1000)
    steps = p.ytm_bisection_steps(1037.2, t, cf, 2, 0.0, 0.20, n_steps=30)
    assert steps[-1].mid == pytest.approx(p.irr(1037.2, t, cf, 2), abs=1e-8)
    assert all(s.lo <= s.mid <= s.hi for s in steps)
    with pytest.raises(ValueError):
        p.ytm_bisection_steps(1037.2, t, cf, 2, 0.07, 0.20)
