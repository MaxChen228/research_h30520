#!/usr/bin/env python3
"""Compare multiple r2 datasets on a single Pin vs. density curve."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import numpy as np
import pandas as pd

from plot_style import SUMMARY_AXES_STYLE, apply_common_style, style_axes

apply_common_style()


def normalize_dataset_name(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValueError("Empty dataset identifier provided.")
    if raw.upper() == "ALL":
        return "ALL"
    if raw.lower().startswith("r2="):
        return raw
    if raw.lower().startswith("r="):
        return raw
    return f"r={raw}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot selected r2 datasets on the same Pin vs. density chart (log-log)."
    )
    parser.add_argument(
        "--stats",
        type=Path,
        default=Path("data/all_stats.csv"),
        help="CSV file containing per-Pin summary statistics (default: data/all_stats.csv)",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        required=True,
        help="Datasets to compare (e.g. r2=32 r2=39)",
    )
    parser.add_argument(
        "--stat",
        choices=["mode", "max", "min"],
        default="mode",
        help="Statistic to plot for each dataset (default: mode)",
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


def load_statistics(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Statistics file not found: {path}")
    df = pd.read_csv(path)
    needed = {"dataset", "pin", "mode", "max", "min"}
    missing = needed.difference(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise SystemExit(f"Statistics file missing required columns: {missing_list}")
    return df


def select_dataset_curve(
    df: pd.DataFrame,
    dataset: str,
    stat: str,
    pin_min: float | None,
    pin_max: float | None,
) -> tuple[np.ndarray, np.ndarray]:
    subset = df[df["dataset"] == dataset]
    if subset.empty:
        raise SystemExit(f"Dataset '{dataset}' not found in statistics table.")
    if pin_min is not None:
        subset = subset[subset["pin"] >= pin_min]
    if pin_max is not None:
        subset = subset[subset["pin"] <= pin_max]
    subset = subset.sort_values("pin")
    pins = subset["pin"].to_numpy(dtype=float)
    values = subset[stat].to_numpy(dtype=float)
    mask = (pins > 0) & (values > 0)
    if mask.sum() < len(pins):
        raise SystemExit(
            f"Dataset '{dataset}' contains non-positive values for log scaling."
        )
    if pins.size == 0:
        raise SystemExit(
            f"Dataset '{dataset}' has no entries after applying Pin range filters."
        )
    return pins, values

def main() -> None:
    args = parse_args()
    stats_df = load_statistics(args.stats)

    datasets = [normalize_dataset_name(name) for name in args.datasets]
    if len(datasets) < 2:
        raise SystemExit("Please provide at least two datasets for comparison.")

    output_path = args.output

    fig, ax = plt.subplots(figsize=(10, 6))

    def parse_value(name: str) -> float | None:
        # 支援 r2= 或 r= 格式
        m = re.match(r"r2?=([0-9.]+)", name)
        if not m:
            return None
        try:
            return float(m.group(1))
        except ValueError:
            return None

    value_by_dataset = {ds: parse_value(ds) for ds in datasets}
    group_specs = [
        (lambda v: v is not None and v <= 35.9, "#4b3b8f"),
        (lambda v: v is not None and 35.9 < v <= 99.9, "#b01726"),
        (lambda v: v is not None and v > 99.9, "#1f4d6d"),
    ]

    def make_shades(base_hex: str, count: int) -> list[tuple[float, float, float]]:
        base = np.array(to_rgb(base_hex))
        white = np.ones(3)
        if count <= 1:
            return [tuple(base)]
        blend = np.linspace(0.2, 0.75, count)
        return [tuple(base * (1 - f) + white * f) for f in blend]

    color_lookup: dict[str, tuple[float, float, float]] = {}
    for predicate, base_hex in group_specs:
        members = [ds for ds in datasets if predicate(value_by_dataset.get(ds))]
        if not members:
            continue
        shades = make_shades(base_hex, len(members))
        for ds, color in zip(members, shades):
            color_lookup[ds] = color

    remaining = [ds for ds in datasets if ds not in color_lookup]
    if remaining:
        fallback_shades = make_shades("#555555", len(remaining))
        for ds, color in zip(remaining, fallback_shades):
            color_lookup[ds] = color

    for dataset in datasets:
        pins, values = select_dataset_curve(
            stats_df,
            dataset,
            args.stat,
            args.pin_min,
            args.pin_max,
        )
        color = color_lookup.get(dataset, (0.3, 0.3, 0.3))
        # 將 r2= 替換為 r= 用於顯示
        display_label = dataset.replace("r2=", "r=")
        ax.plot(
            pins,
            values,
            marker="o",
            linewidth=2.0,
            markersize=5,
            label=display_label,
            color=color,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$P_{\mathrm{in}}$ (W)", fontfamily="Times New Roman")

    # 統一的標題和標籤格式
    stat_title = {
        "mode": "Mode",
        "max": "Maximum",
        "min": "Minimum",
    }[args.stat]

    # Y 軸標籤使用完整名稱
    ylabel_text = {
        "mode": r"Mode electron density $(m^{-3})$",
        "max": r"Maximum electron density $(m^{-3})$",
        "min": r"Minimum electron density $(m^{-3})$",
    }[args.stat]
    ax.set_ylabel(ylabel_text, fontfamily="Times New Roman")

    # 標題簡潔，不列出所有 r 值
    ax.set_title(rf"$P_{{\mathrm{{in}}}}$ vs. {stat_title} Electron Density")

    style_axes(ax, axis_style=SUMMARY_AXES_STYLE, grid={"alpha": 0.35})

    # Legend 標題包含單位說明
    legend = ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5),
                      borderaxespad=0.5, title="r (mm)")
    legend.get_title().set_fontsize(12)

    fig.tight_layout()
    if output_path is None:
        plt.show()
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=300)
        print(f"Saved plot to {output_path}")


if __name__ == "__main__":
    main()
