import numpy as np
import pandas as pd
import pytest

from shared import validation as v


def test_assert_close_respects_abs_tol():
    v.assert_close(1.234, 1.23, abs_tol=0.005)
    with pytest.raises(AssertionError, match="Ex 1"):
        v.assert_close(1.24, 1.23, abs_tol=0.005, label="Ex 1")


def test_reference_check_and_nan():
    v.Reference("x", 2.0, "Table 1", abs_tol=1e-3).check(2.0004)
    with pytest.raises(AssertionError):
        v.assert_close(float("nan"), 0.0, abs_tol=1.0)


def test_compare_table():
    exp = pd.DataFrame({"a": [1.0, 2.0]}, index=["r1", "r2"])
    v.compare_table(exp + 0.001, exp, abs_tol=0.01)
    with pytest.raises(AssertionError, match=r"\[r2, a\]"):
        v.compare_table(exp.assign(a=[1.0, 2.5]), exp, abs_tol=0.01)


def test_no_lookahead():
    idx = pd.date_range("2020-01-01", periods=10)
    origins = [idx[4], idx[5]]
    v.assert_no_lookahead(origins, [idx[:5], idx[:6]])
    with pytest.raises(AssertionError, match="Look-ahead"):
        v.assert_no_lookahead(origins, [idx[:6], idx[:6]])


def test_errors_by_horizon():
    yt = pd.DataFrame({1: [0.0, 0.0], 2: [0.0, 0.0]})
    yp = pd.DataFrame({1: [1.0, -1.0], 2: [2.0, 0.0]})
    out = v.errors_by_horizon(yt, yp)
    assert out.loc[1, "RMSE"] == pytest.approx(1.0)
    assert out.loc[2, "MAE"] == pytest.approx(1.0)


def test_coverage():
    g = v.rng(0)
    y = g.standard_normal(20_000)
    cov = v.empirical_coverage(y, -1.96 * np.ones_like(y), 1.96 * np.ones_like(y))
    lo, hi = v.coverage_ci(0.95, len(y))
    assert lo <= cov <= hi


def test_label_overlap_with_embargo():
    test = [(10, 20)]
    v.assert_no_label_overlap([(0, 9), (25, 30)], test, embargo=3)
    with pytest.raises(AssertionError, match="Leakage"):
        v.assert_no_label_overlap([(5, 10)], test)          # touches test start
    with pytest.raises(AssertionError, match="Leakage"):
        v.assert_no_label_overlap([(22, 30)], test, embargo=3)  # inside embargo


def test_time_ordered():
    v.assert_time_ordered([1, 2, 2, 3])
    with pytest.raises(AssertionError):
        v.assert_time_ordered([1, 3, 2])
