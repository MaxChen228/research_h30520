#!/usr/bin/env python3
"""Plot decay radius vs. cavity radius for a given fractional level of peak density."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colormaps

try:
    from plot_style import (
        SUMMARY_AXES_STYLE,
        apply_common_style,
        create_figure,
        style_axes,
    )
except ImportError:  # pragma: no cover
    here = Path(__file__).resolve().parent
    shared = here.parent / "research1"
    if shared.exists():
        sys.path.append(str(shared))
    from plot_style import (  # type: ignore  # noqa: E402
        SUMMARY_AXES_STYLE,
        apply_common_style,
        create_figure,
        style_axes,
    )

from plot_radial_slice import CaseData, SliceResult, select_cases, sample_slice  # type: ignore


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute the radius where density decays to alpha * peak and plot against cavity size.",
    )
    default_data_dir = Path(__file__).resolve().parent / "500W_ne+Te"
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir,
        help="Directory containing plasma_500W(*).vtu files (default: %(default)s)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        nargs='+',
        default=[0.5],
        help="One or more fractions of the peak density used as decay thresholds (0 < alpha < 1).",
    )
    parser.add_argument(
        "--z",
        type=float,
        help="Override axial coordinate z (per-case peak density is used if omitted).",
    )
    parser.add_argument(
        "--cases",
        type=int,
        nargs="+",
        help="Subset of case indices to include (e.g. 2 5 9). Defaults to all.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=800,
        help="Number of radial sample points per case (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output image path. If omitted, saves to plots/decay_radius_alpha<value>.png.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the figure interactively after saving.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Figure DPI when saving (default: %(default)s)",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Computation helpers
# ---------------------------------------------------------------------------


def validate_alpha(values: Sequence[float]) -> List[float]:
    cleaned: List[float] = []
    for alpha in values:
        if not (0.0 < alpha < 1.0):
            raise SystemExit("alpha must be between 0 and 1 (exclusive)")
        cleaned.append(float(alpha))
    return cleaned


def compute_decay_radius(slice_data: SliceResult, alpha: float) -> float | None:
    densities = slice_data.density
    radii = slice_data.r
    if densities.size == 0:
        return None

    peak_idx = int(np.argmax(densities))
    peak_value = float(densities[peak_idx])
    threshold = alpha * peak_value

    tail_dens = densities[peak_idx:]
    tail_r = radii[peak_idx:]

    below = np.nonzero(tail_dens <= threshold)[0]
    if below.size == 0:
        return None
    j = below[0]
    if j == 0:
        return float(tail_r[0])

    r0, r1 = tail_r[j - 1], tail_r[j]
    d0, d1 = tail_dens[j - 1], tail_dens[j]
    if d0 == d1:
        return float(r1)
    t = (threshold - d0) / (d1 - d0)
    r_interp = r0 + t * (r1 - r0)
    return float(r_interp)

def build_plot(points_by_alpha: Dict[float, List[Tuple[float, float]]], *, dpi: int, show_mode: bool, alpha_label: bool = True) -> plt.Figure:
    apply_common_style()
    fig_dpi = min(dpi, 180) if show_mode else dpi
    fig, ax, _ = create_figure(dpi=fig_dpi)
    width, height = fig.get_size_inches()
    fig.set_size_inches(width * 1.25, height, forward=True)
    style_axes(ax, axis_style=SUMMARY_AXES_STYLE)

    non_empty = {alpha: sorted(points, key=lambda item: item[0]) for alpha, points in points_by_alpha.items() if points}
    if not non_empty:
        raise ValueError("no valid decay radii to plot")

    all_x = np.concatenate([np.array([p[0] for p in pts]) for pts in non_empty.values()])
    all_y = np.concatenate([np.array([p[1] for p in pts]) for pts in non_empty.values()])

    limit = max(all_x.max(), all_y.max()) * 1.05
    ax.plot([0, limit], [0, limit], ls="--", color="gray", lw=1.0)

    cmap = colormaps["viridis"]
    colors = cmap(np.linspace(0.1, 0.9, len(non_empty)))

    for color, alpha in zip(colors, sorted(non_empty), strict=True):
        pts = non_empty[alpha]
        x = np.array([p[0] for p in pts])
        y = np.array([p[1] for p in pts])
        ax.plot(
            x,
            y,
            marker="x",
            linestyle="-",
            linewidth=1.1,
            markersize=6,
            color=color,
            label=f"alpha = {alpha:.2f}",
        )

    ax.set_xlim(0, limit)
    ax.set_ylim(0, limit)
    ax.set_xlabel("Radius (mm)")
    ax.set_ylabel("Radius at alpha×peak density (mm)")
    ax.set_title("Decay radius vs. radius")

    # Add y=x annotation on the diagonal line
    mid_point = limit * 0.85
    ax.text(mid_point, mid_point * 1.02, "y = x",
            fontsize=10, color="gray", ha="center", va="bottom",
            rotation=45, fontfamily="Times New Roman")
    ax.legend(loc="upper left")
    return fig


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def _format_alpha(alpha: float) -> str:
    text = f"{alpha:.3f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    alphas = validate_alpha(args.alpha)

    data_dir = args.data_dir.resolve()
    cases = select_cases(data_dir, args.cases)

    auto_mode = args.z is None
    if auto_mode:
        print("Auto-selecting z at peak electron density for each case:")

    points_by_alpha: Dict[float, List[Tuple[float, float]]] = {alpha: [] for alpha in alphas}

    for case in cases:
        z_target = args.z
        if z_target is None:
            idx = int(np.argmax(case.density))
            z_target = float(case.z[idx])
            print(f"  Case {case.index}: z_peak = {z_target:.6f}")
        slice_data = sample_slice(case, z_target, samples=args.samples)
        if slice_data is None:
            print(
                f"⚠️  Case {case.index} skipped (z={z_target:.3f} outside domain or insufficient data)",
                file=sys.stderr,
            )
            continue
        print(f"  Case {case.index}: cavity r_max = {case.r_max:.3f}")
        for alpha in alphas:
            decay_r = compute_decay_radius(slice_data, alpha)
            if decay_r is None:
                print(
                    f"    ⚠️ alpha={alpha:.2f}: density never fell below {alpha:.2f}×peak",
                    file=sys.stderr,
                )
                continue
            points_by_alpha[alpha].append((case.r_max, decay_r))
            print(f"    alpha={alpha:.2f}: decay radius = {decay_r:.3f}")

    non_empty = {alpha: pts for alpha, pts in points_by_alpha.items() if pts}
    if not non_empty:
        raise SystemExit("no decay radii computed — adjust alpha set or selected cases")

    fig = build_plot(non_empty, dpi=args.dpi, show_mode=args.show)

    output_path = args.output
    if output_path is None:
        default_dir = data_dir.parent / "plots"
        default_dir.mkdir(parents=True, exist_ok=True)
        alpha_tag = "-".join(_format_alpha(alpha) for alpha in sorted(non_empty))
        base = "decay_radius"
        if auto_mode:
            base += "_auto"
        output_path = default_dir / f"{base}_alpha{alpha_tag}.png"
    else:
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path, dpi=args.dpi)
    print(f"✓ Saved figure to {output_path}")

    if args.show:
        plt.show()
    plt.close(fig)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
