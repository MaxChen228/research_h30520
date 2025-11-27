#!/usr/bin/env python3
"""Inspect Pin coverage and highlight gaps."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List covered Pin values and highlight gaps.")
    parser.add_argument(
        "--stats",
        type=Path,
        default=Path("data/all_stats.csv"),
        help="Path to the aggregated statistics CSV (default: data/all_stats.csv)",
    )
    parser.add_argument(
        "--dataset",
        default="ALL",
        help="Dataset name to inspect (default: ALL)",
    )
    parser.add_argument(
        "--max-gap",
        type=float,
        default=500.0,
        help="Report gaps larger than this value (default: 500)",
    )
    return parser.parse_args()


def format_pin_list(pins: Sequence[float]) -> str:
    return ", ".join(f"{pin:g}" for pin in pins)


def main() -> None:
    args = parse_args()
    if not args.stats.exists():
        raise SystemExit(f"stats file not found: {args.stats}")

    df = pd.read_csv(args.stats)
    required = {"dataset", "pin"}
    missing = required.difference(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise SystemExit(f"stats file missing required columns: {missing_list}")

    available = sorted(df["dataset"].unique())
    if args.dataset not in available:
        raise SystemExit(
            f"Dataset '{args.dataset}' not found. Available datasets: {', '.join(available)}"
        )

    df = df[df["dataset"] == args.dataset]
    pins = sorted(set(df["pin"].astype(float)))
    if not pins:
        print(f"Dataset '{args.dataset}' contains no Pin entries")
        return

    print(f"Dataset: {args.dataset}")
    print(f"總計覆蓋 Pin 數: {len(pins)}")
    print("Pin 值 (排序後):")
    print(format_pin_list(pins))

    gaps = []
    for prev, curr in zip(pins, pins[1:]):
        diff = curr - prev
        if diff > args.max_gap:
            gaps.append((prev, curr, diff))

    if gaps:
        print(f"\n缺口 (間距 > {args.max_gap:g} W):")
        for prev, curr, diff in gaps:
            print(f"  {prev:g} → {curr:g}  (差 {diff:g} W)")
    else:
        print(f"\n未發現間距大於 {args.max_gap:g} W 的 Pin 缺口。")


if __name__ == "__main__":
    main()
