"""Standard plotly chart helpers.

Every helper requires a title and axis labels (with units) so no chart ships without them.
Helpers return ``go.Figure``; pages render with ``st.plotly_chart(fig, width="stretch")``.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import plotly.graph_objects as go

from shared import theme

ArrayLike = Sequence[float] | np.ndarray


def _require(title: str, x_label: str, y_label: str) -> None:
    for name, val in (("title", title), ("x_label", x_label), ("y_label", y_label)):
        if not val or not str(val).strip():
            raise ValueError(f"Chart {name} is required (see CLAUDE.md §5).")


def base_figure(title: str, x_label: str, y_label: str, height: int = 420) -> go.Figure:
    """Empty figure with title, axis labels and the lab template applied."""
    _require(title, x_label, y_label)
    fig = go.Figure()
    fig.update_layout(title=title, height=height, xaxis_title=x_label, yaxis_title=y_label)
    return fig


def line_chart(
    x: ArrayLike,
    series: Mapping[str, ArrayLike],
    *,
    title: str,
    x_label: str,
    y_label: str,
    colors: Mapping[str, str] | None = None,
    dashed: Sequence[str] = (),
    height: int = 420,
) -> go.Figure:
    """One line per entry in ``series`` (name -> y values)."""
    fig = base_figure(title, x_label, y_label, height)
    colors = colors or {}
    for name, y in series.items():
        fig.add_trace(
            go.Scatter(
                x=x, y=y, mode="lines", name=name,
                line=dict(color=colors.get(name), width=2.2, dash="dash" if name in dashed else None),
            )
        )
    return fig


def add_band(
    fig: go.Figure,
    x: ArrayLike,
    lower: ArrayLike,
    upper: ArrayLike,
    *,
    name: str = "Interval",
    color: str | None = None,
) -> go.Figure:
    """Shaded band between ``lower`` and ``upper`` (prediction/confidence intervals)."""
    color = color or theme.ROLE["band"]
    x = np.asarray(x)
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([x, x[::-1]]),
            y=np.concatenate([np.asarray(upper), np.asarray(lower)[::-1]]),
            fill="toself", fillcolor=color, line=dict(width=0),
            name=name, hoverinfo="skip",
        )
    )
    return fig


def add_vline(fig: go.Figure, x: float, label: str, color: str | None = None,
              position: str = "top") -> go.Figure:
    """Vertical reference line, e.g. a forecast origin or an equilibrium value."""
    color = color or theme.ROLE["highlight"]
    fig.add_vline(x=x, line=dict(color=color, dash="dot", width=1.5),
                  annotation_text=label, annotation_position=position)
    return fig


def add_hline(fig: go.Figure, y: float, label: str, color: str | None = None) -> go.Figure:
    """Horizontal reference line, e.g. the true parameter value."""
    color = color or theme.ROLE["truth"]
    fig.add_hline(y=y, line=dict(color=color, dash="dot", width=1.5),
                  annotation_text=label, annotation_position="top left")
    return fig


def scatter(
    x: ArrayLike,
    y: ArrayLike,
    *,
    title: str,
    x_label: str,
    y_label: str,
    name: str = "Data",
    color: str | None = None,
    height: int = 420,
) -> go.Figure:
    color = color or theme.ROLE["data"]
    fig = base_figure(title, x_label, y_label, height)
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name=name,
                             marker=dict(color=color, size=6, opacity=0.7)))
    return fig


def histogram(
    samples: Mapping[str, ArrayLike],
    *,
    title: str,
    x_label: str,
    y_label: str = "Density",
    nbins: int = 50,
    height: int = 420,
) -> go.Figure:
    """Overlaid normalized histograms, e.g. Monte Carlo distributions of an estimator."""
    fig = base_figure(title, x_label, y_label, height)
    for name, s in samples.items():
        fig.add_trace(go.Histogram(x=s, name=name, nbinsx=nbins, histnorm="probability density",
                                   opacity=0.6))
    fig.update_layout(barmode="overlay", hovermode="closest")
    return fig


def bar_chart(
    categories: Sequence[str],
    values: Mapping[str, ArrayLike],
    *,
    title: str,
    x_label: str,
    y_label: str,
    height: int = 420,
) -> go.Figure:
    """Grouped bars: one group per category, one bar per entry in ``values``."""
    fig = base_figure(title, x_label, y_label, height)
    for name, v in values.items():
        fig.add_trace(go.Bar(x=list(categories), y=v, name=name))
    fig.update_layout(barmode="group", hovermode="closest")
    return fig


def heatmap(
    z: np.ndarray,
    labels_x: Sequence[str],
    labels_y: Sequence[str],
    *,
    title: str,
    x_label: str,
    y_label: str,
    diverging: bool = True,
    height: int = 480,
) -> go.Figure:
    """Matrix heatmap (correlation matrices, sensitivity grids). Diverging scale centered at 0."""
    fig = base_figure(title, x_label, y_label, height)
    fig.add_trace(go.Heatmap(
        z=z, x=list(labels_x), y=list(labels_y),
        colorscale="RdBu_r" if diverging else "Blues",
        zmid=0 if diverging else None,
    ))
    fig.update_layout(hovermode="closest")
    return fig
