"""Smoke test: a minimal page using every widget renders and reacts to a slider."""
import inspect
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = str(Path(__file__).resolve().parents[2])


def _page():
    import sys
    sys.path.insert(0, ROOT)  # noqa: F821  (ROOT is prepended to the script source)
    import numpy as np
    import streamlit as st
    from shared import plotting, widgets as w

    w.section("Intuition")
    p = w.parameter_panel([w.Param("a", "Slope a", 0.0, 2.0, 1.0, 0.1),
                           w.Param("n", "Points n", 10, 100, 50, 10)])
    x = np.linspace(0, 1, p["n"])
    st.plotly_chart(plotting.line_chart(x, {"y": p["a"] * x}, title="Line", x_label="x", y_label="y"))
    w.equation(r"y = a x", {"a": "slope"}, label="Eq. 1.1")
    w.metric_row({"slope": p["a"]})
    w.what_to_notice(["Slope moves."])
    w.exercises([w.Exercise("Q?", "A.")])
    w.source_reference("Demo", "§1", ["Eq. 1.1"])


def test_page_renders_and_reacts():
    src = f"ROOT = {ROOT!r}\n" + inspect.getsource(_page) + "\n_page()\n"
    at = AppTest.from_string(src)
    at.run()
    assert not at.exception
    assert at.metric[0].value == "1"
    at.sidebar.slider[0].set_value(1.5).run()
    assert not at.exception
    assert at.metric[0].value == "1.5"


def test_check_answer_tolerance():
    from shared.widgets import Exercise, check_answer
    ex = Exercise("q", "a", numeric_answer=4.7288, tolerance=2e-3)
    assert check_answer(4.7300, ex)
    assert not check_answer(4.74, ex)
