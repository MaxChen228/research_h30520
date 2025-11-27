#!/usr/bin/env python3
"""Plot electron-density probability distributions for a Pin range."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

from plot_style import (
    DISTRIBUTION_AXES_STYLE,
    FigureLayout,
    apply_common_style,
    create_figure,
    set_ylabel_with_offset,
    style_axes,
    style_colorbar,
)

apply_common_style()

LAYOUT = FigureLayout(
    ax_width=4.0,
    ax_height=3.0,
    margin_left=0.8,
    margin_right=0.4,
    margin_bottom=0.8,
    margin_top=0.55,
    pad=0.15,
    colorbar_width=0.25,
)
LINE_WIDTH_PT = 1.44
YLABEL_PAD_PT = 35.0
YLABEL_Y_FRAC = 0.4


def load_density_values(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Required CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required_columns = {"dataset", "pin", "field_name", "value"}
    missing = required_columns.difference(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"CSV is missing required columns: {missing_list}")

    mask = df["field_name"].str.contains("electron_density", case=False, na=False)
    filtered = df.loc[mask, ["dataset", "pin", "value"]].copy()
    filtered = filtered[np.isfinite(filtered["value"]) & (filtered["value"] > 0)]
    if filtered.empty:
        raise ValueError("No positive electron-density values found in CSV.")

    return filtered


def select_pin_values(
    df: pd.DataFrame,
    dataset: str,
    pin_min: float | None,
    pin_max: float | None,
) -> Dict[float, np.ndarray]:
    if dataset != "ALL":
        df = df[df["dataset"] == dataset]
        if df.empty:
            raise ValueError(f"Dataset '{dataset}' has no electron-density values.")

    pins = df["pin"].unique()
    if pin_min is not None:
        pins = pins[pins >= pin_min]
    if pin_max is not None:
        pins = pins[pins <= pin_max]

    selected: Dict[float, np.ndarray] = {}
    for pin in sorted(pins):
        values = df.loc[df["pin"] == pin, "value"].to_numpy(dtype=float)
        values = values[np.isfinite(values) & (values > 0)]
        if values.size >= 2:
            selected[float(pin)] = np.log10(values)
    return selected


def plot_distributions(pin_data: Dict[float, np.ndarray], dataset: str, output: Path | None) -> None:
    if not pin_data:
        raise ValueError("No data available in the selected Pin range.")

    fig, ax, cax = create_figure(LAYOUT, include_colorbar=True, dpi=300)
    if output is None:
        fig.set_dpi(140)

    cmap = plt.get_cmap("viridis")
    pins = np.array(sorted(pin_data))
    if (pins <= 0).any():
        raise ValueError('All Pin values must be positive to use a log color scale.')
    norm = mpl.colors.LogNorm(vmin=pins.min(), vmax=pins.max())

    for pin in pins:
        values = pin_data[pin]
        kde = gaussian_kde(values)
        x = np.linspace(values.min(), values.max(), 200)
        ax.plot(x, kde(x), color=cmap(norm(pin)), lw=LINE_WIDTH_PT)

    ax.set_xlabel(r"$\log_{10}(\mathrm{Electron~Density}~(1/m^{3}))$")
    set_ylabel_with_offset(
        ax,
        "Probability density",
        pad_pt=YLABEL_PAD_PT,
        y_frac=YLABEL_Y_FRAC,
    )
    ax.set_title(f"Electron Density Distribution ({dataset})")

    style_axes(ax, axis_style=DISTRIBUTION_AXES_STYLE, grid=True)

    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    if cax is None:
        raise RuntimeError("Colorbar axis missing from figure layout configuration.")
    cbar = fig.colorbar(sm, cax=cax)
    cbar.ax.set_yscale('log')
    cbar.set_label(r"$P_{\mathrm{in}}$ (W)", labelpad=6)
    style_colorbar(cbar.ax, axis_style=DISTRIBUTION_AXES_STYLE)

    fig.tight_layout()
    if output is None:
        plt.show()
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, bbox_inches="tight")
        print(f"Saved plot to {output}")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot electron-density distribution curves for Pins in a given range."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/all_values.csv"),
        help="CSV file containing concatenated point values (default: data/all_values.csv)",
    )
    parser.add_argument(
        "--dataset",
        default="ALL",
        help="Dataset name to plot (default: ALL)",
    )
    parser.add_argument(
        "--pin-min",
        type=float,
        help="Minimum Pin value (inclusive)",
    )
    parser.add_argument(
        "--pin-max",
        type=float,
        help="Maximum Pin value (inclusive)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output image path; omit to show the figure interactively",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    values_df = load_density_values(args.csv)
    try:
        pin_data = select_pin_values(values_df, args.dataset, args.pin_min, args.pin_max)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    output_path = args.output

    plot_distributions(pin_data, args.dataset, output_path)


if __name__ == "__main__":
    main()
