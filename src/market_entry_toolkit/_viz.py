"""Shared chart styling for the toolkit's three exhibits.

Not one of the five case-analysis modules -- just the small, shared visual
theme (colors, axis cleanup) so `market_sizing.py`,
`competitive_benchmarking.py`, and `financial_feasibility.py` each expose
one plotting function without re-declaring the same palette three times.
Colors are the validated categorical/status slots from the toolkit's
design-system palette (fixed hue order, not reassigned per chart).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

BLUE = "#2a78d6"  # categorical slot 1
ORANGE = "#eb6834"  # categorical slot 2
AQUA = "#1baf7a"  # categorical slot 3
RED = "#e34948"  # categorical slot 8 / also used as a downside cue
GRAY_GRID = "#e1e0d9"  # hairline gridline
GRAY_AXIS = "#c3c2b7"  # baseline/axis
MUTED = "#898781"  # axis/tick labels
PRIMARY_TEXT = "#0b0b0b"
SECONDARY_TEXT = "#52514e"
SURFACE = "#fcfcfb"


def new_figure(figsize: tuple[float, float] = (8, 5)) -> tuple[Figure, Axes]:
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    return fig, ax


def clean_axes(ax: Axes, y_grid: bool = True) -> None:
    """Strip chart-junk: no top/right spines, hairline recessive gridlines,
    muted tick labels -- per the toolkit's chart style guide.
    """
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRAY_AXIS)
    ax.tick_params(colors=MUTED, labelsize=9)
    if y_grid:
        ax.yaxis.grid(True, color=GRAY_GRID, linewidth=1, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
