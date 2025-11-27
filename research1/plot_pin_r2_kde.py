#!/usr/bin/env python3
"""Compare electron-density KDE curves across r2 datasets at a single Pin."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.stats import gaussian_kde

from plot_style import (
    DISTRIBUTION_AXES_STYLE,
    FigureLayout,
    apply_common_style,
    create_figure,
    style_axes,
)

apply_common_style()

LAYOUT = FigureLayout(
    ax_width=4.0,
    ax_height=3.0,
    margin_left=0.8,
    margin_right=0.6,
    margin_bottom=0.8,
    margin_top=0.6,
)
LINE_WIDTH_PT = 1.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare electron-density KDE curves for multiple datasets sharing a Pin value.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/all_values.csv"),
        help="CSV file containing concatenated point values (default: data/all_values.csv)",
    )
    parser.add_argument(
        "--stats",
        type=Path,
        default=Path("data/all_stats.csv"),
        help="CSV file with per-Pin stats (used for validation).",
    )
    parser.add_argument(
        "--pin",
        type=float,
        required=True,
        help="Pin value to compare across datasets.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        required=True,
        help="Dataset names (r2=...) to include in the comparison.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output image path; omit to show the figure interactively.",
    )
    return parser.parse_args()


def load_values(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Values CSV not found: {path}")
    df = pd.read_csv(path)
    needed = {"dataset", "pin", "field_name", "value"}
    missing = needed.difference(df.columns)
    if missing:
        raise SystemExit(f"Values CSV missing columns: {', '.join(sorted(missing))}")
    mask = df["field_name"].str.contains("electron_density", case=False, na=False)
    df = df.loc[mask, ["dataset", "pin", "value"]].copy()
    df = df[np.isfinite(df["value"]) & (df["value"] > 0)]
    if df.empty:
        raise SystemExit("No positive electron-density values available.")
    return df


def validate_datasets(stats_path: Path, datasets: List[str], pin_value: float) -> None:
    if not stats_path.exists():
        return
    df = pd.read_csv(stats_path, usecols=["dataset", "pin"])
    mask = np.isclose(df["pin"], pin_value, atol=1e-6)
    available = set(df.loc[mask, "dataset"].astype(str))
    missing = [ds for ds in datasets if ds not in available]
    if missing:
        raise SystemExit(
            "Pin {} not available in datasets: {}".format(pin_value, ", ".join(missing))
        )


def gather_kde_inputs(df: pd.DataFrame, datasets: List[str], pin_value: float) -> Dict[str, np.ndarray]:
    result: Dict[str, np.ndarray] = {}
    for dataset in datasets:
        mask = (df["dataset"] == dataset) & np.isclose(df["pin"], pin_value, atol=1e-6)
        subset = df.loc[mask]
        values = subset["value"].to_numpy(dtype=float)
        values = values[np.isfinite(values) & (values > 0)]
        if values.size < 2:
            raise SystemExit(
                f"Dataset '{dataset}' has insufficient positive values at Pin={pin_value}."
            )
        result[dataset] = np.log10(values)
    return result


def plot_kde_curves(kde_inputs: Dict[str, np.ndarray], pin_value: float, output: Path | None) -> None:
    fig, ax, _ = create_figure(LAYOUT, include_colorbar=False, dpi=300)
    if output is None:
        fig.set_dpi(140)

    cmap = plt.get_cmap("viridis")
    num_curves = max(len(kde_inputs), 1)
    color_cycle = cmap(np.linspace(0.1, 0.9, num_curves))

    handles = []
    for idx, (dataset, values) in enumerate(sorted(kde_inputs.items())):
        kde = gaussian_kde(values)
        x = np.linspace(values.min(), values.max(), 200)
        color = color_cycle[idx % len(color_cycle)]
        handle, = ax.plot(x, kde(x), color=color, lw=LINE_WIDTH_PT, label=dataset)
        handles.append(handle)

    ax.set_xlabel(r"$\log_{10}(\mathrm{Electron~Density}~(1/m^{3}))$")
    ax.set_ylabel("Probability density")
    ax.set_title(f"KDE comparison at $P_{{\\mathrm{{in}}}}$ = {pin_value:g} W")

    style_axes(ax, axis_style=DISTRIBUTION_AXES_STYLE, grid=True)
    if handles:
        ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0.5)

    fig.tight_layout()
    if output is None:
        plt.show()
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=300, bbox_inches="tight")
        print(f"Saved plot to {output}")
    plt.close(fig)


def main() -> None:
    args = parse_args()

    values_df = load_values(args.csv)
    validate_datasets(args.stats, args.datasets, args.pin)
    kde_inputs = gather_kde_inputs(values_df, args.datasets, args.pin)
    plot_kde_curves(kde_inputs, args.pin, args.output)


if __name__ == "__main__":
    main()
