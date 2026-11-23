import numpy as np
import pytest

from shared import plotting


def test_title_and_labels_required():
    with pytest.raises(ValueError):
        plotting.line_chart([0, 1], {"a": [0, 1]}, title="", x_label="t", y_label="y")


def test_line_chart_with_band():
    x = np.arange(5)
    fig = plotting.line_chart(x, {"model": x, "rw": x * 0}, title="T", x_label="t (days)",
                              y_label="y (%)", dashed=["rw"])
    plotting.add_band(fig, x, x - 1, x + 1)
    assert len(fig.data) == 3
    assert fig.layout.title.text == "T"
    assert fig.data[1].line.dash == "dash"
