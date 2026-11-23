"""Page smoke tests (CLAUDE.md §2 step 5): the page renders, and controls change outputs."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

LAB = Path(__file__).resolve().parents[1]
PAGE = str(LAB / "chapters" / "01_Instruments_and_conventions.py")


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_page_renders_with_book_values():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    assert not at.exception
    assert _metric(at, "Accrued interest") == "0.25138"
    assert _metric(at, "Gross (paid)") == "96.40763"
    assert _metric(at, "Long carry / day") == "€21.41"


def test_controls_change_outputs():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.radio(key="we_conv").set_value("ACT/360").run()
    assert _metric(at, "Accrued interest") != "0.25138"
    before = _metric(at, "Money-market yield")
    at.slider(key="mm_n").set_value(300).run()
    assert not at.exception
    assert _metric(at, "Money-market yield") != before
    at.slider(key="rp_rr").set_value(6.0).run()
    assert _metric(at, "Long carry / day").startswith("€-")


def test_preset_switch_updates_controls():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.selectbox(key="mm___preset").set_value("Ex. 1.19 — 62-day Japan bill, P = 99").run()
    assert not at.exception
    assert at.slider(key="mm_n").value == 62
    assert _metric(at, "Money-market yield") == "5.9465 %"  # book: 5.947 %


def test_numeric_exercise_check():
    at = AppTest.from_file(PAGE, default_timeout=60).run()
    at.number_input(key="ex_3").set_value(4.7288).run()
    assert any("Correct" in s.value for s in at.success)
    at.number_input(key="ex_3").set_value(4.0).run()
    assert any("Not quite" in e.value for e in at.error)


def test_router_renders_home_with_chrome():
    """The router (app.py) draws the theme, sidebar and banner, then runs the default page (home.py)."""
    at = AppTest.from_file(str(LAB / "app.py"), default_timeout=30).run()
    assert not at.exception
    assert any("interactive lab" in h.value for h in at.markdown) or at.get("html")
