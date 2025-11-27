#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

CASES_DIR="${1:-$PROJECT_ROOT/datasets}"
OUTPUT_DIR="${2:-$PROJECT_ROOT/data}"
PLOT_OUTPUT="${3:-}"
PIN_MIN="${4:-}"
PIN_MAX="${5:-}"

PYTHON_BIN="${PYTHON:-python3}"
if [ -x "$PROJECT_ROOT/electron_density_env/bin/python" ]; then
  PYTHON_BIN="$PROJECT_ROOT/electron_density_env/bin/python"
fi

if [ ! -d "$CASES_DIR" ]; then
  echo "Cases directory not found: $CASES_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

"$PYTHON_BIN" "$PROJECT_ROOT/build_dataset.py" \
  --datasets-dir "$CASES_DIR" \
  --output-dir "$OUTPUT_DIR"

ALL_STATS="$OUTPUT_DIR/all_stats.csv"
if [ ! -f "$ALL_STATS" ]; then
  echo "Aggregated statistics not found at $ALL_STATS" >&2
  exit 0
fi

if [ -n "$PLOT_OUTPUT" ] || [ -n "$PIN_MIN" ] || [ -n "$PIN_MAX" ]; then
  if [ -z "$PLOT_OUTPUT" ]; then
    PLOT_OUTPUT="$PROJECT_ROOT/plots/pin_summary.png"
  fi
  mkdir -p "$(dirname "$PLOT_OUTPUT")"

  cmd=("$PYTHON_BIN" "$PROJECT_ROOT/plot_pin_statistics.py" \
    --stats "$ALL_STATS" \
    --output "$PLOT_OUTPUT")

  if [ -n "$PIN_MIN" ]; then
    cmd+=(--pin-min "$PIN_MIN")
  fi
  if [ -n "$PIN_MAX" ]; then
    cmd+=(--pin-max "$PIN_MAX")
  fi

  "${cmd[@]}"
fi
