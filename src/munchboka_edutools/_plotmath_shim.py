"""Minimal plotmath shim for development and tests.

This is NOT a full replacement for the real plotmath package. It implements
just enough for the plot directive tests to run:
- plot(): create fig/ax and set up ticks/grid/limits.
- annotate(): arrow annotation on current axes.
- polygon(): draw edges and/or filled polygon.
- make_bar(): draw a simple double-headed measurement bar.
- COLORS: a small named color palette.

If the real plotmath is installed, the directive will use that instead.
"""

from __future__ import annotations

from typing import Iterable, Tuple, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {
    "red": "#d62728",
    "blue": "#1f77b4",
    "green": "#2ca02c",
    "orange": "#ff7f0e",
    "purple": "#9467bd",
    "teal": "#17becf",
    "black": "#000000",
}


def plot(
    functions: List = None,
    fn_labels: bool = False,
    xmin: float = -6,
    xmax: float = 6,
    ymin: float = -6,
    ymax: float = 6,
    xstep: float = 1,
    ystep: float = 1,
    ticks: bool = True,
    grid: bool = True,
    lw: float = 2.5,
    alpha: float | None = None,
    fontsize: int = 20,
):
    fig, ax = plt.subplots()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    if ticks:
        try:
            ax.set_xticks([x for x in frange(xmin, xmax, xstep)])
            ax.set_yticks([y for y in frange(ymin, ymax, ystep)])
        except Exception:
            pass
    else:
        ax.set_xticks([])
        ax.set_yticks([])
    if grid:
        ax.grid(True, which="both", alpha=0.25)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
    return fig, ax


def annotate(xy, xytext, s: str, arc: float = 0.3, fontsize: int = 14):
    ax = plt.gca()
    ax.annotate(
        s,
        xy=xy,
        xytext=xytext,
        arrowprops=dict(arrowstyle="->", connectionstyle=f"arc3,rad={arc}"),
        fontsize=fontsize,
    )


def polygon(
    *pts: Tuple[float, float],
    edges: bool = True,
    color=None,
    facecolor=None,
    alpha=None,
    show_vertices: bool = False,
):
    ax = plt.gca()
    xs = [p[0] for p in pts] + [pts[0][0]]
    ys = [p[1] for p in pts] + [pts[0][1]]
    if facecolor or (color and not edges):
        ax.fill(xs, ys, color=(facecolor or color), alpha=alpha or 0.1)
    if edges:
        ax.plot(xs, ys, color=(color or COLORS.get("black", "black")))
    if show_vertices:
        ax.plot(
            [p[0] for p in pts],
            [p[1] for p in pts],
            "o",
            color=(color or COLORS.get("black", "black")),
        )


def make_bar(xy: Tuple[float, float], length: float, orientation: str = "horizontal"):
    x, y = xy
    ax = plt.gca()
    if orientation.lower().startswith("h"):
        ax.annotate("", xy=(x, y), xytext=(x + length, y), arrowprops=dict(arrowstyle="|-|"))
    else:
        ax.annotate("", xy=(x, y), xytext=(x, y + length), arrowprops=dict(arrowstyle="|-|"))


def frange(start: float, stop: float, step: float):
    vals = []
    if step == 0:
        return vals
    x = start
    # ensure inclusion of stop within floating tolerance
    if start <= stop:
        while x <= stop + 1e-9:
            vals.append(x)
            x += step
    else:
        while x >= stop - 1e-9:
            vals.append(x)
            x -= abs(step)
    return vals
