#!/usr/bin/env python3
"""Plot radial electron density slices at a fixed axial position."""

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

# ---------------------------------------------------------------------------
# Optional import of shared plotting style (falls back if unavailable).
# ---------------------------------------------------------------------------

try:  # try to import from the current directory first
    from plot_style import (
        SUMMARY_AXES_STYLE,
        apply_common_style,
        create_figure,
        style_axes,
    )
except ImportError:  # pragma: no cover - executed when run from research2/
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
    r_max: float
    z_min: float
    z_max: float
    radius: float  # cavity radius


@dataclass(frozen=True)
class SliceResult:
    index: int
    z_peak: float
    r: np.ndarray
    density: np.ndarray
    r_max: float
    radius: float  # cavity radius


# ---------------------------------------------------------------------------
# Data loading utilities
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
# Slice generation
# ---------------------------------------------------------------------------


def sample_slice(case: CaseData, z_target: float, *, samples: int) -> SliceResult | None:
    if not case.z_min <= z_target <= case.z_max:
        return None
    interpolator = LinearTriInterpolator(case.triangulation, case.density)
    r_line = np.linspace(0.0, case.r_max, samples)
    z_line = np.full_like(r_line, z_target)
    values = interpolator(r_line, z_line)
    if isinstance(values, np.ma.MaskedArray):
        mask = ~values.mask
        r_line = r_line[mask]
        values = values.data[mask]
    values = np.asarray(values)
    finite = np.isfinite(values)
    r_line = r_line[finite]
    values = values[finite]
    if r_line.size < 2:
        return None
    return SliceResult(index=case.index, z_peak=z_target, r=r_line, density=values, r_max=case.r_max, radius=case.radius)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot electron-density vs radius for VTU cavities at a fixed axial position.",
    )
    default_data_dir = Path(__file__).resolve().parent / "500W_ne+Te"
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir,
        help="Directory containing plasma_500W(*).vtu files (default: %(default)s)",
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
        help="Subset of case indices to include (e.g. 1 5 7). Defaults to all.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=400,
        help="Number of radial sample points per case (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output image path. If omitted, saves to plots/radial_slice_z<value>.png.",
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


def build_figure(results: Iterable[SliceResult], *, dpi: int, show_mode: bool, global_z: float | None) -> plt.Figure:
    from matplotlib.colors import LogNorm
    from matplotlib.cm import ScalarMappable

    apply_common_style()
    fig_dpi = min(dpi, 180) if show_mode else dpi
    fig, ax, _ = create_figure(dpi=fig_dpi)
    # widen the canvas to keep axes readable even with colorbar
    width, height = fig.get_size_inches()
    fig.set_size_inches(width * 1.25, height, forward=True)
    style_axes(ax, axis_style=SUMMARY_AXES_STYLE)
    # shrink axis width to reserve space for colorbar
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
        ax.plot(res.r, res.density, color=color, linewidth=1.6)

    ax.set_xlabel("Radius r")
    ax.set_ylabel(r"Electron density (1/m$^{3}$)")
    if global_z is not None:
        title = f"Radial slice at z = {global_z:.3f}"
    else:
        title = "Radial slice at peak electron density"
    ax.set_title(title)

    # Add colorbar with log scale instead of legend
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.02, aspect=30)
    cbar.set_label("Radius (mm)", fontfamily="Times New Roman", fontsize=12)

    ax.set_xlim(0.0, 500.0)
    ax.set_ylim(bottom=0.0)
    return fig


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    data_dir = args.data_dir.resolve()
    cases = select_cases(data_dir, args.cases)

    results: List[SliceResult] = []
    auto_mode = args.z is None
    if auto_mode:
        print("Auto-selecting z at peak electron density for each case:")

    for case in cases:
        z_target = args.z
        if z_target is None:
            idx = int(np.argmax(case.density))
            z_target = float(case.z[idx])
            print(f"  Case {case.index}: z_peak = {z_target:.6f}")
        sampled = sample_slice(case, z_target, samples=args.samples)
        if sampled is None:
            print(
                f"⚠️  Case {case.index} skipped (z={z_target:.3f} outside domain or insufficient data)",
                file=sys.stderr,
            )
            continue
        results.append(sampled)

    if not results:
        raise SystemExit("no cases produced radial data — check z range or selected cases")

    fig = build_figure(results, dpi=args.dpi, show_mode=args.show, global_z=None if auto_mode else args.z)

    output_path = args.output
    if output_path is None:
        default_dir = data_dir.parent / "plots"
        default_dir.mkdir(parents=True, exist_ok=True)
        if auto_mode:
            tag = "z_peak-density"
        else:
            tag = f"z{str(args.z).replace('.', 'p')}"
        output_path = default_dir / f"radial_slice_{tag}.png"
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
