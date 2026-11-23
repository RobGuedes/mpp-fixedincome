"""Helpers for validating lab results against source reference values (CLAUDE.md §4).

Pure numpy/pandas; no Streamlit. Used from each lab's ``tests/``.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

ArrayLikeF = Sequence[float] | np.ndarray


# --------------------------------------------------------------------------- reference values

@dataclass(frozen=True)
class Reference:
    """A value printed in the source, with where it comes from and the tolerance we accept."""

    name: str
    expected: float
    where: str            # e.g. "Example 5.2, p. 112" or "Table 3, col. 2"
    abs_tol: float = 0.0
    rel_tol: float = 1e-6

    def check(self, actual: float) -> None:
        assert_close(actual, self.expected, abs_tol=self.abs_tol, rel_tol=self.rel_tol,
                     label=f"{self.name} ({self.where})")


def assert_close(actual: float, expected: float, *, abs_tol: float = 0.0, rel_tol: float = 1e-6,
                 label: str = "value") -> None:
    """Assert ``|actual - expected| <= max(abs_tol, rel_tol * |expected|)`` with a readable message.

    Books print rounded numbers: set ``abs_tol`` to half the last printed digit
    (e.g. 0.005 for a value printed with 2 decimals).
    """
    tol = max(abs_tol, rel_tol * abs(expected))
    diff = abs(float(actual) - float(expected))
    if not np.isfinite(actual) or diff > tol:
        raise AssertionError(f"{label}: got {actual!r}, expected {expected!r} (|diff|={diff:.3g} > tol={tol:.3g})")


def compare_table(actual: pd.DataFrame, expected: pd.DataFrame, *, abs_tol: float) -> pd.DataFrame:
    """Element-wise comparison of a reproduced table vs the source's table.

    Returns a frame of absolute differences; raises if any cell exceeds ``abs_tol``.
    Indices/columns must match exactly.
    """
    if not actual.index.equals(expected.index) or not actual.columns.equals(expected.columns):
        raise AssertionError("Table shape/labels differ from the source table.")
    diff = (actual.astype(float) - expected.astype(float)).abs()
    bad = diff[diff > abs_tol].stack()
    if len(bad):
        cells = ", ".join(f"[{r}, {c}]={v:.3g}" for (r, c), v in bad.items())
        raise AssertionError(f"Cells exceed tol={abs_tol}: {cells}")
    return diff


# --------------------------------------------------------------------------- forecasting

def assert_no_lookahead(origins: Sequence, info_sets: Iterable[pd.Index | Sequence]) -> None:
    """Each forecast made at ``origins[i]`` may only use observations dated ``<= origins[i]``.

    ``info_sets[i]`` are the timestamps of the data actually used to build forecast ``i``.
    """
    for i, (origin, used) in enumerate(zip(origins, info_sets, strict=True)):
        used = pd.Index(used)
        if len(used) and used.max() > origin:
            raise AssertionError(f"Look-ahead at forecast {i}: origin={origin}, used data up to {used.max()}")


def errors_by_horizon(y_true: pd.DataFrame, y_pred: pd.DataFrame) -> pd.DataFrame:
    """RMSE and MAE per horizon. Inputs: rows = forecast origins, columns = horizons (1..H)."""
    if not y_true.columns.equals(y_pred.columns):
        raise ValueError("Horizon columns must match.")
    err = y_pred - y_true
    return pd.DataFrame({
        "RMSE": np.sqrt((err ** 2).mean()),
        "MAE": err.abs().mean(),
        "n": err.notna().sum(),
    })


def empirical_coverage(y: ArrayLikeF, lower: ArrayLikeF, upper: ArrayLikeF) -> float:
    """Share of observations inside ``[lower, upper]`` — compare against the nominal level."""
    y, lo, up = (np.asarray(a, dtype=float) for a in (y, lower, upper))
    return float(np.mean((y >= lo) & (y <= up)))


def coverage_ci(nominal: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Binomial ~95% band for empirical coverage under correct calibration."""
    se = np.sqrt(nominal * (1 - nominal) / n)
    return nominal - z * se, nominal + z * se


# --------------------------------------------------------------------------- financial ML

def assert_no_label_overlap(
    train_label_spans: Mapping | Sequence[tuple],
    test_spans: Sequence[tuple],
    embargo: pd.Timedelta | float = 0,
) -> None:
    """Purged/embargoed CV check: no training label window overlaps a test window (+ embargo).

    Spans are ``(start, end)`` inclusive. ``train_label_spans`` may be a mapping id -> span.
    The embargo extends each test window forward: training labels may not *start* within
    ``(test_end, test_end + embargo]``.
    """
    spans = list(train_label_spans.values()) if isinstance(train_label_spans, Mapping) else list(train_label_spans)
    for t0, t1 in test_spans:
        t1e = t1 + embargo
        for s0, s1 in spans:
            if s0 <= t1e and s1 >= t0:
                raise AssertionError(
                    f"Leakage: train label [{s0}, {s1}] overlaps test [{t0}, {t1}] (+embargo -> {t1e})")


def assert_time_ordered(timestamps: Sequence) -> None:
    """Events (e.g. barrier touches) must be resolved in non-decreasing time order."""
    ts = pd.Index(timestamps)
    if not ts.is_monotonic_increasing:
        raise AssertionError("Events are not in time order.")


# --------------------------------------------------------------------------- reproducibility

def rng(seed: int = 42) -> np.random.Generator:
    """The one way to get randomness in labs: an explicit, seeded Generator."""
    return np.random.default_rng(seed)

