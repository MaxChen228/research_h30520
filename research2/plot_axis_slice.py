#!/usr/bin/env python3
"""Plot axial electron density profiles along the symmetry axis (r = 0)."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import meshio
import numpy as np
from matplotlib import colormaps
import matplotlib.pyplot as plt
from matplotlib.tri import LinearTriInterpolator, Triangulation

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


@dataclass(frozen=True)
class CaseData:
    index: int
    path: Path
    r: np.ndarray
    z: np.ndarray
    density: np.ndarray
    triangulation: Triangulation
    r_min: float
    r_max: float
    z_min: float
    z_max: float
    radius: float  # cavity radius


@dataclass(frozen=True)
class AxisSlice:
    index: int
    h: np.ndarray
    density: np.ndarray
    r_target: float
    h_peak: float
    z_peak: float
    radius: float  # cavity radius


# ---------------------------------------------------------------------------
# Mesh loading helpers
# ---------------------------------------------------------------------------


def _find_triangles(mesh: meshio.Mesh) -> np.ndarray:
    for block in mesh.cells:
        if block.type.lower().startswith("tri"):
            return block.data
    raise ValueError("mesh does not contain triangle cells")


def load_case(path: Path) -> CaseData:
    mesh = meshio.read(path)
    points = mesh.points
    r = points[:, 0]
    z = points[:, 1]
    density = mesh.point_data.get("Electron_density")
    if density is None:
        raise KeyError(f"Electron_density field missing in {path.name}")
    triangles = _find_triangles(mesh)
    triangulation = Triangulation(r, z, triangles)
    return CaseData(
        index=_extract_index(path.name),
        path=path,
        r=r,
        z=z,
        density=density,
        triangulation=triangulation,
        r_min=float(r.min()),
        r_max=float(r.max()),
        z_min=float(z.min()),
        z_max=float(z.max()),
        radius=float(r.max()),  # cavity radius is r_max
    )


def _extract_index(name: str) -> int:
    start = name.find("(")
    end = name.find(")", start + 1)
    if start == -1 or end == -1:
        raise ValueError(f"unexpected filename format: {name}")
    return int(name[start + 1 : end])


# ---------------------------------------------------------------------------
# Sampling utilities
# ---------------------------------------------------------------------------


def sample_axis(case: CaseData, r_target: float, *, samples: int) -> AxisSlice | None:
    if not (case.r_min - 1e-9 <= r_target <= case.r_max + 1e-9):
        return None

    interpolator = LinearTriInterpolator(case.triangulation, case.density)
    z_line = np.linspace(case.z_min, case.z_max, samples)
    r_line = np.full_like(z_line, r_target)
    values = interpolator(r_line, z_line)

    if isinstance(values, np.ma.MaskedArray):
        mask = ~values.mask
        z_line = z_line[mask]
        values = values.data[mask]

    values = np.asarray(values)
    finite = np.isfinite(values)
    z_line = z_line[finite]
    values = values[finite]
    if z_line.size < 2:
        return None

    h_line = z_line - case.z_min
    peak_idx = int(np.argmax(values))
    return AxisSlice(
        index=case.index,
        h=h_line,
        density=values,
        r_target=r_target,
        h_peak=float(h_line[peak_idx]),
        z_peak=float(z_line[peak_idx]),
        radius=case.radius,
    )


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot electron-density vs height along the symmetry axis (r = const).",
    )
    default_data_dir = Path(__file__).resolve().parent / "500W_ne+Te"
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir,
        help="Directory containing plasma_500W(*).vtu files (default: %(default)s)",
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=0.0,
        help="Radial location for sampling (default: 0.0).",
    )
    parser.add_argument(
        "--cases",
        type=int,
        nargs="+",
        help="Subset of case indices to include (e.g. 1 5 7). Defaults to all.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=400,
        help="Number of axial sample points per case (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output image path. If omitted, saves to plots/axis_slice_r<radius>.png.",
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
# Plotting
# ---------------------------------------------------------------------------


def select_cases(data_dir: Path, requested: Sequence[int] | None) -> List[CaseData]:
    vtus = sorted(data_dir.glob("plasma_500W(*).vtu"), key=lambda p: _extract_index(p.name))
    if not vtus:
        raise FileNotFoundError(f"no VTU files found in {data_dir}")
    cases = [load_case(vtu) for vtu in vtus]
    if not requested:
        return cases
    requested_set = set(requested)
    filtered = [case for case in cases if case.index in requested_set]
    missing = requested_set - {case.index for case in filtered}
    if missing:
        raise ValueError(f"cases not found: {sorted(missing)}")
    return filtered


def build_figure(results: Iterable[AxisSlice], *, dpi: int, show_mode: bool, radius: float) -> plt.Figure:
    from matplotlib.colors import LogNorm
    from matplotlib.cm import ScalarMappable

    apply_common_style()
    fig_dpi = min(dpi, 180) if show_mode else dpi
    fig, ax, _ = create_figure(dpi=fig_dpi)
    width, height = fig.get_size_inches()
    fig.set_size_inches(width * 1.25, height, forward=True)
    style_axes(ax, axis_style=SUMMARY_AXES_STYLE)
    bbox = ax.get_position()
    ax.set_position([bbox.x0, bbox.y0, bbox.width * 0.80, bbox.height])

    results = sorted(results, key=lambda item: item.radius)
    if not results:
        raise ValueError("no slice data to plot")

    # Map radius to colors using continuous colormap with log scale
    radii = np.array([res.radius for res in results])
    norm = LogNorm(vmin=radii.min(), vmax=radii.max())
    cmap = colormaps["viridis"]

    for res in results:
        color = cmap(norm(res.radius))
        ax.plot(res.h, res.density, color=color, linewidth=1.6)

    ax.set_xlabel("Height h")
    ax.set_ylabel(r"Electron density (1/m$^{3}$)")
    ax.set_title("Axial slice")

    # Add colorbar with log scale instead of legend
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.02, aspect=30)
    cbar.set_label("Radius (mm)", fontfamily="Times New Roman", fontsize=12)

    ax.set_xlim(left=0.0)
    ax.set_ylim(bottom=0.0)
    return fig


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    data_dir = args.data_dir.resolve()
    cases = select_cases(data_dir, args.cases)

    results: List[AxisSlice] = []
    print(f"Sampling along r = {args.radius:.6f}")
    for case in cases:
        sampled = sample_axis(case, args.radius, samples=args.samples)
        if sampled is None:
            print(
                f"⚠️  Case {case.index} skipped (radius outside domain or insufficient data)",
                file=sys.stderr,
            )
            continue
        print(
            f"  Case {case.index}: h range = [{sampled.h.min():.3f}, {sampled.h.max():.3f}], "
            f"peak at h = {sampled.h_peak:.3f} (z = {sampled.z_peak:.3f})",
        )
        results.append(sampled)

    if not results:
        raise SystemExit("no cases produced axial data — check radius or selected cases")

    fig = build_figure(results, dpi=args.dpi, show_mode=args.show, radius=args.radius)

    output_path = args.output
    if output_path is None:
        default_dir = data_dir.parent / "plots"
        default_dir.mkdir(parents=True, exist_ok=True)
        tag = f"r{str(args.radius).replace('.', 'p')}"
        output_path = default_dir / f"axis_slice_{tag}.png"
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
