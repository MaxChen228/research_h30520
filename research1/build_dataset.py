#!/usr/bin/env python3
"""Aggregate VTU cases into per-dataset and overall statistics tables."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

from generate_pin_table import convert_vtu_to_tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate multiple VTU datasets into CSV tables."
    )
    parser.add_argument(
        "--datasets-dir",
        type=Path,
        default=Path("datasets"),
        help="Directory containing dataset folders or standalone VTU files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Directory where consolidated CSV files will be written",
    )
    return parser.parse_args()


def read_pin_values(pin_file: Path) -> List[float]:
    text = pin_file.read_text(encoding="utf-8")
    tokens = [token for token in text.replace(",", " ").split() if token]
    if not tokens:
        raise ValueError(f"No Pin values found in {pin_file}")
    try:
        return [float(token) for token in tokens]
    except ValueError as exc:
        raise ValueError(f"Failed to parse Pin values in {pin_file}: {exc}") from exc


def determine_dataset_name(datasets_dir: Path, vtu_path: Path) -> str:
    """Use the top-level folder name as dataset; fallback to file stem."""
    rel = vtu_path.relative_to(datasets_dir)
    if len(rel.parts) == 1:
        return rel.stem
    return rel.parts[0]


def process_case(dataset_name: str, vtu_path: Path, pins: Iterable[float]) -> pd.DataFrame:
    values_df, _ = convert_vtu_to_tables(vtu_path, pins)
    values_df.insert(0, "dataset", dataset_name)
    return values_df


def summarise_by_pin(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("pin")["value"]

    summary = grouped.agg(
        std=lambda s: float(np.std(s, ddof=0)),
        min=lambda s: float(np.min(s)),
        q1=lambda s: float(np.quantile(s, 0.25)),
        median=lambda s: float(np.median(s)),
        q3=lambda s: float(np.quantile(s, 0.75)),
        max=lambda s: float(np.max(s)),
        valid_points=lambda s: int(s.size),
    ).reset_index().sort_values("pin")

    modes = []
    for pin, series in grouped:
        values = series.to_numpy(dtype=float)
        values = values[np.isfinite(values) & (values > 0)]
        if values.size >= 2:
            log_vals = np.log10(values)
            try:
                kde = gaussian_kde(log_vals)
                grid = np.linspace(log_vals.min(), log_vals.max(), 512)
                mode_log = grid[np.argmax(kde(grid))]
                mode_val = float(10 ** mode_log)
            except Exception:
                mode_val = float(np.median(values))
        elif values.size == 1:
            mode_val = float(values[0])
        else:
            mode_val = float("nan")
        modes.append((float(pin), mode_val))

    modes_df = pd.DataFrame(modes, columns=["pin", "mode"])
    return summary.merge(modes_df, on="pin", how="left")


def collect_vtu_files(datasets_dir: Path) -> List[Path]:
    return sorted(p for p in datasets_dir.rglob("*.vtu") if p.is_file())


def main() -> None:
    args = parse_args()

    datasets_dir = args.datasets_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    vtu_files = collect_vtu_files(datasets_dir)
    if not vtu_files:
        print(f"No VTU files found in {datasets_dir}")
        return

    all_values: List[pd.DataFrame] = []
    per_dataset_stats: List[pd.DataFrame] = []
    processed_names: List[str] = []

    for vtu_path in vtu_files:
        dataset_name = determine_dataset_name(datasets_dir, vtu_path)
        pins_path = vtu_path.with_suffix(".pins")
        if not pins_path.exists():
            print(f"Skipping {dataset_name}: missing Pin list {pins_path}")
            continue

        try:
            pin_values = read_pin_values(pins_path)
        except ValueError as exc:
            print(f"Skipping {dataset_name}: {exc}")
            continue

        try:
            values_df = process_case(dataset_name, vtu_path, pin_values)
        except Exception as exc:  # pragma: no cover
            print(f"Failed to process {dataset_name}: {exc}")
            continue

        all_values.append(values_df)
        processed_names.append(dataset_name)

        stats_df = summarise_by_pin(values_df)
        stats_df.insert(0, "dataset", dataset_name)
        stats_df["dataset_count"] = 1
        per_dataset_stats.append(stats_df)

    if not processed_names:
        print("No datasets were processed successfully")
        return

    all_values_df = pd.concat(all_values, ignore_index=True)

    values_output = output_dir / "all_values.csv"
    stats_output = output_dir / "all_stats.csv"
    index_output = output_dir / "dataset_index.txt"

    all_values_df.to_csv(values_output, index=False)

    aggregate_stats = summarise_by_pin(all_values_df)
    aggregate_stats.insert(0, "dataset", "ALL")
    source_counts = (
        all_values_df.groupby("pin")["dataset"].nunique().rename("dataset_count")
    )
    aggregate_stats = aggregate_stats.merge(source_counts, on="pin", how="left")
    per_dataset_stats.append(aggregate_stats)

    all_stats = pd.concat(per_dataset_stats, ignore_index=True)
    ordered_cols = [
        "dataset",
        "pin",
        "mode",
        "std",
        "min",
        "q1",
        "median",
        "q3",
        "max",
        "valid_points",
        "dataset_count",
    ]
    for col in ordered_cols:
        if col not in all_stats.columns:
            all_stats[col] = np.nan
    all_stats = all_stats[ordered_cols]

    all_stats.to_csv(stats_output, index=False)
    index_output.write_text("\n".join(sorted(set(processed_names))), encoding="utf-8")

    print(f"Aggregated values -> {values_output}")
    print(f"Aggregated statistics -> {stats_output}")
    print(f"Dataset index -> {index_output}")


if __name__ == "__main__":
    main()
