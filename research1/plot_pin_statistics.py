#!/usr/bin/env python3
"""Plot electron-density statistics for a selected dataset from aggregated CSV data."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:  # pragma: no cover - environment dependency guard
    import matplotlib.pyplot as plt
except ImportError as exc:
    print("Error: matplotlib is required for plotting (pip install matplotlib).", file=sys.stderr)
    raise SystemExit(1) from exc

try:  # pragma: no cover - environment dependency guard
    import numpy as np
except ImportError as exc:
    print("Error: numpy is required for plotting (pip install numpy).", file=sys.stderr)
    raise SystemExit(1) from exc

try:  # pragma: no cover - environment dependency guard
    import pandas as pd
except ImportError as exc:
    print("Error: pandas is required to read the statistics table (pip install pandas).", file=sys.stderr)
    raise SystemExit(1) from exc

from plot_style import SUMMARY_AXES_STYLE, apply_common_style, style_axes

apply_common_style()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot aggregated Pin vs. electron-density statistics from data/all_stats.csv."
    )
    parser.add_argument(
        "--stats",
        default=Path("data/all_stats.csv"),
        type=Path,
        help="CSV file containing aggregated per-Pin statistics (default: data/all_stats.csv)",
    )
    parser.add_argument(
        "--dataset",
        default="ALL",
        help="Dataset name to plot (default: ALL)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output image path; omit to show the figure interactively",
    )
    parser.add_argument(
        "--pin-min",
        dest="pin_min",
        type=float,
        help="Minimum Pin value to include in the plot",
    )
    parser.add_argument(
        "--pin-max",
        dest="pin_max",
        type=float,
        help="Maximum Pin value to include in the plot",
    )
    parser.add_argument(
        "--series",
        choices=["mode", "max", "min", "all"],
        default="all",
        help="Which series to plot (default: all)",
    )
    parser.add_argument(
        "--scale",
        choices=["linear", "log"],
        default="linear",
        help="Axis scaling: linear or log-log (default: linear)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.stats.exists():
        raise SystemExit(f"Statistics file not found: {args.stats}")

    stats_df = pd.read_csv(args.stats)

    required_columns = {"dataset", "pin", "mode", "max", "min"}
    missing = required_columns.difference(stats_df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise SystemExit(f"Statistics file is missing required columns: {missing_list}")

    available_datasets = sorted(stats_df["dataset"].unique())
    if args.dataset not in available_datasets:
        raise SystemExit(
            f"Dataset '{args.dataset}' not found. Available datasets: {', '.join(available_datasets)}"
        )

    stats_df = stats_df[stats_df["dataset"] == args.dataset]

    if args.pin_min is not None:
        stats_df = stats_df[stats_df["pin"] >= args.pin_min]
    if args.pin_max is not None:
        stats_df = stats_df[stats_df["pin"] <= args.pin_max]

    if stats_df.empty:
        raise SystemExit("No entries remain after applying the Pin range filter.")

    stats_df = stats_df.sort_values("pin").reset_index(drop=True)

    pins = stats_df["pin"].to_numpy()
    modes = stats_df["mode"].to_numpy()
    maxima = stats_df["max"].to_numpy()
    minima = stats_df["min"].to_numpy()
    include_mode = args.series in {"mode", "all"}
    include_max = args.series in {"max", "all"}
    include_min = args.series in {"min", "all"}

    fig, ax = plt.subplots(figsize=(10, 6))

    legend_handles = []
    series_data = []

    if include_mode:
        handle = ax.scatter(
            pins,
            modes,
            marker="o",
            color="tab:blue",
            edgecolors="white",
            linewidths=0.6,
            label="Mode (KDE peak)",
        )
        legend_handles.append(handle)
        series_data.append(("Mode", pins, modes, "tab:blue"))

    if include_max:
        handle = ax.scatter(
            pins,
            maxima,
            marker="s",
            color="tab:orange",
            edgecolors="white",
            linewidths=0.6,
            label="Maximum electron density",
        )
        legend_handles.append(handle)
        series_data.append(("Max", pins, maxima, "tab:orange"))

    if include_min:
        handle = ax.scatter(
            pins,
            minima,
            marker="^",
            color="tab:green",
            edgecolors="white",
            linewidths=0.6,
            label="Minimum electron density",
        )
        legend_handles.append(handle)
        series_data.append(("Min", pins, minima, "tab:green"))

    dataset_label = args.dataset
    ax.set_xlabel(r"$P_{\mathrm{in}}$ (W)")
    ax.set_ylabel(r"Electron density $(1/m^{3})$")
    ax.set_title(f"$P_{{\mathrm{{in}}}}$ vs. Electron Density ({dataset_label})")
    style_axes(ax, axis_style=SUMMARY_AXES_STYLE, grid={"alpha": 0.35})

    if args.scale == "log":
        ax.set_xscale("log")
        ax.set_yscale("log")

        text_y = 0.92
        text_step = 0.07
        for label, series_pins, series_vals, color in series_data:
            positive_mask = (series_pins > 0) & (series_vals > 0)
            if np.count_nonzero(positive_mask) < 2:
                print(f"Warning: insufficient positive data for log-log fit ({label})",
                      file=sys.stderr)
                continue

            log_x = np.log10(series_pins[positive_mask])
            log_y = np.log10(series_vals[positive_mask])
            slope, intercept = np.polyfit(log_x, log_y, 1)
            x_fit = np.linspace(log_x.min(), log_x.max(), 200)
            y_fit = slope * x_fit + intercept
            fit_handle, = ax.plot(
                10 ** x_fit,
                10 ** y_fit,
                linestyle="--",
                color=color,
                linewidth=1.5,
                label=f"{label} fit (slope = {slope:.2f})",
            )
            legend_handles.append(fit_handle)
            ax.text(
                0.04,
                text_y,
                f"log-log slope ({label}): {slope:.2f}",
                transform=ax.transAxes,
                fontsize=15,
                color=color,
            )
            text_y -= text_step

    if legend_handles:
        ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0.5)
    else:
        raise SystemExit("Nothing to plot: series selection excluded all data")

    fig.tight_layout()
    if args.output is None:
        plt.show()
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=300)
        print(f"Saved plot to {args.output}")


if __name__ == "__main__":
    main()
