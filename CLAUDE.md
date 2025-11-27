# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a plasma simulation analysis project with three research areas focused on electron density and power relationships in plasma systems. The codebase processes VTU (VTK Unstructured Grid) files from plasma simulations and generates statistical analysis and visualizations.

## Quick Start - Unified CLI

**The fastest way to use all analysis tools:**

```bash
# From the project root directory
python cli.py
```

This unified CLI provides interactive access to all three research areas with guided menus.

## Directory Structure

- **research1/**: Main plasma data integration and plotting pipeline for Pin (power) vs electron density analysis
- **research2/**: 500W plasma electron density and temperature analysis with radial/axial slicing
- **research3/**: Power vs radius trend analysis
- **venv/**: Unified Python 3.12 virtual environment (shared by all research areas)
- **cli.py**: Unified interactive CLI for all analysis tools
- **requirements.txt**: Consolidated dependency list

## Python Environment

The project now uses a **unified virtual environment** at `venv/` shared by all research areas.

**Activate unified environment:**
```bash
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Key dependencies:** numpy, pandas, matplotlib, scipy, vtk, meshio, seaborn, rich

**Note:** Individual research directories still contain legacy `electron_density_env/` environments for backward compatibility, but the unified environment is recommended for all new work.

## Research 1: Pin vs Electron Density Analysis

### Core Workflow

**1. Data Organization**
- Place VTU files and corresponding `.pins` files in `research1/datasets/<dataset_name>/`
- Dataset names typically follow `r2=<value>` pattern (e.g., `r2=32`, `r2=39`, `r2=95`)
- Each `.vtu` file must have a matching `.pins` file containing space/newline-separated power values

**2. Build Consolidated Dataset**
```bash
cd research1
./process_vtu_cases.sh [datasets_dir] [output_dir]
```
- Default: `./process_vtu_cases.sh datasets data`
- Generates:
  - `data/all_values.csv`: Raw point data (columns: dataset, pin, point_index, value)
  - `data/all_stats.csv`: Per-pin statistics (mode, std, min, q1, median, q3, max, valid_points, source_count)
  - `data/dataset_index.txt`: List of processed datasets

**3. Generate Visualizations**

**Option 1: Unified CLI (recommended):**
```bash
# From project root
python cli.py
# Then select: 1) Research 1 - Pin vs 電子密度分析
```

**Option 2: Direct Research 1 CLI:**
```bash
cd research1
python chart_cli.py
```

Direct plotting scripts:
```bash
# Pin vs electron density summary
python plot_pin_statistics.py \
  --stats data/all_stats.csv \
  --dataset ALL \
  --series all \
  --scale log \
  --pin-min 30 --pin-max 2000 \
  --output plots/output.png

# Compare multiple r2 datasets
python plot_r2_comparison.py \
  --datasets r2=32 r2=39 r2=95 \
  --stat max \
  --pin-min 30 --pin-max 5000 \
  --output plots/r2_compare.png

# KDE comparison for same Pin across r2 values
python plot_pin_r2_kde.py \
  --pin 500 \
  --datasets r2=32 r2=39 r2=95 \
  --output plots/pin500_kde.png

# Electron density distribution
python plot_pin_density_distribution.py \
  --csv data/all_values.csv \
  --dataset ALL \
  --pin-min 30 --pin-max 2000 \
  --output plots/density_dist.png

# Analyze Pin coverage gaps
python analyze_pin_gap.py --max-gap 1000
```

### Key Scripts

- `build_dataset.py`: Core aggregation logic (called by process_vtu_cases.sh)
- `generate_pin_table.py`: VTU → table conversion with Pin assignment
- `chart_cli.py`: Interactive menu-driven plotting interface
- `plot_pin_statistics.py`: Summary plots (mode/max/min vs Pin)
- `plot_r2_comparison.py`: Multi-dataset comparison on single plot
- `plot_pin_r2_kde.py`: KDE comparison for same Pin across datasets
- `analyze_pin_gap.py`: Identify missing Pin ranges in dataset coverage

### Plot Characteristics

- Font: Times New Roman (14pt body, 18pt labels)
- Tick marks: Inward-facing with minor ticks
- Grid: Light gray dashed lines
- Legend: Positioned outside right edge
- Log-log plots: Include power-law fit with slope annotation
- All plots use standardized styling from `plot_style.py`

## Research 2: 500W Plasma Radial/Axial Analysis

Located in `research2/`, analyzes 17 VTU files (`plasma_500W(1).vtu` through `plasma_500W(17).vtu`) containing electron temperature and density data.

**Option 1: Unified CLI (recommended):**
```bash
# From project root
python cli.py
# Then select: 2) Research 2 - 500W 電漿徑向/軸向分析
```

**Option 2: Direct command-line scripts:**

```bash
cd research2

# Radial slice at specified height
python plot_radial_slice.py --z -50 --show

# Axial slice at specified radius
python plot_axis_slice.py --radius 0 --samples 400

# Decay radius analysis
python plot_decay_radius.py --alpha 0.5 0.7 0.9 --show
```

**Common Parameters:**
- `--z <value>`: Slice height (defaults to peak density location)
- `--radius <value>`: Radial position for axial slices
- `--cases <indices>`: Specify subset of files (e.g., `1 5 10`)
- `--samples <N>`: Number of sampling points
- `--show`: Display plot interactively
- `--output <path>`: Custom output path

Output directory: `research2/plots/`

## Research 3: Power-Radius Trends

Single-script analysis plotting average power vs radius with log-log fitting.

**Option 1: Unified CLI (recommended):**
```bash
# From project root
python cli.py
# Then select: 3) Research 3 - 功率-半徑趨勢分析
```

**Option 2: Direct script execution:**
```bash
cd research3
python plot_research3_trends.py
```

**Input:** `research3 - 工作表1.csv` (columns: radius, power)
**Output:** `research3_loglog.png`, `research3_linear.png`

## Development Commands

**Run single VTU file analysis (research1):**
```bash
cd research1
python generate_pin_table.py path/to/file.vtu path/to/file.pins
```

**Test plotting without regenerating data:**
```bash
cd research1
python plot_pin_statistics.py --stats data/all_stats.csv --series mode --scale log
```

**Check dataset coverage:**
```bash
cd research1
python analyze_pin_gap.py --max-gap 500
```

## Data Format Notes

**VTU Files:**
- UnstructuredGrid format with triangular cells
- Point data fields: `Electron_temperature`, `Electron_density`
- Must contain finite (non-NaN) values after cleaning

**Pin Files (.pins):**
- Plain text with space/newline-separated power values
- Supports scientific notation (e.g., `1E4`, `2E5`)
- Number of values must match number of timesteps in VTU

**Statistics CSV (all_stats.csv):**
- Columns: `dataset`, `pin`, `mode`, `std`, `min`, `q1`, `median`, `q3`, `max`, `valid_points`, `source_count`
- Mode calculated via KDE peak on log10-transformed positive values
- Aggregated per-Pin across all timesteps and datasets

## Architecture Notes

**Two-Stage Processing (research1):**
1. **VTU → Raw Values**: `generate_pin_table.py` extracts point data and assigns Pin labels
2. **Aggregation → Statistics**: `build_dataset.py` computes per-Pin summary statistics with KDE-based mode estimation

**Dataset Hierarchy:**
- Individual datasets (e.g., `r2=32`) can be analyzed separately
- `ALL` pseudo-dataset aggregates across all r2 values
- Dataset name determined by top-level folder in `datasets/` directory

**Plotting Pipeline:**
- All plot scripts accept `--dataset` filter (defaults to `ALL`)
- Pin range filtering via `--pin-min` and `--pin-max`
- Output can be saved (`--output`) or displayed interactively (omit `--output`)
- Scripts validate data existence before execution

## Common Workflows

**Add new simulation data:**
1. Create directory: `research1/datasets/r2=<value>/`
2. Add VTU and pins files (matching basenames)
3. Run: `./process_vtu_cases.sh`
4. Generate plots: `python chart_cli.py`

**Compare different r2 configurations:**
```bash
python plot_r2_comparison.py --datasets r2=32 r2=39 r2=95 --stat mode --output plots/comparison.png
```

**Analyze specific Pin range:**
```bash
python plot_pin_statistics.py --stats data/all_stats.csv --pin-min 100 --pin-max 1000 --scale log --output plots/focused.png
```

## Troubleshooting

**"pins file missing" error:**
Ensure every `.vtu` has matching `.pins` file with same basename.

**"Statistics file not found":**
Run `./process_vtu_cases.sh` first to generate aggregated data.

**"No VTU files found":**
Verify `datasets/` directory structure and file locations.

**Missing fit line in log-log plots:**
Check for zero/negative values or insufficient data points (need ≥2 valid points).

**Virtual environment issues:**
Activate environment: `source venv/bin/activate`

## Unified CLI Features

The `cli.py` provides a centralized interface for all analysis tools:

**Main Menu:**
1. Research 1 - Pin vs 電子密度分析 (redirects to research1/chart_cli.py)
2. Research 2 - 500W 電漿徑向/軸向分析 (interactive parameter input)
3. Research 3 - 功率-半徑趨勢分析 (one-click execution)

**Research 2 Submenu Options:**
- Radial Slice Analysis (徑向切片分析)
- Axial Slice Analysis (軸向切片分析)
- Decay Radius Analysis (衰減半徑分析)

**Benefits:**
- ✅ Single entry point for all tools
- ✅ Guided parameter input with defaults
- ✅ Unified Python environment
- ✅ Command preview before execution
- ✅ Consistent user experience across research areas

**Example Usage:**
```bash
# Activate environment (first time only)
source venv/bin/activate

# Launch unified CLI
python cli.py

# Follow the interactive menus
# All outputs are saved to respective research directories
```
