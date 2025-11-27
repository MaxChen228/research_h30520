#!/usr/bin/env python3
"""Convert plasma VTU electron density series into a pin-aligned data table."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import re
from typing import Dict, Iterable, List, Tuple

try:  # pragma: no cover - environment dependency guard
    import numpy as np
except ImportError as exc:
    print("Error: numpy is required for this script (pip install numpy).", file=sys.stderr)
    raise SystemExit(1) from exc

try:  # pragma: no cover - environment dependency guard
    import pandas as pd
except ImportError as exc:
    print("Error: pandas is required for this script (pip install pandas).", file=sys.stderr)
    raise SystemExit(1) from exc

try:  # pragma: no cover - environment dependency guard
    import meshio  # type: ignore
except ImportError as exc:
    print("Error: meshio is required to read VTU files (pip install meshio).", file=sys.stderr)
    raise SystemExit(1) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract electron-density point data from a VTU file, align it with the provided Pin "
            "sequence, validate counts, and store a structured table that includes both raw "
            "values and per-Pin summary statistics."
        )
    )
    parser.add_argument(
        "pin_values",
        metavar="PIN",
        nargs="+",
        type=float,
        help="Pin power values (W) ordered to match the VTU time/field sequence",
    )
    parser.add_argument(
        "--vtu",
        default="plasma.vtu",
        type=Path,
        help="Path to the VTU file (default: plasma.vtu)",
    )
    parser.add_argument(
        "--values-output",
        default=Path("pin_electron_density_table.csv"),
        type=Path,
        help="Output CSV file containing per-point values with summary statistics",
    )
    parser.add_argument(
        "--stats-output",
        default=Path("pin_electron_density_stats.csv"),
        type=Path,
        help="Output CSV file containing per-Pin summary statistics",
    )
    return parser.parse_args()


def _extract_step_index(field_name: str) -> int:
    match = re.search(r"_(\d+)$", field_name)
    if match:
        return int(match.group(1))
    return 1


def _select_density_fields(point_data: Dict[str, np.ndarray]) -> List[Tuple[str, np.ndarray]]:
    pattern = re.compile(r"electron_density(?:_\d+)?$", re.IGNORECASE)
    selected: List[Tuple[str, np.ndarray]] = []

    for name, array in point_data.items():
        if not pattern.search(name):
            continue
        np_array = np.asarray(array)
        if np_array.ndim == 2 and np_array.shape[1] == 1:
            np_array = np_array[:, 0]
        if np_array.ndim != 1:
            continue  # skip vector/tensor data
        selected.append((name, np_array))

    if not selected:
        raise ValueError("No electron density fields were found in the VTU file.")

    selected.sort(key=lambda item: _extract_step_index(item[0]))
    return selected


def _build_tables(
    density_fields: List[Tuple[str, np.ndarray]],
    pin_values: Iterable[float],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    pin_list = list(pin_values)
    stats_rows: List[Dict[str, float]] = []
    value_rows: List[Dict[str, float]] = []

    if len(density_fields) != len(pin_list):
        raise ValueError(
            f"Pin count ({len(pin_list)}) does not match the number of electron-density fields "
            f"({len(density_fields)})."
        )

    for step_index, ((field_name, raw_values), pin) in enumerate(zip(density_fields, pin_list), start=1):
        flattened = raw_values.reshape(-1)
        total_points = flattened.size
        valid_mask = np.isfinite(flattened)
        valid_indices = np.nonzero(valid_mask)[0]
        valid_values = flattened[valid_mask]
        missing_points = total_points - valid_values.size

        if valid_values.size == 0:
            raise ValueError(f"Field '{field_name}' contains no finite values.")

        stats = {
            "pin": float(pin),
            "field_name": field_name,
            "time_step": step_index,
            "total_points": int(total_points),
            "valid_points": int(valid_values.size),
            "missing_points": int(missing_points),
            "mean": float(np.mean(valid_values)),
            "std": float(np.std(valid_values, ddof=0)),
            "min": float(np.min(valid_values)),
            "q1": float(np.percentile(valid_values, 25)),
            "median": float(np.median(valid_values)),
            "q3": float(np.percentile(valid_values, 75)),
            "max": float(np.max(valid_values)),
        }
        stats_rows.append(stats)

        for point_idx, value in zip(valid_indices, valid_values):
            value_rows.append(
                {
                    "pin": float(pin),
                    "field_name": field_name,
                    "time_step": step_index,
                    "point_index": int(point_idx),
                    "value": float(value),
                }
            )

    stats_df = pd.DataFrame(stats_rows)
    values_df = pd.DataFrame(value_rows)
    values_df = values_df.merge(
        stats_df,
        on=["pin", "field_name", "time_step"],
        how="left",
    )

    return values_df, stats_df


def convert_vtu_to_tables(
    vtu_path: Path,
    pin_values: Iterable[float],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Read a VTU file and build per-point and per-Pin tables."""

    if not Path(vtu_path).exists():
        raise FileNotFoundError(f"VTU file not found: {vtu_path}")

    mesh = meshio.read(str(vtu_path))
    density_fields = _select_density_fields(mesh.point_data)

    return _build_tables(density_fields, pin_values)


def main() -> None:
    args = parse_args()

    try:
        values_df, stats_df = convert_vtu_to_tables(args.vtu, args.pin_values)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    args.values_output.parent.mkdir(parents=True, exist_ok=True)
    args.stats_output.parent.mkdir(parents=True, exist_ok=True)

    values_df.to_csv(args.values_output, index=False)
    stats_df.to_csv(args.stats_output, index=False)

    print(f"Saved per-point data with statistics to {args.values_output}")
    print(f"Saved per-pin summary statistics to {args.stats_output}")


if __name__ == "__main__":
    main()
