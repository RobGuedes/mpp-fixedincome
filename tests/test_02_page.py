"""Ch. 2 page smoke tests (CLAUDE.md §2 step 5): the page renders, and controls change outputs."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

LAB = Path(__file__).resolve().parents[1]
PAGE = str(LAB / "chapters" / "02_Prices_and_yields.py")


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_page_renders_with_book_values():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    assert not at.exception
    assert _metric(at, "Yield to maturity") == "5.9991 %"      # Ex. 2.16, exact 103-23
    assert _metric(at, "Price") == "92.6399"                   # Ex. 2.4 per 100
    assert _metric(at, "Realised return") == "10.000 %"        # Remark 2.3
    assert _metric(at, "F(0,1,1)") == "5.002 %"                # Remark 2.5


def test_worked_example_rounded_price():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.toggle(key="we2_round").set_value(True).run()
    assert _metric(at, "Yield to maturity") == "5.9985 %"


def test_controls_change_outputs():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.slider(key="py_y").set_value(5.0).run()
    assert _metric(at, "Price") == "100.0000"
    at.slider(key="rr_re").set_value(5.0).run()
    assert float(_metric(at, "Realised return").rstrip(" %")) < 10
    at.selectbox(key="zc_shape").set_value("Inverted (7 % → 4.5 %)").run()
    assert not at.exception
    at.slider(key="zc_x").set_value(2).run()
    assert _metric(at, "F(0,2,1)") != "5.002 %"
    at.selectbox(key="cp_n").set_value("Continuous (∞)").run()
    assert _metric(at, "Effective annual rate") == "6.1837 %"   # Ex. 2.14


def test_preset_switch_updates_controls():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.selectbox(key="py___preset").set_value("Ex. 2.17 — 10 % 3-year at 9.601 % (premium)").run()
    assert not at.exception
    assert at.slider(key="py_T").value == 3
    assert _metric(at, "Price") == "100.9993"  # book: 101 at the rounded 9.601 %
    at.selectbox(key="rr___preset").set_value("Semiannual 6 % 10-year at 5 %, sold after 4 years").run()
    assert not at.exception
    assert _metric(at, "Realised return") == "5.000 %"


def test_numeric_exercise_check():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.number_input(key="ex_3").set_value(6.0072).run()
    assert any("Correct" in s.value for s in at.success)
    at.number_input(key="ex_1").set_value(110.0).run()
    assert any("Not quite" in e.value for e in at.error)
