"""Shared plotting style utilities for plasma visualization scripts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Global style helpers
# ---------------------------------------------------------------------------

_COMMON_RC = {
    "figure.autolayout": False,
    "axes.edgecolor": "black",
    "axes.facecolor": "white",
}

_FONT_RC = {
    "font.family": "Times New Roman",
    "font.size": 14,
    "axes.titlesize": 20,
    "axes.labelsize": 18,
    "legend.fontsize": 14,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
}

_STYLE_APPLIED = False


def apply_common_style() -> None:
    """Apply project-wide matplotlib defaults once per session."""
    global _STYLE_APPLIED
    if _STYLE_APPLIED:
        return
    mpl.rcParams.update(_COMMON_RC)
    mpl.rcParams.update(_FONT_RC)
    _STYLE_APPLIED = True


# ---------------------------------------------------------------------------
# Axis and figure layout definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AxisStyle:
    """Controls tick appearance and spine widths for an axis."""

    tick_direction: str = "in"
    major_length: float = 6.0
    major_width: float = 1.2
    minor_length: float = 3.0
    minor_width: float = 0.8
    spine_width: float = 1.2
    enable_minor: bool = True


SUMMARY_AXES_STYLE = AxisStyle()
DISTRIBUTION_AXES_STYLE = AxisStyle(
    major_length=4.0,
    major_width=1.44,
    minor_length=2.0,
    minor_width=0.72,
    spine_width=1.44,
)

DEFAULT_GRID: Mapping[str, Any] = {"linestyle": "--", "alpha": 0.3}


@dataclass(frozen=True)
class FigureLayout:
    """Encapsulates axis geometry in physical inches."""

    ax_width: float = 4.0
    ax_height: float = 3.0
    margin_left: float = 0.8
    margin_right: float = 0.4
    margin_bottom: float = 0.8
    margin_top: float = 0.55
    pad: float = 0.15
    colorbar_width: float = 0.25

    def figure_size(self, include_colorbar: bool = False) -> Tuple[float, float]:
        width = self.margin_left + self.ax_width + self.margin_right
        if include_colorbar:
            width += self.pad + self.colorbar_width
        height = self.margin_top + self.ax_height + self.margin_bottom
        return width, height

    def add_axes(
        self,
        fig: mpl.figure.Figure,
        *,
        include_colorbar: bool = False,
    ) -> Tuple[mpl.axes.Axes, mpl.axes.Axes | None]:
        fig_w, fig_h = self.figure_size(include_colorbar)
        ax = fig.add_axes(
            [
                self.margin_left / fig_w,
                self.margin_bottom / fig_h,
                self.ax_width / fig_w,
                self.ax_height / fig_h,
            ]
        )
        cax = None
        if include_colorbar:
            cax = fig.add_axes(
                [
                    (self.margin_left + self.ax_width + self.pad) / fig_w,
                    self.margin_bottom / fig_h,
                    self.colorbar_width / fig_w,
                    self.ax_height / fig_h,
                ]
            )
        return ax, cax


DEFAULT_LAYOUT = FigureLayout()


def create_figure(
    layout: FigureLayout | None = None,
    *,
    include_colorbar: bool = False,
    dpi: int = 300,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes, mpl.axes.Axes | None]:
    """Create a figure and axes following the provided layout."""
    layout = layout or DEFAULT_LAYOUT
    fig = plt.figure(figsize=layout.figure_size(include_colorbar), dpi=dpi)
    ax, cax = layout.add_axes(fig, include_colorbar=include_colorbar)
    return fig, ax, cax


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------


def style_axes(
    ax: mpl.axes.Axes,
    *,
    axis_style: AxisStyle | None = None,
    grid: bool | Mapping[str, Any] = False,
) -> None:
    """Apply consistent tick, spine, and optional grid styling."""
    style = axis_style or AxisStyle()
    ax.tick_params(
        axis="both",
        which="major",
        direction=style.tick_direction,
        length=style.major_length,
        width=style.major_width,
    )
    if style.enable_minor:
        ax.minorticks_on()
        ax.tick_params(
            axis="both",
            which="minor",
            direction=style.tick_direction,
            length=style.minor_length,
            width=style.minor_width,
        )
    else:
        ax.minorticks_off()
    for spine in ax.spines.values():
        spine.set_linewidth(style.spine_width)

    if isinstance(grid, Mapping):
        opts = dict(DEFAULT_GRID)
        opts.update(grid)
        ax.grid(True, **opts)
    elif grid:
        ax.grid(True, **DEFAULT_GRID)


def style_colorbar(ax: mpl.axes.Axes, *, axis_style: AxisStyle | None = None) -> None:
    """Apply tick styling to a colorbar axis."""
    style = axis_style or AxisStyle()
    ax.tick_params(
        axis="both",
        which="major",
        direction=style.tick_direction,
        length=style.major_length,
        width=style.major_width,
    )
    for spine in ax.spines.values():
        spine.set_linewidth(style.spine_width)


def set_ylabel_with_offset(
    ax: mpl.axes.Axes,
    text: str,
    *,
    pad_pt: float,
    y_frac: float,
) -> None:
    """Place a y-label using physical padding converted to axis coordinates."""
    ax.set_ylabel(text, labelpad=pad_pt)
    ax.yaxis.label.set_verticalalignment("center")
    fig = ax.figure
    fig_w_in = fig.get_size_inches()[0]
    bbox = ax.get_position()
    ax_width_in = bbox.width * fig_w_in
    if ax_width_in == 0:
        offset = 0.0
    else:
        offset = -pad_pt / 72.0 / ax_width_in
    ax.yaxis.set_label_coords(offset, y_frac)


__all__ = [
    "apply_common_style",
    "AxisStyle",
    "SUMMARY_AXES_STYLE",
    "DISTRIBUTION_AXES_STYLE",
    "DEFAULT_GRID",
    "FigureLayout",
    "DEFAULT_LAYOUT",
    "create_figure",
    "style_axes",
    "style_colorbar",
    "set_ylabel_with_offset",
]
